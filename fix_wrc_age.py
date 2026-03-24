#!/usr/bin/env python3
"""Remove double-counted age adjustment from wRC+. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# The wRC+ line currently includes ageAdj which double-counts aging
# (OPS already has aging via avgAgeF on xBA/xSLG)
old = "  const wrc = Math.max(60, Math.min(195, Math.round((ops / 0.720) * 100 + db + ageAdj)));"
new = "  const wrc = Math.max(60, Math.min(195, Math.round((ops / 0.720) * 100 + db)));"

if old in src:
    src = src.replace(old, new)
    changes += 1
    print("1. Removed ageAdj from wRC+ (OPS already reflects aging via avgAgeF)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Trout: .884 OPS -> 123 wRC+ (was 120, ageAdj was double-counting)")
print("wRC+ now purely = (displayed OPS / .720) * 100 + discipline bonus")
