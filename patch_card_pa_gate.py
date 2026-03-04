#!/usr/bin/env python3
"""Fix PlayerCard to respect 250 PA Statcast threshold. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# The PlayerCard's base useMemo calls projectFromStatcast directly,
# bypassing the 250 PA gate in projectPlayer. Fix both hitter and pitcher paths.

old_card = """    // Hitter projection (also base for two-way)
    let hitProj = null;
    const savP = getSavantPlayer(player.id, player.fullName);
    if (savP && Object.keys(savP.seasons || {}).length > 0) {
      hitProj = projectFromStatcast(savP, player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id);
    }
    if (!hitProj && career.length) {
      hitProj = projectFromSeasons(career, player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id);
    }"""

new_card = """    // Hitter projection (also base for two-way)
    let hitProj = null;
    const savP = getSavantPlayer(player.id, player.fullName);
    if (savP && Object.keys(savP.seasons || {}).length > 0) {
      // Only use Statcast for 250+ MLB PA; below that Marcel with MiLB data is better
      const totalMLBPA = Object.values(savP.seasons || {}).reduce((s, yr) => s + (yr.pa || 0), 0);
      if (totalMLBPA >= 250) {
        hitProj = projectFromStatcast(savP, player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id);
      }
    }
    if (!hitProj && career.length) {
      hitProj = projectFromSeasons(career, player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id);
    }"""

if old_card in src:
    src = src.replace(old_card, new_card)
    changes += 1
    print("1. Fixed PlayerCard hitter path: 250 PA Statcast gate")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
