#!/usr/bin/env python3
"""Unify projection paths across all tabs. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. Create a projectPitcher() router (mirrors projectPlayer for hitters)
# ═══════════════════════════════════════════════════════════════

# Insert after the existing projectPlayer function
old_after_projectPlayer = """function projectFromSeasons(splits, age, posCode, playerName, playerId) {"""

# Find where projectPlayer ends and projectFromSeasons begins
# We'll add projectPitcher right before projectFromSeasons

new_after_projectPlayer = """// Unified pitcher projection router (mirrors projectPlayer for hitters)
function projectPitcher(career, age, playerName, playerId) {
  const pSav = getPitcherSavant(playerId, playerName);
  if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
    const sc = projectPitcherFromStatcast(pSav, age, playerName, playerId);
    if (sc) return sc;
  }
  const pitchSplits = career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0);
  return pitchSplits.length ? projectPitcherFromSeasons(pitchSplits, age, playerName, playerId) : null;
}

function projectFromSeasons(splits, age, posCode, playerName, playerId) {"""

if old_after_projectPlayer in src:
    src = src.replace(old_after_projectPlayer, new_after_projectPlayer, 1)
    changes += 1
    print("1. Created projectPitcher() unified router function")

# ═══════════════════════════════════════════════════════════════
# 2. Make PlayerCard use projectPlayer() and projectPitcher()
# ═══════════════════════════════════════════════════════════════

old_card_proj = """    if (isPitcher) {
      const pSav = getPitcherSavant(player.id, player.fullName);
      if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
        const scP = projectPitcherFromStatcast(pSav, player.currentAge, player.fullName, player.id);
        if (scP) return scP;
      }
      return pitchCareer.length ? projectPitcherFromSeasons(pitchCareer, player.currentAge, player.fullName, player.id) : null;
    }
    // Hitter projection (also base for two-way)
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

new_card_proj = """    if (isPitcher) {
      return pitchCareer.length ? projectPitcher(pitchCareer, player.currentAge, player.fullName, player.id) : null;
    }
    // Hitter projection — uses same router as leaderboard & compare
    let hitProj = career.length
      ? projectPlayer(career.filter(s => s.stat?.plateAppearances > 0), player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id)
      : null;"""

if old_card_proj in src:
    src = src.replace(old_card_proj, new_card_proj)
    changes += 1
    print("2. PlayerCard now uses projectPlayer() and projectPitcher() routers")

# ═══════════════════════════════════════════════════════════════
# 3. Fix VpD pitcher path to use the router
# ═══════════════════════════════════════════════════════════════

old_vpd_pitcher = """                const pSav2 = getPitcherSavant(player.id, player.fullName);
                if (pSav2 && Object.keys(pSav2.seasons || {}).length > 0) {
                  const scP2 = projectPitcherFromStatcast(pSav2, player.currentAge, player.fullName, player.id);
                  if (scP2) { base = scP2; } else {
                    base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                  }
                } else {
                  base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                }"""

new_vpd_pitcher = """                base = projectPitcher(career, player.currentAge, player.fullName, player.id);"""

if old_vpd_pitcher in src:
    src = src.replace(old_vpd_pitcher, new_vpd_pitcher)
    changes += 1
    print("3. VpD pitcher path now uses projectPitcher() router")

# Check for duplicate VpD pitcher blocks
count = src.count(old_vpd_pitcher)
if count > 0:
    src = src.replace(old_vpd_pitcher, new_vpd_pitcher)
    changes += 1
    print(f"3b. Fixed {count} additional VpD pitcher block(s)")

# ═══════════════════════════════════════════════════════════════
# 4. Fix Compare pitcher path to use the router (currently only uses Marcel)
# ═══════════════════════════════════════════════════════════════

old_compare_pitcher = """      if (isPitcher) {
        base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), (fullPlayer || player).currentAge, (fullPlayer || player).fullName, (fullPlayer || player).id);"""

new_compare_pitcher = """      if (isPitcher) {
        base = projectPitcher(career, (fullPlayer || player).currentAge, (fullPlayer || player).fullName, (fullPlayer || player).id);"""

if old_compare_pitcher in src:
    src = src.replace(old_compare_pitcher, new_compare_pitcher)
    changes += 1
    print("4. Compare pitcher path now uses projectPitcher() router")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("All tabs now use the same projection router:")
print("  Hitters:  projectPlayer() -> Statcast (250+ PA) or Marcel")
print("  Pitchers: projectPitcher() -> Statcast or Marcel")
print()
print("This means the same player will always show the same WAR,")
print("whether viewed on the player card, leaderboard, compare, or VpD.")
