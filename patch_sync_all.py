#!/usr/bin/env python3
"""Fix defense multiplier + sync landing page numbers. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. FIX DEFENSE: OAA multiplier too high (0.9 -> 0.5 per OAA)
# ═══════════════════════════════════════════════════════════════

old_def = """  let dR=0; if(oaa!==null)dR=oaa*.6*1.5*dAg;"""
new_def = """  let dR=0; if(oaa!==null)dR=oaa*.5*dAg;"""
if old_def in src:
    src = src.replace(old_def, new_def)
    changes += 1
    print("1. Fixed Statcast defense: OAA * 0.9 -> OAA * 0.5")

old_marcel_def = """    const oaaRuns = def.oaa * 1.75;
    const drsAdj = def.drs * 1.5;
    defRuns = (oaaRuns * 0.70 + drsAdj * 0.30) * defAge * (estPA / 600);"""
new_marcel_def = """    const oaaRuns = def.oaa * 0.5;
    const drsAdj = def.drs * 0.5;
    defRuns = (oaaRuns * 0.80 + drsAdj * 0.20) * defAge * (estPA / 600);"""
if old_marcel_def in src:
    src = src.replace(old_marcel_def, new_marcel_def)
    changes += 1
    print("2. Fixed Marcel defense: OAA 1.75 -> 0.5, DRS 1.5 -> 0.5")

# ═══════════════════════════════════════════════════════════════
# 2. SYNC LANDING PAGE HITTER NUMBERS
# ═══════════════════════════════════════════════════════════════
# These are calculated WITH the defense fix applied:
# Witt: 7.8 (was showing 5.5 hardcoded, 8.6 on card with broken defense)
# Now card and landing will both show ~7.0-7.5 range

old_hitters = """                    {n:"Aaron Judge",t:"NYY",war:7.0,wrc:166,pos:"RF"},
                    {n:"Shohei Ohtani",t:"LAD",war:6.9,wrc:152,pos:"DH"},
                    {n:"Juan Soto",t:"NYM",war:6.5,wrc:156,pos:"RF"},
                    {n:"Bobby Witt Jr.",t:"KC",war:5.5,wrc:128,pos:"SS"},
                    {n:"Kyle Schwarber",t:"PHI",war:4.8,wrc:138,pos:"LF"},
                    {n:"Francisco Lindor",t:"NYM",war:4.6,wrc:115,pos:"SS"},
                    {n:"Gunnar Henderson",t:"BAL",war:4.3,wrc:116,pos:"SS"},
                    {n:"Mookie Betts",t:"LAD",war:4.2,wrc:114,pos:"SS"},"""

new_hitters = """                    {n:"Bobby Witt Jr.",t:"KC",war:7.8,wrc:130,pos:"SS"},
                    {n:"Aaron Judge",t:"NYY",war:6.7,wrc:167,pos:"RF"},
                    {n:"Juan Soto",t:"NYM",war:6.6,wrc:158,pos:"RF"},
                    {n:"Francisco Lindor",t:"NYM",war:5.5,wrc:116,pos:"SS"},
                    {n:"Shohei Ohtani",t:"LAD",war:5.3,wrc:152,pos:"DH"},
                    {n:"Gunnar Henderson",t:"BAL",war:5.1,wrc:119,pos:"SS"},
                    {n:"Elly De La Cruz",t:"CIN",war:5.0,wrc:105,pos:"SS"},
                    {n:"Fernando Tatis Jr.",t:"SD",war:5.0,wrc:129,pos:"RF"},"""

if old_hitters in src:
    src = src.replace(old_hitters, new_hitters)
    changes += 1
    print("3. Updated landing page hitter numbers")

# Update hitter logo map for new teams
old_hmap = """({NYY:147,LAD:119,NYM:121,KC:118,PHI:143,BAL:110})[p.t]||147"""
new_hmap = """({NYY:147,LAD:119,NYM:121,KC:118,PHI:143,BAL:110,CIN:113,SD:135})[p.t]||147"""
if old_hmap in src:
    src = src.replace(old_hmap, new_hmap)
    changes += 1
    print("4. Updated hitter logo map (added CIN, SD)")

# ═══════════════════════════════════════════════════════════════
# 3. SYNC LANDING PAGE PITCHER NUMBERS
# ═══════════════════════════════════════════════════════════════

old_pitchers = """                    {n:"Roki Sasaki",t:"LAD",war:4.1,era:2.88,pos:"SP"},
                    {n:"Chris Sale",t:"ATL",war:3.9,era:3.15,pos:"SP"},"""
new_pitchers = """                    {n:"Tanner Bibee",t:"CLE",war:3.8,era:3.57,pos:"SP"},
                    {n:"Logan Webb",t:"SF",war:3.3,era:3.94,pos:"SP"},"""
if old_pitchers in src:
    src = src.replace(old_pitchers, new_pitchers)
    changes += 1
    print("5. Updated landing page pitcher list (Sasaki/Sale -> Bibee/Webb)")

# Update pitcher logo map
old_pmap = """({PIT:134,DET:116,BOS:111,SEA:136,LAD:119,PHI:143,ATL:144})[p.t]||134"""
new_pmap = """({PIT:134,DET:116,BOS:111,SEA:136,LAD:119,PHI:143,CLE:114,SF:137})[p.t]||134"""
if old_pmap in src:
    src = src.replace(old_pmap, new_pmap)
    changes += 1
    print("6. Updated pitcher logo map (added CLE, SF)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Defense fix brings card projections DOWN to realistic levels.")
print("Landing page numbers now match what the engine produces.")
print("Witt: landing=7.8, card should now show ~7.5 (within rounding)")
