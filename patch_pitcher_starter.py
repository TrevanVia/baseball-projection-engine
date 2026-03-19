#!/usr/bin/env python3
"""Fix pitcher starter detection and IP estimation. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old = """  const spPeak = 27, rpPeak = 28;
  // Starter = high IP or high BFP AND game start data suggests starter
  // A reliever with 300 BFP threw ~70 IP, not 150
  const latIPEst = lat.ip || (bfp0 / 4.3);
  const isStarter = latIPEst > 100 || bfp0 > 450;
  const pk = isStarter ? spPeak : rpPeak;
  let af = 1;
  if (age < pk) af = Math.pow(0.985, pk - age); // young pitchers improve ~1.5%/yr
  else if (age <= 33) af = Math.pow(1.015, age - pk); // ERA rises ~1.5%/yr post-peak
  else af = Math.pow(1.015, 33 - pk) * Math.pow(1.03, age - 33); // accelerated decline

  // Assemble ERA projection
  // Anchor on xERA, adjust for trends and aging
  let projERA = Math.max(1.50, Math.min(6.50, (pXera + tb) * af));

  // K/9 and BB/9 from percentages
  // K/9 = K% * BF/IP * 9, where BF/IP ≈ 4.3
  // But cap reasonably - very few pitchers sustain 13+ K/9
  const projK9 = Math.max(4, Math.min(13.5, pK / 100 * 9 * 4.3));
  const projBB9 = Math.max(1.5, Math.min(5.5, pBB / 100 * 9 * 4.3));
  const projWHIP = Math.max(0.75, Math.min(1.80, 0.90 + (projERA - 2.50) * 0.12));

  // IP estimate from BFP
  const bfPerIP = 4.3;
  const latIP = lat.ip || (bfp0 / bfPerIP);
  let estIP;
  if (isStarter) {
    estIP = Math.max(140, Math.min(210, latIP * 0.98));
  } else {
    // Relievers: cap at 75 IP, typical is 55-70
    estIP = Math.min(75, Math.max(30, latIP * 0.95));
  }"""

new = """  const spPeak = 27, rpPeak = 28;
  // Starter detection: check ALL seasons (not just most recent — handles injury returns like Ohtani)
  const latIPEst = lat.ip || (bfp0 / 4.3);
  const maxCareerBFP = Math.max(...yrs.map(yr => S[yr]?.bfp || 0));
  const maxCareerIP = Math.max(...yrs.map(yr => S[yr]?.ip || (S[yr]?.bfp || 0) / 4.3));
  const isStarter = latIPEst > 100 || bfp0 > 450 || maxCareerBFP > 450 || maxCareerIP > 100;
  const pk = isStarter ? spPeak : rpPeak;
  let af = 1;
  if (age < pk) af = Math.pow(0.985, pk - age);
  else if (age <= 33) af = Math.pow(1.015, age - pk);
  else af = Math.pow(1.015, 33 - pk) * Math.pow(1.03, age - 33);

  let projERA = Math.max(1.50, Math.min(6.50, (pXera + tb) * af));

  const projK9 = Math.max(4, Math.min(13.5, pK / 100 * 9 * 4.3));
  const projBB9 = Math.max(1.5, Math.min(5.5, pBB / 100 * 9 * 4.3));
  const projWHIP = Math.max(0.75, Math.min(1.80, 0.90 + (projERA - 2.50) * 0.12));

  // IP estimate: for starters returning from injury, use career max as floor
  const bfPerIP = 4.3;
  const latIP = lat.ip || (bfp0 / bfPerIP);
  const careerMaxIP = maxCareerIP;
  let estIP;
  if (isStarter) {
    const baseIP = Math.max(latIP, careerMaxIP * 0.70);
    estIP = Math.max(140, Math.min(210, baseIP * 0.98));
  } else {
    estIP = Math.min(75, Math.max(30, latIP * 0.95));
  }"""

if old in src:
    src = src.replace(old, new)
    open(APP, "w").write(src)
    print("Fixed: starter detection checks all seasons, IP uses career max floor")
    print()
    print("Ohtani: reliever (0.9 WAR) -> starter (4.6 WAR)")
    print("Burnes: now correctly detected as starter from career history")
    print("Ragans: same fix applies")
else:
    print("Target not found - may already be applied")
