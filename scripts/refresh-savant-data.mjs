#!/usr/bin/env node
/**
 * VIAcast Data Refresh Pipeline
 * 
 * Pulls fresh Statcast data from Baseball Savant CSV endpoints and regenerates
 * the JSON data files used by the projection engine.
 * 
 * Endpoints:
 *   1. Expected Statistics (xwOBA, xBA, xSLG) — hitters & pitchers
 *   2. Exit Velocity & Barrels (avg_ev, max_ev, ev50, barrel%, hard_hit%)
 *   3. Sprint Speed (sprint_speed, bolts, hp_to_1b)
 *   4. Outs Above Average (OAA, fielding_runs_prevented)
 *   5. Pitch Arsenal Stats (per-pitch run values, whiff%, usage)
 *   6. Pitcher xERA / expected stats
 * 
 * Usage:
 *   node scripts/refresh-savant-data.mjs                  # Current year
 *   node scripts/refresh-savant-data.mjs --years 2023,2024,2025  # Multiple years
 *   node scripts/refresh-savant-data.mjs --dry-run        # Preview without writing
 * 
 * Output:
 *   src/savant_data.json         — Hitter Statcast profiles
 *   src/pitcher_savant_data.json — Pitcher Statcast profiles
 *   src/baserunning_data.json    — Sprint speed & baserunning
 *   src/defense_data.json        — OAA & fielding runs (if exists)
 *   src/pitch_arsenal_data.json  — Per-pitch-type grades (NEW)
 *   src/park_factors.json        — Park factor adjustments (NEW)
 */

import { writeFileSync, readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(__dirname, '..', 'src');

// ── CONFIG ───────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const CURRENT_YEAR = new Date().getFullYear();
// Default: pull 3 most recent FULL seasons. If we're early in the year (before June),
// the current year won't have meaningful data yet, so use last 3 complete seasons.
const currentMonth = new Date().getMonth(); // 0-indexed
const latestFullYear = currentMonth < 5 ? CURRENT_YEAR - 1 : CURRENT_YEAR;
const YEARS = args.find(a => a.startsWith('--years='))
  ? args.find(a => a.startsWith('--years=')).split('=')[1].split(',').map(Number)
  : [latestFullYear - 2, latestFullYear - 1, latestFullYear];

console.log(`\n🔄 VIAcast Data Refresh Pipeline`);
console.log(`   Years: ${YEARS.join(', ')}`);
console.log(`   Dry run: ${DRY_RUN}\n`);

// ── CSV PARSER ───────────────────────────────────────────────────────────────
function parseCSV(text) {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return [];
  
  // Parse header — handle quoted fields
  const parseRow = (line) => {
    const fields = [];
    let current = '';
    let inQuote = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') { inQuote = !inQuote; continue; }
      if (ch === ',' && !inQuote) { fields.push(current.trim()); current = ''; continue; }
      current += ch;
    }
    fields.push(current.trim());
    return fields;
  };

  // Remove BOM
  const headerLine = lines[0].replace(/^\uFEFF/, '');
  const headers = parseRow(headerLine);
  
  return lines.slice(1).map(line => {
    const vals = parseRow(line);
    const obj = {};
    headers.forEach((h, i) => {
      const v = vals[i];
      // Try to parse as number
      const num = Number(v);
      obj[h] = v === '' || v === undefined ? null : (!isNaN(num) && v !== '' ? num : v);
    });
    return obj;
  });
}

// ── FETCH HELPER (uses curl for DNS compatibility) ───────────────────────────
import { execSync } from 'child_process';

async function fetchCSV(url, label) {
  try {
    const text = execSync(`curl -s -L --max-time 30 "${url}"`, { 
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024 
    });
    if (!text || text.startsWith('<!DOCTYPE') || text.startsWith('<html')) {
      console.log(`   ⚠️  ${label}: got HTML instead of CSV (endpoint may have changed)`);
      return [];
    }
    const rows = parseCSV(text);
    console.log(`   ✅ ${label}: ${rows.length} rows`);
    return rows;
  } catch (err) {
    console.log(`   ❌ ${label}: ${err.message?.substring(0, 80)}`);
    return [];
  }
}

