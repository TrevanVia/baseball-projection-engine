#!/usr/bin/env python3
"""Fix HR convergence: reduce non-barrel baseline from 0.018 to 0.010. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old = """  const hr=Math.round(Math.max(0,pBrl/100*(ePA*.75)*.45+ePA*.018));"""
new = """  const hr=Math.round(Math.max(0,pBrl/100*(ePA*.75)*.45+ePA*.010));"""

if old in src:
    src = src.replace(old, new)
    open(APP, "w").write(src)
    print("Fixed: non-barrel HR baseline 0.018 -> 0.010")
    print("Chourio/Merrill/Holliday no longer all project to 28 HR")
else:
    print("Target not found - may already be applied")
