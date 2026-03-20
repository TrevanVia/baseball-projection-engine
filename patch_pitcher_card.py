#!/usr/bin/env python3
"""Redesign pitcher card to match hitter card layout. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Slim down pitcher stat boxes to just Career fWAR + 10yr WAR (like hitters)
old_pitcher_stats = """            {base&&isPitcher&&<>
            <div className="via-stat-row" style={{display:"flex",gap:6,flexWrap:"wrap"}}>
              <Stat label="Proj ERA" value={base.era?.toFixed(2)} color={base.era<=3.00?C.green:base.era<=3.80?C.blue:base.era<=4.50?C.text:C.accent}/>
              <Stat label="Proj FIP" value={base.fip?.toFixed(2)} color={base.fip<=3.00?C.green:base.fip<=3.80?C.blue:base.fip<=4.50?C.text:C.accent}/>
              <Stat label="Proj WHIP" value={base.whip?.toFixed(2)} color={base.whip<=1.05?C.green:base.whip<=1.20?C.blue:base.whip<=1.35?C.text:C.accent}/>
              <Stat label="Proj K/9" value={base.k9?.toFixed(1)} color={base.k9>=10?C.green:base.k9>=8.5?C.blue:C.text}/>
              <Stat label="Proj IP" value={base.ip} color={base.ip>=180?C.green:base.ip>=140?C.blue:C.text}/>
              <Stat label="Proj WAR" value={base.baseWAR?.toFixed(1)} color={base.baseWAR>=5?C.green:base.baseWAR>=3?C.blue:base.baseWAR>=1?C.purple:C.text}/>
              {cWAR!==null&&<Stat label="Career fWAR" value={cWAR.toFixed(1)} color={cWAR>=30?C.green:cWAR>=15?C.blue:C.purple}/>}
            </div>
          </>}"""

new_pitcher_stats = """            {base&&isPitcher&&<>
            <div className="via-stat-row" style={{display:"flex",gap:6,flexWrap:"wrap"}}>
              {cWAR!==null&&<Stat label="Career fWAR" value={cWAR.toFixed(1)} color={cWAR>=30?C.green:cWAR>=15?C.blue:C.purple} sub="FanGraphs"/>}
              <Stat label="10yr WAR" value={cum.toFixed(1)} color={C.purple} sub="Projected"/>
            </div>
          </>}"""

if old_pitcher_stats in src:
    src = src.replace(old_pitcher_stats, new_pitcher_stats)
    changes += 1
    print("1. Slimmed pitcher stat boxes to Career fWAR + 10yr WAR")

# 2. Add pitcher season projection table (before the chart section)
old_chart = """      {forward.length>0&&<>
        <div style={{display:"flex",gap:4,background:"#efe9dd",borderRadius:10,padding:4,width:"fit-content"}}>
          {(isPitcher?[{k:"war",l:"WAR"}]:[{k:"war",l:"WAR"},{k:"wrc",l:"wRC+"},{k:"ops",l:"OPS"}]).map(t=><Pill key={t.k} label={t.l} active={projTab===t.k} onClick={()=>setProjTab(t.k)}/>)}"""

new_chart = """      {/* Pitcher Season Projection Table */}
      {base && isPitcher && (
        <Panel title="2026 SEASON PROJECTION" sub="Projected pitching stats for the upcoming season.">
          <div className="via-table-wrap" style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,fontFamily:F}}>
              <thead>
                <tr style={{borderBottom:`2px solid ${C.navy}20`}}>
                  {["W","L","ERA","FIP","WHIP","K/9","BB/9","IP","K","WAR"].map(h=>(
                    <th key={h} style={{padding:"6px 10px",fontSize:10,fontWeight:700,color:C.navy,textAlign:"right",fontFamily:F,letterSpacing:".04em"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.w||Math.round((base.ip||150)/9*(1-base.era/9.5)*0.55+5)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.l||Math.round((base.ip||150)/9*(base.era/9.5)*0.55+4)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.era<=3.00?C.green:base.era<=3.80?"#1a6b3c":C.text,fontFamily:F}}>{base.era?.toFixed(2)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.fip<=3.00?C.green:base.fip<=3.80?"#1a6b3c":C.text,fontFamily:F}}>{base.fip?.toFixed(2)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.whip<=1.05?C.green:base.whip<=1.20?"#1a6b3c":C.text,fontFamily:F}}>{base.whip?.toFixed(2)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.k9>=10?C.green:base.k9>=8.5?"#1a6b3c":C.text,fontFamily:F}}>{base.k9?.toFixed(1)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.bb9<=2.5?C.green:base.bb9<=3.5?"#1a6b3c":C.text,fontFamily:F}}>{base.bb9?.toFixed(1)||"—"}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.ip>=180?C.green:base.ip>=140?"#1a6b3c":C.text,fontFamily:F}}>{base.ip}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{Math.round((base.k9||8)*(base.ip||150)/9)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:800,color:base.baseWAR>=5?C.green:base.baseWAR>=3?"#1a6b3c":C.text,fontFamily:F}}>{base.baseWAR?.toFixed(1)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {forward.length>0&&<>
        <div style={{display:"flex",gap:4,background:"#efe9dd",borderRadius:10,padding:4,width:"fit-content"}}>
          {(isPitcher?[{k:"war",l:"WAR"}]:[{k:"war",l:"WAR"},{k:"wrc",l:"wRC+"},{k:"ops",l:"OPS"}]).map(t=><Pill key={t.k} label={t.l} active={projTab===t.k} onClick={()=>setProjTab(t.k)}/>)}"""

if old_chart in src:
    src = src.replace(old_chart, new_chart, 1)
    changes += 1
    print("2. Added pitcher 2026 Season Projection table (W, L, ERA, FIP, WHIP, K/9, BB/9, IP, K, WAR)")

# 3. Add bb9 to the Statcast pitcher return object (currently missing)
old_return_pitch = """      k9: Math.round(projK9 * 10) / 10,"""
new_return_pitch = """      k9: Math.round(projK9 * 10) / 10,
      bb9: Math.round(projBB9 * 10) / 10,"""
if old_return_pitch in src:
    src = src.replace(old_return_pitch, new_return_pitch, 1)
    changes += 1
    print("3. Added bb9 to Statcast pitcher return")

# 4. Also add bb9 to Marcel pitcher return if not present
# Check if Marcel already returns bb9
if src.count("bb9:") < 3:  # should have 2 after step 3 (statcast + display), need marcel too
    old_marcel_k9 = """    k9: Math.round(finalK9 * 10) / 10,"""
    new_marcel_k9 = """    k9: Math.round(finalK9 * 10) / 10,
    bb9: Math.round(finalBB9 * 10) / 10,"""
    if old_marcel_k9 in src:
        src = src.replace(old_marcel_k9, new_marcel_k9, 1)
        changes += 1
        print("4. Added bb9 to Marcel pitcher return")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