// ── SAVANT ENDPOINTS ─────────────────────────────────────────────────────────
const ENDPOINTS = {
  expectedHitting: (year) =>
    `https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=batter&year=${year}&position=&team=&min=1&csv=true`,
  
  evBarrels: (year) =>
    `https://baseballsavant.mlb.com/leaderboard/statcast?type=batter&year=${year}&position=&team=&min=1&csv=true`,
  
  sprintSpeed: (year) =>
    `https://baseballsavant.mlb.com/leaderboard/sprint_speed?min_season=${year}&max_season=${year}&position=&team=&min=1&csv=true`,
  
  oaa: (year) =>
    `https://baseballsavant.mlb.com/leaderboard/outs_above_average?type=Fielder&year=${year}&team=&range=year&min=1&pos=&csv=true`,
  
  expectedPitching: (year) =>
    `https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=pitcher&year=${year}&position=&team=&min=1&csv=true`,
  
  pitchArsenal: (year) =>
    `https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats?type=pitcher&pitchType=&year=${year}&team=&min=1&csv=true`,
};

// ── EXTRACT PLAYER ID FROM "last_name, first_name" + player_id ───────────────
function getName(row) {
  const raw = row['last_name, first_name'] || '';
  const parts = raw.split(',').map(s => s.trim());
  return parts.length >= 2 ? `${parts[1]} ${parts[0]}` : raw;
}

