#!/usr/bin/env python3
"""Add pitcher career stats table and fix pitcher forward projection. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Add pitchSeasons memo after the seasons memo
PITCH_SEASONS = """
  const pitchSeasons = useMemo(()=>pitchCareer.filter(s=>parseFloat(s.stat?.inningsPitched||0)>0).map(s=>{
    const lvl = detectLevel(s);
    const st = s.stat;
    return {
      season:s.season, age:player.currentAge-(2025-parseInt(s.season)),
      era:parseFloat(st.era||0), ip:parseFloat(st.inningsPitched||0),
      k9:parseFloat(st.strikeoutsPer9Inn||0), bb9:parseFloat(st.walksPer9Inn||0),
      whip:parseFloat(st.whip||0), fip:parseFloat(st.era||0),
      w:parseInt(st.wins||0), l:parseInt(st.losses||0), sv:parseInt(st.saves||0),
      so:parseInt(st.strikeOuts||0), bb:parseInt(st.baseOnBalls||0),
      hr:parseInt(st.homeRuns||0), gs:parseInt(st.gamesStarted||0), g:parseInt(st.gamesPlayed||0),
      team:s.team?.abbreviation||"", level:lvl,
    };
  }).sort((a,b)=>{const sy=parseInt(a.season)-parseInt(b.season);if(sy!==0)return sy;return LEVEL_ORDER.indexOf(a.level)-LEVEL_ORDER.indexOf(b.level);}),[pitchCareer,player]);
"""

marker = "const isPitcher = player.primaryPosition?.code === \"1\";"
if "pitchSeasons" not in src:
    idx = src.find(marker)
    if idx > 0:
        src = src[:idx] + PITCH_SEASONS + "\n  " + src[idx:]
        changes += 1
        print("1. Added pitchSeasons memo")

# 2. Add pitcher career stats table after the hitter table
# Find the hitter career stats panel closing and add pitcher version
PITCHER_TABLE = """
      {isPitcher&&pitchSeasons.length>0&&<Panel title="CAREER PITCHING STATS" sub={base?.highestLevel!=="MLB"?"Minor league stats with level indicators.":"Year-by-year from MLB Stats API."}>
        <div className="via-table-wrap" style={{overflowX:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
              {["Year","Age","Tm","Lvl","W","L","ERA","G","GS","IP","K/9","BB/9","WHIP","SO","BB","HR","SV"].map(h=>
                <th key={h} style={{padding:"5px 7px",textAlign:["Year","Tm","Lvl"].includes(h)?"left":"right",color:C.muted,fontWeight:600,fontSize:9,letterSpacing:".04em"}}>{h}</th>
              )}
            </tr></thead>
            <tbody>{pitchSeasons.map((s,i)=>(
              <tr key={i} style={{borderBottom:`1px solid ${C.border}40`,background:i%2===0?"#f5f0e6":"transparent"}}>
                <td style={{padding:"4px 7px",color:C.text,fontWeight:600}}>{s.season}</td>
                <td style={{padding:"4px 7px",color:C.dim,textAlign:"right"}}>{s.age}</td>
                <td style={{padding:"4px 7px",color:C.dim}}>{s.team}</td>
                <td style={{padding:"4px 7px"}}><LevelBadge level={s.level}/></td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.text}}>{s.w}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.text}}>{s.l}</td>
                <td style={{padding:"4px 7px",textAlign:"right",fontWeight:700,color:s.era<=2.50?C.green:s.era<=3.50?C.blue:s.era<=4.50?C.text:C.accent}}>{s.era.toFixed(2)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.g}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.gs}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.ip>=160?C.green:C.text}}>{s.ip.toFixed(1)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.k9>=10?C.green:s.k9>=8.5?C.blue:C.text}}>{s.k9.toFixed(1)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.bb9<=2.5?C.green:s.bb9>=4.0?C.accent:C.text}}>{s.bb9.toFixed(1)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.whip<=1.05?C.green:s.whip<=1.20?C.blue:s.whip>=1.40?C.accent:C.text}}>{s.whip.toFixed(2)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.so}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.bb}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.hr}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.sv>=10?C.cyan:C.dim}}>{s.sv}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Panel>}
