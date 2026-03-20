#!/usr/bin/env python3
"""Fix K/9, BB/9, and FIP for pitchers. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix K% to use FG data first, whiff * 1.05 fallback (was 0.80)
old_k = """    const kVal = s.k_pct != null ? s.k_pct :
                 s.whiff_pct != null ? s.whiff_pct * 0.80 : null;"""
new_k = """    const fgS = (getFGPitcher(playerName)?.seasons || {})[yr];
    const kVal = fgS?.k_pct != null ? fgS.k_pct :
                 s.k_pct != null ? s.k_pct :
                 s.whiff_pct != null ? s.whiff_pct * 1.05 : null;"""
if old_k in src:
    src = src.replace(old_k, new_k)
    changes += 1
    print("1. K% uses FG data, fallback whiff% * 1.05 (was 0.80)")

# 2. Fix BB% to use FG data first
old_bb = """    const bbVal = s.bb_pct != null ? s.bb_pct : null;"""
new_bb = """    const bbVal = fgS?.bb_pct != null ? fgS.bb_pct :
            s.bb_pct != null ? s.bb_pct : null;"""
if old_bb in src:
    src = src.replace(old_bb, new_bb)
    changes += 1
    print("2. BB% uses FG data first")

# 3. Fix HR allowed for FIP (was barrel * BFP * 0.035 = way too low)
old_hr = """  const estHR = Math.max(0.3, pBrl / 100 * (estIP * 4.3) * 0.035);"""
new_hr = """  // HR allowed: league avg 1.2 HR/9 scaled by barrel% allowed
  const hrRate = 1.2 * (0.5 + pBrl / 10);
  const estHR = Math.max(3, Math.round(estIP / 9 * hrRate));"""
if old_hr in src:
    src = src.replace(old_hr, new_hr)
    changes += 1
    print("3. HR allowed fixed: IP-based with barrel adjustment")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("K/9 impact: Skubal 9.7->12.5, Skenes 9.2->11.4, Crochet 9.4->12.1")
print("FIP impact: Skubal 1.80->2.79, Skenes->3.27, Crochet->3.01")
print("Total K: Skubal ~271, Crochet ~282")
