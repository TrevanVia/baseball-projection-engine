#!/usr/bin/env python3
"""Sync tweet script WAR formulas with site. Run from project root."""
import re

with open('scripts/tweet-potd.js') as f:
    src = f.read()
changes = 0

# 1. Fix hitter WAR: use rawWrc instead of amplified wrc
old_hbat = "const bat = ((wrc-100)/100)*ePA*0.115;"
new_hbat = "const bat = ((rawWrc-100)/100)*ePA*0.115;"
if old_hbat in src:
    src = src.replace(old_hbat, new_hbat)
    changes += 1
    print("1. Hitter WAR now uses raw wRC+ (matches site)")

# 2. Fix pitcher BFP: 4.1 -> 3.8
old_bfp = "const bfp = ip * 4.1;"
new_bfp = "const bfp = ip * 3.8;"
if old_bfp in src:
    src = src.replace(old_bfp, new_bfp)
    changes += 1
    print("2. Pitcher BFP: 4.1 -> 3.8 (K/9 calibration)")

# 3. Fix pitcher WAR: match site formula (5.34 - ERA) / 9.5 * IP/9
old_pwar = "const war = Math.round((5.5 - era * 1.08) * ip / 9 / 9.5 * 10) / 10;"
new_pwar = "const war = Math.round((5.34 - era) / 9.5 * ip / 9 * 10) / 10;"
if old_pwar in src:
    src = src.replace(old_pwar, new_pwar)
    changes += 1
    print("3. Pitcher WAR: now matches site formula (5.34 - ERA) / 9.5 * IP/9")

with open('scripts/tweet-potd.js', 'w') as f:
    f.write(src)
print(f"\nApplied {changes} changes")
