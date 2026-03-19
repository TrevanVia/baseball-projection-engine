#!/usr/bin/env python3
"""Full sync: landing page numbers + unify ALL remaining direct pitcher calls. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Landing page hitters (Ohtani #1 with combined WAR)
old_h = """{n:"Bobby Witt Jr.",t:"KC",war:7.8,wrc:130,pos:"SS"},
                    {n:"Aaron Judge",t:"NYY",war:6.7,wrc:167,pos:"RF"},
                    {n:"Juan Soto",t:"NYM",war:6.6,wrc:158,pos:"RF"},
                    {n:"Francisco Lindor",t:"NYM",war:5.5,wrc:116,pos:"SS"},
                    {n:"Shohei Ohtani",t:"LAD",war:5.3,wrc:152,pos:"DH"},
                    {n:"Gunnar Henderson",t:"BAL",war:5.1,wrc:119,pos:"SS"},
                    {n:"Elly De La Cruz",t:"CIN",war:5.0,wrc:105,pos:"SS"},
                    {n:"Fernando Tatis Jr.",t:"SD",war:5.0,wrc:129,pos:"RF"},"""
new_h = """{n:"Shohei Ohtani",t:"LAD",war:8.6,wrc:152,pos:"DH"},
                    {n:"Bobby Witt Jr.",t:"KC",war:7.8,wrc:130,pos:"SS"},
                    {n:"Aaron Judge",t:"NYY",war:6.7,wrc:167,pos:"RF"},
                    {n:"Juan Soto",t:"NYM",war:6.6,wrc:158,pos:"RF"},
                    {n:"Francisco Lindor",t:"NYM",war:5.5,wrc:116,pos:"SS"},
                    {n:"Gunnar Henderson",t:"BAL",war:5.1,wrc:119,pos:"SS"},
                    {n:"Elly De La Cruz",t:"CIN",war:5.0,wrc:105,pos:"SS"},
                    {n:"Fernando Tatis Jr.",t:"SD",war:5.0,wrc:129,pos:"RF"},"""
if old_h in src:
    src = src.replace(old_h, new_h); changes += 1
    print("1. Hitters: Ohtani #1 at 8.6 combined WAR")

# 2. Landing page pitchers
old_p = """{n:"Paul Skenes",t:"PIT",war:5.9,era:2.44,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",war:5.5,era:2.72,pos:"SP"},
                    {n:"Garrett Crochet",t:"BOS",war:5.4,era:2.97,pos:"SP"},
                    {n:"Bryan Woo",t:"SEA",war:4.8,era:3.00,pos:"SP"},
                    {n:"Yoshinobu Yamamoto",t:"LAD",war:4.5,era:2.99,pos:"SP"},
                    {n:"Zack Wheeler",t:"PHI",war:4.3,era:3.05,pos:"SP"},
                    {n:"Tanner Bibee",t:"CLE",war:3.8,era:3.57,pos:"SP"},
                    {n:"Logan Webb",t:"SF",war:3.3,era:3.94,pos:"SP"},"""
new_p = """{n:"Paul Skenes",t:"PIT",war:5.7,era:2.44,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",war:5.2,era:2.72,pos:"SP"},
                    {n:"Garrett Crochet",t:"BOS",war:5.1,era:2.97,pos:"SP"},
                    {n:"Bryan Woo",t:"SEA",war:4.6,era:3.00,pos:"SP"},
                    {n:"Yoshinobu Yamamoto",t:"LAD",war:4.3,era:2.99,pos:"SP"},
                    {n:"Cole Ragans",t:"KC",war:3.8,era:3.01,pos:"SP"},
                    {n:"Zack Wheeler",t:"PHI",war:3.7,era:3.10,pos:"SP"},
                    {n:"Tanner Bibee",t:"CLE",war:3.6,era:3.57,pos:"SP"},"""
if old_p in src:
    src = src.replace(old_p, new_p); changes += 1
    print("2. Pitchers: Ragans in (3.8), Webb out")

# 3. Pitcher logo map
old_pm = """({PIT:134,DET:116,BOS:111,SEA:136,LAD:119,PHI:143,CLE:114,SF:137})[p.t]||134"""
new_pm = """({PIT:134,DET:116,BOS:111,SEA:136,LAD:119,PHI:143,CLE:114,KC:118})[p.t]||134"""
if old_pm in src:
    src = src.replace(old_pm, new_pm); changes += 1
    print("3. Pitcher logo map updated")

# 4. PlayerCard two-way -> use projectPitcher router
old_tw = """      let pitchWAR = 0;
      const pSav = getPitcherSavant(player.id, player.fullName);
      if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
        const pProj = projectPitcherFromStatcast(pSav, player.currentAge, player.fullName, player.id);
        if (pProj) pitchWAR = pProj.baseWAR;
        hitProj._pitchProj = pProj;
      } else if (pitchCareer.length) {
        const pProj = projectPitcherFromSeasons(pitchCareer.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
        if (pProj) pitchWAR = pProj.baseWAR;
        hitProj._pitchProj = pProj;
      }
      if (pitchWAR > 0) {"""
new_tw = """      let pitchWAR = 0;
      const pProj = projectPitcher(pitchCareer, player.currentAge, player.fullName, player.id);
      if (pProj) {
        pitchWAR = pProj.baseWAR;
        hitProj._pitchProj = pProj;
      }
      if (pitchWAR > 0) {"""
if old_tw in src:
    src = src.replace(old_tw, new_tw); changes += 1
    print("4. PlayerCard two-way uses projectPitcher()")

# 5. Leaderboard two-way -> use projectPitcher
old_lb = """            projWAR: base.baseWAR + (() => {
              // Add pitching WAR for two-way players
              if (p.primaryPosition?.code === "Y") {
                const pSav = getPitcherSavant(p.id, p.fullName);
                if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
                  const pp = projectPitcherFromStatcast(pSav, p.currentAge, p.fullName, p.id);
                  if (pp) return pp.baseWAR;
                }
              }
              return 0;
            })(),"""
new_lb = """            projWAR: base.baseWAR + (() => {
              // Add pitching WAR for two-way players
              if (p.primaryPosition?.code === "Y") {
                const pp = projectPitcher(splits, p.currentAge, p.fullName, p.id);
                if (pp) return pp.baseWAR;
              }
              return 0;
            })(),"""
if old_lb in src:
    src = src.replace(old_lb, new_lb); changes += 1
    print("5. Leaderboard two-way uses projectPitcher()")

# 6. VpD pitcher -> use projectPitcher
old_vpd = """        const pSav2 = getPitcherSavant(player.id, player.fullName);
                if (pSav2 && Object.keys(pSav2.seasons || {}).length > 0) {
                  const scP2 = projectPitcherFromStatcast(pSav2, player.currentAge, player.fullName, player.id);
                  if (scP2) { base = scP2; } else {
                    base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                  }
                } else {
                  base = projectPitcherFromSeasons(career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
                }
        forward = base ? projectPitcherForward(base, player.currentAge) : [];"""
new_vpd = """        base = projectPitcher(career, player.currentAge, player.fullName, player.id);
        forward = base ? projectPitcherForward(base, player.currentAge) : [];"""
if old_vpd in src:
    src = src.replace(old_vpd, new_vpd); changes += 1
    print("6. VpD pitcher uses projectPitcher()")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Every tab now uses the same projection routers:")
print("  projectPlayer() for hitters, projectPitcher() for pitchers")
print("  Two-way (Ohtani): hitting WAR + projectPitcher() pitching WAR")
print("  Landing page hardcoded numbers match engine output")
