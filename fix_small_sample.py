#!/usr/bin/env python3
"""Fix small-sample players: PA regression + FV-based PA override. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Add PA regression before dev boost (regress xBA/xSLG toward league avg for small samples)
old_devboost = """  // Pre-peak development boost: young hitters projected to improve toward peak
  const yrsToPeak = Math.max(0, pk - age);"""

new_devboost = """  // Small-sample regression: regress xBA/xSLG toward league avg based on PA
  const _tPA = yrs.reduce((s,yr) => s + (S[yr]?.pa || 0), 0);
  const _paReg = Math.min(1.0, _tPA / 400);
  if (pXba != null) pXba = pXba * _paReg + 0.248 * (1 - _paReg);
  if (pXslg != null) pXslg = pXslg * _paReg + 0.405 * (1 - _paReg);
  // Pre-peak development boost: young hitters projected to improve toward peak
  const yrsToPeak = Math.max(0, pk - age);"""

if old_devboost in src:
    src = src.replace(old_devboost, new_devboost)
    changes += 1
    print("1. Added PA regression (xBA/xSLG regressed toward league avg for small samples)")

# 2. Add FV-based PA override after ePA calculation
old_epa = "  const ePA=Math.min(700,Math.max(200,Math.max(pa0, bestPA * 0.90) * 0.97));"

new_epa = """  let ePA=Math.min(700,Math.max(200,Math.max(pa0, bestPA * 0.90) * 0.97));
  // FV-based PA override for prospects with small MLB samples
  const _fvPA = getPlayerFV(playerId, playerName);
  if (_fvPA && ePA < 400) {
    const _fvFloor = {70:600,65:550,60:550,55:500,50:450,45:350,40:250}[Math.min(70,Math.max(40,_fvPA))] || 300;
    ePA = Math.max(ePA, _fvFloor);
  }"""

if old_epa in src:
    src = src.replace(old_epa, new_epa)
    changes += 1
    print("2. Added FV-based PA override for prospects")

# Also need to change const to let for ePA since we reassign it
# Wait - the new_epa already uses let. But we also need to fix the 
# bat= line which references wrc (amplified) - should use _rawWrc.
# Let me check if that fix is already deployed.

# Check if _rawWrc fix is in place
if "((_rawWrc-100)/100)*ePA" in src:
    print("   (WAR already uses _rawWrc - good)")
elif "((wrc-100)/100)*ePA" in src:
    # Fix it
    src = src.replace("((wrc-100)/100)*ePA", "((_rawWrc-100)/100)*ePA", 1)
    changes += 1
    print("3. Fixed WAR to use _rawWrc (unamplified)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Small-sample regression: _paReg = min(1.0, totalPA / 400)")
print("  58 PA player: regression 0.145 (heavily regressed to league avg)")
print("  200 PA player: regression 0.50 (50/50 blend)")
print("  400+ PA player: regression 1.0 (unchanged)")
print()
print("FV PA override (only for players with ePA < 400):")
print("  FV 70: 600 PA | FV 60-65: 550 PA | FV 55: 500 PA")
print("  FV 50: 450 PA | FV 45: 350 PA | FV 40: 250 PA")
