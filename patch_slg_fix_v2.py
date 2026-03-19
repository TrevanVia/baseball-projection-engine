#!/usr/bin/env python3
"""Fix slash line: OBP/SLG/OPS/HR all consistent with FV blend. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old = """  const finalOBP = (wOBP/tw) * ageBoost * performanceBoost;
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

new = """  const rawOBP = (wOBP/tw) * ageBoost * performanceBoost;
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

  // HR scales with SLG boost for FV prospects
  let projHR = Math.round((wHR/tw) * (estPA / Math.max(1, rawPA)) * ageBoost * performanceBoost);
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

if old in src:
    src = src.replace(old, new)
    open(APP, "w").write(src)
    print("Fixed: OBP + SLG = OPS, all scale with FV blend, HR scales with SLG boost")
else:
    print("Target not found - check if already applied")
