#!/usr/bin/env node
// scripts/scrape-fwar.mjs
// Fetches FanGraphs fWAR leaderboard via their API (no browser needed).
// Runs daily at 2am ET via GitHub Actions.
// Writes to src/live_leaderboard.json

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_PATH = path.join(__dirname, "..", "src", "live_leaderboard.json");
const YEAR = new Date().getFullYear();

// FanGraphs API: top 8 by fWAR
function fgUrl(stats, qual) {
  return `https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=${stats}&lg=all&qual=${qual}&season=${YEAR}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`;
}

// Headers that mimic a real browser — avoids most Cloudflare challenges
const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-US,en;q=0.9",
  "Referer": "https://www.fangraphs.com/leaders/major-league",
  "Origin": "https://www.fangraphs.com",
};

async function fetchFG(stats) {
  // Try qualified first, then all players
  for (const qual of ["y", "0"]) {
    const url = fgUrl(stats, qual);
    try {
      const res = await fetch(url, { headers: HEADERS, signal: AbortSignal.timeout(15000) });
      if (!res.ok) {
        console.log(`  ${stats} qual=${qual}: HTTP ${res.status}`);
        continue;
      }
      const ct = res.headers.get("content-type") || "";
      if (!ct.includes("json")) {
        console.log(`  ${stats} qual=${qual}: not JSON (${ct.slice(0, 50)})`);
        continue;
      }
      const data = await res.json();
      if (data?.data?.length > 0) {
        console.log(`  ✓ ${stats} qual=${qual}: ${data.data.length} rows`);
        return data;
      }
    } catch (err) {
      console.log(`  ${stats} qual=${qual}: ${err.code || err.cause?.code || err.message}`);
    }
  }
  return null;
}

// Fallback: MLB Stats API for basic WAR-like data (less accurate but always available)
async function fetchMLBFallback(group) {
  const url = `https://statsapi.mlb.com/api/v1/stats?stats=season&season=${YEAR}&group=${group}&gameType=R&sortStat=wins&order=desc&limit=8`;
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

function formatOutput(rawHitters, rawPitchers) {
  const parseTm = (t) => (t || "").replace(/<[^>]+>/g, "").trim();

  const hitters = (rawHitters?.data || []).slice(0, 8).map((p) => ({
    name: p.PlayerName || p.playerName || p.name || "Unknown",
    tm: parseTm(p.Team || p.team || p.TeamName || ""),
    war: +(p.WAR ?? p.war ?? 0).toFixed?.(1) || 0,
    hr: Math.round(p.HR || p.hr || 0),
    wrc: Math.round(p["wRC+"] || p.wrc || 0),
  }));

  const pitchers = (rawPitchers?.data || []).slice(0, 8).map((p) => ({
    name: p.PlayerName || p.playerName || p.name || "Unknown",
    tm: parseTm(p.Team || p.team || p.TeamName || ""),
    war: +(p.WAR ?? p.war ?? 0).toFixed?.(1) || 0,
    ip: +(p.IP ?? p.ip ?? 0).toFixed?.(1) || 0,
    k9: +(p["K/9"] ?? p.k9 ?? 0).toFixed?.(1) || 0,
    era: +(p.ERA ?? p.era ?? 0).toFixed?.(2) || 0,
  }));

  return { generated: new Date().toISOString(), season: YEAR, hitters, pitchers };
}

// ── MAIN ────────────────────────────────────────────────────────────────
(async () => {
  console.log(`\n🏟  Fetching FanGraphs ${YEAR} fWAR leaderboard...\n`);

  // Attempt 1: Direct FanGraphs API fetch (fast, no deps)
  let hitters = await fetchFG("bat");
  let pitchers = await fetchFG("pit");

  // Attempt 2: Retry once after a short delay (Cloudflare rate limit)
  if (!hitters || !pitchers) {
    console.log("\n→ Retrying in 5s...");
    await new Promise(r => setTimeout(r, 5000));
    if (!hitters) hitters = await fetchFG("bat");
    if (!pitchers) pitchers = await fetchFG("pit");
  }

  if (!hitters && !pitchers) {
    console.error("✗ No data fetched. FanGraphs may be blocking. Keeping existing file.");
    process.exit(1);
  }

  const output = formatOutput(hitters, pitchers);

  if (output.hitters.length === 0 && output.pitchers.length === 0) {
    console.error("✗ Formatted data empty. Keeping existing file.");
    process.exit(1);
  }

  fs.writeFileSync(OUT_PATH, JSON.stringify(output, null, 2));
  console.log(`\n✅ Wrote ${OUT_PATH}`);
  console.log(`   ${output.hitters.length} hitters, ${output.pitchers.length} pitchers`);
  if (output.hitters[0]) console.log(`   #1 hitter: ${output.hitters[0].name} — ${output.hitters[0].war} fWAR`);
  if (output.pitchers[0]) console.log(`   #1 pitcher: ${output.pitchers[0].name} — ${output.pitchers[0].war} fWAR`);
})();
