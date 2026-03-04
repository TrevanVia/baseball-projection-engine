#!/usr/bin/env python3
"""Add pitcher Statcast engine. Run from project root after build_pitcher_data.py."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Import pitcher_savant_data.json
if "pitcher_savant_data.json" not in src:
    src = src.replace(
        'import savantDataJson from "./savant_data.json";',
        'import savantDataJson from "./savant_data.json";\nimport pitcherSavantJson from "./pitcher_savant_data.json";'
    )
    src = src.replace(
        'const SAVANT_DATA = savantDataJson.default || savantDataJson;',
        'const SAVANT_DATA = savantDataJson.default || savantDataJson;\nconst PITCHER_SAVANT = pitcherSavantJson.default || pitcherSavantJson;'
    )
    changes += 1
    print("1. Added pitcher savant import")

# 2. Add pitcher lookup function
LOOKUP = '''
function getPitcherSavant(playerId, playerName) {
  const byId = PITCHER_SAVANT[String(playerId)];
  if (byId && byId.seasons) return byId;
  if (playerName) {
    const norm = normalizeN(playerName);
    const match = Object.values(PITCHER_SAVANT).find(p => normalizeN(p.name) === norm);
    if (match && match.seasons) return match;
  }
  return null;
}
'''
if "getPitcherSavant" not in src:
    idx = src.find("function getSavantPlayer(")
    if idx > 0:
        end = src.find("\n}\n", idx) + 3
        src = src[:end] + LOOKUP + src[end:]
        changes += 1
        print("2. Added getPitcherSavant lookup")

# 3. Add projectPitcherFromStatcast engine
ENGINE = '''
// VIAcast Pitcher Statcast Engine (5 Layers)
function projectPitcherFromStatcast(pSav, age, playerName, playerId) {
  const S = pSav.seasons || {}, yrs = Object.keys(S).sort().reverse();
  if (!yrs.length) return null;
  const W = [0.55, 0.30, 0.15], lat = S[yrs[0]] || {};
  const bfp0 = lat.bfp || 0;
  if (bfp0 < 30) return null;

  // L1: Stuff Quality (xwOBA against, xERA)
  let wxw = 0, wxe = 0, wbrl = 0, tw1 = 0;
  yrs.forEach((yr, i) => {
    const s = S[yr], w = W[i] || 0.05, pw = w * Math.min(1, (s.bfp || 0) / 300);
    if (s.xwoba != null) { wxw += s.xwoba * pw; tw1 += pw; }
    if (s.xera != null) wxe += s.xera * pw;
    if (s.barrel_pct != null) wbrl += s.barrel_pct * pw;
  });
  const pXw = tw1 > 0 ? wxw / tw1 : 0.315;
  const pXera = tw1 > 0 ? wxe / tw1 : 4.20;
  const pBrl = tw1 > 0 ? wbrl / tw1 : 8;

  // L2: Command (K%, BB%, SwStr%)
  let wk = 0, wbb = 0, wsw = 0, tw2 = 0;
  yrs.forEach((yr, i) => {
    const s = S[yr], w = W[i] || 0.05, pw = w * Math.min(1, (s.bfp || 0) / 200);
    if (s.k_pct != null) { wk += s.k_pct * pw; tw2 += pw; }
    if (s.bb_pct != null) wbb += s.bb_pct * pw;
    if (s.swstr != null) wsw += s.swstr * pw;
    else if (s.whiff_pct != null) wsw += s.whiff_pct * pw;
  });
  const pK = tw2 > 0 ? wk / tw2 : 22;
  const pBB = tw2 > 0 ? wbb / tw2 : 8;
  const pSw = tw2 > 0 ? wsw / tw2 : 10;

  // L3: Velocity
  const fbVelo = pSav.fb_velo || null;
  const veloT = yrs.length >= 2 && S[yrs[0]]?.fb_velo && S[yrs[1]]?.fb_velo
    ? S[yrs[0]].fb_velo - S[yrs[1]].fb_velo : 0;

  // L4: Contact Management (EV against, hard hit against)
  let wev = 0, whh = 0, tw4 = 0;
  yrs.forEach((yr, i) => {
    const s = S[yr], w = W[i] || 0.05, pw = w * Math.min(1, (s.bfp || 0) / 300);
    if (s.avg_ev != null) { wev += s.avg_ev * pw; tw4 += pw; }
    if (s.hard_hit_pct != null) whh += s.hard_hit_pct * pw;
  });
  const pEV = tw4 > 0 ? wev / tw4 : 88;
  const pHH = tw4 > 0 ? whh / tw4 : 35;

  // L5: Trends
  let tb = 0;
  if (yrs.length >= 2) {
    const x0 = S[yrs[0]]?.xera, x1 = S[yrs[1]]?.xera;
    if (x0 != null && x1 != null) {
      const d = x1 - x0; // positive = improvement (lower xERA)
      tb += d * 0.15;
    }
  }
  if (veloT < -1.5) tb += 0.15; // velo loss = bad
  if (veloT > 1.0) tb -= 0.10; // velo gain = good (lower ERA)

  // Aging
  const spPeak = 27, rpPeak = 28;
  const isStarter = (lat.ip || 0) > 50 || bfp0 > 250;
  const pk = isStarter ? spPeak : rpPeak;
  let af = 1;
  if (age < pk) af = Math.pow(0.985, pk - age); // young pitchers still developing
  else if (age <= 33) af = Math.pow(1.015, age - pk); // ERA rises post-peak
  else af = Math.pow(1.015, 33 - pk) * Math.pow(1.03, age - 33);

  // Assemble ERA projection
  // Anchor on xERA, adjust for trends and aging
  let projERA = Math.max(1.50, Math.min(6.50, (pXera + tb) * af));

  // K/9 and BB/9 from percentages
  const projK9 = Math.max(4, Math.min(15, pK / 100 * 9 * 4.3));
  const projBB9 = Math.max(1, Math.min(6, pBB / 100 * 9 * 4.3));
  const projWHIP = Math.max(0.75, Math.min(1.80, 0.90 + (projERA - 2.50) * 0.12));

  // IP estimate
  const latIP = lat.ip || (bfp0 / 4.3);
  let estIP;
  if (isStarter) {
    estIP = Math.max(140, Math.min(210, latIP * 0.97));
  } else {
    estIP = Math.min(75, latIP * 0.96);
  }

  // FIP from components
  const estK = projK9 * estIP / 9;
  const estBB = projBB9 * estIP / 9;
  const estHR = Math.max(0.3, pBrl / 100 * (estIP * 4.3) * 0.035);
  const fip = Math.max(1.50, Math.min(6.50,
    ((13 * estHR) + (3 * estBB) - (2 * estK)) / estIP + 3.10));

  // WAR: replacement level approach
  const replLevel = 5.50;
  const rpw = 9.5;
  const rawWAR = ((replLevel - fip) / rpw) * (estIP / 9);

  // FV clamp
  const fv = getPlayerFV(playerId, playerName);
  let finalWAR = rawWAR;
  if (fv) {
    const b = FV_BENCHMARKS[Math.min(70, Math.max(40, fv))] || FV_BENCHMARKS[50];
    finalWAR = Math.max(b.war * 0.25, Math.min(b.war * 2.0, rawWAR));
  }
  finalWAR = Math.round(finalWAR * 10) / 10;

  const tBFP = yrs.reduce((s, yr) => s + (S[yr]?.bfp || 0), 0);

  return {
    era: Math.round(projERA * 100) / 100,
    fip: Math.round(fip * 100) / 100,
    whip: Math.round(projWHIP * 100) / 100,
    k9: Math.round(projK9 * 10) / 10,
    bb9: Math.round(projBB9 * 10) / 10,
    kPct: Math.round(pK * 10) / 10,
    bbPct: Math.round(pBB * 10) / 10,
    ip: Math.round(estIP),
    w: Math.round(estIP / 9 * 0.55),
    l: Math.round(estIP / 9 * 0.45 * (projERA / 4.20)),
    sv: isStarter ? 0 : Math.round(estIP / 1.2 * 0.3),
    baseWAR: finalWAR,
    estIP: Math.round(estIP),
    isReliever: !isStarter,
    isPitcher: true,
    peakAge: pk,
    paReliability: Math.min(95, Math.round((tBFP / 2000) * 95)),
    highestLevel: "MLB",
    translationNote: null,
    _statcast: {
      xwoba: Math.round(pXw * 1000) / 1000,
      xera: Math.round(pXera * 100) / 100,
      projBarrelAgainst: Math.round(pBrl * 10) / 10,
      projEVAgainst: Math.round(pEV * 10) / 10,
      fbVelo: fbVelo ? Math.round(fbVelo * 10) / 10 : null,
      veloTrend: Math.round(veloT * 10) / 10,
      swStr: Math.round(pSw * 10) / 10,
      trendBoost: Math.round(tb * 100) / 100,
    },
  };
}
'''

if "projectPitcherFromStatcast" not in src:
    idx = src.find("function projectPitcherFromSeasons(")
    if idx > 0:
        src = src[:idx] + ENGINE + "\n\n" + src[idx:]
        changes += 1
        print("3. Added projectPitcherFromStatcast engine")

# 4. Wire into call sites - try Statcast first, fall back to Marcel
# Main player card
old_pitch_call = "return pitchCareer.length ? projectPitcherFromSeasons(pitchCareer, player.currentAge, player.fullName, player.id) : null;"
new_pitch_call = """const pSav = getPitcherSavant(player.id, player.fullName);
      if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
        const scP = projectPitcherFromStatcast(pSav, player.currentAge, player.fullName, player.id);
        if (scP) return scP;
      }
      return pitchCareer.length ? projectPitcherFromSeasons(pitchCareer, player.currentAge, player.fullName, player.id) : null;"""
if old_pitch_call in src:
    src = src.replace(old_pitch_call, new_pitch_call, 1)
    changes += 1
    print("4. Wired Statcast into main pitcher projection")

# 5. Wire into batch call sites (leaderboard, VpD, compare)
old_batch = "base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);"
new_batch = """const pSav2 = getPitcherSavant(player.id, player.fullName);
                if (pSav2 && Object.keys(pSav2.seasons || {}).length > 0) {
                  const scP2 = projectPitcherFromStatcast(pSav2, player.currentAge, player.fullName, player.id);
                  if (scP2) { base = scP2; } else {
                    base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                  }
                } else {
                  base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                }"""
c = src.count(old_batch)
if c > 0:
    src = src.replace(old_batch, new_batch)
    changes += 1
    print("5. Wired Statcast into %d batch pitcher call sites" % c)

# Also handle the VpD batch loader variant
old_vpd_pitch = "const base = projectPitcherFromSeasons(splits, p.currentAge, p.fullName, p.id);"
new_vpd_pitch = """const pSavV = getPitcherSavant(p.id, p.fullName);
                let base;
                if (pSavV && Object.keys(pSavV.seasons || {}).length > 0) {
                  base = projectPitcherFromStatcast(pSavV, p.currentAge, p.fullName, p.id) || projectPitcherFromSeasons(splits, p.currentAge, p.fullName, p.id);
                } else {
                  base = projectPitcherFromSeasons(splits, p.currentAge, p.fullName, p.id);
                }"""
if old_vpd_pitch in src:
    src = src.replace(old_vpd_pitch, new_vpd_pitch, 1)
    changes += 1
    print("6. Wired Statcast into VpD pitcher loading")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