"""

# Insert pitcher table right before the closing </div> of the PlayerCard
# Find the hitter career stats panel end
hitter_table_end = src.find("    </div>\n  );\n}\n\n// __ ROSTER BROWSER")
if hitter_table_end > 0 and "CAREER PITCHING STATS" not in src:
    src = src[:hitter_table_end] + PITCHER_TABLE + "\n" + src[hitter_table_end:]
    changes += 1
    print("2. Added pitcher career stats table")

# 3. Fix pitcher forward projection (same bug as hitters)
old_pitch_forward = """function projectPitcherForward(base, age, years = 10) {
  if (!base) return [];
  const ap = base.isReliever ? PITCHER_AGING.RP : PITCHER_AGING.SP;
  const out = [];
  for (let y = 0; y < years; y++) {
    const a = age + y;
    const d = a - ap.peak;
    let f;
    if (d <= 0) {
      const yearsToGo = Math.abs(d);
      f = 1 + Math.min(0.12, (3 - yearsToGo) * 0.03);
      f = Math.max(0.88, Math.min(1.20, f));
    } else {
      f = Math.pow(1 - ap.dr, d);
    }
    out.push({ age: a, season: String(2026 + (out.length)), war: Math.max(-0.5, base.baseWAR * f) });"""

new_pitch_forward = """function projectPitcherForward(base, age, years = 10) {
  if (!base) return [];
  const ap = base.isReliever ? PITCHER_AGING.RP : PITCHER_AGING.SP;
  const yearsToPeak = Math.max(0, ap.peak - age);
  const peakMult = yearsToPeak > 0 ? 1 + yearsToPeak * 0.05 : 1.0;
  const peakWAR = base.baseWAR * Math.min(2.0, peakMult);
  const out = [];
  for (let y = 0; y < years; y++) {
    const a = age + y;
    const d = a - ap.peak;
    let war;
    if (d <= 0) {
      const progress = yearsToPeak > 0 ? y / yearsToPeak : 1;
      const t = Math.min(1, progress);
      war = base.baseWAR + (peakWAR - base.baseWAR) * t;
    } else {
      war = peakWAR * Math.pow(1 - ap.dr, d);
    }
    out.push({ age: a, season: String(2026 + y), war: Math.round(Math.max(-0.5, war)*10)/10 });"""

if old_pitch_forward in src:
    src = src.replace(old_pitch_forward, new_pitch_forward)
    changes += 1
    print("3. Fixed pitcher forward projection (ramps up to peak)")

# 4. Update pitcher WAR clamp
old_p_clamp = "clampedWAR = Math.max(bench.war * 0.3, Math.min(bench.war * 1.7, clampedWAR));"
new_p_clamp = "clampedWAR = Math.max(bench.war * 0.25, Math.min(bench.war * 2.0, clampedWAR));"
if old_p_clamp in src:
    src = src.replace(old_p_clamp, new_p_clamp)
    changes += 1
    print("4. Raised pitcher WAR clamp to 2.0x")

# 5. Hide the hitter career stats table for pitchers
# The current table shows for everyone because it checks seasons.length
# Need to add !isPitcher check
old_hitter_table = "seasons.length>0&&<Panel title=\"CAREER STATS\""
new_hitter_table = "!isPitcher&&seasons.length>0&&<Panel title=\"CAREER STATS\""
if old_hitter_table in src and "!isPitcher&&seasons.length>0&&<Panel title=\"CAREER STATS\"" not in src:
    src = src.replace(old_hitter_table, new_hitter_table)
    changes += 1
    print("5. Hidden hitter career table for pitchers")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
