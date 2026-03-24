#!/usr/bin/env python3
"""HOTFIX: define slgAgeF that HR formula references. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old = """  const avgAgeF = age > 32 ? Math.max(0.97, 1 - (age - 32) * 0.005) : 1.0;
  const avg = pXba != null ? Math.max(.18, Math.min(.34, pXba * avgAgeF)) : Math.max(.2, Math.min(.32, .248));
  const obp = Math.max(.26, Math.min(.45, avg + pBB * .65 + .015));
  const slg = pXslg != null ? Math.max(.3, Math.min(.7, pXslg * avgAgeF)) : Math.max(.3, Math.min(.65, obp + .120));"""

new = """  // Separate aging for AVG (contact, mild decline) and SLG (power, steeper decline)
  const avgAgeF = age > 32 ? Math.max(0.95, 1 - (age - 32) * 0.008) : 1.0;
  const slgAgeF = age > 30 ? Math.max(0.88, 1 - (age - 30) * 0.015) : 1.0;
  const avg = pXba != null ? Math.max(.18, Math.min(.34, pXba * avgAgeF)) : Math.max(.2, Math.min(.32, .248));
  const obp = Math.max(.26, Math.min(.45, avg + pBB * .65 + .015));
  const slg = pXslg != null ? Math.max(.3, Math.min(.7, pXslg * slgAgeF)) : Math.max(.3, Math.min(.65, obp + .120));"""

if old in src:
    src = src.replace(old, new)
    open(APP, "w").write(src)
    print("FIXED: slgAgeF defined + applied to SLG and HR aging")
    print("Site should work again immediately after deploy")
else:
    print("ERROR: pattern not found")
