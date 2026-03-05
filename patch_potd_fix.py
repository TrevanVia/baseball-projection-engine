#!/usr/bin/env python3
"""Fix POTD section: center content, add slash line, fill space. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Replace the entire POTD component render
old_potd = '''    <Panel title="\u2605 PLAYER OF THE DAY" style={{flex:1,background:`linear-gradient(135deg, ${C.navy}06, ${C.accent}04)`,border:`1px solid ${C.navy}15`}}>
      <div style={{textAlign:"center"}}>
      {loading ? (
        <div style={{fontSize:11,color:C.muted,fontFamily:F,padding:8}}>Loading...</div>
      ) : potdData ? (
        <div>
          <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,marginBottom:8}}>
            <button onClick={()=>onSelect(potdData.player)}
              style={{background:"none",border:"none",cursor:"pointer",fontSize:22,fontWeight:800,color:C.navy,fontFamily:F,padding:0}}
              onMouseEnter={e=>e.target.style.color=C.accent}
              onMouseLeave={e=>e.target.style.color=C.navy}
            >{potdData.player.fullName}</button>
            {potdData.fv && <FVBadge fv={potdData.fv}/>}
          </div>
          <div style={{fontSize:10,color:C.muted,fontFamily:F,marginBottom:10}}>
            {posLabel(potdData.player.primaryPosition?.code)} &middot; {potdData.player.currentTeam?.name||"Free Agent"} &middot; Age {potdData.player.currentAge}
          </div>
          {potdData.base && (
            <div style={{display:"flex",justifyContent:"center",gap:12}}>
              {potdData.base.isPitcher ? <>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.era<=3.00?C.green:potdData.base.era<=3.80?C.blue:C.text,fontFamily:F}}>{potdData.base.era.toFixed(2)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em",marginTop:1}}>Proj ERA</div>
                </div>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.k9>=10?C.green:potdData.base.k9>=8.5?C.blue:C.text,fontFamily:F}}>{potdData.base.k9.toFixed(1)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em",marginTop:1}}>Proj K/9</div>
                </div>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.baseWAR>=4?C.green:potdData.base.baseWAR>=2?C.blue:C.text,fontFamily:F}}>{potdData.base.baseWAR.toFixed(1)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em",marginTop:1}}>Proj WAR</div>
                </div>
              </> : <>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.ops>=.850?C.green:potdData.base.ops>=.720?C.blue:C.text,fontFamily:F}}>{potdData.base.ops.toFixed(3)}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>Proj OPS</div>
                </div>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.wRCPlus>=120?C.green:potdData.base.wRCPlus>=100?C.blue:C.text,fontFamily:F}}>{potdData.base.wRCPlus}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>wRC+</div>
                </div>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.hr>=30?C.green:potdData.base.hr>=20?C.blue:C.text,fontFamily:F}}>{potdData.base.hr}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>Proj HR</div>
                </div>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.baseWAR>=4?C.green:potdData.base.baseWAR>=2?C.blue:C.text,fontFamily:F}}>{potdData.base.baseWAR.toFixed(1)}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>Proj WAR</div>
                </div>
              </>}
              {potdData.cWAR !== null && (
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.cWAR>=30?C.green:potdData.cWAR>=15?C.blue:C.purple,fontFamily:F}}>{potdData.cWAR.toFixed(1)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em",marginTop:1}}>Career fWAR</div>
                </div>
              )}
            </div>
          )}
          <button onClick={()=>onSelect(potdData.player)} style={{marginTop:14,padding:"8px 20px",borderRadius:6,border:`1px solid ${C.accent}40`,background:`${C.accent}08`,color:C.accent,fontSize:11,fontWeight:700,fontFamily:F,cursor:"pointer",transition:"all 0.15s"}} onMouseEnter={e=>{e.currentTarget.style.background=C.accent;e.currentTarget.style.color="#fff";}} onMouseLeave={e=>{e.currentTarget.style.background=`${C.accent}08`;e.currentTarget.style.color=C.accent;}}>View Full Projection &rarr;</button>
        </div>
      ) : (
        <div style={{fontSize:11,color:C.muted,fontFamily:F}}>{name}</div>
      )}
      </div>
    </Panel>'''

new_potd = '''    <Panel title="\u2605 PLAYER OF THE DAY" style={{flex:1,background:`linear-gradient(135deg, ${C.navy}06, ${C.accent}04)`,border:`1px solid ${C.navy}15`,display:"flex",flexDirection:"column"}}>
      <div style={{textAlign:"center",flex:1,display:"flex",flexDirection:"column",justifyContent:"center"}}>
      {loading ? (
        <div style={{fontSize:11,color:C.muted,fontFamily:F,padding:8}}>Loading...</div>
      ) : potdData ? (
        <div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:4}}>
          <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,marginBottom:4}}>
            <button onClick={()=>onSelect(potdData.player)}
              style={{background:"none",border:"none",cursor:"pointer",fontSize:24,fontWeight:800,color:C.navy,fontFamily:F,padding:0}}
              onMouseEnter={e=>e.target.style.color=C.accent}
              onMouseLeave={e=>e.target.style.color=C.navy}
            >{potdData.player.fullName}</button>
            {potdData.fv && <FVBadge fv={potdData.fv}/>}
          </div>
          <div style={{fontSize:11,color:C.muted,fontFamily:F,marginBottom:12}}>
            {posLabel(potdData.player.primaryPosition?.code)} &middot; {potdData.player.currentTeam?.name||"Free Agent"} &middot; Age {potdData.player.currentAge}
          </div>
          {potdData.base && !potdData.base.isPitcher && (
            <div style={{display:"flex",flexDirection:"column",gap:14,width:"100%",maxWidth:320}}>
              {/* Slash line */}
              <div style={{display:"flex",justifyContent:"center",gap:4,fontSize:13,fontFamily:F,color:C.dim}}>
                <span><span style={{fontWeight:700,color:C.text}}>{potdData.base.avg?.toFixed(3)||".000"}</span><span style={{fontSize:9,color:C.muted}}> AVG</span></span>
                <span style={{color:C.border}}>/</span>
                <span><span style={{fontWeight:700,color:C.text}}>{potdData.base.obp?.toFixed(3)||".000"}</span><span style={{fontSize:9,color:C.muted}}> OBP</span></span>
                <span style={{color:C.border}}>/</span>
                <span><span style={{fontWeight:700,color:C.text}}>{potdData.base.slg?.toFixed(3)||".000"}</span><span style={{fontSize:9,color:C.muted}}> SLG</span></span>
              </div>
              {/* Main stats grid */}
              <div style={{display:"grid",gridTemplateColumns:"repeat(4, 1fr)",gap:8}}>
                <div style={{textAlign:"center",padding:"8px 0",background:`${C.navy}05`,borderRadius:6}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.ops>=.850?C.green:potdData.base.ops>=.720?C.blue:C.text,fontFamily:F}}>{potdData.base.ops.toFixed(3)}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>OPS</div>
                </div>
                <div style={{textAlign:"center",padding:"8px 0",background:`${C.navy}05`,borderRadius:6}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.wRCPlus>=120?C.green:potdData.base.wRCPlus>=100?C.blue:C.text,fontFamily:F}}>{potdData.base.wRCPlus}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>wRC+</div>
                </div>
                <div style={{textAlign:"center",padding:"8px 0",background:`${C.navy}05`,borderRadius:6}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.hr>=30?C.green:potdData.base.hr>=20?C.blue:C.text,fontFamily:F}}>{potdData.base.hr}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>HR</div>
                </div>
                <div style={{textAlign:"center",padding:"8px 0",background:`${C.navy}05`,borderRadius:6}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.baseWAR>=4?C.green:potdData.base.baseWAR>=2?C.blue:C.text,fontFamily:F}}>{potdData.base.baseWAR.toFixed(1)}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>WAR</div>
                </div>
              </div>
              {/* Career WAR bar */}
              {potdData.cWAR !== null && (
                <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,padding:"6px 0",borderTop:`1px solid ${C.border}30`}}>
                  <span style={{fontSize:9,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em"}}>Career fWAR</span>
                  <span style={{fontSize:16,fontWeight:800,color:potdData.cWAR>=30?C.green:potdData.cWAR>=15?C.blue:C.text,fontFamily:F}}>{potdData.cWAR.toFixed(1)}</span>
                </div>
              )}
            </div>
          )}
          {potdData.base && potdData.base.isPitcher && (
            <div style={{display:"flex",flexDirection:"column",gap:14,width:"100%",maxWidth:320}}>
              {/* Pitcher stats grid */}
              <div style={{display:"grid",gridTemplateColumns:"repeat(3, 1fr)",gap:8}}>
                <div style={{textAlign:"center",padding:"10px 0",background:`${C.navy}05`,borderRadius:6}}>
                  <div style={{fontSize:24,fontWeight:800,color:potdData.base.era<=3.00?C.green:potdData.base.era<=3.80?C.blue:C.text,fontFamily:F}}>{potdData.base.era.toFixed(2)}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>ERA</div>
                </div>
                <div style={{textAlign:"center",padding:"10px 0",background:`${C.navy}05`,borderRadius:6}}>
                  <div style={{fontSize:24,fontWeight:800,color:potdData.base.k9>=10?C.green:potdData.base.k9>=8.5?C.blue:C.text,fontFamily:F}}>{potdData.base.k9.toFixed(1)}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>K/9</div>
                </div>
                <div style={{textAlign:"center",padding:"10px 0",background:`${C.navy}05`,borderRadius:6}}>
                  <div style={{fontSize:24,fontWeight:800,color:potdData.base.baseWAR>=4?C.green:potdData.base.baseWAR>=2?C.blue:C.text,fontFamily:F}}>{potdData.base.baseWAR.toFixed(1)}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>WAR</div>
                </div>
              </div>
              <div style={{display:"grid",gridTemplateColumns:"repeat(3, 1fr)",gap:8}}>
                <div style={{textAlign:"center",padding:"6px 0"}}>
                  <div style={{fontSize:15,fontWeight:700,color:C.text,fontFamily:F}}>{potdData.base.whip?.toFixed(2)||"\u2014"}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase"}}>WHIP</div>
                </div>
                <div style={{textAlign:"center",padding:"6px 0"}}>
                  <div style={{fontSize:15,fontWeight:700,color:C.text,fontFamily:F}}>{potdData.base.ip||"\u2014"}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase"}}>IP</div>
                </div>
                <div style={{textAlign:"center",padding:"6px 0"}}>
                  <div style={{fontSize:15,fontWeight:700,color:C.text,fontFamily:F}}>{potdData.base.fip?.toFixed(2)||"\u2014"}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase"}}>FIP</div>
                </div>
              </div>
              {potdData.cWAR !== null && (
                <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,padding:"6px 0",borderTop:`1px solid ${C.border}30`}}>
                  <span style={{fontSize:9,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em"}}>Career fWAR</span>
                  <span style={{fontSize:16,fontWeight:800,color:potdData.cWAR>=30?C.green:potdData.cWAR>=15?C.blue:C.text,fontFamily:F}}>{potdData.cWAR.toFixed(1)}</span>
                </div>
              )}
            </div>
          )}
          <button onClick={()=>onSelect(potdData.player)} style={{marginTop:10,padding:"9px 24px",borderRadius:6,border:`1px solid ${C.accent}40`,background:`${C.accent}08`,color:C.accent,fontSize:11,fontWeight:700,fontFamily:F,cursor:"pointer",transition:"all 0.15s"}} onMouseEnter={e=>{e.currentTarget.style.background=C.accent;e.currentTarget.style.color="#fff";}} onMouseLeave={e=>{e.currentTarget.style.background=`${C.accent}08`;e.currentTarget.style.color=C.accent;}}>View Full Projection &rarr;</button>
        </div>
      ) : (
        <div style={{fontSize:11,color:C.muted,fontFamily:F}}>{name}</div>
      )}
      </div>
    </Panel>'''

if old_potd in src:
    src = src.replace(old_potd, new_potd)
    changes += 1
    print("1. Redesigned POTD: vertically centered, grid stats, slash line, no dead space")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
