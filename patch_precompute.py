#!/usr/bin/env python3
"""
Pre-compute leaderboard + modify App.jsx to load from static JSON.
Run from project root.

This creates:
  1. src/precompute_leaderboard.mjs - Node script to generate projections
  2. Patches App.jsx to try loading precomputed data first
"""
import os, json

APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ══════════════════════════════════════════════════════════════════════
# STEP 1: Create the precompute Node.js script
# ══════════════════════════════════════════════════════════════════════

precompute_script = r'''#!/usr/bin/env node
/**
 * VIAcast Pre-compute Leaderboard
 * ================================
 * Fetches all MLB rosters + stats, runs projections, outputs JSON.
 * 
 * Usage: node src/precompute_leaderboard.mjs
 * Output: src/precomputed_leaderboard.json
 * 
 * Run nightly or before deploy to keep projections fresh.
 */

import { readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const API = "https://statsapi.mlb.com/api/v1";

// ── Load static data ─────────────────────────────────────────────────
console.log("Loading static data...");
const savantData = JSON.parse(readFileSync(join(__dirname, 'savant_data.json'), 'utf8'));
const pitcherData = JSON.parse(readFileSync(join(__dirname, 'pitcher_savant_data.json'), 'utf8'));
const warData = JSON.parse(readFileSync(join(__dirname, 'war_data.json'), 'utf8'));
const contractData = JSON.parse(readFileSync(join(__dirname, 'contract_data.json'), 'utf8'));
console.log(`  Savant: ${Object.keys(savantData).length} hitters`);
console.log(`  Pitchers: ${Object.keys(pitcherData).length} pitchers`);

// ── Aging params ─────────────────────────────────────────────────────
const AGING_PARAMS = {
  C:  { peak: 27, dr: 0.035, pa: -1.0 },
  "1B":{ peak: 29, dr: 0.030, pa: -12.5 },
  "2B":{ peak: 28, dr: 0.035, pa: 2.5 },
  "3B":{ peak: 28, dr: 0.033, pa: 2.5 },
  SS: { peak: 28, dr: 0.035, pa: 7.5 },
  LF: { peak: 28, dr: 0.033, pa: -7.5 },
  CF: { peak: 27, dr: 0.037, pa: 2.5 },
  RF: { peak: 28, dr: 0.034, pa: -5.0 },
  DH: { peak: 30, dr: 0.028, pa: -17.5 },
};
const POS_MAP = {"2":"C","3":"1B","4":"2B","5":"3B","6":"SS","7":"LF","8":"CF","9":"RF","10":"DH"};
function getAP(code) {
  return AGING_PARAMS[POS_MAP[code]||code] || { peak:28, dr:0.035, pa:0 };
}
function posLabel(c) {
  const map = {C:"C","2":"C","3":"1B","4":"2B","5":"3B","6":"SS","7":"LF","8":"CF","9":"RF","10":"DH","D":"DH","Y":"TWP","O":"OF"};
  return map[c]||c||"—";
}

// ── FV Lookup ────────────────────────────────────────────────────────
// Extract from App.jsx - simplified version
const FV_LOOKUP = {};
const FV_BY_NAME = {};
// Parse FV from App.jsx source
const appSrc = readFileSync(join(__dirname, 'App.jsx'), 'utf8');
const fvMatch = appSrc.match(/const FV_LOOKUP = \{([^}]+)\}/);
if (fvMatch) {
  const entries = fvMatch[1].matchAll(/(\d+)\s*:\s*(\d+)/g);
  for (const m of entries) FV_LOOKUP[m[1]] = parseInt(m[2]);
}
const fvNameMatch = appSrc.match(/const FV_BY_NAME = \{([^}]+)\}/);
if (fvNameMatch) {
  const entries = fvNameMatch[1].matchAll(/"([^"]+)"\s*:\s*(\d+)/g);
  for (const m of entries) FV_BY_NAME[m[1]] = parseInt(m[2]);
}
function getPlayerFV(id, name) {
  return FV_LOOKUP[id] || FV_BY_NAME[name] || null;
}

// ── Career WAR ───────────────────────────────────────────────────────
function getCareerWAR(id, name) {
  if (warData[id]) return warData[id];
  if (warData[name]) return warData[name];
  // Normalize name
  const norm = name?.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  if (norm && warData[norm]) return warData[norm];
  return null;
}

// ── Savant lookup ────────────────────────────────────────────────────
function getSavantPlayer(id, name) {
  if (savantData[id]) return savantData[id];
  for (const p of Object.values(savantData)) {
    if (p.name === name) return p;
  }
  return null;
}
function getPitcherSavant(id, name) {
  if (pitcherData[id]) return pitcherData[id];
  for (const p of Object.values(pitcherData)) {
    if (p.name === name) return p;
  }
  return null;
}

// ── Hitter projection (simplified port) ──────────────────────────────
function projectHitter(savP, age, posCode, name, id) {
  const S = savP.seasons || {}, yrs = Object.keys(S).sort().reverse();
  if (!yrs.length) return null;
  const W = [0.55, 0.30, 0.15];
  let wxw=0, wev=0, wbr=0, wxba=0, wxslg=0, tw1=0;
  let wbb=0, wk=0, tw2=0;
  yrs.forEach((yr, i) => {
    const s = S[yr], w = W[i] || 0.05;
    const pw = w * Math.min(1, (s.pa||0)/400);
    const pw2 = w * Math.min(1, (s.pa||0)/200);
    if (s.xwoba != null) { wxw += s.xwoba*pw; tw1 += pw; }
    if (s.avg_ev != null) wev += s.avg_ev*pw;
    if (s.barrel_pct != null) wbr += s.barrel_pct*pw;
    if (s.xba != null) wxba += s.xba*pw;
    if (s.xslg != null) wxslg += s.xslg*pw;
    if (s.bb_pct != null) { wbb += s.bb_pct*pw2; tw2 += pw2; }
    if (s.k_pct != null) { wk += s.k_pct*pw2; }
    else if (s.whiff_pct != null) { wk += s.whiff_pct*0.80*pw2; if(!tw2) tw2=pw2; }
  });
  if (tw1 === 0) return null;
  const pXw = wxw/tw1, pBrl = wbr/tw1, pXba = wxba/tw1||null, pXslg = wxslg/tw1||null;
  const pBB = tw2>0 ? wbb/tw2 : 0.08, pK = tw2>0 ? wk/tw2 : 0.22;
  
  // Trend
  let tb = 0;
  if (yrs.length >= 2) {
    const x0 = S[yrs[0]]?.xwoba, x1 = S[yrs[1]]?.xwoba;
    if (x0 != null && x1 != null) {
      const d1 = x0-x1;
      const x2 = yrs.length>=3 ? S[yrs[2]]?.xwoba : null;
      if (x2 != null && Math.sign(d1) === Math.sign(x1-x2) && d1>0) tb = d1*0.3;
      else tb = d1*0.15;
    }
  }
  const axw = Math.max(0.2, Math.min(0.5, pXw+tb));
  let db = 0;
  if (pK < 0.15) db += 3; else if (pK > 0.30) db -= 2;
  if (pBB > 0.12) db += 2;
  const rawWrc = Math.round(((axw-0.315)/0.01)*4.5+100+db);
  const ap = getAP(posCode), pk = ap.peak;
  let ageAdj = 0;
  if (age < pk) ageAdj = 1.5;
  else if (age === pk) ageAdj = 0;
  else if (age <= 32) ageAdj = -1.5;
  else ageAdj = -3.0;
  const wrc = Math.max(60, Math.min(195, rawWrc + Math.round(ageAdj)));
  const avgAgeF = age > 32 ? Math.max(0.97, 1-(age-32)*0.005) : 1.0;
  const avg = pXba ? Math.max(.18,Math.min(.34,pXba*avgAgeF)) : .248;
  const obp = Math.max(.26,Math.min(.45,avg+pBB*.85+.02));
  const slg = pXslg ? Math.max(.30,Math.min(.70,pXslg*avgAgeF)) : Math.max(.30,obp+.12);
  const ops = Math.max(.52,Math.min(1.15,obp+slg));
  const pa0 = S[yrs[0]]?.pa || 500;
  const ePA = Math.min(700, Math.max(200, pa0*0.97));
  const bat = ((wrc-100)/100)*ePA*0.115;
  const pos = ap.pa*(ePA/600), rep = 20*(ePA/600);
  const hr = Math.round(Math.max(0, pBrl/100*(ePA*0.75)*0.24));
  const fv = getPlayerFV(id, name);
  let war = (bat+pos+rep)/9.5;

  // Forward projection
  const yearsToPeak = Math.max(0, pk - age);
  const peakMult = yearsToPeak > 0 ? 1 + yearsToPeak * 0.05 : 1.0;
  const peakWAR = war * Math.min(2.5, peakMult);
  let cumWAR = 0;
  for (let yr = 0; yr < 10; yr++) {
    const a = age + yr;
    if (a > 42) break;
    const d = a - pk;
    let w;
    if (d <= 0) {
      const t = yearsToPeak > 0 ? Math.min(1, yr/yearsToPeak) : 1;
      w = war + (peakWAR - war) * t;
    } else {
      w = peakWAR * Math.max(0.25, 1 - ap.dr * d);
    }
    cumWAR += Math.max(0, w);
  }

  return {
    projWAR: Math.round(war*10)/10,
    cumWAR: Math.round(cumWAR*10)/10,
    projWRC: wrc, projOPS: Math.round(ops*1e3)/1e3,
    projAVG: Math.round(avg*1e3)/1e3, projOBP: Math.round(obp*1e3)/1e3,
    projSLG: Math.round(slg*1e3)/1e3, projHR: hr, peakAge: pk, fv,
  };
}

// ── Pitcher projection (simplified) ─────────────────────────────────
function projectPitcher(pSav, age, name, id) {
  const S = pSav.seasons || {}, yrs = Object.keys(S).sort().reverse();
  if (!yrs.length) return null;
  const W = [0.55, 0.30, 0.15], lat = S[yrs[0]] || {};
  let wxe=0, tw=0;
  yrs.forEach((yr, i) => {
    const s = S[yr], w = W[i]||0.05, pw = w*Math.min(1,(s.bfp||0)/300);
    if (s.xera != null) { wxe += s.xera*pw; tw += pw; }
  });
  if (tw === 0) return null;
  const pXera = wxe/tw;
  const bfp0 = lat.bfp || 0;
  const latIP = lat.ip_est || (bfp0 / 4.1);
  const isStarter = latIP > 100 || bfp0 > 450;
  const replLevel = isStarter ? 5.34 : 4.49;
  
  // Aging
  const pk = isStarter ? 27 : 28;
  let af = 1;
  if (age < pk) af = Math.pow(0.985, pk-age);
  else if (age <= 33) af = Math.pow(1.015, age-pk);
  else af = Math.pow(1.015, 33-pk) * Math.pow(1.03, age-33);
  
  const projERA = Math.max(1.50, Math.min(6.50, pXera * af));
  const ip = isStarter ? Math.max(140, Math.min(210, latIP*0.98)) : Math.min(75, Math.max(30, latIP*0.95));
  const war = Math.max(-1, ((replLevel - projERA)/9.5) * (ip/9));
  
  // Derive stats
  const whiff = lat.whiff_pct || 0.24;
  const kPct = whiff * 0.80;
  const k9 = Math.min(13.5, kPct * 9 / 0.22 * 9);
  const bb9 = Math.max(1.5, Math.min(6, 3.5));
  const whip = Math.max(0.80, Math.min(1.80, (projERA * 0.31 + 0.5)));
  const fip = projERA * 0.95 + 0.2;
  
  // Forward
  let cumWAR = 0;
  for (let yr = 0; yr < 10; yr++) {
    const a = age + yr; if (a > 42) break;
    const d = a - pk;
    let w;
    if (d <= 0) { const t = Math.max(0,pk-age)>0?Math.min(1,yr/Math.max(0,pk-age)):1; w=war*(1+(1.1-1)*t); }
    else w = war * Math.max(0.2, 1 - 0.035*d);
    cumWAR += Math.max(0, w);
  }
  
  return {
    projWAR: Math.round(war*10)/10, cumWAR: Math.round(cumWAR*10)/10,
    projERA: Math.round(projERA*100)/100, projFIP: Math.round(fip*100)/100,
    projWHIP: Math.round(whip*100)/100, projK9: Math.round(k9*10)/10,
    projBB9: Math.round(bb9*10)/10, projIP: Math.round(ip),
    projW: isStarter ? Math.round(ip/9*war*0.6+8) : 0,
    projSV: !isStarter ? Math.round(Math.max(0, war*12)) : 0,
    isReliever: !isStarter, fv: getPlayerFV(id, name),
  };
}

// ── Fetch helpers ────────────────────────────────────────────────────
async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

const TEAMS = {108:'LAA',109:'AZ',110:'BAL',111:'BOS',112:'CHC',113:'CIN',114:'CLE',115:'COL',116:'DET',117:'HOU',118:'KC',119:'LAD',120:'WSH',121:'NYM',133:'OAK',134:'PIT',135:'SD',136:'SEA',137:'SF',138:'STL',139:'TB',140:'TEX',141:'TOR',142:'MIN',143:'PHI',144:'ATL',145:'CWS',146:'MIA',147:'NYY',158:'MIL'};

// ── Main ─────────────────────────────────────────────────────────────
async function main() {
  console.log("\nFetching MLB rosters...");
  const allPlayers = [];
  const teamIds = Object.keys(TEAMS);
  
  for (let i = 0; i < teamIds.length; i += 6) {
    const batch = teamIds.slice(i, i+6);
    const results = await Promise.all(batch.map(async tid => {
      try {
        const data = await fetchJSON(`${API}/teams/${tid}/roster?rosterType=40Man&season=2026&hydrate=person`);
        return (data.roster||[]).map(r => {
          const p = r.person || {};
          p._teamAbbr = TEAMS[tid];
          return p;
        });
      } catch { return []; }
    }));
    allPlayers.push(...results.flat());
    process.stdout.write(`  ${Math.min(i+6, teamIds.length)}/${teamIds.length} teams\r`);
    await sleep(100);
  }
  console.log(`  ${allPlayers.length} players fetched`);

  const hitters = allPlayers.filter(p => p.primaryPosition?.code !== "1" && p.currentAge);
  const pitcherList = allPlayers.filter(p => p.primaryPosition?.code === "1" && p.currentAge);
  console.log(`  ${hitters.length} hitters, ${pitcherList.length} pitchers`);

  // Fetch 2025 stats in bulk via team stats endpoint
  console.log("\nFetching 2025 season stats...");
  const playerStats = {};
  for (let i = 0; i < teamIds.length; i += 6) {
    const batch = teamIds.slice(i, i+6);
    await Promise.all(batch.map(async tid => {
      try {
        const data = await fetchJSON(`${API}/teams/${tid}/stats?stats=byDateRange&season=2025&group=hitting&gameType=R&startDate=2025-01-01&endDate=2025-12-31&hydrate=person`);
        for (const split of (data.stats?.[0]?.splits || [])) {
          const pid = split.player?.id;
          if (pid) playerStats[pid] = split.stat;
        }
      } catch {}
    }));
    await sleep(100);
  }
  console.log(`  ${Object.keys(playerStats).length} hitting stat lines`);

  // Pitcher stats
  const pitcherStats = {};
  for (let i = 0; i < teamIds.length; i += 6) {
    const batch = teamIds.slice(i, i+6);
    await Promise.all(batch.map(async tid => {
      try {
        const data = await fetchJSON(`${API}/teams/${tid}/stats?stats=byDateRange&season=2025&group=pitching&gameType=R&startDate=2025-01-01&endDate=2025-12-31&hydrate=person`);
        for (const split of (data.stats?.[0]?.splits || [])) {
          const pid = split.player?.id;
          if (pid) pitcherStats[pid] = split.stat;
        }
      } catch {}
    }));
    await sleep(100);
  }
  console.log(`  ${Object.keys(pitcherStats).length} pitching stat lines`);

  // Project hitters
  console.log("\nProjecting hitters...");
  const hitterResults = [];
  for (const p of hitters) {
    const savP = getSavantPlayer(p.id, p.fullName);
    const totalMLBPA = savP ? Object.values(savP.seasons||{}).reduce((s,yr)=>s+(yr.pa||0),0) : 0;
    if (!savP || totalMLBPA < 250) continue; // Skip non-Statcast players for now

    const proj = projectHitter(savP, p.currentAge, p.primaryPosition?.code, p.fullName, p.id);
    if (!proj) continue;

    const s25 = playerStats[p.id];
    hitterResults.push({
      id: p.id, name: p.fullName,
      team: p._teamAbbr || "FA",
      pos: posLabel(p.primaryPosition?.code),
      age: p.currentAge,
      ...proj,
      careerWAR: getCareerWAR(p.id, p.fullName),
      lastAVG: s25?.avg ? parseFloat(s25.avg) : null,
      lastOPS: s25?.ops ? parseFloat(s25.ops) : null,
      lastHR: s25?.homeRuns ?? null,
      lastSB: s25?.stolenBases ?? null,
      lastPA: s25?.plateAppearances ?? null,
    });
  }
  console.log(`  ${hitterResults.length} hitter projections`);

  // Project pitchers
  console.log("Projecting pitchers...");
  const pitcherResults = [];
  for (const p of pitcherList) {
    const pSav = getPitcherSavant(p.id, p.fullName);
    if (!pSav || !Object.keys(pSav.seasons||{}).length) continue;

    const proj = projectPitcher(pSav, p.currentAge, p.fullName, p.id);
    if (!proj) continue;

    const lst = pitcherStats[p.id];
    pitcherResults.push({
      id: p.id, name: p.fullName,
      team: p._teamAbbr || "FA",
      pos: proj.isReliever ? "RP" : "SP",
      age: p.currentAge,
      ...proj,
      careerWAR: getCareerWAR(p.id, p.fullName),
      lastERA: lst?.era ? parseFloat(lst.era) : null,
      lastIP: lst?.inningsPitched ? parseFloat(lst.inningsPitched) : null,
      lastSO: lst?.strikeOuts ? parseInt(lst.strikeOuts) : null,
    });
  }
  console.log(`  ${pitcherResults.length} pitcher projections`);

  // Write output
  const output = {
    generated: new Date().toISOString(),
    version: "1.0",
    hitters: hitterResults.sort((a,b) => (b.projWAR||0) - (a.projWAR||0)),
    pitchers: pitcherResults.sort((a,b) => (b.projWAR||0) - (a.projWAR||0)),
  };

  const outPath = join(__dirname, 'precomputed_leaderboard.json');
  writeFileSync(outPath, JSON.stringify(output));
  const sizeMB = (JSON.stringify(output).length / 1024 / 1024).toFixed(2);
  console.log(`\nWrote ${outPath} (${sizeMB} MB)`);
  console.log(`  ${hitterResults.length} hitters, ${pitcherResults.length} pitchers`);
  console.log(`  Generated: ${output.generated}`);
}

main().catch(e => { console.error(e); process.exit(1); });
'''

