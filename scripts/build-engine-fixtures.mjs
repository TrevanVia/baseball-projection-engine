#!/usr/bin/env node
/**
 * Rebuilds tests/engine-fixtures.json from the MLB Stats API: career splits
 * (MLB + all MiLB levels) for players who exercise the engine's edge cases.
 * Re-run when you add a player to the list; commit the output.
 *
 * Usage: node scripts/build-engine-fixtures.mjs
 */
import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const API = 'https://statsapi.mlb.com/api/v1';
const SPORT_IDS = [1, 11, 12, 13, 14, 16];   // same levels the site queries

// Why each player is here
const PLAYERS = [
  // young hitters with 250-600 MLB PA (crashed the Opening Week 2026 engine)
  'Jacob Wilson', 'Roman Anthony', 'Nick Kurtz', 'Dillon Dingler', 'Drake Baldwin', 'Jackson Holliday', 'Junior Caminero',
  // graded prospects / MiLB translation path
  'Konnor Griffin', 'Kevin McGonigle', 'Samuel Basallo', 'JJ Wetherholt', 'Max Clark',
  // traded mid-season (combined + per-team rows)
  'Rafael Devers', 'Josh Naylor', 'Eugenio Suárez',
  // veterans, stars, two-way, part-timers
  'Aaron Judge', 'Freddie Freeman', 'Shohei Ohtani', 'Cal Raleigh', 'Bobby Witt Jr.', 'Nasim Nuñez',
  // pitchers: aces, injury returns, rookies, relievers
  'Tarik Skubal', 'Paul Skenes', 'Garrett Crochet', 'Zack Wheeler', 'Chris Sale', 'Cam Schlittler',
  'Jacob Misiorowski', 'Chase Burns', 'Bubba Chandler', 'Edwin Díaz', 'Mason Miller',
];

const get = async url => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
};
const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

const today = new Date();
const out = [];
for (const name of PLAYERS) {
  const found = await get(`${API}/people/search?names=${encodeURIComponent(name)}&sportIds=${SPORT_IDS.join(',')}`);
  const person = (found.people || []).find(p => norm(p.fullName) === norm(name)) || found.people?.[0];
  if (!person) { console.warn(`  not found: ${name}`); continue; }
  const full = (await get(`${API}/people/${person.id}`)).people[0];
  const splits = async group => (await Promise.all(SPORT_IDS.map(async sid => {
    const d = await get(`${API}/people/${person.id}/stats?stats=yearByYear&group=${group}&gameType=R&sportId=${sid}`);
    return (d.stats?.[0]?.splits || []).map(s => ({ season: s.season, numTeams: s.numTeams, stat: s.stat, _sportId: sid }));
  }))).flat();
  const pos = full.primaryPosition?.code;
  const [by, bm, bd] = (full.birthDate || '2000-01-01').split('-').map(Number);
  const age = today.getFullYear() - by - ((today.getMonth() + 1 < bm || (today.getMonth() + 1 === bm && today.getDate() < bd)) ? 1 : 0);
  const rec = { id: person.id, name: full.fullName, age, pos };
  if (pos !== '1') { rec.hitting = await splits('hitting'); rec.expectHitter = true; }
  if (pos === '1' || pos === 'Y') rec.pitching = await splits('pitching');
  out.push(rec);
  console.log(`  ${full.fullName}: ${(rec.hitting || []).length} hitting / ${(rec.pitching || []).length} pitching rows`);
}
mkdirSync(join(ROOT, 'tests'), { recursive: true });
writeFileSync(join(ROOT, 'tests/engine-fixtures.json'),
  JSON.stringify({ generated: today.toISOString().slice(0, 10), players: out }));
console.log(`Wrote ${out.length} fixtures to tests/engine-fixtures.json`);
