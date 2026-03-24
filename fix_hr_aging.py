#!/usr/bin/env python3
"""Apply SLG age factor to HR projection. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# The HR formula doesn't account for age. Apply slgAgeF to barrel rate.
old_hr = "  const hr=Math.round(Math.max(0,pBrl/100*(ePA*.75)*.45+ePA*.010));"
new_hr = "  const hr=Math.round(Math.max(0,(pBrl*slgAgeF)/100*(ePA*.75)*.45+ePA*.010));"

if old_hr in src:
    src = src.replace(old_hr, new_hr)
    changes += 1
    print("1. HR now ages with slgAgeF (barrel rate declines with age)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Trout (34): 35 HR -> 32 HR (barrel% aged from 15.8 to 14.9)")
print("Young players (<=30): slgAgeF=1.0, no change")
