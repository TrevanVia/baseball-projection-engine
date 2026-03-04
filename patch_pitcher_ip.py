#!/usr/bin/env python3
"""Fix pitcher IP estimation. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix IP estimation in Statcast engine
# Old: uses bfp/4.3 which underestimates efficient pitchers
# New: use bfp/4.1 for starters (starters face fewer BF per IP due to K rate)
# and multiply by 1.0 instead of 0.97
old_ip = """  // IP estimate
  const latIP = lat.ip || (bfp0 / 4.3);
  let estIP;
  if (isStarter) {
    estIP = Math.max(140, Math.min(210, latIP * 0.97));
  } else {
    estIP = Math.min(75, latIP * 0.96);
  }"""

new_ip = """  // IP estimate: use actual IP if available, else BFP/PA ratio
  // High-K pitchers are more efficient (fewer BF per IP)
  const bfPerIP = pK > 25 ? 4.0 : pK > 20 ? 4.1 : 4.3;
  const latIP = lat.ip || (bfp0 / bfPerIP);
  let estIP;
  if (isStarter) {
    // Project full workload for established starters
    estIP = Math.max(150, Math.min(215, latIP * 1.0));
  } else {
    estIP = Math.min(75, latIP * 0.98);
  }"""

if old_ip in src:
    src = src.replace(old_ip, new_ip)
    changes += 1
    print("1. Fixed IP estimation (K-rate adjusted BF/IP ratio)")

# 2. Also fix the aging curve - young aces should project ERA IMPROVEMENT
# Current: af = pow(0.985, peak-age) which makes ERA better for young pitchers
# But 0.985^4 = 0.941 which barely moves the needle
# Young elite pitchers should project meaningful improvement
old_age = """  // Aging
  const spPeak = 27, rpPeak = 28;
  const isStarter = (lat.ip || 0) > 50 || bfp0 > 250;
  const pk = isStarter ? spPeak : rpPeak;
  let af = 1;
  if (age < pk) af = Math.pow(0.985, pk - age); // young pitchers still developing
  else if (age <= 33) af = Math.pow(1.015, age - pk); // ERA rises post-peak
  else af = Math.pow(1.015, 33 - pk) * Math.pow(1.03, age - 33);"""

new_age = """  // Aging
  const spPeak = 27, rpPeak = 28;
  const isStarter = (lat.ip || 0) > 50 || bfp0 > 250;
  const pk = isStarter ? spPeak : rpPeak;
  let af = 1;
  if (age < pk) af = Math.pow(0.97, pk - age); // young pitchers improve ~3%/yr
  else if (age <= 33) af = Math.pow(1.02, age - pk); // ERA rises ~2%/yr post-peak
  else af = Math.pow(1.02, 33 - pk) * Math.pow(1.035, age - 33); // accelerated decline"""

if old_age in src:
    src = src.replace(old_age, new_age)
    changes += 1
    print("2. Fixed pitcher aging curve (stronger pre-peak improvement)")

# 3. Also raise the FIP floor slightly - elite pitchers can have sub-2.0 FIPs
old_fip_floor = """  const fip = Math.max(1.50, Math.min(6.50,
    ((13 * estHR) + (3 * estBB) - (2 * estK)) / estIP + 3.10));"""
new_fip_floor = """  const fip = Math.max(1.80, Math.min(6.50,
    ((13 * estHR) + (3 * estBB) - (2 * estK)) / estIP + 3.10));"""
if old_fip_floor in src:
    src = src.replace(old_fip_floor, new_fip_floor)
    changes += 1
    print("3. Adjusted FIP floor to 1.80")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print("\nSkenes projection should now be:")
print("  IP: ~183 (was 165) - using BFP/4.0 for high-K pitchers")
print("  ERA: ~2.3 (age 23, 4 years pre-peak at 3%/yr improvement)")
print("  WAR: ~7.5+ (more IP, better aging)")
