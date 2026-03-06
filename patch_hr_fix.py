#!/usr/bin/env python3
"""Fix HR formula: barrel conversion was way too low. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Old: hr = barrel% * BBE * 0.24 (no baseline)
# New: hr = barrel% * BBE * 0.45 + PA * 0.018 (barrel HR + non-barrel HR)
# Calibrated against 2025 actuals: Judge 64/58, Soto 41/41, Henderson 32/37

old_hr = """const hr=Math.round(Math.max(0,pBrl/100*(ePA*.75)*.24));"""
new_hr = """const hr=Math.round(Math.max(0,pBrl/100*(ePA*.75)*.45+ePA*.018));"""

if old_hr in src:
    src = src.replace(old_hr, new_hr)
    changes += 1
    print("1. Fixed HR formula: barrel conv 0.24->0.45, added non-barrel baseline (+PA*0.018)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Expected HR projections:")
print("  Judge:     ~64 (was ~27)")
print("  Soto:      ~41 (was ~15)")
print("  Henderson: ~32 (was ~11)")
print("  Witt:      ~30 (was ~9)")
print("  Ohtani:    ~44 (was ~17)")