with open("src/precompute_leaderboard.mjs", "w") as f:
    f.write(precompute_script)
print("Created src/precompute_leaderboard.mjs")

# ══════════════════════════════════════════════════════════════════════
# STEP 2: Patch App.jsx to load precomputed data
# ══════════════════════════════════════════════════════════════════════

# Add import for precomputed data at the top of the leaderboard
old_leaderboard_start = '''function Leaderboard({ onSelect }) {
  const [players, setPlayers] = useState([]);
  const [pitchers, setPitchers] = useState([]);
  const [mode, setMode] = useState("hitters");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [sortCol, setSortCol] = useState("projWAR");
  const [sortAsc, setSortAsc] = useState(false);
  const [posFilter, setPosFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [started, setStarted] = useState(false);'''

new_leaderboard_start = '''function Leaderboard({ onSelect }) {
  const [players, setPlayers] = useState([]);
  const [pitchers, setPitchers] = useState([]);
  const [mode, setMode] = useState("hitters");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [sortCol, setSortCol] = useState("projWAR");
  const [sortAsc, setSortAsc] = useState(false);
  const [posFilter, setPosFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [started, setStarted] = useState(false);
  const [precomputed, setPrecomputed] = useState(null);
  const [precomputedDate, setPrecomputedDate] = useState(null);

  // Try loading precomputed projections on mount
  useEffect(() => {
    import("./precomputed_leaderboard.json")
      .then(mod => {
        const data = mod.default || mod;
        if (data?.hitters?.length) {
          // Add _player stubs for click-to-project compatibility
          const h = data.hitters.map(p => ({
            ...p,
            _player: { id: p.id, fullName: p.name, currentAge: p.age,
              primaryPosition: { code: p.pos === "C" ? "2" : p.pos === "1B" ? "3" : p.pos === "2B" ? "4" : p.pos === "3B" ? "5" : p.pos === "SS" ? "6" : p.pos === "LF" ? "7" : p.pos === "CF" ? "8" : p.pos === "RF" ? "9" : p.pos === "DH" ? "10" : "10",
                abbreviation: p.pos },
              currentTeam: { abbreviation: p.team }, _teamAbbr: p.team },
          }));
          setPlayers(h);
          setPitchers((data.pitchers || []).map(p => ({
            ...p,
            fullData: { id: p.id, fullName: p.name, currentAge: p.age,
              primaryPosition: { code: "1", abbreviation: "P" },
              currentTeam: { abbreviation: p.team }, _teamAbbr: p.team },
          })));
          setPrecomputed(true);
          setPrecomputedDate(data.generated);
          setStarted(true);
        }
      })
      .catch(() => { /* No precomputed data available, user can load live */ });
  }, []);'''

