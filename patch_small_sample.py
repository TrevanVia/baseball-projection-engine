#!/usr/bin/env python3
"""Fix: prefer Marcel over Statcast for small MLB samples. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# The issue: projectPlayer always tries Statcast first. For a player like Basallo
# with 118 MLB PA but 700+ MiLB PA, the Statcast engine uses only the tiny MLB
# sample and produces a terrible projection. The Marcel path (which uses ALL levels)
# never runs because Statcast returns a non-null result.
#
# Fix: only use Statcast when there's a meaningful MLB sample (250+ PA).
# Below that threshold, let Marcel handle it with full MiLB data.

old_routing = """function projectPlayer(splits, age, posCode, name, id) {
  const savP = getSavantPlayer(id, name);
  if (savP && Object.keys(savP.seasons || {}).length > 0) {
    const sc = projectFromStatcast(savP, age, posCode, name, id);
    if (sc) return sc;
  }
  return splits && splits.length
    ? projectFromSeasons(splits, age, posCode, name, id)
    : null;
}"""

new_routing = """function projectPlayer(splits, age, posCode, name, id) {
  const savP = getSavantPlayer(id, name);
  if (savP && Object.keys(savP.seasons || {}).length > 0) {
    // Only use Statcast if meaningful MLB sample exists
    // Below 250 PA, MiLB-inclusive Marcel is more reliable
    const totalMLBPA = Object.values(savP.seasons || {}).reduce((s, yr) => s + (yr.pa || 0), 0);
    if (totalMLBPA >= 250) {
      const sc = projectFromStatcast(savP, age, posCode, name, id);
      if (sc) return sc;
    }
  }
  return splits && splits.length
    ? projectFromSeasons(splits, age, posCode, name, id)
    : null;
}"""

if old_routing in src:
    src = src.replace(old_routing, new_routing)
    changes += 1
    print("1. Added 250 PA minimum for Statcast engine (prefer Marcel for small samples)")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print()
print("Basallo: 118 MLB PA -> now uses Marcel with AAA/AA data")
print("  AAA 2025: .270/.966, 23 HR, 44 BB in 321 PA")
print("  AA 2024: .289/.820, 16 HR in 446 PA")
print("  With 65 FV + AAA translation, should project ~2.5-3.5 WAR")
