#!/usr/bin/env node
// scripts/scrape-fwar.mjs
// Fetches the fWAR leaderboard (FanGraphs WAR via the MLB Stats API).
// Runs daily at 2am ET via GitHub Actions.
// Writes to src/live_leaderboard.json

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_PATH = path.join(__dirname, "..", "src", "live_leaderboard.json");
const YEAR = new Date().getFullYear();

// fWAR leaders come from the MLB Stats API "sabermetrics" feed, which serves
// FanGraphs' own WAR (e.g. Crow-Armstrong 2026: 10.6192 on both). FanGraphs'
// site blocks GitHub's servers; MLB's API doesn't.
const API = "https://statsapi.mlb.com/api/v1/stats";

async function getSplits(kind, group, pool = "ALL") {
  const url = `${API}?stats=${kind}&group=${group}&season=${YEAR}&sportId=1&gameType=R&playerPool=${pool}&limit=3000`;
  for (let i = 0; i < 3; i++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(30000) });
      if (res.ok) return (await res.json()).stats?.[0]?.splits || [];
      console.log(`  ${group}/${kind}: HTTP ${res.status}`);
    } catch (err) { console.log(`  ${group}/${kind}: ${err.message}`); }
    await new Promise(r => setTimeout(r, 3000));
  }
  return null;
}

let TEAMS = null;
async function teamAbbr(ids) {
  if (!TEAMS) {
    const t = await fetch("https://statsapi.mlb.com/api/v1/teams?sportId=1").then(r => r.json()).catch(() => ({}));
    TEAMS = Object.fromEntries((t.teams || []).map(x => [x.id, x.abbreviation]));
  }
  const d = await fetch(`https://statsapi.mlb.com/api/v1/people?personIds=${ids.join(",")}&hydrate=currentTeam`).then(r => r.json()).catch(() => ({}));
  return Object.fromEntries((d.people || []).map(p => [p.id, TEAMS[p.currentTeam?.id] || ""]));
}

// Qualified players (like FanGraphs' default leaderboard); falls back to all
// players early in the season when few have qualified.
async function leaders(group) {
  let [saber, season] = await Promise.all([getSplits("sabermetrics", group, "QUALIFIED"), getSplits("season", group, "ALL")]);
  if (saber && saber.length < 8) saber = await getSplits("sabermetrics", group, "ALL");
  if (!saber || !season) return null;
  const stat = Object.fromEntries(season.map(s => [s.player.id, { ...s.stat, team: s.team?.abbreviation }]));
  return saber
    .filter(s => s.stat?.war != null && stat[s.player.id])
    .sort((a, b) => b.stat.war - a.stat.war)
    .slice(0, 8)
    .map(s => ({ id: s.player.id, name: s.player.fullName, war: s.stat.war, wrc: s.stat.wRcPlus, ...stat[s.player.id] }));
}

function existingGenerated() {
  try { return JSON.parse(fs.readFileSync(OUT_PATH, "utf8")).generated || "unknown date"; }
  catch { return "unknown date"; }
}

function ipToNum(ip) { const x = parseFloat(ip || 0); const w = Math.floor(x); return w + Math.round((x - w) * 10) / 3; }

// ── MAIN ────────────────────────────────────────────────────────────────
(async () => {
  console.log(`\n🏟  Fetching ${YEAR} fWAR leaders (MLB Stats API)...\n`);
  const [bat, pit] = await Promise.all([leaders("hitting"), leaders("pitching")]);

  if (!bat?.length || !pit?.length) {
    const msg = `Couldn't fetch ${YEAR} leaders from the MLB Stats API. Kept existing leaderboard from ${existingGenerated()}.`;
    console.log(`::warning title=fWAR not refreshed::${msg}`);
    if (process.env.GITHUB_STEP_SUMMARY) fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, `### fWAR leaderboard not refreshed\n\n${msg}\n`);
    process.exit(0);
  }

  const tm = await teamAbbr([...bat, ...pit].map(p => p.id));
  for (const p of [...bat, ...pit]) p.team = p.team || tm[p.id] || "";
  const output = {
    generated: new Date().toISOString(), season: YEAR,
    hitters: bat.map(p => ({ name: p.name, tm: p.team || "", war: +p.war.toFixed(1), hr: p.homeRuns || 0, wrc: Math.round(p.wrc || 0) })),
    pitchers: pit.map(p => ({ name: p.name, tm: p.team || "", war: +p.war.toFixed(1), ip: +parseFloat(p.inningsPitched || 0).toFixed(1),
                              k9: +parseFloat(p.strikeoutsPer9Inn || 0).toFixed(1), era: +parseFloat(p.era || 0).toFixed(2) })),
  };
  fs.writeFileSync(OUT_PATH, JSON.stringify(output, null, 2));
  console.log(`✅ Wrote ${OUT_PATH}`);
  console.log(`   #1 hitter: ${output.hitters[0].name} — ${output.hitters[0].war} fWAR`);
  console.log(`   #1 pitcher: ${output.pitchers[0].name} — ${output.pitchers[0].war} fWAR`);
})();
