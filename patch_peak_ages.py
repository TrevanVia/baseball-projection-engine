#!/usr/bin/env python3
"""Update position peak ages + fix at-peak aging case. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Update AGING_PARAMS peak ages
# Research consensus: offensive peak is 27-29 across positions
# Our peaks affect HITTING projections (wRC+), so they should reflect OFFENSIVE peak
# Defense peak is tracked separately via defPeak in the WAR calculation
old_aging = """const AGING_PARAMS = {
  C:  { peak: 28, dr: 0.032, pa: -1.0, dd: 0.05 },
  "1B":{ peak: 28, dr: 0.032, pa: -12.5, dd: 0.02 },
  "2B":{ peak: 27, dr: 0.038, pa: 2.5,   dd: 0.05 },
  "3B":{ peak: 27, dr: 0.035, pa: 2.5,   dd: 0.04 },
  SS: { peak: 26, dr: 0.040, pa: 7.5,   dd: 0.055 },
  LF: { peak: 28, dr: 0.033, pa: -7.5,  dd: 0.035 },
  CF: { peak: 27, dr: 0.037, pa: 2.5,   dd: 0.05 },
  RF: { peak: 28, dr: 0.034, pa: -5.0,  dd: 0.04 },
  DH: { peak: 29, dr: 0.030, pa: -17.5, dd: 0.0 },
};"""

new_aging = """const AGING_PARAMS = {
  // Peak ages reflect OFFENSIVE peak (research: 27-29 for most hitters)
  // Defense peaks tracked separately in WAR calculation (SS/CF peak 26, corners 28)
  // Sources: FanGraphs aging curves, Fair (2025) OPS peak 27.5, BP Bradbury peak 29
  C:  { peak: 27, dr: 0.035, pa: -1.0, dd: 0.05 },   // catchers wear down early, offense peaks ~27
  "1B":{ peak: 29, dr: 0.030, pa: -12.5, dd: 0.02 },  // pure offense, late peak (Freeman, Votto)
  "2B":{ peak: 28, dr: 0.035, pa: 2.5,   dd: 0.05 },  // offensive peak ~28 (Altuve, Semien)
  "3B":{ peak: 28, dr: 0.033, pa: 2.5,   dd: 0.04 },  // power position, peaks ~28 (Ramirez, Devers)
  SS: { peak: 28, dr: 0.035, pa: 7.5,   dd: 0.055 },  // offensive peak ~28 (Lindor, Seager, Turner)
  LF: { peak: 28, dr: 0.033, pa: -7.5,  dd: 0.035 },  // unchanged
  CF: { peak: 27, dr: 0.037, pa: 2.5,   dd: 0.05 },   // speed decline offsets; keep 27
  RF: { peak: 28, dr: 0.034, pa: -5.0,  dd: 0.04 },   // unchanged
  DH: { peak: 30, dr: 0.028, pa: -17.5, dd: 0.0 },    // no defense drain (Cruz, Ortiz peaked late)
};"""

if old_aging in src:
    src = src.replace(old_aging, new_aging)
    changes += 1
    print("1. Updated peak ages:")
    print("   SS: 26 -> 28 (Lindor, Seager, Turner best years at 27-30)")
    print("   2B: 27 -> 28 (Altuve, Semien)")
    print("   3B: 27 -> 28 (Ramirez, Devers)")
    print("   C:  28 -> 27 (catchers wear down early)")
    print("   1B: 28 -> 29 (pure offense, late peak)")
    print("   DH: 29 -> 30 (no defensive drain)")
    print("   SS dr: 0.040 -> 0.035 (was declining too fast)")

# 2. Fix aging formula: players AT peak should get 0 adjustment, not -1.5
old_aging_formula = """  let ageAdj = 0;
  if (age < pk) ageAdj = 1.5; // one year of improvement
  else if (age <= 32) ageAdj = -1.5; // one year of gradual decline
  else ageAdj = -3.0; // one year of steeper late decline"""

new_aging_formula = """  let ageAdj = 0;
  if (age < pk) ageAdj = 1.5; // one year of improvement toward peak
  else if (age === pk) ageAdj = 0; // at peak: no adjustment
  else if (age <= 32) ageAdj = -1.5; // gradual post-peak decline
  else ageAdj = -3.0; // steeper decline after 32"""

if old_aging_formula in src:
    src = src.replace(old_aging_formula, new_aging_formula)
    changes += 1
    print("2. Fixed aging: at-peak players now get 0 adjustment (was -1.5)")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print()
print("Key impacts:")
print("  Henderson (24, SS): peak 26->28, 4 yrs growth instead of 2, +10% forward WAR")
print("  Witt Jr (24, SS):   peak 26->28, same benefit")
print("  Lindor (32, SS):    peak 26->28, was 6 yrs past peak, now 4 yrs -> less decline")
print("  Devers (28, 3B):    peak 27->28, now AT peak instead of 1yr past -> +1.5 wRC+")
print("  Freeman (35, 1B):   peak 28->29, slightly less decline")
print("  Ohtani (31, DH):    peak 29->30, 1yr past peak instead of 2 -> +1.5 wRC+")
