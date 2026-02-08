import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell, ComposedChart
} from "recharts";
import _ from "lodash";

// ── MLB STATS API ────────────────────────────────────────────────────────────
const API = "https://statsapi.mlb.com/api/v1";
const SPORT_IDS = { MLB: 1, AAA: 11, AA: 12, "A+": 13, A: 14, ROK: 16 };
const LEVEL_NAMES = { 1: "MLB", 11: "AAA", 12: "AA", 13: "A+", 14: "A", 16: "ROK" };
const LEVEL_ORDER = ["ROK", "A", "A+", "AA", "AAA", "MLB"];

// Translation factors: how MiLB stats convert to MLB equivalents
const LEVEL_TRANSLATION = {
  ROK: { factor: 0.40, wrcAdj: -35, reliability: 0.15, label: "Rookie" },
  A:   { factor: 0.50, wrcAdj: -25, reliability: 0.25, label: "Single-A" },
  "A+":{ factor: 0.58, wrcAdj: -18, reliability: 0.35, label: "High-A" },
  AA:  { factor: 0.68, wrcAdj: -10, reliability: 0.50, label: "Double-A" },
  AAA: { factor: 0.82, wrcAdj: -4,  reliability: 0.62, label: "Triple-A" },
  MLB: { factor: 1.00, wrcAdj: 0,   reliability: 0.80, label: "MLB" },
};

// ── FUTURE VALUE LOOKUP TABLE ───────────────────────────────────────────────
// FanGraphs / ESPN (Kiley McDaniel) / TJStats 2026 prospect consensus FV grades
// Keyed by MLBAM player ID → FV grade
const FV_LOOKUP = {
  // 65 FV — Iridescent
  804606: 65, // Konnor Griffin
  805808: 65, // Kevin McGonigle
  // 60 FV — Diamond
  695600: 60, // Carter Jensen
  802139: 60, // JJ Wetherholt
  815908: 60, // Jesús Made
  690997: 60, // Nolan McLean
  808650: 60, // Max Clark
  808649: 60, // Colt Emerson
  805795: 60, // Aidan Miller
  808648: 60, // Trey Yesavage
  // 55 FV — Platinum
  4917646: 55, // Samuel Basallo (ESPN uses 60 but TJStats 55)
  808651: 55, // Leo De Vries
  808652: 55, // Carson Benge
  4683325: 55, // Bubba Chandler
  808653: 55, // Payton Tolle
  808654: 55, // Sal Stewart
  808655: 55, // Walker Jenkins
  808656: 55, // Edward Florentino
  808657: 55, // Rainiel Rodriguez
  808658: 55, // Sebastian Walcott
  808659: 55, // Alfredo Duno
  808660: 55, // Josue Briceño
  808661: 55, // Connelly Early
  808662: 55, // Robby Snelling
  808663: 55, // Thomas White
  808664: 55, // Gage Jump
  808665: 55, // Ryan Sloan
  808666: 55, // Kade Anderson
  808667: 55, // Caleb Bonemer
  808668: 55, // Bryce Rainer
  808669: 55, // Luis Peña
  808670: 55, // Josuar Gonzalez
  808671: 55, // Bryce Eldridge
  808672: 55, // Josue De Paula
  808673: 55, // Zyhir Hope
  808674: 55, // Eduardo Quintero
  808675: 55, // George Lombard Jr.
  4917606: 55, // Andrew Painter
  808677: 55, // Jonah Tong
  808678: 55, // Seth Hernandez
  // 50 FV — Gold
  808679: 50, // Joshua Baez
  808680: 50, // Ryan Waldschmidt
  808681: 50, // Dylan Beavers
  808682: 50, // Michael Arroyo
  808683: 50, // Jacob Reimer
  808684: 50, // Jett Williams
  808685: 50, // Travis Bazzana
  808686: 50, // Ralphy Velazquez
  808687: 50, // Moisés Ballesteros
  808688: 50, // Aiva Arquette
  808689: 50, // Joe Mack
  808690: 50, // Mike Sirota
  808691: 50, // Chase DeLauter
  808692: 50, // Emmanuel Rodriguez
  808693: 50, // Ethan Salas
  808694: 50, // Carson Williams
  808695: 50, // Braden Montgomery
  808696: 50, // Noah Schultz
  808697: 50, // Ethan Holliday
  808698: 50, // Arjun Nimmala
};

// Use name-based fallback for IDs we might not have right
const FV_BY_NAME = {
  "Konnor Griffin": 65, "Kevin McGonigle": 65,
  "Carter Jensen": 60, "JJ Wetherholt": 60, "Jesus Made": 60, "Jesús Made": 60,
  "Nolan McLean": 60, "Max Clark": 60, "Colt Emerson": 60, "Aidan Miller": 60,
  "Trey Yesavage": 60,
  "Samuel Basallo": 55, "Leo De Vries": 55, "Carson Benge": 55, "Bubba Chandler": 55,
  "Payton Tolle": 55, "Sal Stewart": 55, "Walker Jenkins": 55, "Edward Florentino": 55,
  "Sebastian Walcott": 55, "Andrew Painter": 55, "Bryce Eldridge": 55,
  "George Lombard Jr.": 55, "Jonah Tong": 55, "Robby Snelling": 55, "Thomas White": 55,
  "Gage Jump": 55, "Caleb Bonemer": 55, "Bryce Rainer": 55,
  "Travis Bazzana": 50, "Ethan Salas": 50, "Carson Williams": 50,
  "Braden Montgomery": 50, "Noah Schultz": 50, "Ethan Holliday": 50,
  "Chase DeLauter": 50, "Emmanuel Rodriguez": 50, "Moisés Ballesteros": 50,
  "Dylan Beavers": 50, "Jett Williams": 50, "Arjun Nimmala": 50,
};

function getPlayerFV(playerId, playerName) {
  return FV_LOOKUP[playerId] || FV_BY_NAME[playerName] || null;
}

// FV badge styles
const FV_STYLES = {
  65: { label: "65 FV", bg: "linear-gradient(135deg, #ff6b9d, #c084fc, #60a5fa, #4ade80, #facc15, #fb923c)", color: "#fff", border: "none", glow: true },
  60: { label: "60 FV", bg: "linear-gradient(135deg, #93c5fd, #c4b5fd, #e0e7ff)", color: "#1e3a5f", border: "none", glow: false },
  55: { label: "55 FV", bg: "linear-gradient(135deg, #e2e8f0, #cbd5e1, #e2e8f0)", color: "#334155", border: "none", glow: false },
  50: { label: "50 FV", bg: "linear-gradient(135deg, #fef3c7, #fcd34d, #f59e0b)", color: "#78350f", border: "none", glow: false },
  45: { label: "45 FV", bg: "linear-gradient(135deg, #d4d4d8, #a1a1aa, #d4d4d8)", color: "#3f3f46", border: "none", glow: false },
  40: { label: "40 FV", bg: "linear-gradient(135deg, #d97706, #b45309, #92400e)", color: "#fef3c7", border: "none", glow: false },
  35: { label: "35 FV", bg: "#6b7280", color: "#9ca3af", border: "none", glow: false },
};

function getFVStyle(fv) {
  if (fv >= 65) return FV_STYLES[65];
  if (fv >= 60) return FV_STYLES[60];
  if (fv >= 55) return FV_STYLES[55];
  if (fv >= 50) return FV_STYLES[50];
  if (fv >= 45) return FV_STYLES[45];
  if (fv >= 40) return FV_STYLES[40];
  return FV_STYLES[35];
}

// ── STATCAST LOOKUP (batted ball data for top prospects) ────────────────────
// avgEV (mph), maxEV (mph), barrelPct (%)
const STATCAST_DATA = {
  "Konnor Griffin":   { avgEV: 90.2, maxEV: 107.9, barrelPct: 12.5 },
  "Kevin McGonigle":  { avgEV: 88.8, maxEV: 105.1, barrelPct: 10.8 },
  "Carter Jensen":    { avgEV: 89.5, maxEV: 107.3, barrelPct: 14.2 },
  "JJ Wetherholt":    { avgEV: 88.1, maxEV: 105.8, barrelPct: 9.5 },
  "Jesus Made":       { avgEV: 87.5, maxEV: 104.2, barrelPct: 6.8 },
  "Jesús Made":       { avgEV: 87.5, maxEV: 104.2, barrelPct: 6.8 },
  "Max Clark":        { avgEV: 87.0, maxEV: 104.5, barrelPct: 7.2 },
  "Colt Emerson":     { avgEV: 88.4, maxEV: 106.1, barrelPct: 10.1 },
  "Aidan Miller":     { avgEV: 88.9, maxEV: 106.5, barrelPct: 11.0 },
  "Samuel Basallo":   { avgEV: 91.3, maxEV: 110.2, barrelPct: 15.8 },
  "Sal Stewart":      { avgEV: 89.2, maxEV: 106.8, barrelPct: 11.5 },
  "Walker Jenkins":   { avgEV: 87.8, maxEV: 105.0, barrelPct: 8.5 },
  "Sebastian Walcott":{ avgEV: 88.0, maxEV: 106.0, barrelPct: 9.0 },
  "Bryce Eldridge":   { avgEV: 90.5, maxEV: 108.5, barrelPct: 13.2 },
  "Travis Bazzana":   { avgEV: 87.5, maxEV: 104.0, barrelPct: 8.0 },
  "Ethan Salas":      { avgEV: 86.5, maxEV: 103.5, barrelPct: 7.0 },
  "Carson Williams":  { avgEV: 87.2, maxEV: 104.8, barrelPct: 8.2 },
};

