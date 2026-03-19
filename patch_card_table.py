#!/usr/bin/env python3
"""Add season projection table to player card. Run AFTER patch_card_redesign.py."""
APP = "src/App.jsx"
src = open(APP).read()

old = """      {forward.length>0&&<>"""

new = """      {/* Season Projection Table */}
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
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.estPA||"\u2014"}</td>
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

      {forward.length>0&&<>"""

if old in src:
    src = src.replace(old, new, 1)
    open(APP, "w").write(src)
    print("Added 2026 Season Projection table")
else:
    print("Already applied or target not found")
