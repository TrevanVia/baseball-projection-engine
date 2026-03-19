#!/usr/bin/env python3
"""Replace PA-based HR with games-based HR projection. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old = """  // HR scales with SLG boost for FV prospects
  let projHR = Math.round((wHR/tw) * (estPA / Math.max(1, rawPA)) * ageBoost * performanceBoost);
  const baselineSLG = Math.max(0.310, rawSLG * paRel + 0.405 * (1 - paRel));
  if (fv && projSLG > baselineSLG) {
    projHR = Math.round(projHR * (projSLG / baselineSLG));
  }"""

new = """  // HR: project games first, then apply translated HR/G rate
  const avgG = wG > 0 ? wG / tw : 100;
  const projGames = highestLevel === "MLB"
    ? Math.min(162, Math.max(100, avgG * 0.97))
    : posCode === "2" ? Math.min(130, Math.max(90, 120))
    : Math.min(155, Math.max(100, 140));
  const hrPerGame = wG > 0 ? (wHR / tw) / (wG / tw) : 0;
  let projHR = Math.round(hrPerGame * projGames * ageBoost * performanceBoost);
  const baselineSLG = Math.max(0.310, rawSLG * paRel + 0.405 * (1 - paRel));
  if (fv && projSLG > baselineSLG) {
    projHR = Math.round(projHR * (projSLG / baselineSLG));
  }"""

if old in src:
    src = src.replace(old, new)
    open(APP, "w").write(src)
    print("Fixed: HR now uses games-based projection (HR/G * projected games)")
else:
    print("Target not found - may already be applied")