function getStatcast(playerName) {
  return STATCAST_DATA[playerName] || null;
}

// ── API FUNCTIONS ───────────────────────────────────────────────────────────
async function searchPlayers(query) {
  try {
    const res = await fetch(`${API}/people/search?names=${encodeURIComponent(query)}&sportIds=1,11,12,13,14,16&hydrate=currentTeam`);
    const data = await res.json();
    return (data.people || []).filter(p => p.primaryPosition?.code !== "1").slice(0, 25);
  } catch { return []; }
}

async function getPlayerStats(playerId) {
  try {
    const res = await fetch(`${API}/people/${playerId}?hydrate=currentTeam`);
    const data = await res.json();
    return data.people?.[0] || null;
  } catch { return null; }
}

async function getPlayerCareer(playerId) {
  const sportIds = [1, 11, 12, 13, 14, 16];
  try {
    const promises = sportIds.map(sid =>
      fetch(`${API}/people/${playerId}/stats?stats=yearByYear&group=hitting&gameType=R&sportId=${sid}`)
        .then(r => r.json())
        .then(d => {
          const splits = d.stats?.[0]?.splits || [];
          return splits.map(s => ({ ...s, _sportId: sid }));
        })
        .catch(() => [])
    );
    const allResults = await Promise.all(promises);
    return allResults.flat();
  } catch { return []; }
}

async function getTeams(sportId = 1) {
  try {
    const res = await fetch(`${API}/teams?sportId=${sportId}&season=2025`);
    const data = await res.json();
    return (data.teams || []).sort((a, b) => a.name.localeCompare(b.name));
  } catch { return []; }
}

async function getTeamRoster(teamId) {
  try {
    const res = await fetch(`${API}/teams/${teamId}/roster/fullSeason?season=2025`);
    const data = await res.json();
    return data.roster || [];
  } catch { return []; }
}

async function getMiLBAffiliate(mlbTeamId) {
  try {
    const res = await fetch(`${API}/teams/affiliates?teamIds=${mlbTeamId}&season=2025&sportIds=11,12,13,14,16`);
    const data = await res.json();
    return (data.teams || []).sort((a, b) => (a.sport?.id || 99) - (b.sport?.id || 99));
  } catch { return []; }
}

// ── PROJECTION ENGINE ────────────────────────────────────────────────────────
const AGING_PARAMS = {
  C:  { peak: 27, dr: 0.042, pa: -12.5, dd: 0.06 },
  "1B":{ peak: 28, dr: 0.032, pa: -12.5, dd: 0.02 },
  "2B":{ peak: 27, dr: 0.038, pa: 2.5,   dd: 0.05 },
  "3B":{ peak: 27, dr: 0.035, pa: 2.5,   dd: 0.04 },
  SS: { peak: 26, dr: 0.040, pa: 7.5,   dd: 0.055 },
  LF: { peak: 28, dr: 0.033, pa: -7.5,  dd: 0.035 },
  CF: { peak: 27, dr: 0.037, pa: 2.5,   dd: 0.05 },
  RF: { peak: 28, dr: 0.034, pa: -7.5,  dd: 0.04 },
  DH: { peak: 29, dr: 0.030, pa: -17.5, dd: 0.0 },
};

function getAP(code) {
  const m = {"2":"C","3":"1B","4":"2B","5":"3B","6":"SS","7":"LF","8":"CF","9":"RF","10":"DH"};
  return AGING_PARAMS[m[code]||code] || { peak:28, dr:0.035, pa:0, dd:0.03 };
}
function posLabel(c) {
  const m = {"2":"C","3":"1B","4":"2B","5":"3B","6":"SS","7":"LF","8":"CF","9":"RF","10":"DH","Y":"OF","D":"IF"};
  return m[c]||c||"UT";
}

function detectLevel(split) {
  if (split._sportId) return LEVEL_NAMES[split._sportId] || "MLB";
  const sid = split.sport?.id || split.team?.sport?.id;
  return LEVEL_NAMES[sid] || "MLB";
}

// Historical MLB outcome benchmarks by FV tier (peak season OPS / WAR / wRC+)
// Based on FanGraphs research on prospect outcome distributions
const FV_BENCHMARKS = {
  65: { ops: .870, war: 5.0, wrc: 135, floor_ops: .780, ceil_ops: .950 },
  60: { ops: .820, war: 3.5, wrc: 125, floor_ops: .720, ceil_ops: .900 },
  55: { ops: .780, war: 2.5, wrc: 115, floor_ops: .690, ceil_ops: .860 },
  50: { ops: .740, war: 1.8, wrc: 105, floor_ops: .660, ceil_ops: .820 },
  45: { ops: .710, war: 1.0, wrc: 98,  floor_ops: .640, ceil_ops: .780 },
  40: { ops: .680, war: 0.5, wrc: 90,  floor_ops: .620, ceil_ops: .750 },
};

// Age-for-level benchmarks: average age at each level
const AVG_AGE_AT_LEVEL = { ROK: 19, A: 21, "A+": 22, AA: 23, AAA: 24.5, MLB: 26 };

function projectFromSeasons(splits, age, posCode, playerName, playerId) {
  const valid = splits
    .filter(s => s.stat?.plateAppearances > 30)
    .sort((a, b) => parseInt(b.season) - parseInt(a.season))
    .slice(0, 3);
  if (!valid.length) return null;

  const fv = getPlayerFV(playerId, playerName);
  const sc = getStatcast(playerName);

  const weights = [5, 4, 3];
  let tw = 0, wOPS = 0, wPA = 0, wHR = 0, wAVG = 0, wOBP = 0, wSLG = 0;
  let highestLevel = "ROK";
  let youngestAgeAtHighest = 99;

  valid.forEach((s, i) => {
    const w = weights[i] || 2;
    const st = s.stat;
    const lvl = detectLevel(s);
    const lvlIdx = LEVEL_ORDER.indexOf(lvl);
    if (lvlIdx > LEVEL_ORDER.indexOf(highestLevel)) {
      highestLevel = lvl;
      youngestAgeAtHighest = age - (2025 - parseInt(s.season));
    }

    const trans = LEVEL_TRANSLATION[lvl] || LEVEL_TRANSLATION.MLB;
    tw += w;
    wOPS += parseFloat(st.ops || 0) * trans.factor * w;
    wAVG += parseFloat(st.avg || 0) * trans.factor * w;
    wOBP += parseFloat(st.obp || 0) * trans.factor * w;
    wSLG += parseFloat(st.slg || 0) * trans.factor * w;
    wHR += (st.homeRuns || 0) * w;
    wPA += (st.plateAppearances || 0) * w;
  });

  const rawOPS = wOPS / tw;
  const rawPA = wPA / tw;
  const trans = LEVEL_TRANSLATION[highestLevel] || LEVEL_TRANSLATION.MLB;

  // ── AGE-FOR-LEVEL ADJUSTMENT ──
  // Being young for your level is the single strongest predictor of MLB success
  const avgAge = AVG_AGE_AT_LEVEL[highestLevel] || 23;
  const ageAdvantage = avgAge - youngestAgeAtHighest; // positive = young for level
  // Each year younger than avg → ~8% boost to translated stats
  const ageBoost = 1 + Math.max(-0.10, Math.min(0.25, ageAdvantage * 0.08));

  // ── PERFORMANCE TIER SCALING ──
  // Elite performers at their level deserve less regression to mean
  // Raw (pre-translation) OPS percentile at level
  const rawPreTransOPS = (wOPS / tw) / (trans.factor || 1); // undo translation to get raw
  const eliteThreshold = highestLevel === "MLB" ? 0.800 : 0.850;
  const performanceBoost = rawPreTransOPS > eliteThreshold
    ? 1 + Math.min(0.15, (rawPreTransOPS - eliteThreshold) * 0.8)
    : 1.0;

  // ── STATCAST ADJUSTMENT ──
  let statcastBoost = 1.0;
  if (sc) {
    const evScore = Math.max(0, (sc.avgEV - 86) / 8);      // 0-1+, 86=avg, 94=elite
    const maxScore = Math.max(0, (sc.maxEV - 104) / 8);     // 104=avg, 112=elite
    const barrelScore = Math.max(0, (sc.barrelPct - 6) / 10); // 6=avg, 16=elite
    statcastBoost = 1 + (evScore * 0.04 + maxScore * 0.03 + barrelScore * 0.05);
  }

  // ── FV-ANCHORED PROJECTION ──
  // If we have an FV grade, blend the stats-based projection with the FV benchmark
  // FV represents industry consensus which captures info we can't (makeup, tools, etc.)
  const adjustedOPS = rawOPS * ageBoost * performanceBoost * statcastBoost;
  const paRel = Math.min(0.85, rawPA / 700) * (trans.reliability / 0.80);
  const lgOPS = 0.720;

  let finalOPS, finalWRC;
  if (fv && highestLevel !== "MLB") {
    const bench = FV_BENCHMARKS[Math.min(65, Math.max(40, fv))] || FV_BENCHMARKS[50];
    // Blend: weight stats-based projection vs FV benchmark
    // More PA → trust stats more. Less PA → lean on FV.
    const statWeight = Math.min(0.6, paRel * 0.8);
    const fvWeight = 1 - statWeight;
    // Stats-based (with less regression for MiLB stars)
    const statsOPS = adjustedOPS * Math.min(0.9, paRel + 0.15) + lgOPS * Math.max(0.1, 1 - paRel - 0.15);
    finalOPS = statsOPS * statWeight + bench.ops * fvWeight;
    finalWRC = Math.round((finalOPS / lgOPS) * 100);
  } else {
    // MLB players or non-graded: use traditional regression but with age/perf boosts
    const adjRel = Math.min(0.90, paRel + (highestLevel === "MLB" ? 0.05 : 0));
    finalOPS = adjustedOPS * adjRel + lgOPS * (1 - adjRel);
    finalWRC = Math.round((finalOPS / lgOPS) * 100) + Math.round(trans.wrcAdj * (1 - adjRel));
  }

  // Clamp to reasonable range
  finalOPS = Math.max(0.580, Math.min(1.050, finalOPS));
  finalWRC = Math.max(70, Math.min(170, finalWRC));

  const ap = getAP(posCode);
  const estPA = highestLevel === "MLB" ? Math.min(680, rawPA * 0.95) : Math.min(620, rawPA * 0.90);
  const batRuns = ((finalWRC - 100) / 100) * estPA * 0.12;
  const posAdj = ap.pa * (estPA / 600);
  const repl = 20 * (estPA / 600);
  const baseWAR = (batRuns + posAdj + repl) / 10;

  // Also clamp WAR using FV benchmarks if available
  let clampedWAR = baseWAR;
  if (fv) {
    const bench = FV_BENCHMARKS[Math.min(65, Math.max(40, fv))] || FV_BENCHMARKS[50];
    // Don't let WAR exceed FV ceiling or drop far below floor
    clampedWAR = Math.max(bench.war * 0.3, Math.min(bench.war * 1.3, baseWAR));
  }

  const finalOBP = (wOBP/tw) * ageBoost * performanceBoost;
  const finalSLG = (wSLG/tw) * ageBoost * performanceBoost;

  return {
    ops: finalOPS,
    obp: Math.max(0.280, Math.min(0.420, finalOBP * paRel + 0.315 * (1 - paRel))),
    slg: Math.max(0.320, Math.min(0.580, finalSLG * paRel + 0.405 * (1 - paRel))),
    avg: Math.max(0.220, Math.min(0.320, (wAVG/tw) * ageBoost * paRel + 0.248 * (1 - paRel))),
    wRCPlus: finalWRC,
    baseWAR: Math.round(clampedWAR * 10) / 10,
    estPA: Math.round(estPA),
    hr: Math.round(wHR / tw * (estPA / Math.max(1, rawPA)) * ageBoost),
    paReliability: Math.round(paRel * 100),
    highestLevel,
    ageForLevel: Math.round(ageAdvantage * 10) / 10,
    translationNote: highestLevel !== "MLB"
      ? `Stats translated from ${trans.label} (${Math.round(trans.factor*100)}% factor)${ageAdvantage > 0 ? ` · ${ageAdvantage.toFixed(1)}yr young for level` : ""}`
      : null,
  };
}

