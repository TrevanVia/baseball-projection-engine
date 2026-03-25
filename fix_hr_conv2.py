#!/usr/bin/env python3
"""Fix HR barrel conversion 0.45 -> 0.38. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

old = "  const hr=Math.round(Math.max(0,(pBrl*(1-slgRegress)*slgAgeF)/100*(ePA*.75)*.45+ePA*.010));"
new = "  const hr=Math.round(Math.max(0,(pBrl*(1-slgRegress)*slgAgeF)/100*(ePA*.75)*.38+ePA*.010));"

if old in src:
    src = src.replace(old, new)
    changes += 1
    print("1. Barrel-to-HR conversion: 0.45 -> 0.38")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Trout (34): ~23 HR (was 27 with 0.45, was 33 before aging)")
print("Judge (33): ~38 HR")
print("Young hitters: modest reduction across the board")