if old_leaderboard_start in src:
    src = src.replace(old_leaderboard_start, new_leaderboard_start)
    changes += 1
    print("1. Added precomputed data loading to Leaderboard")

# Update the "not started" screen to show precomputed status
old_not_started = '''        <button onClick={loadAll} style={{
          marginTop: 20, padding: "10px 28px", borderRadius: 8, border: "none", cursor: "pointer",
          background: C.accent, color: "#fff", fontSize: 13, fontWeight: 700, fontFamily: F,
        }}>Load All Players &amp; Project</button>'''

new_not_started = '''        <button onClick={loadAll} style={{
          marginTop: 20, padding: "10px 28px", borderRadius: 8, border: "none", cursor: "pointer",
          background: C.accent, color: "#fff", fontSize: 13, fontWeight: 700, fontFamily: F,
        }}>Load All Players &amp; Project (Live)</button>'''

if old_not_started in src:
    src = src.replace(old_not_started, new_not_started)
    changes += 1
    print("2. Updated load button label")

# Add a "last updated" badge when precomputed data is shown
old_leaderboard_header = '''        <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>'''

new_leaderboard_header = '''        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>
          {precomputedDate && <span style={{fontSize:9,color:C.muted,fontFamily:F,padding:"2px 6px",borderRadius:4,background:`${C.green}10`,border:`1px solid ${C.green}20`}}>Updated {new Date(precomputedDate).toLocaleDateString()}</span>}
        </div>'''

if old_leaderboard_header in src:
    src = src.replace(old_leaderboard_header, new_leaderboard_header, 1)
    changes += 1
    print("3. Added 'Updated' date badge to leaderboard header")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes to App.jsx")
print()
print("Next steps:")
print("  1. Run: node src/precompute_leaderboard.mjs")
print("  2. Build and deploy")
print("  3. Leaderboard will load instantly from precomputed JSON")
print("  4. 'Load All Players (Live)' button still available for fresh data")
print("  5. Re-run precompute script weekly or before each deploy")
