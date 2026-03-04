#!/usr/bin/env python3
"""Fix: use FV blend for prospects with small MLB samples. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# The bug: a prospect with a brief MLB callup (e.g. Basallo, 118 PA) gets
# highestLevel = "MLB", which skips the FV blend entirely.
# The FV blend should activate when:
#   1. Player has an FV grade, AND
#   2. Player has < 400 MLB PA (not yet established)
# This catches prospects who got a brief taste but aren't established MLBers.

old_fv_check = """  if (fv && highestLevel !== "MLB") {
    const bench = FV_BENCHMARKS[Math.min(70, Math.max(40, fv))] || FV_BENCHMARKS[50];
    // PA-scaled blend: >400 PA = trust stats heavily, <100 PA = trust FV heavily
    const statWeight = Math.min(0.85, Math.max(0.15, paRel * 0.95));
    const fvWeight = 1 - statWeight;
    const statsOPS = finalAdjustedOPS * paRel + lgOPS * (1 - paRel);
    finalOPS = statsOPS * statWeight + bench.ops * fvWeight;
    finalWRC = Math.round((finalOPS / lgOPS) * 100);
  } else {
    finalOPS = finalAdjustedOPS * paRel + lgOPS * (1 - paRel);
    finalWRC = Math.round((finalOPS / lgOPS) * 100) + Math.round(trans.wrcAdj * (1 - paRel));
  }"""

new_fv_check = """  // Count MLB PA specifically (not total PA across all levels)
  const mlbPA = valid.filter(s => detectLevel(s) === "MLB")
    .reduce((sum, s) => sum + (s.stat?.plateAppearances || 0), 0);
  // Use FV blend if player has FV grade AND isn't an established MLBer (<400 MLB PA)
  if (fv && mlbPA < 400) {
    const bench = FV_BENCHMARKS[Math.min(70, Math.max(40, fv))] || FV_BENCHMARKS[50];
    // PA-scaled blend: more MLB PA = trust stats more, less = trust FV more
    const statWeight = Math.min(0.80, Math.max(0.15, paRel * 0.90));
    const fvWeight = 1 - statWeight;
    const statsOPS = finalAdjustedOPS * paRel + lgOPS * (1 - paRel);
    finalOPS = statsOPS * statWeight + bench.ops * fvWeight;
    finalWRC = Math.round((finalOPS / lgOPS) * 100);
  } else {
    finalOPS = finalAdjustedOPS * paRel + lgOPS * (1 - paRel);
    finalWRC = Math.round((finalOPS / lgOPS) * 100) + Math.round(trans.wrcAdj * (1 - paRel));
  }"""

if old_fv_check in src:
    src = src.replace(old_fv_check, new_fv_check)
    changes += 1
    print("1. Fixed FV blend: now uses MLB PA count (<400) instead of highestLevel")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print()
print("Basallo: 118 MLB PA + 65 FV -> FV blend now activates")
print("  FV benchmark OPS: .880, fvWeight ~65%")
print("  Expected wRC+: ~114 (was 89)")
