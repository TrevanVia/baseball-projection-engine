#!/usr/bin/env python3
"""Fix hitter PA: use best recent full season instead of most recent (injury fix). Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Replace ePA formula to use best full season PA from last 3 years
old_epa = "  const ePA=Math.min(700,Math.max(200,pa0*.97));"
new_epa = """  // PA estimate: use best full season from last 3 yrs (handles injury-shortened seasons)
  const bestPA = Math.max(...yrs.slice(0,3).map(yr => S[yr]?.pa || 0));
  const ePA=Math.min(700,Math.max(200,Math.max(pa0, bestPA * 0.90) * 0.97));"""

if old_epa in src:
    src = src.replace(old_epa, new_epa)
    changes += 1
    print("1. ePA now uses best recent full season PA (90% floor for injury returns)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Rutschman: 354 PA -> ~600 PA (best season 687 * 0.90 * 0.97 = 600)")
print("Trout: stays ~539 (2025 was his best recent year at 556 PA)")
print("Healthy full-time players: minimal change (most recent ≈ best)")
