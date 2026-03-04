#!/usr/bin/env python3
"""Fix pitcher replacement level to match FanGraphs. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Fix in Statcast engine
old1 = """  // WAR: replacement level approach
  const replLevel = 5.50;
  const rpw = 9.5;
  const rawWAR = ((replLevel - fip) / rpw) * (estIP / 9);"""

new1 = """  // WAR: FIP vs replacement level (FG uses 0.12 wins/game for SP)
  // replLevel = 0.12 * 9.5 + lgFIP = 5.34
  const replLevel = 5.34;
  const rpw = 9.5;
  const rawWAR = ((replLevel - fip) / rpw) * (estIP / 9);"""

if old1 in src:
    src = src.replace(old1, new1)
    changes += 1
    print("1. Fixed Statcast engine replacement level (5.50 -> 5.34)")

# Fix in Marcel engine
old2 = """  // Pitcher WAR: FIP-based vs replacement level
  // Replacement level ~ 5.5 RA/9 (a freely available minor league arm)
  // This means a league-avg pitcher (4.20 ERA) ~ 2.0 WAR, matching FanGraphs
  const replLevel = 5.50;
  const runsPerWin = 9.5;
  const pitchWAR = ((replLevel - finalFIP) / runsPerWin) * (estIP / 9);"""

new2 = """  // Pitcher WAR: FIP-based vs replacement level
  // FanGraphs: starter replLvl = 0.12 wins/game -> 5.34 runs/9
  const replLevel = 5.34;
  const runsPerWin = 9.5;
  const pitchWAR = ((replLevel - finalFIP) / runsPerWin) * (estIP / 9);"""

if old2 in src:
    src = src.replace(old2, new2)
    changes += 1
    print("2. Fixed Marcel engine replacement level (5.50 -> 5.34)")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print("\nExpected impact: all pitcher WARs drop ~0.3-0.4")
print("  League avg: 2.7 -> 2.4 WAR")
print("  Good #3:    4.4 -> 4.1 WAR")
print("  Ace:        7.0 -> 6.6 WAR")
