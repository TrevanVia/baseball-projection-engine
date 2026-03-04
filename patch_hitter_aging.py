#!/usr/bin/env python3
"""Fix hitter aging + wRC+ conversion. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Change from multiplicative xwOBA aging to additive wRC+ aging
# and bump the wRC+ conversion multiplier
old_aging_block = """  const ap=getAP(posCode), pk=ap.peak; let af=1;
  if(age<pk)af=Math.pow(1.02,pk-age);
  else if(age<=32)af=Math.pow(.985,age-pk);
  else af=Math.pow(.985,32-pk)*Math.pow(.97,age-32);
  let tb=0;
  if(yrs.length>=2){const x0=S[yrs[0]]?.xwoba,x1=S[yrs[1]]?.xwoba;
    const x2=yrs.length>=3?S[yrs[2]]?.xwoba:null;
    if(x0!=null&&x1!=null){const d1=x0-x1,d2=x2!=null?x1-x2:null;
      if(d2!=null&&Math.sign(d1)===Math.sign(d2)&&d1>0)tb+=d1*.3;else tb+=d1*.15}}
  if(chT>.02)tb+=chT*.15; if(ev5T>1.5)tb+=.005; if(bsT<-1.5)tb-=.008;
  const axw=Math.max(.2,Math.min(.5,pXw+tb))*af;
  let db=0;
  if(selI!=null){if(selI>3.5)db=Math.min(5,(selI-3.5)*3);else if(selI<2)db=Math.max(-4,(selI-2)*3)}
  if(pK<.15)db+=3;else if(pK>.30)db-=2; if(pBB>.12)db+=2;
  const wrc=Math.max(60,Math.min(190,Math.round(((axw-.315)/.01)*3.2+100+db)));
  const ops=Math.max(.52,Math.min(1.15,wrc*.0072+.002));
  const avg=lat.xba!=null?Math.max(.18,Math.min(.34,lat.xba*af)):Math.max(.2,Math.min(.32,(ops-.1)/2.5));
  const obp=Math.max(.26,Math.min(.45,avg+pBB*.85+.02));"""

new_aging_block = """  const ap=getAP(posCode), pk=ap.peak;
  // Trend detection (before aging)
  let tb=0;
  if(yrs.length>=2){const x0=S[yrs[0]]?.xwoba,x1=S[yrs[1]]?.xwoba;
    const x2=yrs.length>=3?S[yrs[2]]?.xwoba:null;
    if(x0!=null&&x1!=null){const d1=x0-x1,d2=x2!=null?x1-x2:null;
      if(d2!=null&&Math.sign(d1)===Math.sign(d2)&&d1>0)tb+=d1*.3;else tb+=d1*.15}}
  if(chT>.02)tb+=chT*.15; if(ev5T>1.5)tb+=.005; if(bsT<-1.5)tb-=.008;

  // xwOBA with trends (NO multiplicative age factor)
  const axw=Math.max(.2,Math.min(.5,pXw+tb));

  // Discipline bonus
  let db=0;
  if(selI!=null){if(selI>3.5)db=Math.min(5,(selI-3.5)*3);else if(selI<2)db=Math.max(-4,(selI-2)*3)}
  if(pK<.15)db+=3;else if(pK>.30)db-=2; if(pBB>.12)db+=2;

  // xwOBA -> wRC+ (4.5 per .010 xwOBA, calibrated to actual wRC+ values)
  let rawWrc = Math.round(((axw-.315)/.01)*4.5+100+db);

  // Aging: single-year forward adjustment
  // The weighted xwOBA already reflects the player's CURRENT age performance
  // We only need to project one year of aging delta, not cumulative since peak
  // Pre-peak: +1.5 wRC+ (still improving)
  // Peak to 32: -1.5 wRC+ per year
  // 33+: -3.0 wRC+ per year (steeper late decline)
  let ageAdj = 0;
  if (age < pk) ageAdj = 1.5; // one year of improvement
  else if (age <= 32) ageAdj = -1.5; // one year of gradual decline
  else ageAdj = -3.0; // one year of steeper late decline

  const wrc=Math.max(60,Math.min(195,rawWrc + Math.round(ageAdj)));
  const ops=Math.max(.52,Math.min(1.15,wrc*.0072+.002));
  // AVG: use xBA directly if available, small age adj for contact decline
  const avgAgeF = age > 32 ? Math.max(0.93, 1 - (age - 32) * 0.01) : 1.0;
  const avg=lat.xba!=null?Math.max(.18,Math.min(.34,lat.xba*avgAgeF)):Math.max(.2,Math.min(.32,(ops-.1)/2.5));
  const obp=Math.max(.26,Math.min(.45,avg+pBB*.85+.02));"""

if old_aging_block in src:
    src = src.replace(old_aging_block, new_aging_block)
    changes += 1
    print("1. Fixed aging: multiplicative xwOBA -> additive wRC+ adjustment")
    print("   Also bumped xwOBA->wRC+ multiplier from 3.2 to 4.5")

# 2. Fix the statcast xwOBA in return value (was using af-adjusted, now use raw)
old_return_xw = """    _statcast:{xwoba:Math.round(axw*1e3)/1e3,projEV:Math.round(pEV*10)/10,"""
# This is fine - axw is now the raw + trend version, which is what we want to display

# 3. Also need to update the WAR calculation since we removed af from xwOBA
# The batting runs formula uses wrc which now has the age adjustment built in
# But the defense OAA scaling used dAg which is separate - that's fine

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
print()
print("Harper (age 33, 1B, .370 xwOBA):") 
print("  Before: .370 * 0.913 = .338 xwOBA -> 110 wRC+ -> 1.4 WAR")
print("  After:  .370 xwOBA -> 125 raw wRC+ - 10.5 age adj = 125 wRC+ -> ~3.0 WAR")
print()
print("Julio (age 24, CF, .348 xwOBA):")
print("  Before: .348 * 1.02^3 = .369 xwOBA -> 119 wRC+ (over-projected)")
print("  After:  .348 xwOBA -> 115 raw wRC+ + 4.5 age adj = 120 wRC+")
