#!/usr/bin/env node
/**
 * VIAcast POTD Pre-Compute Pipeline
 * 
 * Generates projections for all POTD pool players using the same Savant data
 * and projection logic as the client-side engine. Outputs to src/potd-projections.json
 * which the tweet-potd.js script reads instead of running its own calculations.
 * 
 * Run: node scripts/precompute-potd.mjs
 * Runs automatically during build via package.json prebuild hook.
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join, resolve } from 'path';
import https from 'https';

const __dirname = dirname(fileURLToPath(import.meta.url));
// Try scripts/../ first, then cwd
let ROOT = join(__dirname, '..');
if (!existsSync(join(ROOT, 'src/savant_data.json'))) {
  ROOT = process.cwd();
}
if (!existsSync(join(ROOT, 'src/savant_data.json'))) {
  console.error('ERROR: Cannot find src/savant_data.json. Run from project root.');
  process.exit(1);
}

// ── LOAD DATA ───────────────────────────────────────────────────────────────
const savantData = JSON.parse(readFileSync(join(ROOT, 'src/savant_data.json'), 'utf-8'));
const pitcherSavant = JSON.parse(readFileSync(join(ROOT, 'src/pitcher_savant_data.json'), 'utf-8'));
console.log(`Loaded ${Object.keys(savantData).length} hitters, ${Object.keys(pitcherSavant).length} pitchers from Savant data`);

// ── CONSTANTS (mirrored from App.jsx) ───────────────────────────────────────
const LG_WOBA = 0.305;
const WOBA_SCALE = 1.25;
const LG_R_PER_PA = 0.115;

const LEVEL_TRANSLATION = {
  ROK:{factor:0.35,wrcAdj:-40,reliability:0.15},A:{factor:0.55,wrcAdj:-25,reliability:0.30},
  "A+":{factor:0.65,wrcAdj:-18,reliability:0.40},AA:{factor:0.78,wrcAdj:-10,reliability:0.60},
  AAA:{factor:0.90,wrcAdj:-5,reliability:0.80},MLB:{factor:1.0,wrcAdj:0,reliability:1.0},
};

const POS_ADJ_PER_600 = {C:-1,"1B":-12.5,"2B":2.5,"3B":2.5,SS:7.5,LF:-7.5,CF:2.5,RF:-5,DH:-17.5,Y:0,"10":0,"1":0};
const AGING_PEAKS = {C:27,"1B":29,"2B":28,"3B":28,SS:28,LF:28,CF:27,RF:28,DH:30,"1":29};
const AGING_DR = {C:0.042,"1B":0.035,"2B":0.038,"3B":0.036,SS:0.040,LF:0.035,CF:0.042,RF:0.035,DH:0.030,"1":0.032};

const IP_OVERRIDES = {
  "Zack Wheeler":120,"Shane McClanahan":130,"Shane Baz":100,
  "Walker Buehler":140,"Dustin May":130,"Mitch Keller":140,
  "Andrew Painter":100,"Hunter Greene":140,
};

// ── FV DATA (mirrored from App.jsx) ─────────────────────────────────────────
// Just the POTD pool players we care about
const FV_MAP = {
  "Konnor Griffin":70,"Samuel Basallo":65,"Kevin McGonigle":65,
  "Aidan Miller":55,"Roman Anthony":55,"Max Clark":60,
  "JJ Wetherholt":60,"Jackson Holliday":55,"Dylan Crews":55,
  "Evan Carter":55,"Colt Keith":50,"Jackson Chourio":55,
  "Roki Sasaki":60,"Paul Skenes":60,
};

const FV_BENCHMARKS = {
  70:{ops:.960,war:8.0,wrc:160},65:{ops:.880,war:5.5,wrc:140},
  60:{ops:.830,war:4.0,wrc:128},55:{ops:.785,war:2.8,wrc:118},
  50:{ops:.740,war:1.8,wrc:105},45:{ops:.710,war:1.0,wrc:98},
};

// ── POTD POOL ───────────────────────────────────────────────────────────────
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

const PITCHER_SET = new Set(["Paul Skenes","Tarik Skubal","Garrett Crochet","Roki Sasaki",
  "Corbin Burnes","Zack Wheeler","Chris Sale","Cole Ragans","Logan Webb","Dylan Cease"]);

// ── HELPERS ─────────────────────────────────────────────────────────────────
function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => { try { resolve(JSON.parse(data)); } catch(e) { reject(e); } });
    }).on('error', reject);
  });
}

function norm(s) { return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }

function findSavant(name) {
  const n = norm(name);
  for (const [id, p] of Object.entries(savantData)) {
    if (p.name && norm(p.name) === n) return p;
  }
  const parts = n.split(/\s+/).filter(p => p.length > 1);
  for (const [id, p] of Object.entries(savantData)) {
    if (p.name && parts.every(pt => norm(p.name).includes(pt))) return p;
  }
  return null;
}

function findPitcherSavant(name) {
  const n = norm(name);
  for (const [id, p] of Object.entries(pitcherSavant)) {
    if (p.name && norm(p.name) === n) return p;
  }
  const parts = n.split(/\s+/).filter(p => p.length > 1);
  for (const [id, p] of Object.entries(pitcherSavant)) {
    if (p.name && parts.every(pt => norm(p.name).includes(pt))) return p;
  }
  return null;
}

function estimateWOBA(obp, slg) {
  return obp * 0.72 + slg * 0.28;
}

// ── HITTER PROJECTION (mirrors App.jsx Statcast path) ───────────────────────
function projectHitter(sav, age, posCode, name) {
  const seasons = sav.seasons || {};
  const years = Object.keys(seasons).sort().reverse().slice(0, 3);
  const W = [0.55, 0.30, 0.15];
  
  let wxba=0, wxslg=0, wxwoba=0, wbrl=0, wk=0, wbb=0, wev=0, tw=0;
  for (let i = 0; i < years.length; i++) {
    const s = seasons[years[i]];
    const w = W[i] || 0.05;
    const pw = w * Math.min(1, (s.pa || 200) / 400);
    if (s.xba) { wxba += s.xba * pw; tw += pw; }
    if (s.xslg) wxslg += s.xslg * pw;
    if (s.xwoba) wxwoba += s.xwoba * pw;
    if (s.barrel_pct) wbrl += s.barrel_pct * pw;
    if (s.k_pct) wk += s.k_pct * pw;
    if (s.bb_pct) wbb += s.bb_pct * pw;
    if (s.avg_ev) wev += s.avg_ev * pw;
  }
  if (tw === 0) return null;
  
  const xba = wxba / tw;
  const xslg = (wxslg / tw) * 0.95; // SLG compression
  const xwoba = wxwoba / tw;
  const brl = wbrl / tw;
  const kPct = wk / tw;
  const bbPct = wbb / tw;
  
  const avg = Math.round(xba * 1000) / 1000;
  const obp = Math.round(Math.min(avg + 0.07 + bbPct * 0.8, avg + 0.12) * 1000) / 1000;
  const slg = Math.round(xslg * 1000) / 1000;
  const ops = Math.round((obp + slg) * 1000) / 1000;
  
  const woba = estimateWOBA(obp, slg);
  const wRCPlus = Math.round(((woba - LG_WOBA) / WOBA_SCALE + LG_R_PER_PA) / LG_R_PER_PA * 100);
  
  // Dev boost for young players
  let wrcFinal = wRCPlus;
  if (age <= 24) wrcFinal = Math.round(wRCPlus * (1 + (25 - age) * 0.015));
  
  // FV blend
  const fv = FV_MAP[name];
  if (fv && fv >= 50) {
    const bench = FV_BENCHMARKS[fv];
    if (bench) {
      // Blend toward FV benchmark for prospects with limited data
      const totalPA = Object.values(seasons).reduce((s, yr) => s + (yr.pa || 0), 0);
      const blend = Math.min(0.5, Math.max(0.1, 1 - totalPA / 1200));
      wrcFinal = Math.round(wrcFinal * (1 - blend) + bench.wrc * blend);
    }
  }
  
  const estPA = age <= 22 ? 450 : age <= 24 ? 550 : 600;
  const batRuns = ((wrcFinal - 100) / 100) * estPA * LG_R_PER_PA;
  
  // Baserunning
  const spd = sav.sprint_speed || 27;
  const bsrRuns = ((spd - 27) / 4) * 5 * (estPA / 600) * 0.75;
  
  // Defense
  const oaa = sav.oaa || 0;
  const defRuns = oaa * 0.85 * 0.80 * (estPA / 600);
  
  // Positional
  const posRuns = (POS_ADJ_PER_600[posCode] || 0) * (estPA / 600);
  const replacement = 20 * (estPA / 600);
  
  const baseWAR = Math.round(((batRuns + bsrRuns + defRuns + posRuns + replacement) / 9.5) * 10) / 10;
  
  // HR estimate
  const hr = Math.round(brl * estPA / 100 * 0.85);
  
  return {
    isPitcher: false,
    avg, obp, slg, ops, wRCPlus: wrcFinal, hr,
    baseWAR: Math.max(0, baseWAR),
    estPA,
  };
}

// ── PITCHER PROJECTION (mirrors App.jsx Statcast path) ──────────────────────
function projectPitcher(sav, age, name) {
  const seasons = sav.seasons || {};
  const years = Object.keys(seasons).sort().reverse().slice(0, 3);
  const W = [0.55, 0.30, 0.15];
  
  let wxera=0, wwhip=0, wk9=0, wbb9=0, wip=0, tw=0;
  for (let i = 0; i < years.length; i++) {
    const s = seasons[years[i]];
    const w = W[i] || 0.05;
    // IP derived from BFP (batters faced per 9 = ~3.8 per IP)
    const ip = s.ip || (s.bfp ? Math.round(s.bfp / 3.8) : 0) || (s.pa ? Math.round(s.pa / 3.8) : 0);
    if (ip === 0) continue;
    const pw = w * Math.min(1, ip / 120);
    if (s.xera) wxera += s.xera * pw;
    // Derive WHIP from xBA + BB approximation if not present
    const whip = s.whip || (s.xba ? s.xba * 3.5 + 0.35 : 1.20);
    wwhip += whip * pw;
    // K/9 and BB/9 from whiff% and walk estimates
    const k9 = s.k_per_9 || (s.whiff_pct ? s.whiff_pct * 0.36 : 8.0);
    const bb9 = s.bb_per_9 || (s.xba ? (1 - s.xba) * 1.5 : 3.0);
    wk9 += k9 * pw;
    wbb9 += bb9 * pw;
    wip += ip * pw;
    tw += pw;
  }
  if (tw === 0) return null;
  
  let era = Math.round(wxera / tw * 100) / 100;
  const whip = Math.round(wwhip / tw * 100) / 100;
  const k9 = Math.round(wk9 / tw * 10) / 10;
  const bb9 = Math.round(wbb9 / tw * 10) / 10;
  
  // FV blend for pitchers with small samples
  const fv = FV_MAP[name];
  if (fv && fv >= 55) {
    const totalBFP = Object.values(seasons).reduce((s, yr) => s + (yr.bfp || yr.pa || 0), 0);
    if (totalBFP < 800) {
      // Blend ERA toward FV benchmark (FV 60 ≈ 3.20 ERA, FV 55 ≈ 3.80)
      const fvERA = {70:2.50, 65:2.90, 60:3.20, 55:3.80}[fv] || 3.50;
      const blend = Math.min(0.6, Math.max(0.2, 1 - totalBFP / 1500));
      era = Math.round((era * (1 - blend) + fvERA * blend) * 100) / 100;
    }
  }
  
  const fip = Math.round((era * 0.85 + 0.5) * 100) / 100;
  
  let ip = Math.round(wip / tw);
  if (IP_OVERRIDES[name]) ip = IP_OVERRIDES[name];
  if (ip < 60) ip = 60;
  if (ip > 210) ip = 210;
  
  // WAR: 60% xERA + 40% FIP based
  const blendERA = era * 0.6 + fip * 0.4;
  const pitchWAR = Math.round(((4.50 - blendERA) / 9.5 * ip / 9 + ip / 9 * 0.12) * 10) / 10;
  
  return {
    isPitcher: true,
    era, fip, whip, k9, bb9, ip,
    baseWAR: Math.max(0, pitchWAR),
    k: Math.round(k9 * ip / 9),
    w: Math.round(ip / 9 * (1 - era / 9.5) * 0.55 + 5),
    l: Math.round(ip / 9 * (era / 9.5) * 0.55 + 4),
  };
}

// ── PLAYER METADATA (age/pos for players without API access) ────────────────
const PLAYER_META = {
  "Gunnar Henderson":{age:25,pos:"SS"},"Juan Soto":{age:27,pos:"RF"},"Bobby Witt Jr.":{age:25,pos:"SS"},
  "Shohei Ohtani":{age:31,pos:"DH"},"Aaron Judge":{age:34,pos:"RF"},"Elly De La Cruz":{age:24,pos:"SS"},
  "Corbin Carroll":{age:25,pos:"CF"},"Julio Rodriguez":{age:25,pos:"CF"},"Fernando Tatis Jr.":{age:27,pos:"RF"},
  "Bryce Harper":{age:33,pos:"1B"},"Mookie Betts":{age:33,pos:"SS"},"Kyle Tucker":{age:29,pos:"RF"},
  "Ronald Acuna Jr.":{age:28,pos:"RF"},"Corey Seager":{age:32,pos:"SS"},"Freddie Freeman":{age:36,pos:"1B"},
  "Mike Trout":{age:34,pos:"CF"},"Jackson Chourio":{age:21,pos:"CF"},"Adley Rutschman":{age:28,pos:"C"},
  "Yordan Alvarez":{age:28,pos:"DH"},"Riley Greene":{age:25,pos:"LF"},"Jackson Merrill":{age:22,pos:"CF"},
  "James Wood":{age:23,pos:"LF"},"Cal Raleigh":{age:29,pos:"C"},"Vladimir Guerrero Jr.":{age:27,pos:"1B"},
  "Rafael Devers":{age:29,pos:"3B"},"Jose Ramirez":{age:33,pos:"3B"},"Francisco Lindor":{age:32,pos:"SS"},
  "Kyle Schwarber":{age:33,pos:"DH"},"Trea Turner":{age:32,pos:"SS"},"Bo Bichette":{age:28,pos:"SS"},
  "Pete Alonso":{age:31,pos:"1B"},"Willy Adames":{age:30,pos:"SS"},"Anthony Volpe":{age:25,pos:"SS"},
  "CJ Abrams":{age:25,pos:"SS"},"Jarren Duran":{age:28,pos:"CF"},"Pete Crow-Armstrong":{age:24,pos:"CF"},
  "Steven Kwan":{age:28,pos:"LF"},"Michael Harris II":{age:25,pos:"CF"},"Colt Keith":{age:24,pos:"2B"},
  "Zach Neto":{age:24,pos:"SS"},"Matt Olson":{age:32,pos:"1B"},"Kerry Carpenter":{age:28,pos:"LF"},
  "Bryson Stott":{age:27,pos:"2B"},"Cody Bellinger":{age:30,pos:"CF"},"Maikel Garcia":{age:25,pos:"3B"},
  "Dansby Swanson":{age:32,pos:"SS"},"Marcus Semien":{age:35,pos:"2B"},"Alex Bregman":{age:32,pos:"3B"},
  "Manny Machado":{age:33,pos:"3B"},"Matt McLain":{age:25,pos:"SS"},
  // Prospects
  "Konnor Griffin":{age:19,pos:"SS"},"Samuel Basallo":{age:21,pos:"C"},"Kevin McGonigle":{age:21,pos:"2B"},
  "Max Clark":{age:20,pos:"CF"},"Roman Anthony":{age:21,pos:"LF"},"JJ Wetherholt":{age:23,pos:"2B"},
  "Jackson Holliday":{age:22,pos:"2B"},"Dylan Crews":{age:24,pos:"RF"},"Evan Carter":{age:23,pos:"LF"},
  "Aidan Miller":{age:22,pos:"3B"},
  // Pitchers
  "Paul Skenes":{age:23,pos:"1"},"Tarik Skubal":{age:29,pos:"1"},"Garrett Crochet":{age:25,pos:"1"},
  "Roki Sasaki":{age:24,pos:"1"},"Corbin Burnes":{age:31,pos:"1"},"Zack Wheeler":{age:35,pos:"1"},
  "Chris Sale":{age:37,pos:"1"},"Cole Ragans":{age:28,pos:"1"},"Logan Webb":{age:29,pos:"1"},
  "Dylan Cease":{age:30,pos:"1"},
};

// ── MAIN ────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`\n⚾ VIAcast POTD Pre-Compute Pipeline`);
  console.log(`   Processing ${POTD_POOL.length} players...\n`);
  
  const results = {};
  let success = 0, fail = 0;
  
  for (const name of POTD_POOL) {
    try {
      const meta = PLAYER_META[name];
      if (!meta) { console.log(`  ⚠️  ${name}: no metadata, skipping`); fail++; continue; }
      
      const isPitcher = PITCHER_SET.has(name) || meta.pos === "1";
      const age = meta.age;
      const posCode = meta.pos;
      
      let proj;
      if (isPitcher) {
        const sav = findPitcherSavant(name);
        if (sav) {
          proj = projectPitcher(sav, age, name);
        }
      } else {
        const sav = findSavant(name);
        if (sav) {
          proj = projectHitter(sav, age, posCode, name);
        }
      }
      
      if (proj) {
        results[name] = {
          name, age, pos: posCode,
          isPitcher,
          ...proj,
        };
        const label = isPitcher
          ? `${proj.era} ERA | ${proj.ip} IP | ${proj.baseWAR} fWAR`
          : `${proj.ops} OPS | ${proj.wRCPlus} wRC+ | ${proj.hr} HR | ${proj.baseWAR} fWAR`;
        console.log(`  ✅ ${name.padEnd(22)} ${label}`);
        success++;
      } else {
        console.log(`  ⚠️  ${name}: no Savant data, skipping`);
        fail++;
      }
    } catch (e) {
      console.log(`  ❌ ${name}: ${e.message}`);
      fail++;
    }
  }
  
  const outPath = join(ROOT, 'src', 'potd-projections.json');
  writeFileSync(outPath, JSON.stringify(results, null, 2));
  console.log(`\n✅ Wrote ${success} projections to src/potd-projections.json`);
  console.log(`   ${fail} players skipped (no data)\n`);
}

main().catch(e => { console.error(e); process.exit(1); });
