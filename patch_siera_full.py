#!/usr/bin/env python3
"""SIERA pitcher engine + full landing page sync. Run from project root.
IMPORTANT: First copy fg_pitcher_data.json to src/ directory."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. SIERA ENGINE: Import + Lookup + Layered Anchor
# ═══════════════════════════════════════════════════════════════

# 1a. Import
old_imp = 'import baserunningDataJson from "./baserunning_data.json";'
new_imp = '''import baserunningDataJson from "./baserunning_data.json";
import fgPitcherDataJson from "./fg_pitcher_data.json";'''
if new_imp not in src and old_imp in src:
    src = src.replace(old_imp, new_imp)
    changes += 1
    print("1. Added FG pitcher data import")

# 1b. Lookup function
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

# 1c. Layered ERA anchor
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

# ═══════════════════════════════════════════════════════════════
# 2. LANDING PAGE SYNC
# ═══════════════════════════════════════════════════════════════

# 2a. Hitters (Ohtani 8.5 combined with SIERA-based pitching WAR)
old_h = """{n:"Shohei Ohtani",t:"LAD",war:8.6,wrc:152,pos:"DH"},
                    {n:"Bobby Witt Jr.",t:"KC",war:7.8,wrc:130,pos:"SS"},
                    {n:"Aaron Judge",t:"NYY",war:6.7,wrc:167,pos:"RF"},
                    {n:"Juan Soto",t:"NYM",war:6.6,wrc:158,pos:"RF"},
                    {n:"Francisco Lindor",t:"NYM",war:5.5,wrc:116,pos:"SS"},
                    {n:"Gunnar Henderson",t:"BAL",war:5.1,wrc:119,pos:"SS"},
                    {n:"Elly De La Cruz",t:"CIN",war:5.0,wrc:105,pos:"SS"},
                    {n:"Fernando Tatis Jr.",t:"SD",war:5.0,wrc:129,pos:"RF"},"""

new_h = """{n:"Shohei Ohtani",t:"LAD",war:8.5,wrc:152,pos:"DH"},
                    {n:"Bobby Witt Jr.",t:"KC",war:7.8,wrc:130,pos:"SS"},
                    {n:"Aaron Judge",t:"NYY",war:6.7,wrc:167,pos:"RF"},
                    {n:"Juan Soto",t:"NYM",war:6.6,wrc:158,pos:"RF"},
                    {n:"Francisco Lindor",t:"NYM",war:5.5,wrc:116,pos:"SS"},
                    {n:"Gunnar Henderson",t:"BAL",war:5.1,wrc:119,pos:"SS"},
                    {n:"Elly De La Cruz",t:"CIN",war:5.0,wrc:105,pos:"SS"},
                    {n:"Fernando Tatis Jr.",t:"SD",war:5.0,wrc:129,pos:"RF"},"""
if old_h in src:
    src = src.replace(old_h, new_h)
    changes += 1
    print("4. Updated hitter landing (Ohtani 8.6 -> 8.5 with SIERA pitching)")

# 2b. Pitchers (major reshuffle with SIERA)
old_p = """{n:"Paul Skenes",t:"PIT",war:5.7,era:2.44,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",war:5.2,era:2.72,pos:"SP"},
                    {n:"Garrett Crochet",t:"BOS",war:5.1,era:2.97,pos:"SP"},
                    {n:"Bryan Woo",t:"SEA",war:4.6,era:3.00,pos:"SP"},
                    {n:"Yoshinobu Yamamoto",t:"LAD",war:4.3,era:2.99,pos:"SP"},
                    {n:"Cole Ragans",t:"KC",war:3.8,era:3.01,pos:"SP"},
                    {n:"Zack Wheeler",t:"PHI",war:3.7,era:3.10,pos:"SP"},
                    {n:"Tanner Bibee",t:"CLE",war:3.6,era:3.57,pos:"SP"},"""

new_p = """{n:"Garrett Crochet",t:"BOS",war:5.7,era:2.70,pos:"SP"},
                    {n:"Paul Skenes",t:"PIT",war:5.0,era:2.79,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",war:5.0,era:2.86,pos:"SP"},
                    {n:"Logan Webb",t:"SF",war:4.5,era:3.38,pos:"SP"},
                    {n:"Yoshinobu Yamamoto",t:"LAD",war:3.8,era:3.26,pos:"SP"},
                    {n:"Bryan Woo",t:"SEA",war:3.6,era:3.50,pos:"SP"},
                    {n:"Cole Ragans",t:"KC",war:3.5,era:3.19,pos:"SP"},
                    {n:"Zack Wheeler",t:"PHI",war:3.0,era:3.51,pos:"SP"},"""
if old_p in src:
    src = src.replace(old_p, new_p)
    changes += 1
    print("5. Updated pitcher landing (Crochet #1, Webb enters, SIERA-based)")

# 2c. Pitcher logo map (need SF back, remove CLE)
old_pm = """({PIT:134,DET:116,BOS:111,SEA:136,LAD:119,PHI:143,CLE:114,KC:118})[p.t]||134"""
new_pm = """({PIT:134,DET:116,BOS:111,SEA:136,LAD:119,PHI:143,SF:137,KC:118})[p.t]||134"""
if old_pm in src:
    src = src.replace(old_pm, new_pm)
    changes += 1
    print("6. Updated pitcher logo map (SF back in)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Pitcher leaderboard reshuffle (SIERA-based):")
print("  #1 Crochet 5.7 (was #3) — elite K-BB profile")
print("  #2 Skenes 5.0 (was #1) — SIERA slightly higher than xERA")
print("  #3 Skubal 5.0 (was #2)")
print("  #4 Webb 4.5 (NEW) — SIERA loves his GB rate")
print("  Bibee drops out, Wheeler drops to #8")
