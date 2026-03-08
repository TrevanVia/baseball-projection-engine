#!/usr/bin/env python3
"""Unify projection paths across all tabs. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Only add projectPitcher() if it doesn't already exist
if "function projectPitcher(" not in src:
    old = """function projectFromSeasons(splits, age, posCode, playerName, playerId) {"""
    new = """// Unified pitcher projection router (mirrors projectPlayer for hitters)
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
    if old in src:
        src = src.replace(old, new, 1)
        changes += 1
        print("1. Created projectPitcher() router")
else:
    print("1. projectPitcher() already exists — skipping")

# 2. PlayerCard: use routers instead of direct calls
old_card = """    if (isPitcher) {
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

new_card = """    if (isPitcher) {
      return pitchCareer.length ? projectPitcher(pitchCareer, player.currentAge, player.fullName, player.id) : null;
    }
    // Hitter projection — uses same router as leaderboard & compare
    let hitProj = career.length
      ? projectPlayer(career.filter(s => s.stat?.plateAppearances > 0), player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id)
      : null;"""

if old_card in src:
    src = src.replace(old_card, new_card)
    changes += 1
    print("2. PlayerCard now uses unified routers")
else:
    print("2. PlayerCard already unified — skipping")

# 3. VpD pitcher paths
old_vpd = """                const pSav2 = getPitcherSavant(player.id, player.fullName);
                if (pSav2 && Object.keys(pSav2.seasons || {}).length > 0) {
                  const scP2 = projectPitcherFromStatcast(pSav2, player.currentAge, player.fullName, player.id);
                  if (scP2) { base = scP2; } else {
                    base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                  }
                } else {
                  base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                }"""

new_vpd = """                base = projectPitcher(career, player.currentAge, player.fullName, player.id);"""

vpd_count = src.count(old_vpd)
if vpd_count > 0:
    src = src.replace(old_vpd, new_vpd)
    changes += vpd_count
    print(f"3. Fixed {vpd_count} VpD pitcher block(s)")
else:
    print("3. VpD already unified — skipping")

# 4. Compare pitcher path
old_compare = """      if (isPitcher) {
        base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), (fullPlayer || player).currentAge, (fullPlayer || player).fullName, (fullPlayer || player).id);"""

new_compare = """      if (isPitcher) {
        base = projectPitcher(career, (fullPlayer || player).currentAge, (fullPlayer || player).fullName, (fullPlayer || player).id);"""

if old_compare in src:
    src = src.replace(old_compare, new_compare)
    changes += 1
    print("4. Compare pitcher path unified")
else:
    print("4. Compare already unified — skipping")

# 5. Leaderboard pitcher batch
old_lb = """          const pSavV = getPitcherSavant(p.id, p.fullName);
                let base;
                if (pSavV && Object.keys(pSavV.seasons || {}).length > 0) {
                  base = projectPitcherFromStatcast(pSavV, p.currentAge, p.fullName, p.id) || projectPitcherFromSeasons(splits, p.currentAge, p.fullName, p.id);
                } else {
                  base = projectPitcherFromSeasons(splits, p.currentAge, p.fullName, p.id);
                }"""

new_lb = """          let base = projectPitcher(splits, p.currentAge, p.fullName, p.id);"""

if old_lb in src:
    src = src.replace(old_lb, new_lb)
    changes += 1
    print("5. Leaderboard pitcher batch unified")
else:
    print("5. Leaderboard already unified — skipping")

# 6. Any remaining inline pitcher projection
old_inline = """            ? projectPitcherFromSeasons(splits, player.currentAge, player.fullName, player.id)"""
new_inline = """            ? projectPitcher(splits, player.currentAge, player.fullName, player.id)"""
if old_inline in src:
    src = src.replace(old_inline, new_inline)
    changes += 1
    print("6. Fixed inline pitcher projection")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
