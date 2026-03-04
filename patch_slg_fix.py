#!/usr/bin/env python3
"""Fix SLG so OBP+SLG=OPS in both engines. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix Statcast engine: SLG = OPS - OBP (not ops-obp+avg)
old_slg = """const slg=Math.max(.3,Math.min(.7,ops-obp+avg));"""
new_slg = """const slg=Math.max(.3,Math.min(.7,ops-obp));"""
if old_slg in src:
    src = src.replace(old_slg, new_slg)
    changes += 1
    print("1. Fixed Statcast SLG: ops-obp (was ops-obp+avg)")

# 2. Fix Marcel engine: derive SLG from OPS - OBP in the return
old_marcel_slg = """    slg: Math.max(0.310, Math.min(0.620, finalSLG * paRel + 0.405 * (1 - paRel))),"""
new_marcel_slg = """    slg: Math.max(0.310, Math.min(0.620, finalOPS - Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))))),"""
if old_marcel_slg in src:
    src = src.replace(old_marcel_slg, new_marcel_slg)
    changes += 1
    print("2. Fixed Marcel SLG: derived from OPS-OBP for consistency")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
