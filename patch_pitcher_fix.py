#!/usr/bin/env python3
"""Fix pitcher Statcast engine: use xERA for WAR, fix reliever IP. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Replace the FIP-based WAR with xERA-based WAR in the Statcast engine
# The FIP calculation is broken because K% and BB% data is missing (FG Cloudflare)
# xERA is a better metric anyway - it's Statcast's expected ERA based on quality of contact
old_fip_war = """  // FIP from components
  const estK = projK9 * estIP / 9;
  const estBB = projBB9 * estIP / 9;
  const estHR = Math.max(0.3, pBrl / 100 * (estIP * 4.3) * 0.035);
  const fip = Math.max(1.80, Math.min(6.50,
    ((13 * estHR) + (3 * estBB) - (2 * estK)) / estIP + 3.10));

  // WAR: FIP vs replacement level (FG uses 0.12 wins/game for SP)
  // replLevel = 0.12 * 9.5 + lgFIP = 5.34
  const replLevel = 5.34;
  const rpw = 9.5;
  const rawWAR = ((replLevel - fip) / rpw) * (estIP / 9);"""

new_fip_war = """  // WAR: use projected ERA (derived from xERA) vs replacement level
  // xERA is more reliable than FIP when K%/BB% data may be incomplete
  // FG replacement: 0.12 wins/game for SP, 0.03 for RP
  const replLevel = 5.34;
  const rpw = 9.5;
  const rpReplLevel = isStarter ? 5.34 : 4.49; // RP: 0.03*9.5+4.20=4.49
  const useRepl = isStarter ? replLevel : rpReplLevel;
  const rawWAR = ((useRepl - projERA) / rpw) * (estIP / 9);

  // Also compute FIP for display (even if not used for WAR)
  const estK = projK9 * estIP / 9;
  const estBB = projBB9 * estIP / 9;
  const estHR = Math.max(0.3, pBrl / 100 * (estIP * 4.3) * 0.035);
  const fip = Math.max(1.80, Math.min(6.50,
    ((13 * estHR) + (3 * estBB) - (2 * estK)) / estIP + 3.10));"""

if old_fip_war in src:
    src = src.replace(old_fip_war, new_fip_war)
    changes += 1
    print("1. Switched Statcast WAR from FIP to xERA-based (more reliable)")

# 2. Fix reliever IP estimation - relievers should NOT project 150+ IP
# Current: isStarter check uses (lat.ip || 0) > 50 || bfp0 > 250
# But bfp0 > 250 catches relievers with 250+ BFP in a season
# A reliever with 300 BFP only threw about 70 IP, not 150+
old_starter_check = """  const isStarter = (lat.ip || 0) > 50 || bfp0 > 250;"""
new_starter_check = """  // Starter = high IP or high BFP AND game start data suggests starter
  // A reliever with 300 BFP threw ~70 IP, not 150
  const latIPEst = lat.ip || (bfp0 / 4.3);
  const isStarter = latIPEst > 100 || bfp0 > 450;"""

if old_starter_check in src:
    src = src.replace(old_starter_check, new_starter_check)
    changes += 1
    print("2. Fixed starter detection (reliever BFP threshold raised)")

# 3. Fix reliever IP cap and starter minimum
old_ip_est = """  // IP estimate: use actual IP if available, else BFP/PA ratio
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

new_ip_est = """  // IP estimate from BFP
  const bfPerIP = 4.3;
  const latIP = lat.ip || (bfp0 / bfPerIP);
  let estIP;
  if (isStarter) {
    estIP = Math.max(140, Math.min(210, latIP * 0.98));
  } else {
    // Relievers: cap at 75 IP, typical is 55-70
    estIP = Math.min(75, Math.max(30, latIP * 0.95));
  }"""

if old_ip_est in src:
    src = src.replace(old_ip_est, new_ip_est)
    changes += 1
    print("3. Fixed IP estimation (reliever cap, conservative starter est)")

# 4. Fix the K% default - 22% is too generous when data is missing
# Derive a rough K% from whiff% when available (whiff * 0.85 ≈ K%)
# Also fix the command layer to use whiff more correctly
old_command = """  // L2: Command (K%, BB%, SwStr%)
  let wk = 0, wbb = 0, wsw = 0, tw2 = 0;
  yrs.forEach((yr, i) => {
    const s = S[yr], w = W[i] || 0.05, pw = w * Math.min(1, (s.bfp || 0) / 200);
    if (s.k_pct != null) { wk += s.k_pct * pw; tw2 += pw; }
    if (s.bb_pct != null) wbb += s.bb_pct * pw;
    if (s.swstr != null) wsw += s.swstr * pw;
    else if (s.whiff_pct != null) wsw += s.whiff_pct * pw;
  });
  const pK = tw2 > 0 ? wk / tw2 : 22;
  const pBB = tw2 > 0 ? wbb / tw2 : 8;
  const pSw = tw2 > 0 ? wsw / tw2 : 10;"""

