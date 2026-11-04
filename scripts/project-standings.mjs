#!/usr/bin/env node
/**
 * Projected standings + depth charts + free-agent board.
 *
 *   node scripts/project-standings.mjs        # reads src/precomputed_leaderboard.json
 *
 * Writes src/team_projections.json.
 *
 * How it works:
 *  - Each team's 40-man players (plus free agents who've signed there) fill a
 *    season's playing time: ~6,150 PA and ~1,450 IP (~880 by starters, the
 *    rest by relievers). Better players get their projected playing time first;
 *    whatever is left goes to replacement-level players (0 WAR).
 *  - A player's WAR scales with the playing time he's given.
 *  - Wins = 81 + (team WAR - league-average team WAR). One WAR is one win.
 * Run after scripts/project-season.mjs.
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");
const API = "https://statsapi.mlb.com/api/v1";
const TEAM_PA = 6150, SP_IP = 880, RP_IP = 570;

async function getJSON(url) {
  for (let i = 0; i < 3; i++) {
    try { const r = await fetch(url, { signal: AbortSignal.timeout(30000) }); if (r.ok) return r.json(); } catch {}
    await new Promise(r => setTimeout(r, 1000 * (i + 1)));
  }
  throw new Error(`fetch failed: ${url}`);
}
const r1 = x => Math.round(x * 10) / 10;

function allocate(players, budget, cap, rate) {
  // Highest WAR-per-unit first; each player capped at his projected playing time.
  const sorted = [...players].sort((a, b) => rate(b) - rate(a));
  let left = budget; const out = [];
  for (const p of sorted) {
    const give = Math.max(0, Math.min(cap(p), left));
    left -= give;
    out.push({ ...p, share: give });
  }
  return { players: out, replacement: Math.max(0, left) };
}

async function main() {
  const proj = JSON.parse(fs.readFileSync(path.join(ROOT, "src/precomputed_leaderboard.json"), "utf8"));
  const season = proj.season;
  const teamsRes = await getJSON(`${API}/teams?sportId=1&season=${season - 1}&hydrate=division,league`);
  const teams = (teamsRes.teams || []).map(t => ({
    id: t.id, abbr: t.abbreviation, name: t.teamName, fullName: t.name,
    league: t.league?.abbreviation || (t.league?.name?.startsWith("American") ? "AL" : "NL"),
    division: (t.division?.nameShort || t.division?.name || "").replace(/^(American|National) League /, ""),
  }));
  const byAbbr = Object.fromEntries(teams.map(t => [t.abbr, t]));

  const out = [];
  for (const t of teams) {
    const H = proj.hitters.filter(h => h.team === t.abbr && h.projPA > 0);
    const P = proj.pitchers.filter(p => p.team === t.abbr && p.projIP > 0);
    const hit = allocate(H, TEAM_PA, h => h.projPA, h => h.projWAR / h.projPA);
    const sp = allocate(P.filter(p => !p.isReliever), SP_IP, p => p.projIP, p => p.projWAR / p.projIP);
    // Starters who don't fit in the rotation can still pitch in relief.
    const spare = sp.players.filter(p => p.share < p.projIP).map(p => ({ ...p, projIP: Math.min(60, p.projIP - p.share), projWAR: p.projWAR * Math.min(60, p.projIP - p.share) / p.projIP * 0.8 }));
    const rp = allocate([...P.filter(p => p.isReliever), ...spare], RP_IP, p => p.projIP, p => p.projWAR / p.projIP);

    const hitters = hit.players.filter(p => p.share > 0).map(p => ({ id: p.id, name: p.name, pos: p.pos, age: p.age, pa: Math.round(p.share), war: r1(p.projWAR * p.share / p.projPA), wrc: p.projWRC, hr: Math.round(p.projHR * p.share / p.projPA) }));
    const rotation = sp.players.filter(p => p.share > 0).map(p => ({ id: p.id, name: p.name, age: p.age, ip: Math.round(p.share), war: r1(p.projWAR * p.share / p.projIP), era: p.projERA }));
    // Starters who also pitch in relief are listed once, in the rotation, with both workloads.
    const rotIdx = Object.fromEntries(rotation.map((p, i) => [p.id, i]));
    const bullpen = [];
    for (const p of rp.players.filter(p => p.share > 0)) {
      const war = p.projWAR * p.share / p.projIP;
      if (rotIdx[p.id] != null) { const r = rotation[rotIdx[p.id]]; r.ip += Math.round(p.share); r.war = r1(r.war + war); continue; }
      bullpen.push({ id: p.id, name: p.name, age: p.age, ip: Math.round(p.share), war: r1(war), era: p.projERA });
    }
    const batWAR = hitters.reduce((s, p) => s + p.war, 0);
    const pitWAR = [...rotation, ...bullpen].reduce((s, p) => s + p.war, 0);
    out.push({ ...t, batWAR: r1(batWAR), pitWAR: r1(pitWAR), war: r1(batWAR + pitWAR),
      replacementPA: Math.round(hit.replacement), replacementIP: Math.round(sp.replacement + rp.replacement),
      hitters, rotation, bullpen });
  }
  const avg = out.reduce((s, t) => s + t.war, 0) / out.length;
  for (const t of out) { t.wins = Math.round(81 + (t.war - avg)); t.losses = 162 - t.wins; }
  out.sort((a, b) => b.war - a.war);

  // Free-agent board: this offseason's class with projections.
  const fa = await getJSON(`${API}/people/freeAgents?season=${season - 1}`);
  const projById = Object.fromEntries([...proj.hitters, ...proj.pitchers].map(p => [p.id, p]));
  const board = (fa.freeAgents || []).map(f => {
    const p = projById[f.player.id];
    if (!p) return null;
    return { id: p.id, name: p.name, pos: p.pos, age: p.age, projWAR: p.projWAR,
      from: byAbbr[Object.keys(byAbbr).find(k => byAbbr[k].id === f.originalTeam?.id)]?.abbr || null,
      to: f.newTeam?.id ? (teams.find(t => t.id === f.newTeam.id)?.abbr || null) : null,
      note: f.notes || null, date: f.dateSigned || f.dateDeclared || null };
  }).filter(Boolean).sort((a, b) => b.projWAR - a.projWAR);

  const file = path.join(ROOT, "src", "team_projections.json");
  fs.writeFileSync(file, JSON.stringify({ generated: new Date().toISOString(), season,
    method: "Team playing time filled best-first from projections; leftover goes to replacement level. Wins = 81 + team WAR above league average.",
    teams: out, freeAgents: board }, null, 1));
  console.log(`Wrote ${file}`);
  for (const t of out.slice(0, 5)) console.log(`  ${t.abbr} ${t.wins}-${t.losses}  WAR ${t.war} (bat ${t.batWAR}, pit ${t.pitWAR})`);
  console.log(`  ... ${out[out.length - 1].abbr} ${out[out.length - 1].wins}-${out[out.length - 1].losses}`);
  console.log(`Free agents with projections: ${board.length} (${board.filter(b => !b.to).length} unsigned)`);
}
main().catch(e => { console.error(e); process.exit(1); });
