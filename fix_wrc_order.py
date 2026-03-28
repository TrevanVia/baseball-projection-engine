#!/usr/bin/env python3
"""Fix wRC+ ordering + HR conversion. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

old = """  const ops = Math.max(.52, Math.min(1.15, obp + slg));
  // wRC+ derived from displayed OPS (ensures correlation)
  // wRC+ from event-level linear weights (2024 FanGraphs)
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
  const wrc = Math.max(60, Math.min(195, Math.round(((_wOBA - 0.310) / 1.15 + 0.110) / 0.110 * 100 + db)));
  // PA estimate: use best full season from last 3 yrs (handles injury-shortened seasons)
  const bestPA = Math.max(...yrs.slice(0,3).map(yr => S[yr]?.pa || 0));
  const ePA=Math.min(700,Math.max(200,Math.max(pa0, bestPA * 0.90) * 0.97));
  const hr=Math.round(Math.max(0,(pBrl*slgAgeF)/100*(ePA*.75)*.45+ePA*.010));"""

new = """  const ops = Math.max(.52, Math.min(1.15, obp + slg));
  // PA estimate: use best full season from last 3 yrs (handles injury-shortened seasons)
  const bestPA = Math.max(...yrs.slice(0,3).map(yr => S[yr]?.pa || 0));
  const ePA=Math.min(700,Math.max(200,Math.max(pa0, bestPA * 0.90) * 0.97));
  const hr=Math.round(Math.max(0,(pBrl*slgAgeF)/100*(ePA*.75)*.38+ePA*.010));
  // wRC+ from event-level linear weights (2024 FanGraphs)
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

if old in src:
    src = src.replace(old, new)
    changes += 1
    print("1. Fixed variable ordering: ePA/hr defined before wRC+ block")
    print("   Also fixed HR barrel conversion 0.45 -> 0.38")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
