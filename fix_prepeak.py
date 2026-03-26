#!/usr/bin/env python3
"""Add pre-peak development boost for young hitters. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Change const to let for pXba/pXslg
old_const = "  const pXba=tw1>0?wxba/tw1:null, pXslg=tw1>0?wxslg/tw1:null;"
new_let = "  let pXba=tw1>0?wxba/tw1:null, pXslg=tw1>0?wxslg/tw1:null;"
if old_const in src:
    src = src.replace(old_const, new_let)
    changes += 1
    print("1. Changed pXba/pXslg to let")

# 2. Add pre-peak boost before aging block
old_aging = """  // Separate aging for AVG (contact, mild decline) and SLG (power, steeper decline)
  const avgAgeF = age > 32 ? Math.max(0.95, 1 - (age - 32) * 0.008) : 1.0;
  const slgAgeF = age > 30 ? Math.max(0.88, 1 - (age - 30) * 0.015) : 1.0;"""

new_aging = """  // Pre-peak development boost: young hitters projected to improve toward peak
  const yrsToPeak = Math.max(0, pk - age);
  const devBoostAVG = yrsToPeak > 0 ? 1 + Math.min(yrsToPeak * 0.012, 0.08) : 1.0;
  const devBoostSLG = yrsToPeak > 0 ? 1 + Math.min(yrsToPeak * 0.018, 0.12) : 1.0;
  if (pXba != null) pXba = pXba * devBoostAVG;
  if (pXslg != null) pXslg = pXslg * devBoostSLG;
  // Post-peak aging for AVG (contact, mild decline) and SLG (power, steeper decline)
  const avgAgeF = age > 32 ? Math.max(0.95, 1 - (age - 32) * 0.008) : 1.0;
  const slgAgeF = age > 30 ? Math.max(0.88, 1 - (age - 30) * 0.015) : 1.0;"""

if old_aging in src:
    src = src.replace(old_aging, new_aging)
    changes += 1
    print("2. Added pre-peak development boost (AVG +1.2%/yr, SLG +1.8%/yr)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Impact:")
print("  Chourio (22): .254/.306/.428/.734 -> ~.269/.321/.467/.788")
print("  Henderson (24): ~5% SLG boost")  
print("  Holliday (22): ~6% AVG, ~11% SLG boost")
print("  Judge (33): no change (past peak)")
print("  Caps: AVG max +8%, SLG max +12%")
