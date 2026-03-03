#!/usr/bin/env python3
"""Fix WAR projection caps for elite prospects. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Raise FV benchmark WAR targets
#    Old: 70=7.0, 65=5.0, 60=3.5, 55=2.5
#    New: 70=8.0, 65=5.5, 60=4.0, 55=2.8
old_bench = """const FV_BENCHMARKS = {
  70: { ops: .940, war: 7.0, wrc: 150, floor_ops: .850, ceil_ops: 1.050 },
  65: { ops: .870, war: 5.0, wrc: 135, floor_ops: .780, ceil_ops: .960 },
  60: { ops: .820, war: 3.5, wrc: 125, floor_ops: .720, ceil_ops: .900 },
  55: { ops: .780, war: 2.5, wrc: 115, floor_ops: .690, ceil_ops: .860 },
  50: { ops: .740, war: 1.8, wrc: 105, floor_ops: .660, ceil_ops: .820 },
  45: { ops: .710, war: 1.0, wrc: 98,  floor_ops: .640, ceil_ops: .780 },
  40: { ops: .680, war: 0.5, wrc: 90,  floor_ops: .620, ceil_ops: .750 },
};"""

new_bench = """const FV_BENCHMARKS = {
  70: { ops: .960, war: 8.0, wrc: 160, floor_ops: .860, ceil_ops: 1.100 },
  65: { ops: .880, war: 5.5, wrc: 140, floor_ops: .790, ceil_ops: .980 },
  60: { ops: .830, war: 4.0, wrc: 128, floor_ops: .730, ceil_ops: .920 },
  55: { ops: .785, war: 2.8, wrc: 118, floor_ops: .695, ceil_ops: .870 },
  50: { ops: .740, war: 1.8, wrc: 105, floor_ops: .660, ceil_ops: .820 },
  45: { ops: .710, war: 1.0, wrc: 98,  floor_ops: .640, ceil_ops: .780 },
  40: { ops: .680, war: 0.5, wrc: 90,  floor_ops: .620, ceil_ops: .750 },
};"""

if old_bench in src:
    src = src.replace(old_bench, new_bench)
    changes += 1
    print("1. Raised FV benchmark WAR targets")

# 2. Raise WAR clamp multiplier in Marcel (projectFromSeasons)
#    Old: max = bench.war * 1.7, min = bench.war * 0.35
#    New: max = bench.war * 2.0, min = bench.war * 0.30
old_clamp = "clampedWAR = Math.max(bench.war * 0.35, Math.min(bench.war * 1.7, baseWAR));"
new_clamp = "clampedWAR = Math.max(bench.war * 0.30, Math.min(bench.war * 2.0, baseWAR));"
if old_clamp in src:
    src = src.replace(old_clamp, new_clamp)
    changes += 1
    print("2. Raised Marcel WAR clamp to 2.0x")

# 3. Raise WAR clamp in Statcast engine too
old_sc_clamp = "fW=Math.max(b.war*.3,Math.min(b.war*1.8,rW))"
new_sc_clamp = "fW=Math.max(b.war*.25,Math.min(b.war*2.0,rW))"
if old_sc_clamp in src:
    src = src.replace(old_sc_clamp, new_sc_clamp)
    changes += 1
    print("3. Raised Statcast WAR clamp to 2.0x")

# 4. Fix projectForward pre-peak growth
#    Old: f = 1 + Math.min(0.12, (3 - yearsToGo) * 0.03) with max 1.25
#    Problem: 7+ years from peak = 0.88 factor (DEFLATING young players)
#    New: gradual ramp from current to peak, with more growth per year
old_forward = """    if (d <= 0) {
      const yearsToGo = Math.abs(d);
      f = 1 + Math.min(0.12, (3 - yearsToGo) * 0.03);
      f = Math.max(0.88, Math.min(1.25, f));
    } else {"""

new_forward = """    if (d <= 0) {
      const yearsToGo = Math.abs(d);
      // Growth curve: young players improve ~4% per year toward peak
      // At peak-1: +4%, peak-2: +7%, peak-3: +9%, etc.
      // Farther from peak = more room to grow per year
      f = 1 + Math.min(0.25, yearsToGo * 0.04);
      f = Math.max(1.0, Math.min(1.30, f));
    } else {"""

if old_forward in src:
    src = src.replace(old_forward, new_forward)
    changes += 1
    print("4. Fixed pre-peak growth curve (young players now project upward)")

# 5. Raise OPS hard cap slightly
old_ops_cap = "finalOPS = Math.max(0.560, Math.min(1.100, finalOPS));"
new_ops_cap = "finalOPS = Math.max(0.560, Math.min(1.150, finalOPS));"
if old_ops_cap in src:
    src = src.replace(old_ops_cap, new_ops_cap)
    changes += 1
    print("5. Raised OPS cap to 1.150")

# 6. Raise wRC+ cap
old_wrc_cap = "finalWRC = Math.max(65, Math.min(185, finalWRC));"
new_wrc_cap = "finalWRC = Math.max(65, Math.min(195, finalWRC));"
if old_wrc_cap in src:
    src = src.replace(old_wrc_cap, new_wrc_cap)
    changes += 1
    print("6. Raised wRC+ cap to 195")

# 7. Allow stat weight to go higher for high-PA prospects
#    Old: statWeight capped at 0.75
#    New: capped at 0.85
old_stat_weight = "const statWeight = Math.min(0.75, Math.max(0.2, paRel * 0.9));"
new_stat_weight = "const statWeight = Math.min(0.85, Math.max(0.15, paRel * 0.95));"
if old_stat_weight in src:
    src = src.replace(old_stat_weight, new_stat_weight)
    changes += 1
    print("7. Raised stat weight cap for FV blending")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
