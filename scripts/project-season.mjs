#!/usr/bin/env node
/**
 * VIAcast season projections — runs the SAME engine the site uses (src/engine.js).
 *
 *   node scripts/project-season.mjs                    # project PROJ_SEASON (2027) -> src/precomputed_leaderboard.json
 *   node scripts/project-season.mjs --season=2026 --backtest --out=/tmp/bt2026.json
 *
 * --backtest hides every data year >= season, so the engine sees only what it
 * would have known before Opening Day. That's how we grade the model honestly.
 *
 * Player pool: everyone with MLB Statcast data in the last 3 seasons who is
 * still active (on a 40-man roster or a free agent who played last year).
 * Ages are SEASON ages (age on July 1 of the projected season), not today's age.
 */
import fs from "fs";
import path from "path";
import os from "os";
import { fileURLToPath, pathToFileURL } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");
const args = Object.fromEntries(process.argv.slice(2).map(a => {
  const [k, v] = a.replace(/^--/, "").split("="); return [k, v ?? true];
}));
const API = "https://statsapi.mlb.com/api/v1";

// ── Load engine (bundled so Node can read its JSON imports) ──────────────
async function loadEngine() {
  let bundle = args["engine-bundle"];
  if (!bundle) {
    const { build } = await import("esbuild");
    bundle = path.join(os.tmpdir(), `viacast-engine-${process.pid}.mjs`);
    await build({ entryPoints: [path.join(ROOT, "src/engine.js")], bundle: true, platform: "node",
                  format: "esm", outfile: bundle, logLevel: "error" });
  }
  return import(pathToFileURL(path.resolve(bundle)).href);
}

async function getJSON(url) {
  for (let i = 0; i < 3; i++) {
    try { const r = await fetch(url, { signal: AbortSignal.timeout(30000) }); if (r.ok) return r.json(); } catch {}
    await new Promise(r => setTimeout(r, 1000 * (i + 1)));
  }
  throw new Error(`fetch failed: ${url}`);
}

function seasonAge(birthDate, season) {
  if (!birthDate) return null;
  const [y, m, d] = birthDate.split("-").map(Number);
  return season - y - ((m > 7 || (m === 7 && d > 1)) ? 1 : 0);
}

const TEAM_ABBR = {108:"LAA",109:"AZ",110:"BAL",111:"BOS",112:"CHC",113:"CIN",114:"CLE",115:"COL",116:"DET",117:"HOU",118:"KC",119:"LAD",120:"WSH",121:"NYM",133:"ATH",134:"PIT",135:"SD",136:"SEA",137:"SF",138:"STL",139:"TB",140:"TEX",141:"TOR",142:"MIN",143:"PHI",144:"ATL",145:"CWS",146:"MIA",147:"NYY",158:"MIL"};

async function fetchPeople(ids) {
  const out = {};
  const list = [...ids];
  for (let i = 0; i < list.length; i += 150) {
    const chunk = list.slice(i, i + 150).join(",");
    const d = await getJSON(`${API}/people?personIds=${chunk}&hydrate=currentTeam`);
    for (const p of d.people || []) out[p.id] = p;
  }
  return out;
}

