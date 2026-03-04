#!/usr/bin/env python3
"""Redesign Rosters: alphabetical list with team logos. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Replace the team selector panel
old_selector = '''      <Panel title="SELECT MLB ORGANIZATION">
        <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
          {teams.map(t=><button key={t.id} onClick={()=>pickTeam(t)} style={{
            padding:"4px 10px",fontSize:10,fontWeight:600,fontFamily:F,borderRadius:4,cursor:"pointer",border:"none",
            background:selTeam?.id===t.id?C.accent:"#efe9dd",color:selTeam?.id===t.id?"#000":C.muted,
          }}>{t.abbreviation}</button>)}
        </div>
      </Panel>'''

new_selector = '''      <Panel title="SELECT MLB ORGANIZATION" sub="All 30 teams listed alphabetically.">
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))",gap:6}}>
          {[...teams].sort((a,b)=>a.name.localeCompare(b.name)).map(t=><button key={t.id} onClick={()=>pickTeam(t)} style={{
            display:"flex",alignItems:"center",gap:10,padding:"8px 12px",fontSize:12,fontWeight:selTeam?.id===t.id?700:500,
            fontFamily:F,borderRadius:8,cursor:"pointer",
            border:selTeam?.id===t.id?`2px solid ${C.accent}`:`1px solid ${C.border}`,
            background:selTeam?.id===t.id?`${C.accent}08`:"transparent",color:selTeam?.id===t.id?C.text:C.dim,
            transition:"all 0.15s ease",textAlign:"left",
          }}
          onMouseEnter={e=>{if(selTeam?.id!==t.id){e.currentTarget.style.borderColor=C.accent;e.currentTarget.style.background=`${C.accent}05`;}}}
          onMouseLeave={e=>{if(selTeam?.id!==t.id){e.currentTarget.style.borderColor=C.border;e.currentTarget.style.background="transparent";}}}
          >
            <img src={`https://www.mlbstatic.com/team-logos/${t.id}.svg`} alt="" style={{width:28,height:28,objectFit:"contain",flexShrink:0}} onError={e=>{e.target.style.display="none"}}/>
            <div>
              <div style={{fontSize:12,fontWeight:700,lineHeight:1.2}}>{t.name}</div>
              <div style={{fontSize:9,color:C.muted,letterSpacing:".06em"}}>{t.abbreviation}</div>
            </div>
          </button>)}
        </div>
      </Panel>'''

if old_selector in src:
    src = src.replace(old_selector, new_selector)
    changes += 1
    print("1. Redesigned team selector: alphabetical grid with logos")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
