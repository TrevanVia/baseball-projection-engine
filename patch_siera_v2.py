#!/usr/bin/env python3
"""Switch pitcher anchor to SIERA with full fallback chain. Run from project root.
IMPORTANT: First copy fg_pitcher_data.json to src/ directory."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Add import
old_imp = 'import baserunningDataJson from "./baserunning_data.json";'
new_imp = '''import baserunningDataJson from "./baserunning_data.json";
import fgPitcherDataJson from "./fg_pitcher_data.json";'''
if new_imp not in src and old_imp in src:
    src = src.replace(old_imp, new_imp)
    changes += 1
    print("1. Added import for fg_pitcher_data.json")

# 2. Add lookup function (insert before BsR section)
old_bsr = '// Statcast Baserunning Run Value (runs above average, seasonal)'
new_bsr = '''// FanGraphs Pitcher Data (SIERA, xFIP, FIP, K%, BB%, GB%)
const FG_PITCHER = fgPitcherDataJson || {};
function getFGPitcher(playerName) {
  return FG_PITCHER[playerName] || null;
}

// Statcast Baserunning Run Value (runs above average, seasonal)'''
if 'FG_PITCHER' not in src and old_bsr in src:
    src = src.replace(old_bsr, new_bsr, 1)
    changes += 1
    print("2. Added getFGPitcher() lookup")

# 3. Replace ERA anchor line with layered system
old_era = '  let projERA = Math.max(1.50, Math.min(6.50, (pXera + tb) * af));'
new_era = '''  // Layered ERA anchor (Appel ranking: SIERA > xFIP > xERA > FIP > K-BB > ERA)
  const fg = getFGPitcher(playerName);
  let eraAnchor = pXera; // default: xERA from Savant
  if (fg) {
    const fgYrs = Object.keys(fg.seasons || {}).sort().reverse().slice(0, 3);
    const fgW = [0.55, 0.30, 0.15];
    let wSiera = 0, wXfip = 0, wFip = 0, wKbb = 0, wEra = 0, fgtw = 0;
    fgYrs.forEach((yr, i) => {
      const s = fg.seasons[yr];
      const w = fgW[i] || 0.05;
      const ipW = w * Math.min(1, (s.ip || 0) / 100);
      if (s.siera != null) wSiera += s.siera * ipW;
      if (s.xfip != null) wXfip += s.xfip * ipW;
      if (s.fip != null) wFip += s.fip * ipW;
      if (s.kbb_pct != null) wKbb += (5.40 - s.kbb_pct * 0.10) * ipW;
      if (s.era != null) wEra += s.era * ipW;
      fgtw += ipW;
    });
    if (fgtw > 0) {
      if (wSiera > 0) eraAnchor = wSiera / fgtw;
      else if (wXfip > 0) eraAnchor = wXfip / fgtw;
      else if (wFip > 0) eraAnchor = wFip / fgtw;
      else if (wKbb > 0) eraAnchor = wKbb / fgtw;
      else if (wEra > 0) eraAnchor = wEra / fgtw;
    }
  }
  let projERA = Math.max(1.50, Math.min(6.50, (eraAnchor + tb) * af));'''

if old_era in src:
    src = src.replace(old_era, new_era, 1)
    changes += 1
    print("3. Replaced ERA anchor: SIERA > xFIP > xERA > FIP > K-BB > ERA")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
if changes == 3:
    print("\nAll 3 changes applied successfully!")
    print("Now run: npm run build && git add -A && git commit -m 'SIERA-based pitcher projections' && git push")
else:
    print(f"\nWARNING: Expected 3 changes, got {changes}")