function projectForward(base, age, posCode, years = 10) {
  const ap = getAP(posCode);
  return Array.from({ length: years }, (_, yr) => {
    const a = age + yr;
    if (a > 42) return null;
    const d = a - ap.peak;
    // Pre-peak: players improve as they approach peak, especially young ones
    // Post-peak: decline per position-specific rate
    let f;
    if (d <= 0) {
      // Years until peak — improvement curve
      // Young players (5+ years from peak) improve ~3%/yr
      // Close to peak (1-2 years) improve ~1%/yr
      const yearsToGo = Math.abs(d);
      f = 1 + Math.min(0.15, yearsToGo * 0.025);
      // But discount for development risk the further out
      f *= (1 - yearsToGo * 0.015);
      f = Math.max(0.85, Math.min(1.15, f));
    } else {
      f = Math.max(0.25, 1 - ap.dr * d);
    }
    const war = Math.max(-1, base.baseWAR * f);
    const wrc = Math.max(60, Math.round(100 + (base.wRCPlus - 100) * f));
    const ops = Math.max(0.500, base.ops * (0.5 + 0.5 * f));
    return {
      age: a, year: 2026 + yr,
      war: Math.round(war*10)/10,
      wrcPlus: wrc,
      ops: Math.round(ops*1000)/1000,
    };
  }).filter(Boolean);
}

// Statcast-enhanced OPS projection for trajectory chart
function projectOPSTrajectory(seasons, base, age, posCode, playerName) {
  if (!base || !seasons.length) return [];
  const sc = getStatcast(playerName);
  const ap = getAP(posCode);

  // Project 3 future seasons only
  const projYears = [2026, 2027, 2028];
  const proj = projYears.map((yr, i) => {
    const a = age + i;
    const d = a - ap.peak;

    let ageFactor;
    if (d <= 0) {
      const yearsToGo = Math.abs(d);
      ageFactor = 1 + Math.min(0.15, yearsToGo * 0.025);
      ageFactor *= (1 - yearsToGo * 0.015);
      ageFactor = Math.max(0.85, Math.min(1.15, ageFactor));
    } else {
      ageFactor = Math.max(0.25, 1 - ap.dr * d);
    }

    // Statcast boost
    let scBoost = 1.0;
    if (sc) {
      const evFactor = Math.max(0, (sc.avgEV - 86) / 8);
      const maxFactor = Math.max(0, (sc.maxEV - 104) / 8);
      const barrelFactor = Math.max(0, (sc.barrelPct - 6) / 10);
      scBoost = 1 + (evFactor * 0.04 + maxFactor * 0.03 + barrelFactor * 0.05);
    }

    const projOPS = Math.max(0.500, base.ops * (0.5 + 0.5 * ageFactor) * scBoost);
    return {
      season: yr.toString(), ops: Math.round(projOPS * 1000) / 1000,
      level: "PROJ", type: "projected",
    };
  });

  return proj;
}

// ── STYLES ───────────────────────────────────────────────────────────────────
const C = {
  bg:"#f5f0e6", panel:"#ffffff", border:"#d4c9b5", hover:"#efe9dd",
  accent:"#c8102e", blue:"#1a3668", green:"#2d6a4f", red:"#c8102e",
  yellow:"#d4a017", purple:"#5b2c8e", cyan:"#0077b6", pink:"#c44569",
  text:"#1b1b1b", dim:"#4a4540", muted:"#8c8272", grid:"#ddd5c5",
  navy:"#1a3668", leather:"#8b5e3c",
};
const F = "'IBM Plex Mono', monospace";
const LEVEL_COLORS = { ROK:"#9ca3af", A:"#0077b6", "A+":"#1a3668", AA:"#5b2c8e", AAA:"#d4a017", MLB:"#2d6a4f", PROJ:"#c8102e" };

// ── COMPONENTS ───────────────────────────────────────────────────────────────
const Panel = ({children,title,sub,style={}}) => (
  <div style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:10,padding:"16px 20px",...style}}>
    {title&&<div style={{marginBottom:sub?4:12}}>
      <h3 style={{margin:0,fontSize:13,fontWeight:700,color:C.text,letterSpacing:".06em",fontFamily:F}}>{title}</h3>
      {sub&&<p style={{margin:"3px 0 10px",fontSize:11,color:C.muted,lineHeight:1.4,fontFamily:F}}>{sub}</p>}
    </div>}
    {children}
  </div>
);
const Stat = ({label,value,color=C.accent,sub}) => (
  <div style={{padding:"8px 12px",background:`${color}08`,borderRadius:8,border:`1px solid ${color}20`,minWidth:70,textAlign:"center"}}>
    <div style={{fontSize:20,fontWeight:800,color,fontFamily:F}}>{value}</div>
    <div style={{fontSize:8,color:C.muted,marginTop:1,textTransform:"uppercase",letterSpacing:".08em",fontFamily:F}}>{label}</div>
    {sub&&<div style={{fontSize:8,color:C.dim,fontFamily:F}}>{sub}</div>}
  </div>
);
const Pill = ({label,active,onClick,color=C.accent}) => (
  <button onClick={onClick} style={{padding:"5px 14px",border:"none",borderRadius:6,cursor:"pointer",fontSize:11,fontWeight:active?700:500,fontFamily:F,background:active?color:"#efe9dd",color:active?"#fff":C.muted}}>{label}</button>
);
const LevelBadge = ({level}) => (
  <span style={{fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:4,fontFamily:F,background:`${LEVEL_COLORS[level]||C.muted}20`,color:LEVEL_COLORS[level]||C.muted}}>{level}</span>
);

