#!/usr/bin/env python3
"""Fix prospect PA: derive from projected games instead of raw MiLB average. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Replace estPA formula: prospects get projGames * 4.0 PA/G
old = """  const ap = getAP(posCode);
  const estPA = highestLevel === "MLB"
    ? Math.min(700, rawPA * 0.97)
    : Math.min(650, rawPA * 0.93);"""

new = """  const ap = getAP(posCode);
  // Project games first, then derive PA
  const avgG = wG > 0 ? wG / tw : 100;
  const projGames = highestLevel === "MLB"
    ? Math.min(162, Math.max(100, Math.round(avgG * 0.97)))
    : posCode === "2" ? Math.min(130, Math.max(90, 120))
    : Math.min(155, Math.max(100, 140));
  const estPA = highestLevel === "MLB"
    ? Math.min(700, Math.round(rawPA * 0.97))
    : Math.round(projGames * 4.0);"""

if old in src:
    src = src.replace(old, new)
    changes += 1
    print("1. Fixed: prospect PA now = projected games * 4.0 PA/G")

# 2. Remove duplicate projGames from HR section
old_dup = """  // HR: project games first, then apply translated HR/G rate
  const avgG = wG > 0 ? wG / tw : 100;
  const projGames = highestLevel === "MLB"
    ? Math.min(162, Math.max(100, avgG * 0.97))
    : posCode === "2" ? Math.min(130, Math.max(90, 120))
    : Math.min(155, Math.max(100, 140));
  const hrPerGame = wG > 0 ? (wHR / tw) / (wG / tw) : 0;
  let projHR = Math.round(hrPerGame * projGames * ageBoost * performanceBoost);"""

new_dup = """  // HR: use translated HR/G rate * projected games
  const hrPerGame = wG > 0 ? (wHR / tw) / (wG / tw) : 0;
  let projHR = Math.round(hrPerGame * projGames * ageBoost * performanceBoost);"""

if old_dup in src:
    src = src.replace(old_dup, new_dup)
    changes += 1
    print("2. Removed duplicate projGames from HR section")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Prospect PA projections:")
print("  Catchers: 120G * 4.0 = 480 PA")
print("  Position players: 140G * 4.0 = 560 PA")
print("  MLB players: based on actual PA history (unchanged)")
