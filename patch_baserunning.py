#!/usr/bin/env python3
"""Integrate Statcast Baserunning Run Value. Run from project root.
IMPORTANT: First copy baserunning_data.json to src/ directory."""
import os, json

APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Check if baserunning_data.json exists in src/
if not os.path.exists("src/baserunning_data.json"):
    print("WARNING: src/baserunning_data.json not found!")
    print("Copy it there first: cp ~/Downloads/baserunning_data.json src/")

# 1. Add import for baserunning data (next to other JSON imports)
old_import = 'import warDataJson from "./war_data.json";'
new_import = '''import warDataJson from "./war_data.json";
import baserunningDataJson from "./baserunning_data.json";'''

if new_import not in src and old_import in src:
    src = src.replace(old_import, new_import)
    changes += 1
    print("1. Added import for baserunning_data.json")

# 2. Add a lookup function after getSprintSpeed
old_sprint = 'function getSprintSpeed(playerName) { return SPRINT_SPEED[playerName] || null; }'
new_sprint = '''function getSprintSpeed(playerName) { return SPRINT_SPEED[playerName] || null; }

// Statcast Baserunning Run Value (runs above average, seasonal)
const BSR_DATA = baserunningDataJson || { byId: {}, byName: {} };
function getBaserunningValue(playerId, playerName) {
  const byId = BSR_DATA.byId || {};
  if (byId[playerId]) return byId[playerId].bsr;
  const byName = BSR_DATA.byName || {};
  if (byName[playerName]) return byName[playerName];
  return null;
}'''

if old_sprint in src:
    src = src.replace(old_sprint, new_sprint)
    changes += 1
    print("2. Added getBaserunningValue() lookup function")

# 3. Update Statcast engine to use BsR instead of sprint speed tiers
old_statcast_bsr = '''  const spd=sP.sprint_speed||null; let bsr=0;
  if(spd){let a2=spd;if(age>28)a2-=(age-28)*.15;bsr=a2>=30?5:a2>=29?3.5:a2>=28?2:a2>=27?0:a2>=25.5?-2:-4}'''

new_statcast_bsr = '''  const spd=sP.sprint_speed||null; let bsr=0;
  // Prefer Statcast BsR (already in runs) over sprint speed tiers
  const statcastBsR = getBaserunningValue(playerId, playerName);
  if (statcastBsR !== null) {
    bsr = statcastBsR; // Already a seasonal run value, scale by PA later
  } else if(spd){let a2=spd;if(age>28)a2-=(age-28)*.15;bsr=a2>=30?5:a2>=29?3.5:a2>=28?2:a2>=27?0:a2>=25.5?-2:-4}'''

if old_statcast_bsr in src:
    src = src.replace(old_statcast_bsr, new_statcast_bsr)
    changes += 1
    print("3. Statcast engine: use BsR when available, fallback to sprint speed")

# 4. Update the WAR formula to handle BsR correctly
# BsR is already a seasonal total (based on ~600 PA season)
# The current formula does bsr*(ePA/600) which scales it
# For BsR, we should scale by ePA/600 since BsR is per full season
# This already works correctly - bsr*(ePA/600) scales the BsR to projected PA

# 5. Update Marcel engine to also use BsR
old_marcel_bsr = '''  let bsrRuns = 0;
  if (spd !== null) {
    // MLB sprint speed path
    const speedTier = spd >= 29.5 ? 6.0 : spd >= 28.5 ? 4.0 : spd >= 28.0 ? 3.0 : spd >= 27.0 ? 1.5 : spd >= 26.0 ? 0 : -2.0;
    bsrRuns = speedTier * (estPA / 600);'''

new_marcel_bsr = '''  let bsrRuns = 0;
  // Prefer Statcast BsR over sprint speed tiers
  const marcelBsR = getBaserunningValue(playerId, playerName);
  if (marcelBsR !== null) {
    bsrRuns = marcelBsR * (estPA / 600);
  } else if (spd !== null) {
    // Fallback: sprint speed path
    const speedTier = spd >= 29.5 ? 6.0 : spd >= 28.5 ? 4.0 : spd >= 28.0 ? 3.0 : spd >= 27.0 ? 1.5 : spd >= 26.0 ? 0 : -2.0;
    bsrRuns = speedTier * (estPA / 600);'''

if old_marcel_bsr in src:
    src = src.replace(old_marcel_bsr, new_marcel_bsr)
    changes += 1
    print("4. Marcel engine: use BsR when available, fallback to sprint speed")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Baserunning Run Value integration:")
print("  252 MLB players with Statcast BsR data")
print("  BsR is already in runs (divide by 9.5 for WAR contribution)")
print("  Henderson: +6.8 BsR = +0.7 WAR from baserunning")
print("  Witt Jr.:  +7.4 BsR = +0.8 WAR from baserunning")  
print("  Judge:     -3.6 BsR = -0.4 WAR from baserunning")
print("  Carroll:  +10.1 BsR = +1.1 WAR from baserunning")
print()
print("Players without BsR data fall back to sprint speed tiers (existing behavior)")