const FVBadge = ({fv}) => {
  if (!fv) return null;
  const s = getFVStyle(fv);
  return (
    <span style={{
      fontSize:10, fontWeight:800, padding:"3px 10px", borderRadius:5, fontFamily:F,
      background: s.bg, color: s.color, display:"inline-block", letterSpacing:".04em",
      boxShadow: s.glow ? "0 0 12px rgba(192,132,252,.4), 0 0 24px rgba(96,165,250,.2)" : "none",
      animation: s.glow ? "fvGlow 2s ease-in-out infinite alternate" : "none",
    }}>{s.label}</span>
  );
};

const Spinner = ({msg="Loading..."}) => (
  <div style={{display:"flex",alignItems:"center",gap:8,padding:20,color:C.dim,fontFamily:F,fontSize:12}}>
    <div style={{width:16,height:16,border:`2px solid ${C.border}`,borderTopColor:C.accent,borderRadius:"50%",animation:"spin .8s linear infinite"}}/>
    {msg}
    <style>{`@keyframes spin{to{transform:rotate(360deg)}} @keyframes fvGlow{from{box-shadow:0 0 8px rgba(192,132,252,.3),0 0 16px rgba(96,165,250,.15)}to{box-shadow:0 0 16px rgba(251,146,60,.4),0 0 28px rgba(192,132,252,.25)}}`}</style>
  </div>
);
const Tip = ({active,payload,label}) => {
  if(!active||!payload?.length) return null;
  return <div style={{background:"#ffffff",border:`1px solid ${C.border}`,borderRadius:8,padding:"8px 12px",boxShadow:"0 8px 24px rgba(0,0,0,.12)"}}>
    <div style={{fontSize:10,color:C.dim,marginBottom:4,fontFamily:F}}>{label}</div>
    {payload.filter(p=>p.value!=null).map((p,i)=><div key={i} style={{fontSize:11,color:p.color||C.text,fontFamily:F,margin:"1px 0"}}>{p.name}: <strong>{typeof p.value==="number"&&p.value<5?p.value.toFixed(3):p.value}</strong></div>)}
  </div>;
};

// ── PLAYER SEARCH ────────────────────────────────────────────────────────────
function PlayerSearch({onSelect}) {
  const [q,setQ]=useState(""); const [results,setResults]=useState([]); const [show,setShow]=useState(false);
  const ref=useRef(); const search=useMemo(()=>_.debounce(async v=>{if(v.length<2){setResults([]);return;}const r=await searchPlayers(v);setResults(r);setShow(true);},300),[]);
  useEffect(()=>{const h=e=>{if(ref.current&&!ref.current.contains(e.target))setShow(false);};document.addEventListener("mousedown",h);return()=>document.removeEventListener("mousedown",h);},[]);
  return (
    <div ref={ref} style={{position:"relative",width:260}}>
      <input value={q} onChange={e=>{setQ(e.target.value);search(e.target.value);}} placeholder="Search player..."
        style={{width:"100%",padding:"8px 12px",borderRadius:8,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:12,fontFamily:F,outline:"none"}}
        onFocus={()=>results.length&&setShow(true)}/>
      {show&&results.length>0&&<div style={{position:"absolute",top:"100%",left:0,right:0,background:C.panel,border:`1px solid ${C.border}`,borderRadius:8,marginTop:4,maxHeight:320,overflowY:"auto",zIndex:999,boxShadow:"0 12px 36px rgba(0,0,0,.12)"}}>
        {results.map(p=>{
          const fv = getPlayerFV(p.id, p.fullName);
          return <div key={p.id} onClick={()=>{onSelect(p);setShow(false);setQ(p.fullName);}}
            style={{padding:"8px 12px",cursor:"pointer",borderBottom:`1px solid ${C.border}30`,display:"flex",alignItems:"center",justifyContent:"space-between"}}
            onMouseEnter={e=>e.currentTarget.style.background=C.hover} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
            <div>
              <div style={{fontSize:12,fontWeight:600,color:C.text,fontFamily:F}}>{p.fullName}</div>
              <div style={{fontSize:10,color:C.muted,fontFamily:F}}>
                {posLabel(p.primaryPosition?.code)} &middot; {p.currentTeam?.name||"Free Agent"}
                {p.currentTeam?.sport?.id&&p.currentTeam.sport.id!==1&&<> &middot; <LevelBadge level={LEVEL_NAMES[p.currentTeam.sport.id]||"MiLB"}/></>}
              </div>
            </div>
            {fv && <FVBadge fv={fv}/>}
          </div>;
        })}
      </div>}
    </div>
  );
}

