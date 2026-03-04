#!/usr/bin/env python3
"""Fix pitcher WAR formula to use replacement level baseline. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix the core pitcher WAR formula
# Old: uses league ERA as baseline (treats avg pitcher as 0 WAR)
# New: uses replacement level (~5.5 RA/9) as baseline
old_war = """  // Pitcher WAR: FIP-based, scaled by IP
  const lgERA = 4.20;
  const runsPerWin = 9.5;
  const pitchWAR = ((lgERA - finalFIP) / runsPerWin) * (estIP / 9) + (estIP / 200) * 2.0;"""

new_war = """  // Pitcher WAR: FIP-based vs replacement level
  // Replacement level ~ 5.5 RA/9 (a freely available minor league arm)
  // This means a league-avg pitcher (4.20 ERA) ~ 2.0 WAR, matching FanGraphs
  const replLevel = 5.50;
  const runsPerWin = 9.5;
  const pitchWAR = ((replLevel - finalFIP) / runsPerWin) * (estIP / 9);"""

if old_war in src:
    src = src.replace(old_war, new_war)
    changes += 1
    print("1. Fixed pitcher WAR formula (replacement level baseline)")

# 2. Fix pitcher WAR clamp (still at 1.7 from before)
old_clamp = "clampedWAR = Math.max(bench.war * 0.3, Math.min(bench.war * 1.7, clampedWAR));"
new_clamp = "clampedWAR = Math.max(bench.war * 0.25, Math.min(bench.war * 2.0, clampedWAR));"
c = src.count(old_clamp)
if c > 0:
    src = src.replace(old_clamp, new_clamp)
    changes += 1
    print("2. Fixed pitcher WAR clamp to 2.0x (%d instances)" % c)

# 3. Raise MLB pitcher paRel cap to 0.93 (190 IP ace shouldn't be regressed 10%)
old_rel = """  const paRel = Math.min(highestLevel === "MLB" ? 0.90 : 0.80, (totalRawIP / (valid.length * 160)) * (PITCHER_TRANSLATION[highestLevel]?.reliability || 0.9));"""
new_rel = """  const paRel = Math.min(highestLevel === "MLB" ? 0.93 : 0.82, (totalRawIP / (valid.length * 150)) * (PITCHER_TRANSLATION[highestLevel]?.reliability || 0.9));"""
if old_rel in src:
    src = src.replace(old_rel, new_rel)
    changes += 1
    print("3. Raised pitcher paRel cap (0.93 MLB, 0.82 MiLB)")

# 4. Also increase the pitcher IP denominator reliability
# With 190 IP over 1 season: (190 / 150) * 0.9 = 1.14 -> capped at 0.93
# This is good - a full season ace gets near-max reliability

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print("\nExpected Skenes projection:")
print("  FIP ~3.1, IP ~184, WAR = (5.5 - 3.1) / 9.5 * (184/9) = ~5.2")
print("  vs old: (4.2 - 3.1) / 9.5 * (184/9) + (184/200)*2 = ~4.2")
