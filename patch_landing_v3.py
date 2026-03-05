#!/usr/bin/env python3
"""Landing page overhaul: color, layout, bio fixes, POTD redesign. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. REPLACE THE ENTIRE LANDING PAGE
# ═══════════════════════════════════════════════════════════════

old_landing = '''          {!selPlayer&&!lp&&<div style={{display:"flex",flexDirection:"column",gap:14}}>
            {/* Hero */}
            <Panel style={{textAlign:"center",padding:"40px 28px 32px",background:`linear-gradient(180deg, #f9f5ed 0%, #f4efe4 100%)`}}>
              <div style={{fontSize:11,fontWeight:700,letterSpacing:".15em",color:C.accent,fontFamily:F,textTransform:"uppercase",marginBottom:8}}>2026 Projections</div>
              <h2 style={{margin:0,fontSize:22,color:C.navy,fontFamily:F,lineHeight:1.3,letterSpacing:"-0.02em"}}>Statcast-Powered MLB Projections</h2>
              <p style={{margin:"10px auto 0",fontSize:12,color:C.dim,fontFamily:F,maxWidth:560,lineHeight:1.7}}>
                VIAcast projects every MLB and MiLB player using 3 years of Baseball Savant data — expected stats, barrel rates, plate discipline, sprint speed, and more. Search any player to see their full projection.
              </p>
              <div style={{marginTop:20,display:"flex",gap:8,justifyContent:"center",flexWrap:"wrap"}}>
                {["Aaron Judge","Juan Soto","Gunnar Henderson","Paul Skenes","Bobby Witt Jr.","Samuel Basallo"].map(n=>
                  <button key={n} onClick={()=>searchPlayers(n).then(r=>{if(r[0])pick(r[0]);})}
                    className="via-quick-pick" style={{padding:"7px 14px",borderRadius:8,border:`1px solid ${C.border}`,background:"#fff",color:C.text,fontSize:11,fontWeight:600,fontFamily:F,cursor:"pointer"}}
                  >{n}</button>
                )}
              </div>
            </Panel>'''

new_landing = '''          {!selPlayer&&!lp&&<div style={{display:"flex",flexDirection:"column",gap:14}}>
            {/* Hero */}
            <Panel style={{textAlign:"center",padding:"40px 28px 24px",background:`linear-gradient(180deg, #f9f5ed 0%, #f4efe4 100%)`}}>
              <div style={{fontSize:11,fontWeight:700,letterSpacing:".15em",color:C.accent,fontFamily:F,textTransform:"uppercase",marginBottom:8}}>2026 Projections</div>
              <h2 style={{margin:0,fontSize:22,color:C.navy,fontFamily:F,lineHeight:1.3,letterSpacing:"-0.02em"}}>Statcast-Powered MLB Projections</h2>
              <p style={{margin:"10px auto 0",fontSize:12,color:C.dim,fontFamily:F,maxWidth:560,lineHeight:1.7}}>
                VIAcast projects every MLB and MiLB player using 3 years of Baseball Savant data — expected stats, barrel rates, plate discipline, sprint speed, and more. Search any player to see their full projection.
              </p>
              <div style={{marginTop:16,display:"flex",gap:8,justifyContent:"center",flexWrap:"wrap"}}>
                {["Aaron Judge","Juan Soto","Gunnar Henderson","Paul Skenes","Bobby Witt Jr.","Samuel Basallo"].map(n=>
                  <button key={n} onClick={()=>searchPlayers(n).then(r=>{if(r[0])pick(r[0]);})}
                    className="via-quick-pick" style={{padding:"7px 14px",borderRadius:8,border:`1px solid ${C.border}`,background:"#fff",color:C.text,fontSize:11,fontWeight:600,fontFamily:F,cursor:"pointer"}}
                  >{n}</button>
                )}
              </div>
            </Panel>

            {/* Engine Stats Bar - moved up */}
            <div style={{display:"flex",justifyContent:"center",gap:20,flexWrap:"wrap",padding:"14px 20px",background:`linear-gradient(135deg, ${C.navy}08, ${C.accent}05)`,borderRadius:12,border:`1px solid ${C.navy}12`}}>
              {[
                {v:"900+",l:"MLB Hitters",c:C.green},
                {v:"1,200+",l:"MLB Pitchers",c:C.blue},
                {v:"3 Years",l:"Savant Data",c:C.purple},
                {v:"All Levels",l:"ROK \u2192 MLB",c:C.orange},
                {v:"7 Layers",l:"Projection Engine",c:C.accent},
              ].map(s=>(
                <div key={s.l} style={{textAlign:"center",minWidth:80}}>
                  <div style={{fontSize:20,fontWeight:800,color:s.c,fontFamily:F}}>{s.v}</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".1em",marginTop:2}}>{s.l}</div>
                </div>
              ))}
            </div>'''

if old_landing in src:
    src = src.replace(old_landing, new_landing)
    changes += 1
    print("1. Moved stats bar up below hero, added color to stats")

# ═══════════════════════════════════════════════════════════════
# 2. REMOVE THE OLD ENGINE STATS BAR AT THE BOTTOM
# ═══════════════════════════════════════════════════════════════

old_bottom_stats = '''            {/* Engine Stats */}
            <Panel>
              <div style={{display:"flex",justifyContent:"center",gap:32,flexWrap:"wrap",padding:"8px 0"}}>
                {[
                  {v:"900+",l:"MLB Hitters"},
                  {v:"1,200+",l:"MLB Pitchers"},
                  {v:"3 Years",l:"Savant Data"},
                  {v:"All Levels",l:"ROK \u2192 MLB"},
                  {v:"7 Layers",l:"Projection Engine"},
                ].map(s=>(
                  <div key={s.l} style={{textAlign:"center"}}>
                    <div style={{fontSize:22,fontWeight:800,color:C.navy,fontFamily:F}}>{s.v}</div>
                    <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".1em",marginTop:2}}>{s.l}</div>
                  </div>
                ))}
              </div>
            </Panel>'''

if old_bottom_stats in src:
    src = src.replace(old_bottom_stats, '')
    changes += 1
    print("2. Removed old bottom stats bar (now at top)")

# ═══════════════════════════════════════════════════════════════
# 3. FIX PROSPECT BIOS
# ═══════════════════════════════════════════════════════════════

# Basallo: switch -> lefty
old_basallo = 'Switch-hitting catcher who destroyed AAA at 20'
new_basallo = 'Left-handed hitting catcher who destroyed AAA at 20'
if old_basallo in src:
    src = src.replace(old_basallo, new_basallo)
    changes += 1
    print("3. Fixed Basallo: switch-hitting -> left-handed hitting")

# Miller: left-handed -> right-handed
old_miller = 'Smooth left-handed swing with natural feel to hit. Solid power projection and the bat-to-ball skills to hit for average at the highest level.'
new_miller = 'Smooth right-handed swing with natural feel to hit. Plus bat-to-ball skills with developing power and the hand-eye coordination to be a consistent .280+ hitter.'
if old_miller in src:
    src = src.replace(old_miller, new_miller)
    changes += 1
    print("4. Fixed Miller: left-handed -> right-handed swing, updated description")

# ═══════════════════════════════════════════════════════════════
# 4. REDESIGN PLAYER OF THE DAY
# ═══════════════════════════════════════════════════════════════

old_potd_container = '''    <div style={{padding:"22px 26px",background:`linear-gradient(135deg, ${C.navy}06, ${C.accent}04)`,border:`1px solid ${C.navy}18`,borderRadius:12,textAlign:"center",flex:1}}>
      <div style={{fontSize:8,fontWeight:700,letterSpacing:".12em",color:C.accent,fontFamily:F,textTransform:"uppercase",marginBottom:6}}>&#9733; Player of the Day &#9733;</div>'''

new_potd_container = '''    <Panel title="\u2605 PLAYER OF THE DAY" style={{flex:1,background:`linear-gradient(135deg, ${C.navy}06, ${C.accent}04)`,border:`1px solid ${C.navy}15`}}>
      <div style={{textAlign:"center"}}>'''

if old_potd_container in src:
    src = src.replace(old_potd_container, new_potd_container)
    changes += 1
    print("5. POTD: use Panel component with title")

# Fix the POTD closing tags - replace the raw </div> at the end
old_potd_end = '''      )}\n    </div>\n  );\n}\n\n// ── MAIN APP'''
new_potd_end = '''      )}\n      </div>\n    </Panel>\n  );\n}\n\n// ── MAIN APP'''

# Actually let me find the exact closing structure
old_potd_close = '''      )}
    </div>
  );
}

// ── MAIN APP'''

new_potd_close = '''      )}
      </div>
    </Panel>
  );
}

// ── MAIN APP'''

if old_potd_close in src:
    src = src.replace(old_potd_close, new_potd_close)
    changes += 1
    print("6. POTD: fixed closing tags for Panel")

# Add wRC+ and peak age to POTD hitter stats (more data = less empty space)
old_potd_hitter_stats = '''              <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.ops>=.850?C.green:potdData.base.ops>=.720?C.blue:C.text,fontFamily:F}}>{potdData.base.ops.toFixed(3)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em",marginTop:1}}>Proj OPS</div>
                </div>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.hr>=30?C.green:potdData.base.hr>=20?C.blue:C.text,fontFamily:F}}>{potdData.base.hr}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em",marginTop:1}}>Proj HR</div>
                </div>
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:22,fontWeight:800,color:potdData.base.baseWAR>=4?C.green:potdData.base.baseWAR>=2?C.blue:C.text,fontFamily:F}}>{potdData.base.baseWAR.toFixed(1)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".08em",marginTop:1}}>Proj WAR</div>
                </div>'''

new_potd_hitter_stats = '''              <div style={{textAlign:"center"}}>
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
                </div>'''

if old_potd_hitter_stats in src:
    src = src.replace(old_potd_hitter_stats, new_potd_hitter_stats)
    changes += 1
    print("7. POTD: added wRC+ stat, increased label sizes")

# ═══════════════════════════════════════════════════════════════
# 5. ADD COLOR TO TOP HITTERS/PITCHERS HEADERS
# ═══════════════════════════════════════════════════════════════

old_hitters_panel = '''<Panel title="TOP HITTERS" sub="2026 projected WAR leaders.">'''
new_hitters_panel = '''<Panel title="TOP HITTERS" sub="2026 projected WAR leaders." style={{borderTop:`3px solid ${C.green}`}}>'''
if old_hitters_panel in src:
    src = src.replace(old_hitters_panel, new_hitters_panel)
    changes += 1
    print("8. Added green accent border to Top Hitters")

old_pitchers_panel = '''<Panel title="TOP PITCHERS" sub="2026 projected WAR leaders.">'''
new_pitchers_panel = '''<Panel title="TOP PITCHERS" sub="2026 projected WAR leaders." style={{borderTop:`3px solid ${C.blue}`}}>'''
if old_pitchers_panel in src:
    src = src.replace(old_pitchers_panel, new_pitchers_panel)
    changes += 1
    print("9. Added blue accent border to Top Pitchers")

old_prospects_panel = '''<Panel title="TOP PROSPECTS" sub="Highest FV grades in the system.">'''
new_prospects_panel = '''<Panel title="TOP PROSPECTS" sub="Highest FV grades in the system." style={{borderTop:`3px solid ${C.accent}`}}>'''
if old_prospects_panel in src:
    src = src.replace(old_prospects_panel, new_prospects_panel)
    changes += 1
    print("10. Added red accent border to Top Prospects")

old_what_panel = '''<Panel title="WHAT IS VIACAST?">'''
new_what_panel = '''<Panel title="WHAT IS VIACAST?" style={{borderTop:`3px solid ${C.purple}`}}>'''
if old_what_panel in src:
    src = src.replace(old_what_panel, new_what_panel)
    changes += 1
    print("11. Added purple accent border to What Is VIAcast")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