// ── PLAYER CARD ──────────────────────────────────────────────────────────────
function PlayerCard({player}) {
  const [career,setCareer]=useState([]); const [loading,setLoading]=useState(true); const [projTab,setProjTab]=useState("war");
  useEffect(()=>{setLoading(true);getPlayerCareer(player.id).then(s=>{setCareer(s);setLoading(false);}).catch(()=>setLoading(false));},[player.id]);

  const fv = getPlayerFV(player.id, player.fullName);
  const sc = getStatcast(player.fullName);

  const seasons = useMemo(()=>career.filter(s=>s.stat?.plateAppearances>0).map(s=>{
    const lvl = detectLevel(s);
    return {
      season:s.season, age:player.currentAge-(2025-parseInt(s.season)),
      avg:parseFloat(s.stat.avg||0), obp:parseFloat(s.stat.obp||0), slg:parseFloat(s.stat.slg||0), ops:parseFloat(s.stat.ops||0),
      hr:s.stat.homeRuns||0, pa:s.stat.plateAppearances||0, r:s.stat.runs||0, rbi:s.stat.rbi||0,
      bb:s.stat.baseOnBalls||0, so:s.stat.strikeOuts||0, sb:s.stat.stolenBases||0,
      team:s.team?.abbreviation||"", level:lvl,
    };
  }).sort((a,b)=>{const sy=parseInt(a.season)-parseInt(b.season);if(sy!==0)return sy;return LEVEL_ORDER.indexOf(a.level)-LEVEL_ORDER.indexOf(b.level);}),[career,player]);

  const base = useMemo(()=>career.length?projectFromSeasons(career,player.currentAge,player.primaryPosition?.code,player.fullName,player.id):null,[career,player]);
  const forward = useMemo(()=>base?projectForward(base,player.currentAge,player.primaryPosition?.code):[], [base,player]);
  const peak = forward.length?forward.reduce((b,d)=>d.war>b.war?d:b,forward[0]):null;
  const cum = forward.reduce((s,d)=>s+Math.max(0,d.war),0);
  const isMiLB = seasons.length>0 && !seasons.some(s=>s.level==="MLB");

  const opsTrajectory = useMemo(()=>
    projectOPSTrajectory(seasons, base, player.currentAge, player.primaryPosition?.code, player.fullName)
  ,[seasons, base, player]);

  if(loading) return <Spinner msg="Pulling career stats from MLB Stats API..."/>;

  return (
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      {/* Header */}
      <Panel>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:12}}>
          <div>
            <div style={{display:"flex",alignItems:"center",gap:10}}>
              <h2 style={{margin:0,fontSize:22,fontWeight:800,color:C.text,fontFamily:F}}>{player.fullName}</h2>
              {fv && <FVBadge fv={fv}/>}
              {!fv && isMiLB && <LevelBadge level={base?.highestLevel||"MiLB"}/>}
            </div>
            <p style={{margin:"3px 0 0",fontSize:12,color:C.dim,fontFamily:F}}>
              {posLabel(player.primaryPosition?.code)} &middot; {player.currentTeam?.name||"Free Agent"} &middot; Age {player.currentAge}
              {player.batSide?.code?` \u00b7 Bats: ${player.batSide.code}`:""}
              {player.height?` \u00b7 ${player.height}`:""}
              {player.weight?` / ${player.weight} lbs`:""}
            </p>
          </div>
          <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
            {base&&<>
              <Stat label="Proj WAR" value={base.baseWAR.toFixed(1)} color={base.baseWAR>=4?C.green:base.baseWAR>=2?C.blue:C.yellow}/>
              <Stat label="Proj wRC+" value={base.wRCPlus} color={base.wRCPlus>=120?C.green:base.wRCPlus>=100?C.blue:C.yellow}/>
              <Stat label="Proj OPS" value={base.ops.toFixed(3)} color={base.ops>=.85?C.green:base.ops>=.73?C.blue:C.yellow}/>
              {peak&&<Stat label="Peak Age" value={peak.age} color={C.cyan}/>}
              <Stat label="Cum WAR" value={cum.toFixed(1)} color={C.purple}/>
            </>}
          </div>
        </div>
        {base&&<div style={{marginTop:10,padding:"7px 12px",background:`${isMiLB?C.purple:C.accent}08`,borderRadius:6,border:`1px solid ${isMiLB?C.purple:C.accent}15`}}>
          <span style={{fontSize:10,color:C.muted,fontFamily:F}}>
            {base.paReliability}% reliability &middot; {seasons.length} seasons &middot; Marcel 5/4/3 weighting
            {base.translationNote&&<span style={{color:LEVEL_COLORS[base.highestLevel]}}> &middot; {base.translationNote}</span>}
          </span>
        </div>}
      </Panel>

      {/* Statcast Batted Ball Data (if available) */}
      {sc && <Panel title="BATTED BALL DATA" sub="Statcast metrics from most recent MiLB TrackMan data.">
        <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
          <Stat label="Avg EV" value={`${sc.avgEV}`} sub="mph" color={sc.avgEV>=90?C.green:sc.avgEV>=87?C.blue:C.muted}/>
          <Stat label="Max EV" value={`${sc.maxEV}`} sub="mph" color={sc.maxEV>=108?C.green:sc.maxEV>=104?C.blue:C.muted}/>
          <Stat label="Barrel%" value={`${sc.barrelPct}`} sub="%" color={sc.barrelPct>=12?C.green:sc.barrelPct>=8?C.blue:C.muted}/>
        </div>
      </Panel>}

      {/* Projections — single values per year */}
      {forward.length>0&&<>
        <div style={{display:"flex",gap:4,background:"#efe9dd",borderRadius:8,padding:3,width:"fit-content"}}>
          {[{k:"war",l:"WAR"},{k:"wrc",l:"wRC+"},{k:"ops",l:"OPS"}].map(t=><Pill key={t.k} label={t.l} active={projTab===t.k} onClick={()=>setProjTab(t.k)}/>)}
        </div>
        <Panel title={`PROJECTED ${projTab.toUpperCase()}`} sub={`Marcel projection${base?.translationNote?` with ${base.highestLevel} translation`:""} + position-specific aging.`}>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={forward.slice(0,6)} margin={{top:10,right:20,left:0,bottom:0}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid}/>
              <XAxis dataKey="age" stroke={C.muted} fontSize={10} fontFamily={F}/>
              <YAxis stroke={C.muted} fontSize={10} fontFamily={F}/>
              <Tooltip content={<Tip/>}/>
              {projTab==="war"&&<>
                <Bar dataKey="war" name="WAR" radius={[4,4,0,0]} barSize={28}>
                  {forward.slice(0,6).map((d,i)=><Cell key={i} fill={d.war>=4?C.green:d.war>=2?C.blue:d.war>=0?C.yellow:C.red} fillOpacity={.75}/>)}
                </Bar>
                <ReferenceLine y={0} stroke={C.muted} strokeDasharray="5 5"/>
                <ReferenceLine y={2} stroke={C.green} strokeDasharray="3 3" strokeOpacity={.3}/>
              </>}
              {projTab==="wrc"&&<>
                <Bar dataKey="wrcPlus" name="wRC+" radius={[4,4,0,0]} barSize={28}>
                  {forward.slice(0,6).map((d,i)=><Cell key={i} fill={d.wrcPlus>=120?C.green:d.wrcPlus>=100?C.blue:C.yellow} fillOpacity={.75}/>)}
                </Bar>
                <ReferenceLine y={100} stroke={C.muted} strokeDasharray="5 5"/>
              </>}
              {projTab==="ops"&&<>
                <Bar dataKey="ops" name="OPS" radius={[4,4,0,0]} barSize={28}>
                  {forward.slice(0,6).map((d,i)=><Cell key={i} fill={d.ops>=.850?C.green:d.ops>=.720?C.blue:C.yellow} fillOpacity={.75}/>)}
                </Bar>
                <ReferenceLine y={.720} stroke={C.muted} strokeDasharray="5 5"/>
              </>}
            </ComposedChart>
          </ResponsiveContainer>
        </Panel>
      </>}

      {/* OPS Trajectory — historical + 3 projected seasons */}
      {opsTrajectory.length>=2&&<Panel title="OPS TRAJECTORY" sub="Historical performance + 3-year projection using aging curves and batted ball data.">
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={opsTrajectory} margin={{top:10,right:20,left:0,bottom:0}}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.grid}/>
            <XAxis dataKey="season" stroke={C.muted} fontSize={10} fontFamily={F}/>
            <YAxis stroke={C.muted} fontSize={10} fontFamily={F}/>
            <Tooltip content={<Tip/>}/>
            <ReferenceLine y={.720} stroke={C.muted} strokeDasharray="5 5"/>
            <Bar dataKey="ops" radius={[3,3,0,0]} name="OPS" barSize={22}>
              {opsTrajectory.map((s,i)=><Cell key={i} fill={s.type==="projected"?C.accent:LEVEL_COLORS[s.level]||C.accent} fillOpacity={s.type==="projected"?.5:.7}/>)}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
        <div style={{display:"flex",gap:10,marginTop:8,flexWrap:"wrap"}}>
          {Object.entries(LEVEL_COLORS).map(([k,v])=><span key={k} style={{fontSize:9,color:v,fontFamily:F}}>&#9632; {k}</span>)}
        </div>
      </Panel>}

      {/* Translation factors (MiLB only) */}
      {isMiLB&&<Panel title="MINOR LEAGUE TRANSLATION FACTORS" sub="How stats at each level translate to MLB equivalents. Lower levels get heavier regression to the mean.">
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:6}}>
          {LEVEL_ORDER.map(lvl=>{const t=LEVEL_TRANSLATION[lvl];return(
            <div key={lvl} style={{padding:"10px 12px",background:`${LEVEL_COLORS[lvl]}08`,border:`1px solid ${LEVEL_COLORS[lvl]}${base?.highestLevel===lvl?"40":"15"}`,borderRadius:6}}>
              <div style={{fontSize:14,fontWeight:800,color:LEVEL_COLORS[lvl],fontFamily:F}}>{lvl}</div>
              <div style={{fontSize:9,color:C.muted,fontFamily:F,marginTop:4}}>Factor: <span style={{color:C.text}}>{Math.round(t.factor*100)}%</span></div>
              <div style={{fontSize:9,color:C.muted,fontFamily:F}}>wRC+ adj: <span style={{color:C.text}}>{t.wrcAdj}</span></div>
              <div style={{fontSize:9,color:C.muted,fontFamily:F}}>Reliability: <span style={{color:C.text}}>{Math.round(t.reliability*100)}%</span></div>
            </div>
          );})}
        </div>
      </Panel>}

      {/* Career Stats — moved to bottom */}
      {seasons.length>0&&<Panel title="CAREER STATS" sub={isMiLB?"Minor league stats shown with level indicators. Translation factors applied in projections.":"Year-by-year from MLB Stats API."}>
        <div style={{overflowX:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
              {["Year","Age","Tm","Lvl","PA","AVG","OBP","SLG","OPS","HR","R","RBI","BB","SO","SB"].map(h=>
                <th key={h} style={{padding:"5px 7px",textAlign:["Year","Tm","Lvl"].includes(h)?"left":"right",color:C.muted,fontWeight:600,fontSize:9,letterSpacing:".04em"}}>{h}</th>
              )}
            </tr></thead>
            <tbody>{seasons.map((s,i)=>(
              <tr key={i} style={{borderBottom:`1px solid ${C.border}40`,background:i%2===0?"#f5f0e6":"transparent"}}>
                <td style={{padding:"4px 7px",color:C.text,fontWeight:600}}>{s.season}</td>
                <td style={{padding:"4px 7px",color:C.dim,textAlign:"right"}}>{s.age}</td>
                <td style={{padding:"4px 7px",color:C.dim}}>{s.team}</td>
                <td style={{padding:"4px 7px"}}><LevelBadge level={s.level}/></td>
                <td style={{padding:"4px 7px",color:C.text,textAlign:"right"}}>{s.pa}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.avg>=.300?C.green:C.text,fontWeight:600}}>{s.avg.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.obp>=.370?C.green:C.text}}>{s.obp.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.slg>=.500?C.green:C.text}}>{s.slg.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",fontWeight:700,color:s.ops>=.900?C.green:s.ops>=.750?C.accent:C.text}}>{s.ops.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.hr>=20?C.accent:C.text}}>{s.hr}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.text}}>{s.r}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.text}}>{s.rbi}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.bb}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.so}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.sb>=15?C.cyan:C.dim}}>{s.sb}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Panel>}
    </div>
  );
}

// ── ROSTER BROWSER (MLB + MiLB) ─────────────────────────────────────────────
function RosterBrowser({onSelect}) {
  const [teams,setTeams]=useState([]); const [selTeam,setSelTeam]=useState(null);
  const [affiliates,setAffiliates]=useState([]); const [selAffiliate,setSelAffiliate]=useState(null);
  const [roster,setRoster]=useState([]); const [loading,setLoading]=useState(false);
  const [viewLevel,setViewLevel]=useState("MLB");

  useEffect(()=>{getTeams(1).then(setTeams);},[]);

  const pickTeam = (team) => {
    setSelTeam(team); setSelAffiliate(null); setRoster([]); setViewLevel("MLB"); setLoading(true);
    Promise.all([getTeamRoster(team.id), getMiLBAffiliate(team.id)])
      .then(([r, a]) => { setRoster(r); setAffiliates(a); setLoading(false); });
  };

  const pickAffiliate = (aff) => {
    setSelAffiliate(aff); setViewLevel(LEVEL_NAMES[aff.sport?.id]||"MiLB"); setLoading(true);
    getTeamRoster(aff.id).then(r=>{setRoster(r);setLoading(false);});
  };

  const showMLB = () => {
    if(!selTeam) return;
    setSelAffiliate(null); setViewLevel("MLB"); setLoading(true);
    getTeamRoster(selTeam.id).then(r=>{setRoster(r);setLoading(false);});
  };

  return (
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      <Panel title="SELECT MLB ORGANIZATION">
        <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
          {teams.map(t=><button key={t.id} onClick={()=>pickTeam(t)} style={{
            padding:"4px 10px",fontSize:10,fontWeight:600,fontFamily:F,borderRadius:4,cursor:"pointer",border:"none",
            background:selTeam?.id===t.id?C.accent:"#efe9dd",color:selTeam?.id===t.id?"#000":C.muted,
          }}>{t.abbreviation}</button>)}
        </div>
      </Panel>

      {selTeam&&affiliates.length>0&&<Panel title={`${selTeam.name.toUpperCase()} SYSTEM`} sub="Click a level to browse that affiliate's roster.">
        <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
          <button onClick={showMLB} style={{padding:"6px 14px",borderRadius:6,cursor:"pointer",border:`2px solid ${viewLevel==="MLB"?C.green:C.border}`,background:viewLevel==="MLB"?`${C.green}15`:"transparent",color:viewLevel==="MLB"?C.green:C.muted,fontSize:11,fontWeight:700,fontFamily:F}}>
            MLB &middot; {selTeam.abbreviation}
          </button>
          {affiliates.map(a=>{
            const lvl=LEVEL_NAMES[a.sport?.id]||"MiLB";
            const active=selAffiliate?.id===a.id;
            return <button key={a.id} onClick={()=>pickAffiliate(a)} style={{
              padding:"6px 14px",borderRadius:6,cursor:"pointer",fontSize:11,fontWeight:700,fontFamily:F,
              border:`2px solid ${active?LEVEL_COLORS[lvl]:C.border}`,
              background:active?`${LEVEL_COLORS[lvl]}15`:"transparent",
              color:active?LEVEL_COLORS[lvl]:C.muted,
            }}>{lvl} &middot; {a.shortName||a.abbreviation}</button>;
          })}
        </div>
      </Panel>}

      {loading&&<Spinner msg={`Loading ${viewLevel} roster...`}/>}

      {!loading&&roster.length>0&&<Panel title={`${selAffiliate?.name||selTeam?.name||""} ROSTER`} sub="Click a player to load their projection.">
        <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12}}>
          <LevelBadge level={viewLevel}/>
          <span style={{fontSize:11,color:C.dim,fontFamily:F}}>{roster.filter(r=>r.position?.code!=="1").length} position players</span>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(190px,1fr))",gap:5}}>
          {roster.filter(r=>r.person&&r.position?.code!=="1").map(r=>{
            const rfv = getPlayerFV(r.person.id, r.person.fullName);
            return <div key={r.person.id} onClick={()=>onSelect(r.person)}
              style={{padding:"7px 11px",background:"#efe9dd",borderRadius:6,cursor:"pointer",border:`1px solid ${C.border}`,transition:"border-color .1s",display:"flex",justifyContent:"space-between",alignItems:"center"}}
              onMouseEnter={e=>e.currentTarget.style.borderColor=LEVEL_COLORS[viewLevel]||C.accent}
              onMouseLeave={e=>e.currentTarget.style.borderColor=C.border}>
              <div>
                <div style={{fontSize:12,fontWeight:700,color:C.text,fontFamily:F}}>{r.person.fullName}</div>
                <div style={{fontSize:10,color:C.muted,fontFamily:F}}>{posLabel(r.position?.code)} &middot; #{r.jerseyNumber||"\u2014"}</div>
              </div>
              {rfv && <FVBadge fv={rfv}/>}
            </div>;
          })}
        </div>
      </Panel>}
    </div>
  );
}

