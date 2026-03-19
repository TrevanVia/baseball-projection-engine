#!/usr/bin/env python3
"""Fix HR + slash line: translate MiLB HR, games-based projection, FV-synced OPS. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Translate HR by level factor (currently raw, untranslated)
old_hr = """    wHR += (st.homeRuns || 0) * w;"""
new_hr = """    wHR += (st.homeRuns || 0) * trans.factor * w;"""
if old_hr in src:
    src = src.replace(old_hr, new_hr, 1)
    changes += 1
    print("1. MiLB HR now translated by level factor")

# 2. Add wG to track weighted games
old_init = """  let tw = 0, wOPS = 0, wPA = 0, wHR = 0, wAVG = 0, wOBP = 0, wSLG = 0;"""
new_init = """  let tw = 0, wOPS = 0, wPA = 0, wHR = 0, wAVG = 0, wOBP = 0, wSLG = 0, wG = 0;"""
if old_init in src:
    src = src.replace(old_init, new_init, 1)
    changes += 1
    print("2. Added wG variable")

old_wpa = """    wPA += pa * w;
    totalRawPA += pa;"""
new_wpa = """    wPA += pa * w;
    totalRawPA += pa;
    wG += (s.stat?.gamesPlayed || 0) * w;"""
if old_wpa in src:
    src = src.replace(old_wpa, new_wpa, 1)
    changes += 1
    print("3. Tracking weighted games per season")

# 3. Replace the entire return block (slash line + HR)
old_return = """  const finalOBP = (wOBP/tw) * ageBoost * performanceBoost;
  const finalSLG = (wSLG/tw) * ageBoost * performanceBoost;
  const peakAge = (getAP(posCode)).peak;

  return {
    obp: Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))),
    slg: Math.max(0.310, Math.min(0.620, finalOPS - Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))))),
    ops: Math.max(0.560, Math.min(1.100, Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))) + Math.max(0.310, Math.min(0.620, finalSLG * paRel + 0.405 * (1 - paRel))))),
    avg: Math.max(0.210, Math.min(0.330, (wAVG/tw) * ageBoost * paRel + 0.248 * (1 - paRel))),
    wRCPlus: finalWRC,
    baseWAR: Math.round(clampedWAR * 10) / 10,
    estPA: Math.round(estPA),
    hr: Math.round((wHR/tw) * (estPA / Math.max(1, rawPA)) * ageBoost * performanceBoost),"""

new_return = """  const rawOBP = (wOBP/tw) * ageBoost * performanceBoost;
  const rawSLG = (wSLG/tw) * ageBoost * performanceBoost;
  const peakAge = (getAP(posCode)).peak;

  // Regressed slash line
  let projOBP = Math.max(0.275, Math.min(0.430, rawOBP * paRel + 0.315 * (1 - paRel)));
  let projSLG = Math.max(0.310, Math.min(0.620, rawSLG * paRel + 0.405 * (1 - paRel)));
  let projOPS = projOBP + projSLG;

  // If FV blend boosted OPS, scale slash line to match
  if (finalOPS > projOPS && projOPS > 0) {
    const boost = finalOPS / projOPS;
    projOBP = Math.max(0.275, Math.min(0.430, projOBP * (1 + (boost - 1) * 0.40)));
    projSLG = Math.max(0.310, Math.min(0.620, projSLG * (1 + (boost - 1) * 0.60)));
    projOPS = projOBP + projSLG;
  }

  // HR: project games first, then apply translated HR/G rate
  const avgG = wG > 0 ? wG / tw : 100;
  const projGames = highestLevel === "MLB"
    ? Math.min(162, Math.max(100, avgG * 0.97))
    : posCode === "2" ? Math.min(130, Math.max(90, 120))
    : Math.min(155, Math.max(100, 140));
  const hrPerGame = wG > 0 ? (wHR / tw) / (wG / tw) : 0;
  let projHR = Math.round(hrPerGame * projGames * ageBoost * performanceBoost);
  // FV boost: scale HR with SLG improvement
  const baselineSLG = Math.max(0.310, rawSLG * paRel + 0.405 * (1 - paRel));
  if (fv && projSLG > baselineSLG) {
    projHR = Math.round(projHR * (projSLG / baselineSLG));
  }

  return {
    obp: projOBP,
    slg: projSLG,
    ops: Math.max(0.560, Math.min(1.100, projOPS)),
    avg: Math.max(0.210, Math.min(0.330, (wAVG/tw) * ageBoost * paRel + 0.248 * (1 - paRel))),
    wRCPlus: finalWRC,
    baseWAR: Math.round(clampedWAR * 10) / 10,
    estPA: Math.round(estPA),
    hr: projHR,"""

if old_return in src:
    src = src.replace(old_return, new_return)
    changes += 1
    print("4. Slash line synced with FV blend + games-based HR projection")
else:
    print("4. WARN: Return block not found - may need manual check")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
