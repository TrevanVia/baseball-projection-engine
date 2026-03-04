#!/usr/bin/env python3
"""Fix prospect section + enlarge POTD. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Replace the bottom grid (Prospects + What Is + POTD)
old_bottom = '''            {/* Top Prospects + Player of the Day */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
              <Panel title="TOP PROSPECTS" sub="Highest FV grades in the system.">
                <div style={{display:"flex",flexDirection:"column",gap:4}}>
                  {[
                    {n:"Roki Sasaki",fv:70,t:"LAD",pos:"SP",note:"Generational arm"},
                    {n:"Konnor Griffin",fv:60,t:"DET",pos:"SS",note:"Elite tools"},
                    {n:"Kevin McGonigle",fv:60,t:"DET",pos:"SS",note:"Advanced bat"},
                    {n:"Samuel Basallo",fv:65,t:"BAL",pos:"C",note:"Power + discipline"},
                    {n:"Aidan Miller",fv:55,t:"PHI",pos:"3B",note:"Hit tool"},
                  ].map(p=>(
                    <div key={p.n} onClick={()=>searchPlayers(p.n).then(r=>{if(r[0])pick(r[0]);})}
                      style={{display:"flex",alignItems:"center",gap:8,padding:"7px 10px",borderRadius:6,cursor:"pointer",transition:"background 0.1s"}}
                      onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
                      onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                      <FVBadge fv={p.fv}/>
                      <div style={{flex:1}}>
                        <div style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.n}</div>
                        <div style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.t} · {p.note}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
              <div style={{display:"flex",flexDirection:"column",gap:14}}>
                <Panel title="WHAT IS VIACAST?" style={{flex:1}}>
                  <div style={{fontSize:11,color:C.dim,fontFamily:F,lineHeight:1.8}}>
                    <p style={{margin:"0 0 8px"}}>VIAcast is a baseball projection engine built on <span style={{color:C.text,fontWeight:600}}>Statcast data</span> — expected stats (xwOBA, xBA, xSLG), barrel rates, exit velocities, plate discipline, and sprint speed.</p>
                    <p style={{margin:"0 0 8px"}}>Unlike traditional projection systems, VIAcast uses <span style={{color:C.text,fontWeight:600}}>process-based metrics</span> that measure what a player is actually doing, not just the outcomes. This means better predictions for breakout candidates and aging veterans.</p>
                    <p style={{margin:0}}>Covers <span style={{color:C.text,fontWeight:600}}>900+ MLB hitters</span>, <span style={{color:C.text,fontWeight:600}}>1,200+ pitchers</span>, and all MiLB levels with FanGraphs FV grades for top prospects.</p>
                  </div>
                </Panel>
                <PlayerOfTheDay onSelect={pick}/>
              </div>
            </div>'''

new_bottom = '''            {/* Top Prospects + What Is VIAcast */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
              <Panel title="TOP PROSPECTS" sub="Highest FV grades in the system.">
                <div style={{display:"flex",flexDirection:"column",gap:2}}>
                  {[
                    {n:"Konnor Griffin",fv:70,t:"DET",pos:"SS",note:"Best prospect in baseball. 80-grade power potential with elite bat speed, above-average speed, and premium defense at shortstop. Only 70 FV in the system."},
                    {n:"Samuel Basallo",fv:65,t:"BAL",pos:"C",note:"Switch-hitting catcher who destroyed AAA at 20 — .966 OPS with 23 HR and a 13.7% walk rate. Rare power-discipline combo behind the plate."},
                    {n:"Kevin McGonigle",fv:65,t:"DET",pos:"SS",note:"Advanced hit tool with elite contact skills and an all-fields approach. Profiles as a high-OBP, plus-contact shortstop who rarely strikes out."},
                    {n:"Roki Sasaki",fv:60,t:"LAD",pos:"SP",note:"Triple-digit fastball with an unhittable splitter. Posted a 2.10 ERA in NPB. Electric stuff, just needs to stay healthy."},
                    {n:"JJ Wetherholt",fv:60,t:"CLE",pos:"2B",note:"2024 first-rounder with one of the best college bats in recent memory. Elite contact, barrel rate, and pitch recognition from both sides."},
                    {n:"Max Clark",fv:60,t:"DET",pos:"CF",note:"80-grade speed with a left-handed swing built for contact. Advanced approach for his age with the athleticism to be a defensive weapon in center."},
                    {n:"Aidan Miller",fv:55,t:"PHI",pos:"3B",note:"Smooth left-handed swing with natural feel to hit. Solid power projection and the bat-to-ball skills to hit for average at the highest level."},
                    {n:"Roman Anthony",fv:55,t:"BOS",pos:"LF",note:"Physical lefty with plus raw power and improving plate discipline. Showed he belongs with a strong MLB debut — the bat plays."},
                  ].map((p,i)=>(
                    <div key={p.n} onClick={()=>searchPlayers(p.n).then(r=>{if(r[0])pick(r[0]);})}
                      style={{display:"flex",alignItems:"flex-start",gap:10,padding:"10px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
                      onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
                      onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                      <div style={{paddingTop:2}}><FVBadge fv={p.fv}/></div>
                      <div style={{flex:1}}>
                        <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:3}}>
                          <span style={{fontSize:12,fontWeight:700,color:C.text,fontFamily:F}}>{p.n}</span>
                          <span style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.t}</span>
                        </div>
                        <div style={{fontSize:10,color:C.dim,fontFamily:F,lineHeight:1.5}}>{p.note}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
              <div style={{display:"flex",flexDirection:"column",gap:14}}>
                <Panel title="WHAT IS VIACAST?">
                  <div style={{fontSize:11,color:C.dim,fontFamily:F,lineHeight:1.8}}>
                    <p style={{margin:"0 0 8px"}}>VIAcast is a baseball projection engine built on <span style={{color:C.text,fontWeight:600}}>Statcast data</span> — expected stats (xwOBA, xBA, xSLG), barrel rates, exit velocities, plate discipline, and sprint speed.</p>
                    <p style={{margin:"0 0 8px"}}>Unlike traditional projection systems, VIAcast uses <span style={{color:C.text,fontWeight:600}}>process-based metrics</span> that measure what a player is actually doing, not just the outcomes. This means better predictions for breakout candidates and aging veterans.</p>
                    <p style={{margin:0}}>Covers <span style={{color:C.text,fontWeight:600}}>900+ MLB hitters</span>, <span style={{color:C.text,fontWeight:600}}>1,200+ pitchers</span>, and all MiLB levels with FanGraphs FV grades for top prospects.</p>
                  </div>
                </Panel>
                <PlayerOfTheDay onSelect={pick}/>
              </div>
            </div>'''

if old_bottom in src:
    src = src.replace(old_bottom, new_bottom)
    changes += 1
    print("1. Fixed prospect grades, added scouting descriptions, expanded to 8 prospects")

# Now enlarge the Player of the Day component
old_potd_container = '''    <div style={{margin:"20px auto 0",maxWidth:400,padding:"18px 22px",background:`linear-gradient(135deg, ${C.navy}06, ${C.accent}04)`,border:`1px solid ${C.navy}18`,borderRadius:12,textAlign:"center"}}>'''

new_potd_container = '''    <div style={{padding:"22px 26px",background:`linear-gradient(135deg, ${C.navy}06, ${C.accent}04)`,border:`1px solid ${C.navy}18`,borderRadius:12,textAlign:"center",flex:1}}>'''

if old_potd_container in src:
    src = src.replace(old_potd_container, new_potd_container)
    changes += 1
    print("2. Enlarged POTD container (removed maxWidth, added flex:1)")

# Make POTD player name bigger
old_potd_name = '''style={{background:"none",border:"none",cursor:"pointer",fontSize:18,fontWeight:800,color:C.navy,fontFamily:F,padding:0}}'''
new_potd_name = '''style={{background:"none",border:"none",cursor:"pointer",fontSize:22,fontWeight:800,color:C.navy,fontFamily:F,padding:0}}'''
if old_potd_name in src:
    src = src.replace(old_potd_name, new_potd_name)
    changes += 1
    print("3. Enlarged POTD player name (18px -> 22px)")

# Make POTD stat values bigger
old_potd_stat = '''style={{fontSize:18,fontWeight:800,color:'''
new_potd_stat = '''style={{fontSize:22,fontWeight:800,color:'''
src = src.replace(old_potd_stat, new_potd_stat)
changes += 1
print("4. Enlarged POTD stat values (18px -> 22px)")

# Add "Click for full projection" link that's more prominent
old_potd_click = '''<div style={{fontSize:9,color:C.muted,fontFamily:F,marginTop:10,cursor:"pointer"}} onClick={()=>onSelect(potdData.player)}>Click for full projections &rarr;</div>'''
new_potd_click = '''<button onClick={()=>onSelect(potdData.player)} style={{marginTop:14,padding:"8px 20px",borderRadius:6,border:`1px solid ${C.accent}40`,background:`${C.accent}08`,color:C.accent,fontSize:11,fontWeight:700,fontFamily:F,cursor:"pointer",transition:"all 0.15s"}} onMouseEnter={e=>{e.currentTarget.style.background=C.accent;e.currentTarget.style.color="#fff";}} onMouseLeave={e=>{e.currentTarget.style.background=`${C.accent}08`;e.currentTarget.style.color=C.accent;}}>View Full Projection &rarr;</button>'''
if old_potd_click in src:
    src = src.replace(old_potd_click, new_potd_click)
    changes += 1
    print("5. POTD: replaced text link with styled button")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