new_command = """  // L2: Command (K%, BB%, SwStr%)
  // Note: k_pct often null (FG data unavailable). Estimate from whiff%.
  // Whiff% to K% conversion: K% ≈ whiff% * 0.80 (empirical)
  let wk = 0, wbb = 0, wsw = 0, tw2 = 0;
  yrs.forEach((yr, i) => {
    const s = S[yr], w = W[i] || 0.05, pw = w * Math.min(1, (s.bfp || 0) / 200);
    const kVal = s.k_pct != null ? s.k_pct :
                 s.whiff_pct != null ? s.whiff_pct * 0.80 : null;
    const bbVal = s.bb_pct != null ? s.bb_pct : null;
    if (kVal != null) { wk += kVal * pw; tw2 += pw; }
    if (bbVal != null) wbb += bbVal * pw;
    if (s.swstr != null) wsw += s.swstr * pw;
    else if (s.whiff_pct != null) wsw += s.whiff_pct * pw;
  });
  // Default K%=20 (league avg), BB%=8.5 (slightly above avg = conservative)
  const pK = tw2 > 0 ? wk / tw2 : 20;
  const pBB = tw2 > 0 ? wbb / tw2 : 8.5;
  const pSw = tw2 > 0 ? wsw / tw2 : 10;"""

if old_command in src:
    src = src.replace(old_command, new_command)
    changes += 1
    print("4. Fixed K% estimation (derive from whiff%, conservative defaults)")

# 5. Tighten the aging curve - 3%/yr pre-peak is too aggressive
old_aging = """  if (age < pk) af = Math.pow(0.97, pk - age); // young pitchers improve ~3%/yr
  else if (age <= 33) af = Math.pow(1.02, age - pk); // ERA rises ~2%/yr post-peak
  else af = Math.pow(1.02, 33 - pk) * Math.pow(1.035, age - 33); // accelerated decline"""

new_aging = """  if (age < pk) af = Math.pow(0.985, pk - age); // young pitchers improve ~1.5%/yr
  else if (age <= 33) af = Math.pow(1.015, age - pk); // ERA rises ~1.5%/yr post-peak
  else af = Math.pow(1.015, 33 - pk) * Math.pow(1.03, age - 33); // accelerated decline"""

if old_aging in src:
    src = src.replace(old_aging, new_aging)
    changes += 1
    print("5. Tightened aging curve (1.5%/yr instead of 3%/yr)")

# 6. Also fix the K/9 projection to not use bfPerIP in the formula
# K/9 should be derived from K% more conservatively
old_k9 = """  const projK9 = Math.max(4, Math.min(15, pK / 100 * 9 * 4.3));
  const projBB9 = Math.max(1, Math.min(6, pBB / 100 * 9 * 4.3));"""

new_k9 = """  // K/9 = K% * BF/IP * 9, where BF/IP ≈ 4.3
  // But cap reasonably - very few pitchers sustain 13+ K/9
  const projK9 = Math.max(4, Math.min(13.5, pK / 100 * 9 * 4.3));
  const projBB9 = Math.max(1.5, Math.min(5.5, pBB / 100 * 9 * 4.3));"""

if old_k9 in src:
    src = src.replace(old_k9, new_k9)
    changes += 1
    print("6. Capped K/9 at 13.5, BB/9 floor at 1.5")

# 7. Fix Marcel engine: use RP replacement level for relievers
old_marcel_war = """  const replLevel = 5.34;
  const runsPerWin = 9.5;
  const pitchWAR = ((replLevel - finalFIP) / runsPerWin) * (estIP / 9);
  const isReliever = !isLikelyStarter;"""

new_marcel_war = """  const replLevel = isLikelyStarter ? 5.34 : 4.49; // RP replacement = 0.03 wins/game
  const runsPerWin = 9.5;
  const pitchWAR = ((replLevel - finalFIP) / runsPerWin) * (estIP / 9);
  const isReliever = !isLikelyStarter;"""

if old_marcel_war in src:
    src = src.replace(old_marcel_war, new_marcel_war)
    changes += 1
    print("7. Fixed Marcel engine RP replacement level (5.34 -> 4.49)")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print()
print("Key changes:")
print("  - WAR now uses xERA (which we have) instead of FIP (which needs K%/BB% we dont have)")
print("  - Relievers properly detected and capped at 75 IP")
print("  - K% estimated from whiff% * 0.80 instead of defaulting to 22%")
print("  - Aging curve halved: 1.5%/yr instead of 3%/yr")
print()
print("Expected Irvin: xERA 5.12 * aging -> ~5.3 ERA, 183 IP")
print("  WAR = (5.34 - 5.3) / 9.5 * (183/9) = 0.1 WAR (was ~6.5)")
print("Expected Walker (RP): xERA ~3.2, ~60 IP")
print("  WAR = (4.49 - 3.2) / 9.5 * (60/9) = 0.9 WAR (was ~5.3)")