async function main() {
  const E = await loadEngine();
  const season = Number(args.season || E.PROJ_SEASON);
  E.setProjSeason(season);
  if (args.tune) E.setTune(JSON.parse(args.tune));
  const backtest = !!args.backtest;

  // Hide data the engine shouldn't see.
  const cut = (obj) => {
    for (const p of Object.values(obj)) {
      if (!p?.seasons) continue;
      for (const y of Object.keys(p.seasons)) if (Number(y) >= season) delete p.seasons[y];
    }
  };
  cut(E.SAVANT_DATA); cut(E.PITCHER_SAVANT); cut(E.FG_PITCHER);

  // Candidate pool: anyone with Statcast data in the 3 seasons before `season`.
  const recent = (p) => Object.keys(p.seasons || {}).some(y => Number(y) >= season - 3);
  const hitIds = Object.entries(E.SAVANT_DATA).filter(([, p]) => recent(p)).map(([id]) => id);
  const pitIds = Object.entries(E.PITCHER_SAVANT).filter(([, p]) => recent(p)).map(([id]) => id);

  console.log(`Projecting ${season}${backtest ? " (backtest)" : ""}: ${hitIds.length} hitter / ${pitIds.length} pitcher candidates`);
  // --people-cache=file avoids refetching player bios on repeated backtest runs.
  let people;
  if (args["people-cache"] && fs.existsSync(args["people-cache"])) people = JSON.parse(fs.readFileSync(args["people-cache"], "utf8"));
  else {
    people = await fetchPeople(new Set([...hitIds, ...pitIds]));
    if (args["people-cache"]) fs.writeFileSync(args["people-cache"], JSON.stringify(people));
  }

  // Active filter. Backtest: whoever actually appeared in `season` or was projected that spring
  // (passed via --pool). Live: active players (retired players drop out of the API's active flag).
  let pool = null;
  if (args.pool) pool = new Set(JSON.parse(fs.readFileSync(args.pool, "utf8")).map(String));
  // Free agents show as inactive in the MLB API, so "played last season" also counts.
  const playedLast = new Set();
  if (!pool) {
    for (const g of ["hitting", "pitching"]) {
      const d = await getJSON(`${API}/stats?stats=season&group=${g}&season=${season - 1}&sportId=1&gameType=R&playerPool=ALL&limit=5000`);
      for (const sp of d.stats?.[0]?.splits || []) playedLast.add(String(sp.player.id));
    }
  }
  const isActive = (id) => pool ? pool.has(String(id)) : (people[id]?.active !== false || playedLast.has(String(id)));

  const hitters = [], pitchers = [];
  for (const id of hitIds) {
    const p = people[id]; if (!p || !isActive(id)) continue;
    const pos = p.primaryPosition?.code; if (pos === "1") continue;
    const age = seasonAge(p.birthDate, season); if (!age) continue;
    const proj = E.projectPlayer(null, age, pos, p.fullName, Number(id));
    if (!proj || proj.highestLevel !== "MLB") continue;
    const fwd = E.projectForward(proj, age, pos, 10);
    hitters.push({
      id: Number(id), name: p.fullName, team: TEAM_ABBR[p.currentTeam?.id] || p.currentTeam?.abbreviation || "FA",
      pos: E.posLabel(pos), age,
      projWAR: proj.baseWAR, cumWAR: Math.round(fwd.reduce((s, r) => s + Math.max(0, r.war), 0) * 10) / 10,
      projWRC: proj.wRCPlus, projOPS: proj.ops, projAVG: proj.avg, projOBP: proj.obp, projSLG: proj.slg,
      projHR: proj.hr, projPA: proj.estPA, peakAge: proj.peakAge, fv: E.getPlayerFV(Number(id), p.fullName),
      careerWAR: E.getCareerWAR(Number(id), p.fullName),
    });
  }
  for (const id of pitIds) {
    const p = people[id]; if (!p || !isActive(id)) continue;
    const age = seasonAge(p.birthDate, season); if (!age) continue;
    const proj = E.projectPitcher([], age, p.fullName, Number(id));
    if (!proj) continue;
    const fwd = E.projectPitcherForward(proj, age, 10);
    pitchers.push({
      id: Number(id), name: p.fullName, team: TEAM_ABBR[p.currentTeam?.id] || p.currentTeam?.abbreviation || "FA",
      pos: proj.isReliever ? "RP" : "SP", age,
      projWAR: proj.baseWAR, cumWAR: Math.round(fwd.reduce((s, r) => s + Math.max(0, r.war), 0) * 10) / 10,
      projERA: proj.era, projFIP: proj.fip, projWHIP: proj.whip, projK9: proj.k9, projBB9: proj.bb9,
      projIP: proj.ip, projW: proj.w, projSV: proj.sv, isReliever: proj.isReliever,
      fv: E.getPlayerFV(Number(id), p.fullName), careerWAR: E.getCareerWAR(Number(id), p.fullName),
    });
  }
  const byWAR = (a, b) => (b.projWAR || 0) - (a.projWAR || 0);
  const output = {
    generated: new Date().toISOString(), version: "2.0", season, backtest,
    hitters: hitters.sort(byWAR), pitchers: pitchers.sort(byWAR),
  };
  const out = args.out || path.join(ROOT, "src", "precomputed_leaderboard.json");
  fs.writeFileSync(out, JSON.stringify(output));
  if (args.quiet) return;
  console.log(`Wrote ${out}: ${hitters.length} hitters, ${pitchers.length} pitchers`);
  console.log("Top 5 hitters:", hitters.slice(0, 5).map(h => `${h.name} ${h.projWAR}`).join(", "));
  console.log("Top 5 pitchers:", pitchers.slice(0, 5).map(h => `${h.name} ${h.projWAR}`).join(", "));
}

main().catch(e => { console.error(e); process.exit(1); });