// ── MAIN ─────────────────────────────────────────────────────────────────────
async function main() {
  // Load existing data to merge with (preserves manual overrides, MiLB data, etc.)
  let existingHitters = {};
  let existingPitchers = {};
  try {
    existingHitters = JSON.parse(readFileSync(resolve(SRC, 'savant_data.json'), 'utf-8'));
    existingHitters = existingHitters.default || existingHitters;
    console.log(`📂 Loaded existing hitter data: ${Object.keys(existingHitters).length} players`);
  } catch { console.log('📂 No existing hitter data found, starting fresh'); }
  try {
    existingPitchers = JSON.parse(readFileSync(resolve(SRC, 'pitcher_savant_data.json'), 'utf-8'));
    existingPitchers = existingPitchers.default || existingPitchers;
    console.log(`📂 Loaded existing pitcher data: ${Object.keys(existingPitchers).length} players`);
  } catch { console.log('📂 No existing pitcher data found, starting fresh'); }

  const hitters = { ...existingHitters };
  const pitchers = { ...existingPitchers };
  const sprintData = {};
  const oaaData = {};
  const arsenalData = {};

  for (const year of YEARS) {
    console.log(`\n── ${year} ────────────────────────────────────────`);

    // 1. Expected Hitting Stats (xwOBA, xBA, xSLG)
    const expHit = await fetchCSV(ENDPOINTS.expectedHitting(year), `Expected Hitting ${year}`);
    for (const row of expHit) {
      const id = String(row.player_id);
      if (!id || id === 'null') continue;
      if (!hitters[id]) hitters[id] = { name: getName(row), mlbam_id: row.player_id, seasons: {} };
      if (!hitters[id].seasons[year]) hitters[id].seasons[year] = {};
      const s = hitters[id].seasons[year];
      s.pa = row.pa;
      s.xwoba = row.est_woba;
      s.xba = row.est_ba;
      s.xslg = row.est_slg;
      s.woba = row.woba;
      s.ba = row.ba;
      s.slg = row.slg;
      s.xwoba_diff = row.est_woba_minus_woba_diff;
    }

    // 2. Exit Velocity & Barrels
    const evData = await fetchCSV(ENDPOINTS.evBarrels(year), `EV/Barrels ${year}`);
    for (const row of evData) {
      const id = String(row.player_id);
      if (!id || id === 'null') continue;
      if (!hitters[id]) hitters[id] = { name: getName(row), mlbam_id: row.player_id, seasons: {} };
      if (!hitters[id].seasons[year]) hitters[id].seasons[year] = {};
      const s = hitters[id].seasons[year];
      s.avg_ev = row.avg_hit_speed;
      s.max_ev = row.max_hit_speed;
      s.ev50 = row.ev50;
      s.barrel_pct = row.brl_percent;
      s.hard_hit_pct = row.ev95percent; // ev95percent = % of BBE >= 95mph
      s.sweet_spot_pct = row.anglesweetspotpercent;
      s.avg_la = row.avg_hit_angle;
      s.bbe = row.attempts;
    }

    // 3. Sprint Speed
    const sprint = await fetchCSV(ENDPOINTS.sprintSpeed(year), `Sprint Speed ${year}`);
    for (const row of sprint) {
      const id = String(row.player_id);
      if (!id || id === 'null') continue;
      // Attach to hitter profile
      if (hitters[id]) {
        hitters[id].sprint_speed = row.sprint_speed;
        hitters[id].hp_to_1b = row.hp_to_1b;
        hitters[id].bolts = row.bolts;
      }
      sprintData[id] = {
        name: getName(row),
        sprint_speed: row.sprint_speed,
        hp_to_1b: row.hp_to_1b,
        bolts: row.bolts,
        team: row.team,
        position: row.position,
      };
    }

    // 4. OAA (only need current year for defense)
    if (year === CURRENT_YEAR || year === CURRENT_YEAR - 1) {
      const oaa = await fetchCSV(ENDPOINTS.oaa(year), `OAA ${year}`);
      for (const row of oaa) {
        const id = String(row.player_id);
        if (!id || id === 'null') continue;
        if (!oaaData[id]) oaaData[id] = {};
        oaaData[id][year] = {
          name: getName(row),
          oaa: row.outs_above_average,
          frp: row.fielding_runs_prevented,
          pos: row.primary_pos_formatted,
          team: row.display_team_name,
        };
      }
    }

    // 5. Expected Pitching Stats
    const expPit = await fetchCSV(ENDPOINTS.expectedPitching(year), `Expected Pitching ${year}`);
    for (const row of expPit) {
      const id = String(row.player_id);
      if (!id || id === 'null') continue;
      if (!pitchers[id]) pitchers[id] = { name: getName(row), mlbam_id: row.player_id, seasons: {} };
      if (!pitchers[id].seasons[year]) pitchers[id].seasons[year] = {};
      const s = pitchers[id].seasons[year];
      s.xwoba = row.est_woba;
      s.xba = row.est_ba;
      s.xslg = row.est_slg;
      s.woba = row.woba;
      s.ba = row.ba;
      s.slg = row.slg;
      s.pa = row.pa;
    }

    // 6. Pitch Arsenal (per-pitch-type data for pitchers)
    const arsenal = await fetchCSV(ENDPOINTS.pitchArsenal(year), `Pitch Arsenal ${year}`);
    for (const row of arsenal) {
      const id = String(row.player_id);
      if (!id || id === 'null') continue;
      if (!arsenalData[id]) arsenalData[id] = { name: getName(row), pitches: {} };
      if (!arsenalData[id].pitches[year]) arsenalData[id].pitches[year] = [];
      arsenalData[id].pitches[year].push({
        type: row.pitch_type,
        name: row.pitch_name,
        usage: row.pitch_usage,
        rv100: row.run_value_per_100,
        rv: row.run_value,
        whiff: row.whiff_percent,
        k_pct: row.k_percent,
        put_away: row.put_away,
        xwoba: row.est_woba,
        xba: row.est_ba,
        xslg: row.est_slg,
        hard_hit: row.hard_hit_percent,
        pitches: row.pitches,
      });
    }

    // Rate limit: be nice to Savant servers
    await new Promise(r => setTimeout(r, 1500));
  }

  // ── SUMMARY ──────────────────────────────────────────────────────────────────
  console.log(`\n── SUMMARY ────────────────────────────────────────`);
  console.log(`   Hitters:        ${Object.keys(hitters).length}`);
  console.log(`   Pitchers:       ${Object.keys(pitchers).length}`);
  console.log(`   Sprint Speed:   ${Object.keys(sprintData).length}`);
  console.log(`   OAA:            ${Object.keys(oaaData).length}`);
  console.log(`   Pitch Arsenal:  ${Object.keys(arsenalData).length}`);

  if (DRY_RUN) {
    console.log(`\n🔍 Dry run — no files written.`);
    return;
  }

  // ── WRITE FILES ────────────────────────────────────────────────────────────
  console.log(`\n📝 Writing files...`);
  
  const write = (filename, data) => {
    const path = resolve(SRC, filename);
    writeFileSync(path, JSON.stringify(data, null, 0)); // compact JSON for smaller bundles
    const size = (JSON.stringify(data).length / 1024).toFixed(0);
    console.log(`   ✅ ${filename} (${size} KB)`);
  };

  write('savant_data.json', hitters);
  write('pitcher_savant_data.json', pitchers);
  write('pitch_arsenal_data.json', arsenalData);

  console.log(`\n✨ Data refresh complete! Run 'npm run build' to rebuild.\n`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