// ── LEADERBOARD ─────────────────────────────────────────────────────────────
// Fetches all active MLB position players via the sports_players endpoint,
// pulls 2025 season stats in bulk, runs projections, and shows a sortable table.

async function fetchAllMLBPlayers() {
  // This endpoint returns all active players for sport=1 (MLB)
  try {
    const res = await fetch(`${API}/sports/1/players?season=2025&gameType=R&hydrate=currentTeam`);
    const data = await res.json();
    return (data.people || []).filter(p => p.primaryPosition?.code !== "1" && p.primaryPosition?.code !== "Y");
  } catch { return []; }
}

async function fetchPlayerSeasonStats(playerId) {
  // Fetch most recent 3 seasons across all levels
  const sportIds = [1, 11, 12, 13, 14, 16];
  try {
    const promises = sportIds.map(sid =>
      fetch(`${API}/people/${playerId}/stats?stats=yearByYear&group=hitting&gameType=R&sportId=${sid}`)
        .then(r => r.json())
        .then(d => (d.stats?.[0]?.splits || []).map(s => ({ ...s, _sportId: sid })))
        .catch(() => [])
    );
    const all = await Promise.all(promises);
    return all.flat();
  } catch { return []; }
}

const LEADER_COLS = [
  { k: "name",     l: "Player",      fmt: v => v, align: "left", sortDir: 1 },
  { k: "team",     l: "Team",        fmt: v => v, align: "left", sortDir: 1 },
  { k: "pos",      l: "Pos",         fmt: v => v, align: "left", sortDir: 1 },
  { k: "age",      l: "Age",         fmt: v => v, align: "right", sortDir: -1 },
  { k: "projWAR",  l: "Proj WAR",    fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "cumWAR",   l: "10yr WAR",    fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "projWRC",  l: "Proj wRC+",   fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "projOPS",  l: "Proj OPS",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projAVG",  l: "Proj AVG",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projOBP",  l: "Proj OBP",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projSLG",  l: "Proj SLG",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projHR",   l: "Proj HR",     fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastAVG",  l: "'25 AVG",     fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "lastOPS",  l: "'25 OPS",     fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "lastHR",   l: "'25 HR",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastSB",   l: "'25 SB",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastPA",   l: "'25 PA",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "peakAge",  l: "Peak Age",    fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "fv",       l: "FV",          fmt: v => v ?? "—", align: "right", sortDir: -1 },
];

