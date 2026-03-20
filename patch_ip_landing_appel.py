#!/usr/bin/env python3
"""Fix IP projections, update landing page, remove Appel credit. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix Statcast pitcher IP estimation
old_ip = """    const baseIP = Math.max(latIP, careerMaxIP * 0.70);
    estIP = Math.max(140, Math.min(210, baseIP * 0.98));"""
new_ip = """    // Use FG IP data: best full season (100+ IP) with age adjustment
    let bestFullIP = 0;
    const fgP = getFGPitcher(playerName);
    if (fgP) {
      Object.values(fgP.seasons || {}).forEach(s => {
        if (s.ip >= 100 && s.ip > bestFullIP) bestFullIP = s.ip;
      });
    }
    const ipAgeFactor = age <= 27 ? 1.03 : age <= 30 ? 1.00 : age <= 33 ? 0.97 : 0.93;
    const baseIP = Math.max(bestFullIP, latIP, careerMaxIP * 0.70);
    estIP = Math.max(140, Math.min(210, Math.round(baseIP * ipAgeFactor)));"""
if old_ip in src:
    src = src.replace(old_ip, new_ip)
    changes += 1
    print("1. Fixed Statcast pitcher IP: FG best full season + age adjustment")

# 2. Fix Marcel pitcher IP estimation
old_mip = """    estIP = isLikelyStarter ? Math.max(140, Math.min(210, rawIP * 0.97)) : Math.min(70, rawIP * 0.96);"""
new_mip = """    if (isLikelyStarter) {
      let bestFullIP2 = 0;
      const fgP2 = getFGPitcher(playerName);
      if (fgP2) {
        Object.values(fgP2.seasons || {}).forEach(s => {
          if (s.ip >= 100 && s.ip > bestFullIP2) bestFullIP2 = s.ip;
        });
      }
      const ipAgeFactor2 = age <= 27 ? 1.03 : age <= 30 ? 1.00 : age <= 33 ? 0.97 : 0.93;
      estIP = Math.max(140, Math.min(210, Math.round(Math.max(bestFullIP2, rawIP) * ipAgeFactor2)));
    } else {
      estIP = Math.min(70, Math.round(rawIP * 0.96));
    }"""
if old_mip in src:
    src = src.replace(old_mip, new_mip)
    changes += 1
    print("2. Fixed Marcel pitcher IP: same FG-based approach")

# 3. Update landing page pitcher numbers (with IP-boosted WAR)
old_p = """{n:"Garrett Crochet",t:"BOS",war:5.7,era:2.70,pos:"SP"},
                    {n:"Paul Skenes",t:"PIT",war:5.0,era:2.79,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",war:5.0,era:2.86,pos:"SP"},
                    {n:"Logan Webb",t:"SF",war:4.5,era:3.38,pos:"SP"},
                    {n:"Yoshinobu Yamamoto",t:"LAD",war:3.8,era:3.26,pos:"SP"},
                    {n:"Bryan Woo",t:"SEA",war:3.6,era:3.50,pos:"SP"},
                    {n:"Cole Ragans",t:"KC",war:3.5,era:3.19,pos:"SP"},
                    {n:"Zack Wheeler",t:"PHI",war:3.0,era:3.51,pos:"SP"},"""
new_p = """{n:"Garrett Crochet",t:"BOS",war:6.5,era:2.70,pos:"SP"},
                    {n:"Paul Skenes",t:"PIT",war:5.8,era:2.79,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",war:5.7,era:2.86,pos:"SP"},
                    {n:"Logan Webb",t:"SF",war:4.8,era:3.38,pos:"SP"},
                    {n:"Cole Ragans",t:"KC",war:4.7,era:3.19,pos:"SP"},
                    {n:"Yoshinobu Yamamoto",t:"LAD",war:4.3,era:3.26,pos:"SP"},
                    {n:"Bryan Woo",t:"SEA",war:4.1,era:3.50,pos:"SP"},
                    {n:"Zack Wheeler",t:"PHI",war:4.0,era:3.51,pos:"SP"},"""
if old_p in src:
    src = src.replace(old_p, new_p)
    changes += 1
    print("3. Updated landing page pitcher WAR (IP boost)")

# 4. Remove Appel credit from code comment
old_comment = "  // Layered ERA anchor (Appel ranking: SIERA > xFIP > xERA > FIP > K-BB > ERA)"
new_comment = "  // Layered ERA anchor: SIERA > xFIP > xERA > FIP > K-BB > ERA"
if old_comment in src:
    src = src.replace(old_comment, new_comment)
    changes += 1
    print("4. Removed Appel credit from code comment")

# 5. Remove Appel credit from methodology page
old_method = """based on Peter Appel's predictive ranking: SIERA (primary)"""
new_method = """SIERA (primary)"""
if old_method in src:
    src = src.replace(old_method, new_method)
    changes += 1
    print("5. Removed Appel credit from methodology page")

# 6. Also update methodology IP section if it still references old method
old_ip_method = """Returning starters project minimum 140 IP using 70% of career-max as floor."""
new_ip_method = """IP projection uses the best full season (100+ IP) from FanGraphs data with an age-based workload adjustment: ≤27 × 1.03 (trending up), 28-30 × 1.00 (peak workload), 31-33 × 0.97, 34+ × 0.93. Capped at 210 IP."""
if old_ip_method in src:
    src = src.replace(old_ip_method, new_ip_method)
    changes += 1
    print("6. Updated methodology IP description")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
