#!/usr/bin/env python3
"""Update hardcoded TOP 8 hitters/pitchers with current engine numbers. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0
import re

# Replace the broken DynamicTop8 hitter panel with correct hardcoded data
hitter_pattern = r'<Panel title="TOP HITTERS"[^>]*>.*?</Panel>'
hitter_match = re.search(hitter_pattern, src, re.DOTALL)
if hitter_match:
    new_hitter = '''<Panel title="TOP HITTERS" sub="2026 projected WAR leaders." style={{borderTop:`3px solid ${C.green}`}}>
                <div style={{display:"flex",flexDirection:"column",gap:2}}>
                  {[
                    {n:"Shohei Ohtani",t:"LAD",id:119,war:8.8,wrc:167,pos:"TWP"},
                    {n:"Bobby Witt Jr.",t:"KC",id:118,war:7.1,wrc:143,pos:"SS"},
                    {n:"Elly De La Cruz",t:"CIN",id:113,war:5.1,wrc:114,pos:"SS"},
                    {n:"Gunnar Henderson",t:"BAL",id:110,war:4.9,wrc:133,pos:"SS"},
                    {n:"Juan Soto",t:"NYM",id:121,war:4.9,wrc:179,pos:"RF"},
                    {n:"Francisco Lindor",t:"NYM",id:121,war:4.8,wrc:117,pos:"SS"},
                    {n:"Aaron Judge",t:"NYY",id:147,war:4.8,wrc:189,pos:"RF"},
                    {n:"Geraldo Perdomo",t:"AZ",id:109,war:4.7,wrc:115,pos:"SS"},
                  ].map((p,i)=>(
                    <div key={p.n} onClick={()=>searchPlayers(p.n).then(r=>{if(r[0])pick(r[0]);})}
                      style={{display:"flex",alignItems:"center",gap:10,padding:"7px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
                      onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
                      onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                      <span style={{fontSize:10,fontWeight:800,color:C.muted,fontFamily:F,minWidth:16}}>{i+1}</span>
                      <img src={`https://www.mlbstatic.com/team-logos/${p.id}.svg`} alt="" style={{width:20,height:20,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
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
              </Panel>'''
    src = src[:hitter_match.start()] + new_hitter + src[hitter_match.end():]
    changes += 1
    print("1. Updated TOP HITTERS with current engine numbers")

pitcher_pattern = r'<Panel title="TOP PITCHERS"[^>]*>.*?</Panel>'
pitcher_match = re.search(pitcher_pattern, src, re.DOTALL)
if pitcher_match:
    new_pitcher = '''<Panel title="TOP PITCHERS" sub="2026 projected WAR leaders." style={{borderTop:`3px solid ${C.blue}`}}>
                <div style={{display:"flex",flexDirection:"column",gap:2}}>
                  {[
                    {n:"Garrett Crochet",t:"BOS",id:111,war:6.5,era:2.70,pos:"SP"},
                    {n:"Paul Skenes",t:"PIT",id:134,war:5.8,era:2.77,pos:"SP"},
                    {n:"Tarik Skubal",t:"DET",id:116,war:5.7,era:2.86,pos:"SP"},
                    {n:"Logan Gilbert",t:"SEA",id:136,war:5.4,era:3.14,pos:"SP"},
                    {n:"Cole Ragans",t:"KC",id:118,war:4.5,era:3.27,pos:"SP"},
                    {n:"Logan Webb",t:"SF",id:137,war:4.5,era:3.51,pos:"SP"},
                    {n:"Cristopher Sanchez",t:"PHI",id:143,war:4.5,era:3.42,pos:"SP"},
                    {n:"Kyle Bradish",t:"BAL",id:110,war:4.3,era:3.17,pos:"SP"},
                  ].map((p,i)=>(
                    <div key={p.n} onClick={()=>searchPlayers(p.n).then(r=>{if(r[0])pick(r[0]);})}
                      style={{display:"flex",alignItems:"center",gap:10,padding:"7px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
                      onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
                      onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                      <span style={{fontSize:10,fontWeight:800,color:C.muted,fontFamily:F,minWidth:16}}>{i+1}</span>
                      <img src={`https://www.mlbstatic.com/team-logos/${p.id}.svg`} alt="" style={{width:20,height:20,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
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
              </Panel>'''
    src = src[:pitcher_match.start()] + new_pitcher + src[pitcher_match.end():]
    changes += 1
    print("2. Updated TOP PITCHERS with current engine numbers")

# Remove the broken DynamicTop8 component
dyn_start = src.find("// ── DYNAMIC TOP 8 PROJECTED LEADERS")
dyn_end = src.find("// ── LIVE fWAR LEADERBOARD")
if dyn_start >= 0 and dyn_end > dyn_start:
    src = src[:dyn_start] + src[dyn_end:]
    changes += 1
    print("3. Removed broken DynamicTop8 component")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
