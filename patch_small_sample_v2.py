#!/usr/bin/env python3
"""Fix: prefer Marcel over Statcast for small MLB samples. Run from project root."""
import re

APP = "src/App.jsx"
src = open(APP).read()

# Use regex to be more forgiving of whitespace
pattern = r'(function projectPlayer\(splits, age, posCode, name, id\) \{\s*const savP = getSavantPlayer\(id, name\);\s*if \(savP && Object\.keys\(savP\.seasons \|\| \{\}\)\.length > 0\) \{)\s*(const sc = projectFromStatcast\(savP, age, posCode, name, id\);)\s*(if \(sc\) return sc;)\s*(\})'

replacement = r"""\1
    // Only use Statcast if meaningful MLB sample exists (250+ PA)
    // Below that, MiLB-inclusive Marcel is more reliable
    const totalMLBPA = Object.values(savP.seasons || {}).reduce((s, yr) => s + (yr.pa || 0), 0);
    if (totalMLBPA >= 250) {
      \2
      \3
    }
  \4"""

new_src, count = re.subn(pattern, replacement, src)
if count > 0:
    open(APP, "w").write(new_src)
    print("Applied fix: 250 PA minimum for Statcast engine")
    print("Basallo (118 MLB PA) will now use Marcel with AAA/AA data")
else:
    # Check if already applied
    if "totalMLBPA" in src:
        print("Already applied!")
    else:
        print("ERROR: Could not find projectPlayer function to patch")
        print("Trying direct string replacement...")
        # Fallback: try exact string
        old = "    const sc = projectFromStatcast(savP, age, posCode, name, id);\n    if (sc) return sc;"
        new = """    const totalMLBPA = Object.values(savP.seasons || {}).reduce((s, yr) => s + (yr.pa || 0), 0);
    if (totalMLBPA >= 250) {
      const sc = projectFromStatcast(savP, age, posCode, name, id);
      if (sc) return sc;
    }"""
        if old in src:
            src = src.replace(old, new, 1)
            open(APP, "w").write(src)
            print("Applied via fallback method")
        else:
            print("FAILED - please check src/App.jsx manually")
