#!/usr/bin/env python3
"""Fix OBP/SLG: project independently from xBA/xSLG. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Add xBA and xSLG to the Statcast engine's weighted data collection
old_layer1 = """  let wxw=0,wev=0,wbr=0,tw1=0;
  yrs.forEach((yr,i)=>{const s=S[yr],w=W[i]||.05,pw=w*Math.min(1,(s.pa||0)/400);
    if(s.xwoba!=null){wxw+=s.xwoba*pw;tw1+=pw}if(s.avg_ev!=null)wev+=s.avg_ev*pw;
    if(s.barrel_pct!=null)wbr+=s.barrel_pct*pw});
  const pXw=tw1>0?wxw/tw1:.310, pEV=tw1>0?wev/tw1:87, pBrl=tw1>0?wbr/tw1:6;"""

new_layer1 = """  let wxw=0,wev=0,wbr=0,wxba=0,wxslg=0,tw1=0;
  yrs.forEach((yr,i)=>{const s=S[yr],w=W[i]||.05,pw=w*Math.min(1,(s.pa||0)/400);
    if(s.xwoba!=null){wxw+=s.xwoba*pw;tw1+=pw}if(s.avg_ev!=null)wev+=s.avg_ev*pw;
    if(s.barrel_pct!=null)wbr+=s.barrel_pct*pw;
    if(s.xba!=null)wxba+=s.xba*pw;if(s.xslg!=null)wxslg+=s.xslg*pw});
  const pXw=tw1>0?wxw/tw1:.310, pEV=tw1>0?wev/tw1:87, pBrl=tw1>0?wbr/tw1:6;
  const pXba=tw1>0?wxba/tw1:null, pXslg=tw1>0?wxslg/tw1:null;"""

if old_layer1 in src:
    src = src.replace(old_layer1, new_layer1)
    changes += 1
    print("1. Added xBA and xSLG to Statcast weighted data collection")

# 2. Replace the OPS/AVG/OBP/SLG derivation block
# Currently: OPS from wRC+, AVG from xBA, OBP from avg+BB, SLG from OPS-OBP
# New: AVG from xBA, OBP from xBA+BB, SLG from xSLG, OPS = OBP+SLG
old_slash = """  const ops=Math.max(.52,Math.min(1.15,wrc*.0072+.002));
  // AVG: use xBA directly if available, small age adj for contact decline
  const avgAgeF = age > 32 ? Math.max(0.93, 1 - (age - 32) * 0.01) : 1.0;
  const avg=lat.xba!=null?Math.max(.18,Math.min(.34,lat.xba*avgAgeF)):Math.max(.2,Math.min(.32,(ops-.1)/2.5));
  const obp=Math.max(.26,Math.min(.45,avg+pBB*.85+.02));
  const slg=Math.max(.3,Math.min(.7,ops-obp));"""

new_slash = """  // Project slash line from Statcast expected stats
  // AVG from xBA, OBP from xBA+BB%, SLG from xSLG, OPS = OBP+SLG
  const avgAgeF = age > 32 ? Math.max(0.97, 1 - (age - 32) * 0.005) : 1.0;
  const avg = pXba != null ? Math.max(.18, Math.min(.34, pXba * avgAgeF)) : Math.max(.2, Math.min(.32, .248));
  const obp = Math.max(.26, Math.min(.45, avg + pBB * .85 + .02));
  const slg = pXslg != null ? Math.max(.3, Math.min(.7, pXslg * avgAgeF)) : Math.max(.3, Math.min(.65, obp + .120));
  const ops = Math.max(.52, Math.min(1.15, obp + slg));"""

if old_slash in src:
    src = src.replace(old_slash, new_slash)
    changes += 1
    print("2. Fixed slash line: AVG from xBA, SLG from xSLG, OPS = OBP+SLG")

# 3. Fix Marcel engine: keep independent OBP/SLG, derive OPS from them
# Revert the SLG line to use the actual weighted SLG, and make OPS = OBP+SLG
old_marcel_return = """    ops: finalOPS,
    obp: Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))),
    slg: Math.max(0.310, Math.min(0.620, finalOPS - Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))))),"""

new_marcel_return = """    obp: Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))),
    slg: Math.max(0.310, Math.min(0.620, finalSLG * paRel + 0.405 * (1 - paRel))),
    ops: Math.max(0.560, Math.min(1.100, Math.max(0.275, Math.min(0.430, finalOBP * paRel + 0.315 * (1 - paRel))) + Math.max(0.310, Math.min(0.620, finalSLG * paRel + 0.405 * (1 - paRel))))),"""

if old_marcel_return in src:
    src = src.replace(old_marcel_return, new_marcel_return)
    changes += 1
    print("3. Fixed Marcel: independent OBP+SLG, OPS derived from sum")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print()
print("Now: OBP reflects plate discipline (xBA + BB%)")
print("     SLG reflects power (xSLG / barrel%)")
print("     OPS = OBP + SLG (always consistent)")
print("     wRC+ still drives WAR independently")
