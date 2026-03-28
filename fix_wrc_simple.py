#!/usr/bin/env python3
"""Replace event-level wRC+ with simple wOBA approximation. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Statcast engine: replace event-level block with simple wOBA
old_stat = """  // wRC+ from event-level linear weights (2024 FanGraphs)
  const _ab = ePA * (1 - pBB - 0.02);
  const _h = avg * _ab;
  const _bb = pBB * ePA;
  const _hbp = ePA * 0.01;
  const _tb = slg * _ab;
  const _extraTB = Math.max(0, _tb - _h - 3 * hr);
  const _2b = Math.round(_extraTB * 0.85);
  const _3b = Math.round(_extraTB * 0.075);
  const _1b = Math.max(0, Math.round(_h - hr - _2b - _3b));
  const _wOBA = (0.690*_bb + 0.722*_hbp + 0.878*_1b + 1.242*_2b + 1.568*_3b + 2.004*hr) / ePA;
  const wrc = Math.max(60, Math.min(195, Math.round(((_wOBA - 0.310) / 1.15 + 0.110) / 0.110 * 100 + db)));"""

new_stat = """  // wRC+ from wOBA approximation (OBP weighted 2.3x more than SLG)
  const wrc = Math.max(60, Math.min(195, Math.round(((obp * 0.70 + slg * 0.30) / 0.342) * 100 + db)));"""

if old_stat in src:
    src = src.replace(old_stat, new_stat)
    changes += 1
    print("1. Statcast wRC+: simple wOBA (OBP*0.70 + SLG*0.30)")

# 2. Marcel engine: same fix
old_marcel = """  // wRC+ from event-level linear weights (2024 FanGraphs)
  const _mBBpct = Math.max(0.03, (projOBP - (wAVG/tw) * ageBoost * paRel - 0.015) / 0.65);
  const _mAVG = Math.max(0.200, (wAVG/tw) * ageBoost * paRel + 0.248 * (1 - paRel));
  const _mAB = estPA * (1 - _mBBpct - 0.02);
  const _mH = _mAVG * _mAB;
  const _mBB = _mBBpct * estPA;
  const _mHBP = estPA * 0.01;
  const _mTB = projSLG * _mAB;
  const _mXTB = Math.max(0, _mTB - _mH - 3 * projHR);
  const _m2B = Math.round(_mXTB * 0.85);
  const _m3B = Math.round(_mXTB * 0.075);
  const _m1B = Math.max(0, Math.round(_mH - projHR - _m2B - _m3B));
  const _mwOBA = (0.690*_mBB + 0.722*_mHBP + 0.878*_m1B + 1.242*_m2B + 1.568*_m3B + 2.004*projHR) / estPA;
  finalWRC = Math.max(65, Math.min(195, Math.round(((_mwOBA - 0.310) / 1.15 + 0.110) / 0.110 * 100)));"""

new_marcel = """  // wRC+ from wOBA approximation (OBP weighted 2.3x more than SLG)
  finalWRC = Math.max(65, Math.min(195, Math.round(((projOBP * 0.70 + projSLG * 0.30) / 0.342) * 100)));"""

if old_marcel in src:
    src = src.replace(old_marcel, new_marcel)
    changes += 1
    print("2. Marcel wRC+: simple wOBA")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("wRC+ = (OBP*0.70 + SLG*0.30) / 0.342 * 100 + db")
print("League avg (.315 OBP + .405 SLG) = 100 wRC+")
print("OBP weighted 2.3x more than SLG (matches real wOBA weighting)")
