#!/usr/bin/env python3
"""Redesign the landing/home page experience. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Replace the entire home panel (when no player is selected)
old_home = '''          {!selPlayer&&!lp&&<Panel style={{textAlign:"center",padding:"56px 32px"}}>
            <div style={{fontSize:48,marginBottom:16,filter:"drop-shadow(0 2px 4px rgba(0,0,0,0.1))"}}>&#9918;</div>
            <h3 style={{margin:0,fontSize:17,color:C.text,fontFamily:F,letterSpacing:"-0.01em"}}>Search any MLB or minor league player</h3>
            <p style={{margin:"6px auto 0",fontSize:12,color:C.muted,fontFamily:F,maxWidth:520,lineHeight:1.6}}>
              Covers all levels from Rookie ball through the majors. MiLB stats are translated using level-specific conversion factors before projection. Top prospects include FV grades and batted ball data.
            </p>
            <PlayerOfTheDay onSelect={pick}/>
            <div style={{marginTop:20,display:"flex",gap:8,justifyContent:"center",flexWrap:"wrap"}}>
              {["Konnor Griffin","Aidan Miller","Juan Soto","Gunnar Henderson","Kevin McGonigle","Samuel Basallo"].map(n=>
                <button key={n} onClick={()=>searchPlayers(n).then(r=>{if(r[0])pick(r[0]);})}
                  className="via-quick-pick" style={{padding:"6px 14px",borderRadius:8,border:`1px solid ${C.border}`,background:"transparent",color:C.dim,fontSize:11,fontFamily:F,cursor:"pointer"}}
                >{n}</button>
              )}
            </div>
          </Panel>}'''

new_home = '''          {!selPlayer&&!lp&&<div style={{display:"flex",flexDirection:"column",gap:14}}>
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
            </Panel>

            {/* Top Projections Grid */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
              <Panel title="TOP HITTERS" sub="2026 projected WAR leaders.">
                <div style={{display:"flex",flexDirection:"column",gap:2}}>
                  {[
                    {n:"Aaron Judge",t:"NYY",war:7.0,wrc:166,pos:"RF"},
                    {n:"Shohei Ohtani",t:"LAD",war:6.9,wrc:152,pos:"DH"},
                    {n:"Juan Soto",t:"NYM",war:6.5,wrc:156,pos:"RF"},
                    {n:"Bobby Witt Jr.",t:"KC",war:5.5,wrc:128,pos:"SS"},
                    {n:"Kyle Schwarber",t:"PHI",war:4.8,wrc:138,pos:"LF"},
                    {n:"Francisco Lindor",t:"NYM",war:4.6,wrc:115,pos:"SS"},
                    {n:"Gunnar Henderson",t:"BAL",war:4.3,wrc:116,pos:"SS"},
                    {n:"Mookie Betts",t:"LAD",war:4.2,wrc:114,pos:"SS"},
                  ].map((p,i)=>(
                    <div key={p.n} onClick={()=>searchPlayers(p.n).then(r=>{if(r[0])pick(r[0]);})}
                      style={{display:"flex",alignItems:"center",gap:10,padding:"7px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
                      onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
                      onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                      <span style={{fontSize:10,fontWeight:800,color:C.muted,fontFamily:F,minWidth:16}}>{i+1}</span>
                      <img src={`https://www.mlbstatic.com/team-logos/${({NYY:147,LAD:119,NYM:121,KC:118,PHI:143,BAL:110})[p.t]||147}.svg`} alt="" style={{width:20,height:20,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
                      <div style={{flex:1}}>
                        <div style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.n}</div>
                        <div style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.t}</div>
                      </div>
                      <div style={{textAlign:"right"}}>
                        <div style={{fontSize:13,fontWeight:800,color:p.war>=6?C.green:p.war>=4?C.blue:C.text,fontFamily:F}}>{p.war.toFixed(1)}</div>
                        <div style={{fontSize:8,color:C.muted,fontFamily:F}}>WAR</div>
                      </div>
                      <div style={{textAlign:"right",minWidth:32}}>
                        <div style={{fontSize:11,fontWeight:600,color:C.dim,fontFamily:F}}>{p.wrc}</div>
                        <div style={{fontSize:8,color:C.muted,fontFamily:F}}>wRC+</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="TOP PITCHERS" sub="2026 projected WAR leaders.">
                <div style={{display:"flex",flexDirection:"column",gap:2}}>
                  {[
                    {n:"Paul Skenes",t:"PIT",war:5.9,era:2.44,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",war:5.5,era:2.72,pos:"SP"},
                    {n:"Garrett Crochet",t:"BOS",war:5.4,era:2.97,pos:"SP"},
                    {n:"Bryan Woo",t:"SEA",war:4.8,era:3.00,pos:"SP"},
                    {n:"Yoshinobu Yamamoto",t:"LAD",war:4.5,era:2.99,pos:"SP"},
                    {n:"Zack Wheeler",t:"PHI",war:4.3,era:3.05,pos:"SP"},
                    {n:"Roki Sasaki",t:"LAD",war:4.1,era:2.88,pos:"SP"},
                    {n:"Chris Sale",t:"ATL",war:3.9,era:3.15,pos:"SP"},
                  ].map((p,i)=>(
                    <div key={p.n} onClick={()=>searchPlayers(p.n).then(r=>{if(r[0])pick(r[0]);})}
                      style={{display:"flex",alignItems:"center",gap:10,padding:"7px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
                      onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
                      onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                      <span style={{fontSize:10,fontWeight:800,color:C.muted,fontFamily:F,minWidth:16}}>{i+1}</span>
                      <img src={`https://www.mlbstatic.com/team-logos/${({PIT:134,DET:116,BOS:111,SEA:136,LAD:119,PHI:143,ATL:144})[p.t]||134}.svg`} alt="" style={{width:20,height:20,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
                      <div style={{flex:1}}>
                        <div style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.n}</div>
                        <div style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.t}</div>
                      </div>
                      <div style={{textAlign:"right"}}>
                        <div style={{fontSize:13,fontWeight:800,color:p.war>=5?C.green:p.war>=4?C.blue:C.text,fontFamily:F}}>{p.war.toFixed(1)}</div>
                        <div style={{fontSize:8,color:C.muted,fontFamily:F}}>WAR</div>
                      </div>
                      <div style={{textAlign:"right",minWidth:32}}>
                        <div style={{fontSize:11,fontWeight:600,color:p.era<=2.80?C.green:p.era<=3.20?C.blue:C.dim,fontFamily:F}}>{p.era.toFixed(2)}</div>
                        <div style={{fontSize:8,color:C.muted,fontFamily:F}}>ERA</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>

            {/* Top Prospects + Player of the Day */}
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
            </div>

            {/* Engine Stats */}
            <Panel>
              <div style={{display:"flex",justifyContent:"center",gap:32,flexWrap:"wrap",padding:"8px 0"}}>
                {[
                  {v:"900+",l:"MLB Hitters"},
                  {v:"1,200+",l:"MLB Pitchers"},
                  {v:"3 Years",l:"Savant Data"},
                  {v:"All Levels",l:"ROK → MLB"},
                  {v:"7 Layers",l:"Projection Engine"},
                ].map(s=>(
                  <div key={s.l} style={{textAlign:"center"}}>
                    <div style={{fontSize:18,fontWeight:800,color:C.navy,fontFamily:F}}>{s.v}</div>
                    <div style={{fontSize:8,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".1em",marginTop:2}}>{s.l}</div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>}'''

if old_home in src:
    src = src.replace(old_home, new_home)
    changes += 1
    print("1. Redesigned landing page with top projections, prospects, and explainer")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
