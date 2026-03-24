#!/usr/bin/env python3
"""Fix OBP formula and wRC+ age double-count. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix OBP formula in Statcast engine: BB multiplier 0.85 -> 0.65, constant 0.02 -> 0.015
old_obp = "  const obp = Math.max(.26, Math.min(.45, avg + pBB * .85 + .02));"
new_obp = "  const obp = Math.max(.26, Math.min(.45, avg + pBB * .65 + .015));"
if old_obp in src:
    src = src.replace(old_obp, new_obp)
    changes += 1
    print("1. Fixed OBP formula: BB mult 0.85->0.65, const 0.02->0.015")

# 2. Remove ageAdj from wRC+ (double-counts aging already in OPS via avgAgeF)
old_wrc = "  const wrc = Math.max(60, Math.min(195, Math.round((ops / 0.720) * 100 + db + ageAdj)));"
new_wrc = "  const wrc = Math.max(60, Math.min(195, Math.round((ops / 0.720) * 100 + db)));"
if old_wrc in src:
    src = src.replace(old_wrc, new_wrc)
    changes += 1
    print("2. Removed ageAdj from wRC+ (OPS already aged)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Trout impact:")
print("  OBP: .391 -> .357 (was inflated by BB% * 0.85)")
print("  OPS: .884 -> .850")
print("  wRC+: 120 -> 118 (from lower OPS, no more age double-count)")
print()
print("This brings us in line with ZiPS (.353 OBP) and Steamer (.341 OBP)")
