#!/usr/bin/env python3
"""Raise FV WAR floors for elite prospects. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix Statcast engine FV clamp (for players who go through Statcast path)
old_statcast_clamp = """  if(fv){const b=FV_BENCHMARKS[Math.min(70,Math.max(40,fv))]||FV_BENCHMARKS[50];
    fW=Math.max(b.war*.25,Math.min(b.war*2.0,rW))}"""

new_statcast_clamp = """  if(fv){const b=FV_BENCHMARKS[Math.min(70,Math.max(40,fv))]||FV_BENCHMARKS[50];
    fW=Math.max(b.war*.50,Math.min(b.war*2.0,rW))}"""

if old_statcast_clamp in src:
    src = src.replace(old_statcast_clamp, new_statcast_clamp)
    changes += 1
    print("1. Statcast FV clamp floor: 0.25 -> 0.50")

# 2. Fix Marcel engine FV clamp
old_marcel_clamp = """    clampedWAR = Math.max(bench.war * 0.30, Math.min(bench.war * 2.0, baseWAR));"""
new_marcel_clamp = """    clampedWAR = Math.max(bench.war * 0.50, Math.min(bench.war * 2.0, baseWAR));"""

if old_marcel_clamp in src:
    src = src.replace(old_marcel_clamp, new_marcel_clamp)
    changes += 1
    print("2. Marcel FV clamp floor: 0.30 -> 0.50")

# 3. Give higher FV prospects more FV weight in the OPS blend
# Currently: statWeight = min(0.80, max(0.15, paRel * 0.90))
# Problem: even for a 70 FV, stats get 40%+ weight despite being unreliable MiLB translations
# Fix: scale fvWeight up for higher FV grades
old_fv_blend = """  if (fv && mlbPA < 400) {
    const bench = FV_BENCHMARKS[Math.min(70, Math.max(40, fv))] || FV_BENCHMARKS[50];
    // PA-scaled blend: more MLB PA = trust stats more, less = trust FV more
    const statWeight = Math.min(0.80, Math.max(0.15, paRel * 0.90));
    const fvWeight = 1 - statWeight;
    const statsOPS = finalAdjustedOPS * paRel + lgOPS * (1 - paRel);
    finalOPS = statsOPS * statWeight + bench.ops * fvWeight;
    finalWRC = Math.round((finalOPS / lgOPS) * 100);"""

new_fv_blend = """  if (fv && mlbPA < 400) {
    const bench = FV_BENCHMARKS[Math.min(70, Math.max(40, fv))] || FV_BENCHMARKS[50];
    // PA-scaled blend: more MLB PA = trust stats more, less = trust FV more
    // Higher FV prospects get more FV weight (70 FV = we're very confident in the grade)
    const fvBoost = fv >= 70 ? 0.20 : fv >= 65 ? 0.12 : fv >= 60 ? 0.06 : 0;
    const statWeight = Math.min(0.80, Math.max(0.10, paRel * 0.90 - fvBoost));
    const fvWeight = 1 - statWeight;
    const statsOPS = finalAdjustedOPS * paRel + lgOPS * (1 - paRel);
    finalOPS = statsOPS * statWeight + bench.ops * fvWeight;
    finalWRC = Math.round((finalOPS / lgOPS) * 100);"""

if old_fv_blend in src:
    src = src.replace(old_fv_blend, new_fv_blend)
    changes += 1
    print("3. FV blend: higher FV grades get more FV weight (70 FV +20%, 65 +12%, 60 +6%)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("New FV WAR floors:")
print("  70 FV: 4.0 WAR min (was 2.4) — Griffin should project ~4.0-5.0")
print("  65 FV: 2.8 WAR min (was 1.6) — Basallo/McGonigle ~2.8-3.5")
print("  60 FV: 2.0 WAR min (was 1.2) — Clark/Sasaki ~2.0-3.0")
print("  55 FV: 1.4 WAR min (was 0.8) — Miller/Anthony ~1.4-2.0")
