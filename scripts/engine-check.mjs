#!/usr/bin/env node
/**
 * VIAcast engine check — run before every deploy (CI runs it on push/PR and
 * before the nightly data refresh is committed).
 *
 * Runs the projection engine exactly as written in src/App.jsx over:
 *   1. every hitter in savant_data.json and every pitcher in pitcher_savant_data.json
 *   2. tests/engine-fixtures.json — real career splits for players who broke
 *      the engine before (young hitters, prospects, traded players, two-way)
 * and fails if any projection throws, comes back non-numeric, or lands outside
 * sane ranges. Opening Week 2026 shipped an engine that threw for 23 young
 * hitters ("tPA used before it was defined"); this check catches that class
 * of bug.
 *
 * Usage: node scripts/engine-check.mjs [--verbose] [--app=path/to/App.jsx]
 */
import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const VERBOSE = process.argv.includes('--verbose');
const APP = (process.argv.find(a => a.startsWith('--app=')) || '').slice(6) || join(ROOT, 'src/App.jsx');
const load = f => {
  const p = join(ROOT, 'src', f);
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : {};
};

// ── Extract the engine from App.jsx (everything above the COMPONENTS marker) ──
const DATA = {
  warDataJson: load('war_data.json'),
  baserunningDataJson: load('baserunning_data.json'),
  fgPitcherDataJson: load('fg_pitcher_data.json'),
  xwobaDataJson: load('xwoba_data.json'),
  savantDataJson: load('savant_data.json'),
  pitcherSavantJson: load('pitcher_savant_data.json'),
  arsenalDataJson: load('pitch_arsenal_data.json'),
  precomputedLeaderboard: {},
  liveLeaderboard: {},
};
const src = readFileSync(APP, 'utf-8');
const marker = src.indexOf('// ── COMPONENTS');
if (marker === -1) fail(['Cannot find the "// ── COMPONENTS" marker in src/App.jsx']);
const engineSrc = src.substring(0, marker)
  .replace(/^import\s+[\s\S]*?from\s+["'][^"']+["'];?/gm, '')
  .replace(/^import\s+["'][^"']+["'];?/gm, '')
  .replace(/^export\s+default\s+/gm, '')
  .replace(/^export\s+/gm, '')
  .replace(/inject\(\);?/g, '')
  .replace(/function VpDBadge[\s\S]*?^}/gm, 'function VpDBadge(){return null;}')
  .replace(/function FVBadge[\s\S]*?^}/gm, 'function FVBadge(){return null;}')
  .replace(/function LevelBadge[\s\S]*?^}/gm, 'function LevelBadge(){return null;}')
  .replace(/^const Pill\s*=[\s\S]*?;$/m, 'const Pill = () => null;')
  .replace(/return\s*\(\s*<[A-Za-z]/gm, 'return null; //');

let engine;
try {
  const names = Object.keys(DATA);
  engine = new Function(...names, '_', engineSrc + '\nreturn { projectPlayer, projectPitcher };')(
    ...names.map(n => DATA[n]), {});
} catch (e) {
  fail([`Engine failed to load: ${e.message}`]);
}

// ── Checks ─────────────────────────────────────────────────────────────────
const HIT_RANGES = { wRCPlus: [40, 220], ops: [0.4, 1.3], obp: [0.2, 0.55], slg: [0.2, 0.85], estPA: [0, 720], hr: [0, 70], baseWAR: [-4, 12] };
const PIT_RANGES = { era: [1, 8], fip: [1, 8], whip: [0.6, 2.2], k9: [2, 16], bb9: [0.5, 7], ip: [0, 230], baseWAR: [-4, 12] };
const problems = [];
const stats = { hitters: 0, pitchers: 0, hitNull: 0, pitNull: 0 };
const hitOut = [], pitOut = [];

function checkRanges(label, out, ranges) {
  for (const [k, [lo, hi]] of Object.entries(ranges)) {
    const v = Number(out[k]);
    if (!Number.isFinite(v)) problems.push(`${label}: ${k} is ${out[k]}`);
    else if (v < lo || v > hi) problems.push(`${label}: ${k} = ${v} outside ${lo}–${hi}`);
  }
}
function runHitter(label, splits, age, pos, name, id) {
  stats.hitters++;
  try {
    const out = engine.projectPlayer(splits, age, pos, name, id);
    if (!out) { stats.hitNull++; return null; }
    checkRanges(label, out, HIT_RANGES);
    hitOut.push(out);
    return out;
  } catch (e) { problems.push(`${label}: threw ${e.message}`); return null; }
}
function runPitcher(label, splits, age, name, id) {
  stats.pitchers++;
  try {
    const out = engine.projectPitcher(splits, age, name, id);
    if (!out) { stats.pitNull++; return; }
    checkRanges(label, out, PIT_RANGES);
    pitOut.push(out);
  } catch (e) { problems.push(`${label}: threw ${e.message}`); }
}

// 1. Sweep the data files (Statcast paths). Ages vary so aging code runs too.
const AGES = [21, 24, 27, 30, 33, 36];
Object.entries(DATA.savantDataJson).forEach(([id, p], i) => {
  if (!p?.seasons || !Object.keys(p.seasons).length) return;
  runHitter(`hitter ${p.name} (${id})`, [], AGES[i % AGES.length], ['2', '3', '4', '5', '6', '7', '8', '9', '10'][i % 9], p.name, Number(id));
});
Object.entries(DATA.pitcherSavantJson).forEach(([id, p], i) => {
  if (!p?.seasons || !Object.keys(p.seasons).length) return;
  runPitcher(`pitcher ${p.name} (${id})`, [], AGES[i % AGES.length], p.name, Number(id));
});

// 2. Fixture players with real career splits (MiLB + MLB, traded, two-way)
const fixPath = join(ROOT, 'tests/engine-fixtures.json');
const fixtures = existsSync(fixPath) ? JSON.parse(readFileSync(fixPath, 'utf-8')).players : [];
if (!fixtures.length) problems.push('tests/engine-fixtures.json is missing or empty');
for (const f of fixtures) {
  const label = `fixture ${f.name}`;
  if (f.hitting?.length) {
    const out = runHitter(label, f.hitting.filter(s => s.stat?.plateAppearances > 0), f.age, f.pos === 'Y' ? '10' : f.pos, f.name, f.id);
    if (!out && f.expectHitter) problems.push(`${label}: no hitter projection`);
  }
  if (f.pitching?.length) runPitcher(label, f.pitching, f.age, f.name, f.id);
}

// 3. Whole-population sanity: league-average regulars should look league average
const mean = a => a.reduce((s, x) => s + x, 0) / (a.length || 1);
const regulars = hitOut.filter(o => o.estPA >= 450);
const starters = pitOut.filter(o => o.ip >= 140);
const regWrc = mean(regulars.map(o => o.wRCPlus));
const stERA = mean(starters.map(o => o.era));
if (regulars.length < 50) problems.push(`only ${regulars.length} hitters projected for 450+ PA`);
else if (regWrc < 95 || regWrc > 118) problems.push(`average wRC+ of 450+ PA hitters is ${regWrc.toFixed(1)} (expected 95–118)`);
if (starters.length < 30) problems.push(`only ${starters.length} pitchers projected for 140+ IP`);
else if (stERA < 3.0 || stERA > 4.6) problems.push(`average ERA of 140+ IP starters is ${stERA.toFixed(2)} (expected 3.00–4.60)`);
const hitRate = 1 - stats.hitNull / Math.max(1, stats.hitters);
if (hitRate < 0.5) problems.push(`only ${(hitRate * 100).toFixed(0)}% of hitters got a projection`);

console.log(`Engine check: ${stats.hitters} hitter runs (${stats.hitNull} without projection), ` +
  `${stats.pitchers} pitcher runs (${stats.pitNull} without projection), ${fixtures.length} fixtures`);
console.log(`  450+ PA hitters: ${regulars.length}, avg wRC+ ${regWrc.toFixed(1)} | 140+ IP starters: ${starters.length}, avg ERA ${stERA.toFixed(2)}`);
if (problems.length) fail(problems);
console.log('✅ Engine check passed');

function fail(list) {
  console.error(`❌ Engine check failed (${list.length} problem${list.length === 1 ? '' : 's'}):`);
  list.slice(0, VERBOSE ? list.length : 40).forEach(p => console.error('  - ' + p));
  if (!VERBOSE && list.length > 40) console.error(`  ... and ${list.length - 40} more (use --verbose)`);
  process.exit(1);
}
