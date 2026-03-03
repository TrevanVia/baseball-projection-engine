#!/usr/bin/env python3
"""VIAcast Statcast Engine Patch. Run from project root."""
APP="src/App.jsx"
src=open(APP).read()
n0=src.count("\n")

# P1: imports
if "savant_data.json" not in src:
    src=src.replace('import xwobaDataJson from "./xwoba_data.json";','import xwobaDataJson from "./xwoba_data.json";\nimport savantDataJson from "./savant_data.json";')
    print("P1: import")
if "SAVANT_DATA" not in src:
    src=src.replace("const XWOBA_DATA = xwobaDataJson.default || xwobaDataJson;","const XWOBA_DATA = xwobaDataJson.default || xwobaDataJson;\nconst SAVANT_DATA = savantDataJson.default || savantDataJson;")
    print("P1b: const")

# P2: lookup
L="""
function getSavantPlayer(playerId, playerName) {
  const byId = SAVANT_DATA[String(playerId)];
  if (byId && byId.seasons) return byId;
  if (playerName) {
    const norm = normalizeN(playerName);
    const match = Object.values(SAVANT_DATA).find(p => normalizeN(p.name) === norm);
    if (match && match.seasons) return match;
  }
  return null;
}
"""
if "getSavantPlayer" not in src:
    i=src.find("function getStatcast(")
    if i>0: src=src[:i]+L+"\n"+src[i:]
    print("P2: lookup")

# P3: engine (read from separate file)
import os; E=open(os.path.join(os.path.dirname(__file__) or ".", "engine_func.js")).read()
if "projectFromStatcast" not in src:
    i=src.find("function projectFromSeasons(")
    if i>0: src=src[:i]+"\n"+E+"\n\n"+src[i:]
    print("P3: engine")

# P4: wire calls
o='return career.length ? projectFromSeasons(career, player.currentAge, player.primaryPosition?.code, player.fullName, player.id) : null;'
n="""const savP = getSavantPlayer(player.id, player.fullName);
    if (savP && Object.keys(savP.seasons || {}).length > 0) {
      const scProj = projectFromStatcast(savP, player.currentAge, player.primaryPosition?.code, player.fullName, player.id);
      if (scProj) return scProj;
    }
    return career.length ? projectFromSeasons(career, player.currentAge, player.primaryPosition?.code, player.fullName, player.id) : null;"""
if o in src: src=src.replace(o,n,1); print("P4a: main")
for o2,n2 in [
    ('const base = projectFromSeasons(splits, p.currentAge, p.primaryPosition?.code, p.fullName, p.id);','const base = projectPlayer(splits, p.currentAge, p.primaryPosition?.code, p.fullName, p.id);'),
    ('base = projectFromSeasons(splits, player.currentAge, player.primaryPosition?.code, player.fullName, player.id);','base = projectPlayer(splits, player.currentAge, player.primaryPosition?.code, player.fullName, player.id);'),
    ('base = projectFromSeasons(splits, (fullPlayer || player).currentAge, (fullPlayer || player).primaryPosition?.code, (fullPlayer || player).fullName, (fullPlayer || player).id);','base = projectPlayer(splits, (fullPlayer || player).currentAge, (fullPlayer || player).primaryPosition?.code, (fullPlayer || player).fullName, (fullPlayer || player).id);'),
    (': projectFromSeasons(splits, player.currentAge, player.primaryPosition?.code, player.fullName, player.id);',': projectPlayer(splits, player.currentAge, player.primaryPosition?.code, player.fullName, player.id);'),
]:
    c=src.count(o2)
    if c>0: src=src.replace(o2,n2); print("P4: %d"%c)

open(APP,"w").write(src)
print("Lines: %d -> %d"%(n0,src.count("\n")))
print("Run: npm run build")
