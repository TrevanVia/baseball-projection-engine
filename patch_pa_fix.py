#!/usr/bin/env python3
"""Fix PA/G consistency: prospects with <400 MLB PA use games-based PA. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old = """  // Project games first, then derive PA
  const avgG = wG > 0 ? wG / tw : 100;
  const projGames = highestLevel === "MLB"
    ? Math.min(162, Math.max(100, Math.round(avgG * 0.97)))
    : posCode === "2" ? Math.min(130, Math.max(90, 120))
    : Math.min(155, Math.max(100, 140));
  const estPA = highestLevel === "MLB"
    ? Math.min(700, Math.round(rawPA * 0.97))
    : Math.round(projGames * 4.0);"""

new = """  // Project games first, then derive PA
  // Use prospect formula for players with < 400 MLB PA (brief callups shouldn't get MLB treatment)
  const avgG = wG > 0 ? wG / tw : 100;
  const isEstablishedMLB = highestLevel === "MLB" && mlbPA >= 400;
  const projGames = isEstablishedMLB
    ? Math.min(162, Math.max(100, Math.round(avgG * 0.97)))
    : posCode === "2" ? Math.min(130, Math.max(90, 120))
    : Math.min(155, Math.max(100, 140));
  const estPA = isEstablishedMLB
    ? Math.min(700, Math.round(rawPA * 0.97))
    : Math.round(projGames * 4.0);"""

if old in src:
    src = src.replace(old, new)
    open(APP, "w").write(src)
    print("Fixed: players with <400 MLB PA now use prospect PA formula (projGames * 4.0)")
    print()
    print("Basallo (118 MLB PA, catcher):")
    print("  Before: G=100, PA=170 (broken MLB formula on small sample)")
    print("  After:  G=120, PA=480 (catcher prospect: 120G * 4.0 PA/G)")
else:
    print("Target not found - may already be applied")
