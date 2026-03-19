#!/usr/bin/env python3
"""Redesign player card layout. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. Add projGames to Statcast engine return
# ═══════════════════════════════════════════════════════════════
old_statcast_return = """    wRCPlus:wrc,baseWAR:fW,estPA:Math.round(ePA),hr:hr,"""
new_statcast_return = """    wRCPlus:wrc,baseWAR:fW,estPA:Math.round(ePA),hr:hr,projGames:Math.round(ePA/4.1),"""
if old_statcast_return in src:
    src = src.replace(old_statcast_return, new_statcast_return, 1)
    changes += 1
    print("1. Added projGames to Statcast engine return")

# 2. Add projGames to Marcel engine return (it already computes projGames internally)
old_marcel_return = """    estPA: Math.round(estPA),
    hr: projHR,"""
new_marcel_return = """    estPA: Math.round(estPA),
    projGames: projGames,
    hr: projHR,"""
if old_marcel_return in src:
    src = src.replace(old_marcel_return, new_marcel_return, 1)
    changes += 1
    print("2. Added projGames to Marcel engine return")

# ═══════════════════════════════════════════════════════════════
# 3. Redesign the hitter stat box row
# ═══════════════════════════════════════════════════════════════

old_hitter_stats = """          {base&&!isPitcher&&<>
              <Stat label="Proj WAR" value={base.baseWAR.toFixed(1)} color={base.baseWAR>=4?C.green:base.baseWAR>=2?C.blue:C.yellow}/>
              {base._isTwoWay&&<>
                <Stat label="Hit WAR" value={base._hitWAR?.toFixed(1)} color={C.blue} sub="Batting"/>
                <Stat label="Pitch WAR" value={base._pitchWAR?.toFixed(1)} color={C.purple} sub="Pitching"/>
                {base._pitchProj&&<Stat label="Proj ERA" value={base._pitchProj.era?.toFixed(2)} color={base._pitchProj.era<=3.00?C.green:C.text}/>}
              </>}
              <Stat label="Proj wRC+" value={base.wRCPlus} color={base.wRCPlus>=120?C.green:base.wRCPlus>=100?C.blue:C.yellow}/>
              <Stat label="Proj OPS" value={base.ops.toFixed(3)} color={base.ops>=.85?C.green:base.ops>=.73?C.blue:C.yellow}/>
              {peak&&<Stat label="Peak Age" value={peak.age} color={C.cyan}/>}
              {cWAR!==null&&<Stat label="Career fWAR" value={cWAR.toFixed(1)} color={cWAR>=30?C.green:cWAR>=15?C.blue:C.purple} sub="FanGraphs"/>}
              <Stat label="10yr WAR" value={cum.toFixed(1)} color={C.purple} sub="Projected"/>
            </>}"""

new_hitter_stats = """          {base&&!isPitcher&&<>
              {cWAR!==null&&<Stat label="Career fWAR" value={cWAR.toFixed(1)} color={cWAR>=30?C.green:cWAR>=15?C.blue:C.purple} sub="FanGraphs"/>}
              <Stat label="10yr WAR" value={cum.toFixed(1)} color={C.purple} sub="Projected"/>
              {base._isTwoWay&&<>
                <Stat label="Hit WAR" value={base._hitWAR?.toFixed(1)} color={C.blue} sub="Batting"/>
                <Stat label="Pitch WAR" value={base._pitchWAR?.toFixed(1)} color={C.purple} sub="Pitching"/>
              </>}
            </>}"""

if old_hitter_stats in src:
    src = src.replace(old_hitter_stats, new_hitter_stats)
    changes += 1
    print("3. Redesigned hitter stat boxes (Career fWAR + 10yr WAR only)")

# ═══════════════════════════════════════════════════════════════
# 4. Remove reliability bar
# ═══════════════════════════════════════════════════════════════

old_reliability = """        {base&&<div style={{marginTop:10,padding:"7px 12px",background:`${isMiLB?C.purple:C.accent}08`,borderRadius:6,border:`1px solid ${isMiLB?C.purple:C.accent}15`}}>
          <span style={{fontSize:10,color:C.muted,fontFamily:F}}>
            {base.paReliability}% reliability &middot; {isPitcher ? pitchCareer.filter(s=>parseFloat(s.stat?.inningsPitched||0)>0).length : seasons.length} seasons &middot; Marcel 5/4/3 weighting
            {base.translationNote&&<span style={{color:LEVEL_COLORS[base.highestLevel]}}> &middot; {base.translationNote}</span>}
          </span>
        </div>}"""

if old_reliability in src:
    src = src.replace(old_reliability, "")
    changes += 1
    print("4. Removed reliability bar")

# ═══════════════════════════════════════════════════════════════
# 5. Remove Batted Ball Data panel
# ═══════════════════════════════════════════════════════════════

# Find the batted ball panel
bb_start = src.find('{/* Statcast Batted Ball Data (if available) */}')
if bb_start == -1:
    bb_start = src.find("sc && !isPitcher && <Panel title=\"BATTED BALL DATA\"")
if bb_start > 0:
    # Find the closing </Panel> for this section
    # Count Panel opens and closes
    search_from = bb_start
    # Find the <Panel that starts this section
    panel_start = src.rfind("<Panel", 0, search_from + 100)
    if panel_start == -1:
        panel_start = search_from
    
    # Actually, find it by looking for the pattern
    bb_pattern_start = src.find("{sc && !isPitcher && <Panel title=\"BATTED BALL DATA\"")
    if bb_pattern_start == -1:
        bb_pattern_start = src.find('{sc && !isPitcher && <Panel title="BATTED BALL DATA"')
    
    if bb_pattern_start > 0:
        # Find the matching closing
        depth = 0
        i = bb_pattern_start
        found_panel = False
        while i < len(src):
            if src[i:i+6] == "<Panel":
                depth += 1
                found_panel = True
            if src[i:i+8] == "</Panel>":
                depth -= 1
                if found_panel and depth == 0:
                    end = i + 8
                    # Also include the closing }
                    while end < len(src) and src[end] in " \n\t}":
                        if src[end] == '}':
                            end += 1
                            break
                        end += 1
                    block = src[bb_pattern_start:end]
                    src = src[:bb_pattern_start] + src[end:]
                    changes += 1
                    print("5. Removed Batted Ball Data panel")
                    break
            i += 1

# ═══════════════════════════════════════════════════════════════
# 6. Add FanGraphs-style season projection table
# ═══════════════════════════════════════════════════════════════

# Insert after the chart toggle buttons, before the WAR chart
old_chart_section = """      {/* Charts */}
      {base && !isPitcher && ("""

new_chart_section = """      {/* Season Projection Table */}
      {base && !isPitcher && (
        <Panel title="2026 SEASON PROJECTION" sub="Projected counting stats for the upcoming season.">
          <div className="via-table-wrap" style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,fontFamily:F}}>
              <thead>
                <tr style={{borderBottom:`2px solid ${C.navy}20`}}>
                  {["G","PA","HR","AVG","OBP","SLG","OPS","wRC+","WAR"].map(h=>(
                    <th key={h} style={{padding:"6px 10px",fontSize:10,fontWeight:700,color:C.navy,textAlign:"right",fontFamily:F,letterSpacing:".04em"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.projGames||Math.round((base.estPA||550)/4.1)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.estPA||"—"}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.hr>=30?C.green:base.hr>=20?"#1a6b3c":C.text,fontFamily:F}}>{base.hr}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.avg>=.290?C.green:base.avg>=.260?"#1a6b3c":C.text,fontFamily:F}}>{base.avg?.toFixed(3)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.obp>=.370?C.green:base.obp>=.330?"#1a6b3c":C.text,fontFamily:F}}>{base.obp?.toFixed(3)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.slg>=.500?C.green:base.slg>=.430?"#1a6b3c":C.text,fontFamily:F}}>{base.slg?.toFixed(3)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:800,color:base.ops>=.850?C.green:base.ops>=.730?"#1a6b3c":C.text,fontFamily:F}}>{base.ops?.toFixed(3)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:800,color:base.wRCPlus>=120?C.green:base.wRCPlus>=100?"#1a6b3c":C.text,fontFamily:F}}>{base.wRCPlus}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:800,color:base.baseWAR>=4?C.green:base.baseWAR>=2?"#1a6b3c":C.text,fontFamily:F}}>{base.baseWAR?.toFixed(1)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* Charts */}
      {base && !isPitcher && ("""

if old_chart_section in src:
    src = src.replace(old_chart_section, new_chart_section, 1)
    changes += 1
    print("6. Added 2026 Season Projection table (G, PA, HR, AVG, OBP, SLG, OPS, wRC+, WAR)")

# Also remove Peak Age from pitcher stat boxes
old_pitcher_peak = """              {peak&&<Stat label="Peak Age" value={peak.age} color={C.cyan}/>}
            </div>
          </>}
          {base&&!isPitcher&&<>"""

new_pitcher_peak = """            </div>
          </>}
          {base&&!isPitcher&&<>"""

if old_pitcher_peak in src:
    src = src.replace(old_pitcher_peak, new_pitcher_peak, 1)
    changes += 1
    print("7. Removed Peak Age from pitcher stat boxes")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
