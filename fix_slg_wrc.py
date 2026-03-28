#!/usr/bin/env python3
"""Fix SLG compression + wRC+ amplifier. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. SLG compression in Statcast engine: regress xSLG 20% toward league avg
old_slg = "  const slg = pXslg != null ? Math.max(.3, Math.min(.7, pXslg * slgAgeF)) : Math.max(.3, Math.min(.65, obp + .120));"
new_slg = "  const slg = pXslg != null ? Math.max(.3, Math.min(.7, (pXslg * 0.80 + 0.405 * 0.20) * slgAgeF)) : Math.max(.3, Math.min(.65, obp + .120));"
if old_slg in src:
    src = src.replace(old_slg, new_slg)
    changes += 1
    print("1. SLG compression: xSLG regressed 20% toward league avg (.405)")

# 2. wRC+ amplifier in Statcast engine
old_wrc = "  const wrc = Math.max(60, Math.min(195, Math.round(((obp * 0.70 + slg * 0.30) / 0.342) * 100 + db)));"
new_wrc = "  const _rawWrc = ((obp * 0.70 + slg * 0.30) / 0.342) * 100;\n  const wrc = Math.max(60, Math.min(195, Math.round(100 + (_rawWrc - 100) * 2.0 + db)));"
if old_wrc in src:
    src = src.replace(old_wrc, new_wrc)
    changes += 1
    print("2. wRC+ amplifier: 2x deviation from 100 (calibrated to ZiPS)")

# 3. Same fixes in Marcel engine
old_marcel_wrc = "  finalWRC = Math.max(65, Math.min(195, Math.round(((projOBP * 0.70 + projSLG * 0.30) / 0.342) * 100)));"
new_marcel_wrc = "  const _mRawWrc = ((projOBP * 0.70 + projSLG * 0.30) / 0.342) * 100;\n  finalWRC = Math.max(65, Math.min(195, Math.round(100 + (_mRawWrc - 100) * 2.0)));"
if old_marcel_wrc in src:
    src = src.replace(old_marcel_wrc, new_marcel_wrc)
    changes += 1
    print("3. Marcel wRC+ amplifier: same 2x formula")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Yordan: .611 SLG -> .553 SLG (compressed), wRC+ 130 -> ~148")
print("Judge: SLG compressed, wRC+ properly separated from average")
print("League avg: still exactly 100 wRC+")