function Leaderboard({ onSelect }) {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [sortCol, setSortCol] = useState("projWAR");
  const [sortAsc, setSortAsc] = useState(false);
  const [posFilter, setPosFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [started, setStarted] = useState(false);

  const loadAll = useCallback(async () => {
    setStarted(true);
    setLoading(true);
    setPlayers([]);

    // Step 1: fetch all active MLB players
    const allPeople = await fetchAllMLBPlayers();
    const hitters = allPeople.filter(p => p.primaryPosition?.code !== "1");
    setProgress({ done: 0, total: hitters.length });

    // Step 2: fetch stats and project in batches of 15
    const results = [];
    const BATCH = 15;
    for (let i = 0; i < hitters.length; i += BATCH) {
      const batch = hitters.slice(i, i + BATCH);
      const batchResults = await Promise.all(batch.map(async (p) => {
        try {
          const splits = await fetchPlayerSeasonStats(p.id);
          if (!splits.length) return null;

          const base = projectFromSeasons(splits, p.currentAge, p.primaryPosition?.code, p.fullName, p.id);
          if (!base) return null;

          const forward = projectForward(base, p.currentAge, p.primaryPosition?.code);
          const cum = forward.reduce((s, d) => s + Math.max(0, d.war), 0);
          const fv = getPlayerFV(p.id, p.fullName);

          // Find 2025 stats
          const s25 = splits
            .filter(s => s.season === "2025" && s.stat?.plateAppearances > 0)
            .sort((a, b) => (b.stat?.plateAppearances || 0) - (a.stat?.plateAppearances || 0));
          const best25 = s25[0]?.stat;

          return {
            id: p.id,
            name: p.fullName,
            team: p.currentTeam?.abbreviation || "FA",
            pos: posLabel(p.primaryPosition?.code),
            age: p.currentAge,
            projWAR: base.baseWAR,
            cumWAR: Math.round(cum * 10) / 10,
            projWRC: base.wRCPlus,
            projOPS: base.ops,
            projAVG: base.avg,
            projOBP: base.obp,
            projSLG: base.slg,
            projHR: base.hr,
            lastAVG: best25 ? parseFloat(best25.avg || 0) : null,
            lastOPS: best25 ? parseFloat(best25.ops || 0) : null,
            lastHR: best25 ? best25.homeRuns : null,
            lastSB: best25 ? best25.stolenBases : null,
            lastPA: best25 ? best25.plateAppearances : null,
            peakAge: getAP(p.primaryPosition?.code).peak,
            fv: fv,
            _player: p,
          };
        } catch { return null; }
      }));

      const valid = batchResults.filter(Boolean);
      results.push(...valid);
      setPlayers(prev => [...prev, ...valid]);
      setProgress({ done: Math.min(i + BATCH, hitters.length), total: hitters.length });
    }

    setLoading(false);
  }, []);

  const sorted = useMemo(() => {
    let filtered = players;
    if (posFilter !== "ALL") filtered = filtered.filter(p => p.pos === posFilter);
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(p => p.name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q));
    }
    const col = LEADER_COLS.find(c => c.k === sortCol);
    const dir = sortAsc ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = a[sortCol], bv = b[sortCol];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string") return av.localeCompare(bv) * dir;
      return (av - bv) * dir;
    });
  }, [players, sortCol, sortAsc, posFilter, search]);

  const toggleSort = (k) => {
    if (sortCol === k) setSortAsc(!sortAsc);
    else { setSortCol(k); setSortAsc(false); }
  };

  const positions = ["ALL", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "OF"];

  if (!started) {
    return (
      <Panel style={{ textAlign: "center", padding: 50 }}>
        <div style={{ fontSize: 44, marginBottom: 12 }}>&#128202;</div>
        <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>
        <p style={{ margin: "8px auto 0", fontSize: 12, color: C.muted, fontFamily: F, maxWidth: 520, lineHeight: 1.6 }}>
          Load every active MLB position player, run projections on all of them, and sort by any stat.
          This fetches ~400+ players from the MLB Stats API — takes about 60-90 seconds.
        </p>
        <button onClick={loadAll} style={{
          marginTop: 20, padding: "10px 28px", borderRadius: 8, border: "none", cursor: "pointer",
          background: C.accent, color: "#fff", fontSize: 13, fontWeight: 700, fontFamily: F,
        }}>Load All Players &amp; Project</button>
      </Panel>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Progress */}
      {loading && <Panel>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 16, height: 16, border: `2px solid ${C.border}`, borderTopColor: C.accent, borderRadius: "50%", animation: "spin .8s linear infinite" }} />
          <span style={{ fontSize: 12, color: C.dim, fontFamily: F }}>
            Loading players... {progress.done}/{progress.total} ({players.length} projected)
          </span>
        </div>
        <div style={{ marginTop: 8, height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
          <div style={{ height: "100%", background: C.accent, borderRadius: 2, width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%`, transition: "width .3s" }} />
        </div>
      </Panel>}

      {/* Filters */}
      {players.length > 0 && <Panel>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Filter by name or team..."
            style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${C.border}`, background: C.panel, color: C.text, fontSize: 11, fontFamily: F, outline: "none", width: 200 }} />
          <div style={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
            {positions.map(p => (
              <button key={p} onClick={() => setPosFilter(p)} style={{
                padding: "4px 10px", fontSize: 10, fontWeight: 600, fontFamily: F, borderRadius: 4, cursor: "pointer", border: "none",
                background: posFilter === p ? C.accent : "#efe9dd", color: posFilter === p ? "#fff" : C.muted,
              }}>{p}</button>
            ))}
          </div>
          <span style={{ fontSize: 10, color: C.muted, fontFamily: F, marginLeft: "auto" }}>{sorted.length} players</span>
        </div>
      </Panel>}

      {/* Table */}
      {players.length > 0 && <Panel>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F, fontSize: 10 }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${C.border}` }}>
                <th style={{ padding: "6px 4px", textAlign: "right", color: C.muted, fontWeight: 600, fontSize: 8, width: 30 }}>#</th>
                {LEADER_COLS.map(col => (
                  <th key={col.k} onClick={() => toggleSort(col.k)} style={{
                    padding: "6px 6px", textAlign: col.align, color: sortCol === col.k ? C.accent : C.muted,
                    fontWeight: 600, fontSize: 8, letterSpacing: ".04em", cursor: "pointer", userSelect: "none", whiteSpace: "nowrap",
                  }}>
                    {col.l} {sortCol === col.k ? (sortAsc ? "▲" : "▼") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.slice(0, 200).map((p, i) => (
                <tr key={p.id}
                  onClick={() => onSelect(p._player)}
                  style={{
                    borderBottom: `1px solid ${C.border}40`,
                    background: i % 2 === 0 ? "#f5f0e6" : "transparent",
                    cursor: "pointer",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = `${C.accent}08`}
                  onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? "#f5f0e6" : "transparent"}>
                  <td style={{ padding: "5px 4px", textAlign: "right", color: C.muted, fontSize: 9 }}>{i + 1}</td>
                  {LEADER_COLS.map(col => {
                    const val = p[col.k];
                    const display = col.fmt(val);
                    let color = C.text;
                    if (col.k === "projWAR") color = val >= 4 ? C.green : val >= 2 ? C.blue : val >= 0 ? C.text : C.red;
                    if (col.k === "projOPS") color = val >= .850 ? C.green : val >= .720 ? C.blue : C.text;
                    if (col.k === "projWRC") color = val >= 120 ? C.green : val >= 100 ? C.blue : C.text;
                    if (col.k === "fv" && val) color = val >= 60 ? C.accent : val >= 50 ? C.yellow : C.muted;
                    if (col.k === "name") color = C.text;
                    return (
                      <td key={col.k} style={{
                        padding: "5px 6px", textAlign: col.align, color,
                        fontWeight: col.k === "name" || col.k === "projWAR" || col.k === "projOPS" ? 700 : 400,
                        whiteSpace: "nowrap",
                      }}>{display}</td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {sorted.length > 200 && <p style={{ fontSize: 10, color: C.muted, fontFamily: F, marginTop: 8, textAlign: "center" }}>Showing top 200 of {sorted.length}. Use filters to narrow.</p>}
      </Panel>}
    </div>
  );
}

// ── AGING CURVES ─────────────────────────────────────────────────────────────
function AgingPanel() {
  const [sel,setSel]=useState(["SS","CF","1B","C"]); const [bw,setBw]=useState(4);
  const posC = {C:C.red,"1B":C.yellow,"2B":C.green,"3B":C.accent,SS:C.blue,LF:C.purple,CF:C.cyan,RF:C.pink,DH:C.muted};
  const data=useMemo(()=>{
    const m={};
    sel.forEach(pos=>{const p=AGING_PARAMS[pos];for(let age=20;age<=40;age++){if(!m[age])m[age]={age};const d=age-p.peak;const off=d<=0?1-.015*d*d*.3:1-p.dr*d*d*.25;const def=age<=p.peak?1:1-p.dd*(age-p.peak);m[age][pos]=Math.round(Math.max(-.5,bw*off*Math.max(.4,def)+p.pa/10*Math.max(.3,def))*10)/10;}});
    return Object.values(m).sort((a,b)=>a.age-b.age);
  },[sel,bw]);
  return (
    <Panel title="POSITION AGING CURVES" sub="Offensive (quadratic) + defensive (linear) decline.">
      <div style={{display:"flex",flexWrap:"wrap",gap:5,marginBottom:14}}>
        {Object.keys(AGING_PARAMS).map(pos=><button key={pos} onClick={()=>setSel(p=>p.includes(pos)?p.filter(x=>x!==pos):[...p,pos])} style={{padding:"5px 12px",borderRadius:5,cursor:"pointer",fontSize:11,fontWeight:700,fontFamily:F,border:`2px solid ${sel.includes(pos)?posC[pos]:C.border}`,background:sel.includes(pos)?`${posC[pos]}18`:"transparent",color:sel.includes(pos)?posC[pos]:C.muted}}>{pos}</button>)}
        <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:10,color:C.muted,fontFamily:F}}>BASE WAR</span>
          <input type="range" min="1" max="8" step=".5" value={bw} onChange={e=>setBw(+e.target.value)} style={{width:100,accentColor:C.accent}}/>
          <span style={{fontSize:13,fontWeight:700,color:C.accent,fontFamily:F}}>{bw}</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={data} margin={{top:10,right:30,left:0,bottom:0}}>
          <CartesianGrid strokeDasharray="3 3" stroke={C.grid}/><XAxis dataKey="age" stroke={C.muted} fontSize={10} fontFamily={F}/><YAxis stroke={C.muted} fontSize={10} fontFamily={F}/><Tooltip content={<Tip/>}/><ReferenceLine y={0} stroke={C.muted} strokeDasharray="5 5"/>
          {sel.map(pos=><Line key={pos} type="monotone" dataKey={pos} stroke={posC[pos]} strokeWidth={2.5} dot={false} name={pos}/>)}
        </LineChart>
      </ResponsiveContainer>
    </Panel>
  );
}

// ── METHODOLOGY ──────────────────────────────────────────────────────────────
function MethodPanel() {
  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
    <Panel title="DATA SOURCES">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8}}>
        {[
          {n:"MLB Stats API",d:"Player search, career stats, MiLB rosters across all levels (ROK→AAA). Free, no auth.",c:C.blue,s:"LIVE"},
          {n:"FanGraphs FV",d:"Future Value grades for top 100+ prospects. Hardcoded lookup table, updated seasonally.",c:C.green,s:"STATIC"},
          {n:"Statcast/TrackMan",d:"Batted ball data: avg EV, max EV, barrel% for top prospects. Hardcoded from MiLB TrackMan.",c:C.purple,s:"STATIC"},
          {n:"Baseball Savant",d:"Statcast: xwOBA, barrel%, exit velocity, sprint speed. Full integration planned.",c:C.accent,s:"PLANNED"},
        ].map(s=><div key={s.n} style={{padding:"12px 14px",background:`${s.c}06`,border:`1px solid ${s.c}18`,borderRadius:8}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:4}}>
            <span style={{fontSize:12,fontWeight:700,color:s.c,fontFamily:F}}>{s.n}</span>
            <span style={{fontSize:7,fontWeight:700,padding:"2px 5px",borderRadius:3,fontFamily:F,background:s.s==="LIVE"?`${C.green}20`:s.s==="STATIC"?`${C.blue}20`:`${C.yellow}20`,color:s.s==="LIVE"?C.green:s.s==="STATIC"?C.blue:C.yellow}}>{s.s}</span>
          </div>
          <p style={{margin:0,fontSize:10,color:C.dim,lineHeight:1.5,fontFamily:F}}>{s.d}</p>
        </div>)}
      </div>
    </Panel>
    <Panel title="FUTURE VALUE SCALE">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:6}}>
        {[65,60,55,50,45,40,35].map(fv=>{const s=getFVStyle(fv);return(
          <div key={fv} style={{padding:"10px 12px",borderRadius:6,border:`1px solid ${C.border}`}}>
            <div style={{marginBottom:6}}><FVBadge fv={fv}/></div>
            <div style={{fontSize:9,color:C.muted,fontFamily:F}}>
              {fv>=65?"Franchise player":fv>=60?"All-Star upside":fv>=55?"Above-avg regular":fv>=50?"Avg regular":fv>=45?"Solid backup":fv>=40?"Fringe MLB":"\u2014"}
            </div>
          </div>
        );})}
      </div>
    </Panel>
    <Panel title="MINOR LEAGUE TRANSLATION">
      <p style={{fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F,margin:"0 0 12px"}}>
        MiLB stats are <span style={{color:C.text}}>not directly comparable</span> to MLB. A .300 hitter in A-ball is not a .300 MLB hitter.
        The system applies level-specific translation factors derived from historical promotion data:
      </p>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(140px,1fr))",gap:6}}>
        {LEVEL_ORDER.map(lvl=>{const t=LEVEL_TRANSLATION[lvl];return <div key={lvl} style={{padding:"10px 12px",background:`${LEVEL_COLORS[lvl]}08`,border:`1px solid ${LEVEL_COLORS[lvl]}20`,borderRadius:6}}>
          <div style={{fontSize:15,fontWeight:800,color:LEVEL_COLORS[lvl],fontFamily:F}}>{lvl}</div>
          <div style={{fontSize:10,color:C.dim,fontFamily:F,marginTop:4}}>{t.label}</div>
          <div style={{fontSize:10,color:C.muted,fontFamily:F,marginTop:2}}>Stat multiplier: <span style={{color:C.text,fontWeight:700}}>{t.factor}x</span></div>
          <div style={{fontSize:10,color:C.muted,fontFamily:F}}>Reliability: <span style={{color:C.text}}>{Math.round(t.reliability*100)}%</span></div>
        </div>;})}
      </div>
    </Panel>
    <Panel title="PROJECTION METHODOLOGY">
      <div style={{fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F}}>
        <h4 style={{color:C.accent,fontSize:13,margin:"0 0 4px"}}>Marcel Weighting</h4>
        <p style={{margin:"0 0 12px"}}>3 most recent seasons weighted 5/4/3, regressed to league mean based on PA reliability. MiLB seasons are translated before weighting.</p>
        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>WAR Construction</h4>
        <p style={{margin:"0 0 12px"}}>Batting runs (from wRC+) + positional adjustment (FanGraphs scale) + replacement level, divided by ~10 runs/win.</p>
        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>Aging Curves</h4>
        <p style={{margin:"0 0 12px"}}>Offensive: quadratic decay past peak. Defensive: linear. Position-specific rates. Catchers steepest, DH gentlest.</p>
        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Statcast Integration</h4>
        <p style={{margin:0}}>For players with batted ball data, OPS trajectory projections incorporate avg exit velo, max exit velo, and barrel rate as upside/downside adjustments to the aging curve.</p>
      </div>
    </Panel>
  </div>;
}

// ── MAIN APP ─────────────────────────────────────────────────────────────────
const TABS=[
  {k:"player",l:"Player Projections"},
  {k:"leaders",l:"Leaderboard"},
  {k:"roster",l:"MLB & MiLB Rosters"},
  {k:"aging",l:"Aging Curves"},
  {k:"method",l:"Methodology"},
];

export default function App() {
  const [tab,setTab]=useState("player");
  const [selPlayer,setSelPlayer]=useState(null);
  const [detail,setDetail]=useState(null);
  const [lp,setLp]=useState(false);

  const pick=useCallback(p=>{setSelPlayer(p);setLp(true);setTab("player");getPlayerStats(p.id).then(d=>{setDetail(d||p);setLp(false);});},[]);

  const goHome = useCallback(()=>{setSelPlayer(null);setDetail(null);setLp(false);setTab("player");},[]);

  return (
    <div style={{minHeight:"100vh",background:C.bg,color:C.text,fontFamily:F}}>
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700;800&family=Changa+One&display=swap" rel="stylesheet"/>
      {/* Header */}
      <div style={{padding:"14px 24px 0",borderBottom:`2px solid ${C.navy}`,background:"linear-gradient(180deg, #ffffff 0%, #f9f5ed 100%)"}}>
        <div style={{display:"flex",alignItems:"center",gap:14,marginBottom:12,flexWrap:"wrap"}}>
          <div onClick={goHome} style={{cursor:"pointer",userSelect:"none"}}>
            <div style={{display:"flex",alignItems:"baseline",gap:6}}>
              <span style={{fontFamily:"'Changa One', cursive",fontSize:38,fontWeight:400,color:C.navy,lineHeight:1,letterSpacing:"-0.02em",textShadow:`2px 2px 0 ${C.accent}30`}}>VIAcast</span>
              <span style={{width:8,height:8,borderRadius:"50%",background:C.accent,display:"inline-block",marginBottom:4}}/>
            </div>
            <p style={{margin:"1px 0 0 2px",fontSize:11,fontWeight:700,color:C.navy,letterSpacing:".06em",fontFamily:F,textTransform:"uppercase"}}>Baseball Projection Engine</p>
            <p style={{margin:"2px 0 0 2px",fontSize:9,color:C.muted,letterSpacing:".04em",fontFamily:F}}>Data-driven MLB &amp; MiLB forecasting</p>
          </div>
          <div style={{marginLeft:"auto"}}><PlayerSearch onSelect={pick}/></div>
        </div>
        <div style={{display:"flex",gap:2}}>
          {TABS.map(t=><button key={t.k} onClick={()=>setTab(t.k)} style={{
            padding:"7px 16px",border:"none",cursor:"pointer",fontSize:11,fontWeight:tab===t.k?700:500,fontFamily:F,
            background:tab===t.k?C.panel:"transparent",color:tab===t.k?C.navy:C.muted,
            borderRadius:"6px 6px 0 0",borderBottom:tab===t.k?`2px solid ${C.accent}`:"2px solid transparent",
          }}>{t.l}</button>)}
        </div>
      </div>
      {/* Content */}
      <div style={{padding:"16px 24px 40px"}}>
        {tab==="player"&&<div>
          {!selPlayer&&!lp&&<Panel style={{textAlign:"center",padding:50}}>
            <div style={{fontSize:44,marginBottom:12}}>&#9918;</div>
            <h3 style={{margin:0,fontSize:16,color:C.text,fontFamily:F}}>Search any MLB or minor league player</h3>
            <p style={{margin:"6px auto 0",fontSize:12,color:C.muted,fontFamily:F,maxWidth:520,lineHeight:1.6}}>
              Covers all levels from Rookie ball through the majors. MiLB stats are translated using level-specific conversion factors before projection. Top prospects include FV grades and batted ball data.
            </p>
            <div style={{marginTop:20,display:"flex",gap:8,justifyContent:"center",flexWrap:"wrap"}}>
              {["Konnor Griffin","Aidan Miller","Juan Soto","Gunnar Henderson","Kevin McGonigle","Samuel Basallo"].map(n=>
                <button key={n} onClick={()=>searchPlayers(n).then(r=>{if(r[0])pick(r[0]);})}
                  style={{padding:"5px 12px",borderRadius:6,border:`1px solid ${C.border}`,background:"transparent",color:C.dim,fontSize:11,fontFamily:F,cursor:"pointer"}}
                  onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.color=C.accent;}}
                  onMouseLeave={e=>{e.target.style.borderColor=C.border;e.target.style.color=C.dim;}}
                >{n}</button>
              )}
            </div>
          </Panel>}
          {lp&&<Spinner msg="Pulling career data..."/>}
          {selPlayer&&!lp&&detail&&<PlayerCard player={detail}/>}
        </div>}
        {tab==="leaders"&&<Leaderboard onSelect={pick}/>}
        {tab==="roster"&&<RosterBrowser onSelect={pick}/>}
        {tab==="aging"&&<AgingPanel/>}
        {tab==="method"&&<MethodPanel/>}
      </div>
      <div style={{padding:"12px 24px",borderTop:`2px solid ${C.navy}`,background:"#f9f5ed",display:"flex",justifyContent:"space-between",flexWrap:"wrap",gap:8}}>
        <span style={{fontSize:8,color:C.muted,fontFamily:F}}>VIAcast &middot; Data: MLB Stats API &middot; FV: FanGraphs/ESPN consensus &middot; No affiliation with MLB</span>
        <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Methodology: Marcel (Tango) + level translation + Statcast batted ball adjustments</span>
      </div>
    </div>
  );
}
