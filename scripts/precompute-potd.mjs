#!/usr/bin/env node
/**
 * VIAcast POTD Pre-Compute Pipeline v2
 * 
 * Extracts the actual projection engine from App.jsx and runs it in Node.
 * No duplicate logic — uses the exact same code path as the site.
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import https from 'https';
import { createRequire } from 'module';

const __dirname = dirname(fileURLToPath(import.meta.url));
let ROOT = join(__dirname, '..');
if (!existsSync(join(ROOT, 'src/App.jsx'))) ROOT = process.cwd();

// ── LOAD DATA ───────────────────────────────────────────────────────────────
const SAVANT_DATA = JSON.parse(readFileSync(join(ROOT, 'src/savant_data.json'), 'utf-8'));
const PITCHER_SAVANT = JSON.parse(readFileSync(join(ROOT, 'src/pitcher_savant_data.json'), 'utf-8'));
const WAR_DATA_RAW = JSON.parse(readFileSync(join(ROOT, 'src/war_data.json'), 'utf-8'));
const BASERUNNING_DATA = JSON.parse(readFileSync(join(ROOT, 'src/baserunning_data.json'), 'utf-8'));
const FG_PITCHER_DATA = JSON.parse(readFileSync(join(ROOT, 'src/fg_pitcher_data.json'), 'utf-8'));
let WAR_DATA = {};
if (Array.isArray(WAR_DATA_RAW)) WAR_DATA_RAW.forEach(p => { if (p.player_id) WAR_DATA[p.player_id] = p; });
else WAR_DATA = WAR_DATA_RAW;
console.log(`Loaded: ${Object.keys(SAVANT_DATA).length} hitters, ${Object.keys(PITCHER_SAVANT).length} pitchers`);

// ── EXTRACT ENGINE FROM App.jsx ─────────────────────────────────────────────
const appSrc = readFileSync(join(ROOT, 'src/App.jsx'), 'utf-8');
const compIdx = appSrc.indexOf('// ── COMPONENTS');
if (compIdx === -1) { console.error('Cannot find COMPONENTS marker'); process.exit(1); }
let engineSrc = appSrc.substring(0, compIdx);

// Strip imports/exports and fix data references for Node context
engineSrc = engineSrc
  // Remove all import statements (including multi-line)
  .replace(/import\s+[\s\S]*?from\s+["'][^"']+["'];?/gm, '')
  .replace(/import\s+["'][^"']+["'];?/gm, '')
  .replace(/^export .*$/gm, '')
  // Remove inject() call from Vercel analytics
  .replace(/inject\(\);?/g, '')
  // Stub out JSX-containing functions (they return React elements we don't need in Node)
  .replace(/function VpDBadge[\s\S]*?^}/gm, 'function VpDBadge(){return null;}')
  .replace(/function FVBadge[\s\S]*?^}/gm, 'function FVBadge(){return null;}')
  .replace(/function LevelBadge[\s\S]*?^}/gm, 'function LevelBadge(){return null;}')
  .replace(/const Pill[\s\S]*?;/m, 'const Pill = () => null;')
  // Remove any remaining JSX return statements (safety net)
  .replace(/return\s*\(<[a-z]/gm, 'return null; // JSX stripped: (<')
  // Fix data references
  .replace(/const SAVANT_DATA = savantDataJson\.default \|\| savantDataJson;/, '')
  .replace(/const PITCHER_SAVANT = pitcherSavantJson\.default \|\| pitcherSavantJson;/, '')
  .replace(/const XWOBA_DATA = xwobaDataJson\.default \|\| xwobaDataJson;/, 'const XWOBA_DATA = {};')
  .replace(/const ARSENAL_DATA = arsenalDataJson\.default \|\| arsenalDataJson;/g, 'const ARSENAL_DATA = {};')
  .replace(/arsenalDataJson\.default \|\| arsenalDataJson/g, '{}')
  .replace(/let WAR_DATA = \{\};/, '')
  .replace(/precomputedLeaderboard\.default \|\| precomputedLeaderboard/g, '{}')
  .replace(/precomputedLeaderboard/g, '({})')
  .replace(/baserunningDataJson\.default \|\| baserunningDataJson/g, 'BASERUNNING_DATA')
  .replace(/fgPitcherDataJson\.default \|\| fgPitcherDataJson/g, 'FG_PITCHER_DATA')
  .replace(/warDataJson\.default \|\| warDataJson/g, 'WAR_DATA')
  .replace(/warDataJson/g, 'WAR_DATA')
  .replace(/fgPitcherDataJson/g, 'FG_PITCHER_DATA')
  .replace(/baserunningDataJson/g, 'BASERUNNING_DATA')
  .replace(/arsenalDataJson/g, '({})')
  .replace(/xwobaDataJson/g, '({})')
  .replace(/savantDataJson/g, 'SAVANT_DATA')
  .replace(/pitcherSavantJson/g, 'PITCHER_SAVANT');

let engine;
try {
  const fn = new Function(
    'SAVANT_DATA', 'PITCHER_SAVANT', 'WAR_DATA', 'BASERUNNING_DATA', 'FG_PITCHER_DATA',
    engineSrc + '\nreturn{projectPlayer,projectPitcher,projectForward,getPlayerFV};'
  );
  engine = fn(SAVANT_DATA, PITCHER_SAVANT, WAR_DATA, BASERUNNING_DATA, FG_PITCHER_DATA);
  console.log('Engine extracted from App.jsx ✅\n');
} catch (e) {
  console.error('Engine extraction failed:', e.message);
  const lineNum = e.stack?.match(/<anonymous>:(\d+)/)?.[1];
  if (lineNum) {
    const lines = engineSrc.split('\n');
    const n = parseInt(lineNum);
    console.error(`At line ${n} of extracted engine:`);
    for (let i = Math.max(0,n-3); i < Math.min(lines.length, n+2); i++) {
      console.error(`  ${i+1}${i+1===n?' →':'  '} ${lines[i]?.substring(0,150)}`);
    }
  }
  // Also dump the problematic area to a file for inspection
  writeFileSync(join(ROOT, '/tmp/engine_debug.js'), engineSrc);
  console.error('Full extracted engine written to /tmp/engine_debug.js');
  process.exit(1);
}

// ── POTD POOL + METADATA ────────────────────────────────────────────────────
const POTD_POOL = [
  "Gunnar Henderson","Juan Soto","Bobby Witt Jr.","Shohei Ohtani","Paul Skenes",
  "Aaron Judge","Konnor Griffin","Elly De La Cruz","Corbin Carroll","Julio Rodriguez",
  "Fernando Tatis Jr.","Bryce Harper","Mookie Betts","Samuel Basallo","Kyle Tucker",
  "Ronald Acuna Jr.","Corey Seager","Freddie Freeman","Mike Trout","Roki Sasaki",
  "Jackson Chourio","Adley Rutschman","Yordan Alvarez","Tarik Skubal","Garrett Crochet",
  "Riley Greene","Jackson Merrill","James Wood","Cal Raleigh","Kevin McGonigle",
  "Vladimir Guerrero Jr.","Rafael Devers","Jose Ramirez","Francisco Lindor","Kyle Schwarber",
  "Trea Turner","Bo Bichette","Pete Alonso","Willy Adames","Max Clark",
  "Anthony Volpe","CJ Abrams","Jarren Duran","Roman Anthony","JJ Wetherholt",
  "Jackson Holliday","Dylan Crews","Evan Carter","Corbin Burnes","Zack Wheeler",
  "Matt McLain","Dansby Swanson","Marcus Semien","Alex Bregman","Manny Machado",
  "Pete Crow-Armstrong","Steven Kwan","Michael Harris II","Chris Sale","Cole Ragans",
  "Logan Webb","Dylan Cease","Colt Keith","Zach Neto","Matt Olson",
  "Kerry Carpenter","Bryson Stott","Cody Bellinger","Maikel Garcia","Aidan Miller",
];
const PITCHERS = new Set(["Paul Skenes","Tarik Skubal","Garrett Crochet","Roki Sasaki",
  "Corbin Burnes","Zack Wheeler","Chris Sale","Cole Ragans","Logan Webb","Dylan Cease"]);
const META = {
  "Gunnar Henderson":{age:25,pos:"6"},"Juan Soto":{age:27,pos:"9"},"Bobby Witt Jr.":{age:25,pos:"6"},
  "Shohei Ohtani":{age:31,pos:"Y"},"Aaron Judge":{age:34,pos:"9"},"Elly De La Cruz":{age:24,pos:"6"},
  "Corbin Carroll":{age:25,pos:"8"},"Julio Rodriguez":{age:25,pos:"8"},"Fernando Tatis Jr.":{age:27,pos:"9"},
  "Bryce Harper":{age:33,pos:"3"},"Mookie Betts":{age:33,pos:"6"},"Kyle Tucker":{age:29,pos:"9"},
  "Ronald Acuna Jr.":{age:28,pos:"9"},"Corey Seager":{age:32,pos:"6"},"Freddie Freeman":{age:36,pos:"3"},
  "Mike Trout":{age:34,pos:"8"},"Jackson Chourio":{age:21,pos:"8"},"Adley Rutschman":{age:28,pos:"2"},
  "Yordan Alvarez":{age:28,pos:"Y"},"Riley Greene":{age:25,pos:"7"},"Jackson Merrill":{age:22,pos:"8"},
  "James Wood":{age:23,pos:"7"},"Cal Raleigh":{age:29,pos:"2"},"Vladimir Guerrero Jr.":{age:27,pos:"3"},
  "Rafael Devers":{age:29,pos:"5"},"Jose Ramirez":{age:33,pos:"5"},"Francisco Lindor":{age:32,pos:"6"},
  "Kyle Schwarber":{age:33,pos:"Y"},"Trea Turner":{age:32,pos:"6"},"Bo Bichette":{age:28,pos:"6"},
  "Pete Alonso":{age:31,pos:"3"},"Willy Adames":{age:30,pos:"6"},"Anthony Volpe":{age:25,pos:"6"},
  "CJ Abrams":{age:25,pos:"6"},"Jarren Duran":{age:28,pos:"8"},"Pete Crow-Armstrong":{age:24,pos:"8"},
  "Steven Kwan":{age:28,pos:"7"},"Michael Harris II":{age:25,pos:"8"},"Colt Keith":{age:24,pos:"4"},
  "Zach Neto":{age:24,pos:"6"},"Matt Olson":{age:32,pos:"3"},"Kerry Carpenter":{age:28,pos:"7"},
  "Bryson Stott":{age:27,pos:"4"},"Cody Bellinger":{age:30,pos:"8"},"Maikel Garcia":{age:25,pos:"5"},
  "Dansby Swanson":{age:32,pos:"6"},"Marcus Semien":{age:35,pos:"4"},"Alex Bregman":{age:32,pos:"5"},
  "Manny Machado":{age:33,pos:"5"},"Matt McLain":{age:25,pos:"6"},
  "Konnor Griffin":{age:19,pos:"6"},"Samuel Basallo":{age:21,pos:"2"},"Kevin McGonigle":{age:21,pos:"4"},
  "Max Clark":{age:20,pos:"8"},"Roman Anthony":{age:21,pos:"7"},"JJ Wetherholt":{age:23,pos:"4"},
  "Jackson Holliday":{age:22,pos:"4"},"Dylan Crews":{age:24,pos:"9"},"Evan Carter":{age:23,pos:"7"},
  "Aidan Miller":{age:22,pos:"5"},
  "Paul Skenes":{age:23,pos:"1"},"Tarik Skubal":{age:29,pos:"1"},"Garrett Crochet":{age:25,pos:"1"},
  "Roki Sasaki":{age:24,pos:"1"},"Corbin Burnes":{age:31,pos:"1"},"Zack Wheeler":{age:35,pos:"1"},
  "Chris Sale":{age:37,pos:"1"},"Cole Ragans":{age:28,pos:"1"},"Logan Webb":{age:29,pos:"1"},
  "Dylan Cease":{age:30,pos:"1"},
};

// ── FETCH CAREER STATS ──────────────────────────────────────────────────────
function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch(e) { reject(e); } });
    }).on('error', reject);
  });
}
function norm(s) { return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }

async function getCareer(name, isPitcher) {
  const url = `https://statsapi.mlb.com/api/v1/people/search?names=${encodeURIComponent(name)}&sportIds=1,11,12,13,14&limit=5`;
  const data = await fetchJSON(url);
  const people = data.people || [];
  const n = norm(name);
  const player = people.find(p => norm(p.fullName) === n) || people[0];
  if (!player) return null;
  const group = isPitcher ? 'pitching' : 'hitting';
  const statsData = await fetchJSON(`https://statsapi.mlb.com/api/v1/people/${player.id}/stats?stats=yearByYear&group=${group}`);
  return { id: player.id, splits: statsData.stats?.[0]?.splits || [] };
}

// ── RUN ─────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`⚾ VIAcast POTD Pre-Compute v2 — Real Engine`);
  console.log(`  ${POTD_POOL.length} players\n`);
  const results = {};
  let ok = 0, skip = 0;
  for (const name of POTD_POOL) {
    const m = META[name];
    if (!m) { skip++; continue; }
    try {
      const isPitch = PITCHERS.has(name);
      const c = await getCareer(name, isPitch);
      if (!c?.splits?.length) { console.log(`  ⚠️  ${name}: no career splits`); skip++; continue; }
      const base = isPitch
        ? engine.projectPitcher(c.splits, m.age, name, c.id)
        : engine.projectPlayer(c.splits.filter(s=>s.stat?.plateAppearances>0), m.age, m.pos, name, c.id);
      if (!base) { console.log(`  ⚠️  ${name}: engine null`); skip++; continue; }
      const p = isPitch ? {
        isPitcher:true, era:base.era, fip:base.fip, whip:base.whip, k9:base.k9, bb9:base.bb9,
        ip:base.ip, baseWAR:base.baseWAR, k:Math.round((base.k9||8)*(base.ip||150)/9), w:base.w, l:base.l,
      } : {
        isPitcher:false, avg:base.avg, obp:base.obp, slg:base.slg, ops:base.ops,
        wRCPlus:base.wRCPlus, hr:base.hr, baseWAR:base.baseWAR, estPA:base.estPA,
      };
      results[name] = {name, age:m.age, pos:m.pos, ...p};
      const lbl = isPitch
        ? `${p.era} ERA | ${p.ip} IP | ${p.baseWAR} fWAR`
        : `${p.ops} OPS | ${p.wRCPlus} wRC+ | ${p.hr} HR | ${p.baseWAR} fWAR`;
      console.log(`  ✅ ${name.padEnd(24)} ${lbl}`);
      ok++;
      await new Promise(r => setTimeout(r, 120));
    } catch (e) { console.log(`  ❌ ${name}: ${e.message}`); skip++; }
  }
  writeFileSync(join(ROOT, 'src', 'potd-projections.json'), JSON.stringify(results, null, 2));
  console.log(`\n✅ ${ok} projections written, ${skip} skipped`);
}
main().catch(e => { console.error(e); process.exit(1); });
