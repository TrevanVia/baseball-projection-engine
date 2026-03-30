#!/usr/bin/env python3
"""Add live fWAR leaderboard to landing page. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Add the LiveWARLeaderboard component before the PLAYER OF THE DAY section
component = '''
// ── LIVE fWAR LEADERBOARD ─────────────────────────────────────────────────────
function LiveWARBoard({onSelect}) {
  const [hitters, setHitters] = useState([]);
  const [pitchers, setPitchers] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const yr = new Date().getFullYear();
    Promise.all([
      fetch(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=bat&lg=all&qual=0&season=${yr}&month=0&hand=&team=0&pageItems=5&sortCol=WAR&sortDir=desc`).then(r=>r.json()),
      fetch(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=pit&lg=all&qual=0&season=${yr}&month=0&hand=&team=0&pageItems=5&sortCol=WAR&sortDir=desc`).then(r=>r.json()),
    ]).then(([batData, pitData]) => {
      const parseTm = t => (t||'').replace(/<[^>]+>/g,'').trim();
      setHitters((batData.data||[]).slice(0,5).map(p=>({name:p.PlayerName,tm:parseTm(p.Team),war:p.WAR?.toFixed(1),hr:Math.round(p.HR||0),avg:(p.AVG||0).toFixed(3),ops:(p.OPS||0).toFixed(3)})));
      setPitchers((pitData.data||[]).slice(0,5).map(p=>({name:p.PlayerName,tm:parseTm(p.Team),war:p.WAR?.toFixed(1),era:(p.ERA||0).toFixed(2),k:Math.round(p.SO||0),ip:(p.IP||0).toFixed(1)})));
      setLoading(false);
    }).catch(()=>setLoading(false));
  }, []);
  const searchAndPick = (name) => { searchPlayers(name).then(r=>{if(r&&r[0])onSelect(r[0]);}); };
  if (loading) return null;
  if (!hitters.length && !pitchers.length) return null;
  return (
    <div className="via-landing-2col" style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Panel title="LIVE fWAR LEADERS" sub="2026 season — hitters." style={{borderTop:`3px solid ${C.green}`}}>
        <div style={{display:"flex",flexDirection:"column",gap:0}}>
          <div style={{display:"grid",gridTemplateColumns:"24px 1fr 50px 40px 50px 44px",gap:4,padding:"4px 6px",borderBottom:`1px solid ${C.border}33`}}>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>#</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Player</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>AVG</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>HR</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>OPS</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>fWAR</span>
          </div>
          {hitters.map((p,i)=>(
            <div key={p.name} onClick={()=>searchAndPick(p.name)}
              style={{display:"grid",gridTemplateColumns:"24px 1fr 50px 40px 50px 44px",gap:4,padding:"6px 6px",borderBottom:i<4?`1px solid ${C.border}15`:"none",cursor:"pointer",transition:"background 0.1s"}}
              onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
              onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:11,color:C.muted,fontFamily:F,fontWeight:600}}>{i+1}</span>
              <div>
                <span style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.name}</span>
                <span style={{fontSize:9,color:C.muted,fontFamily:F,marginLeft:5}}>{p.tm}</span>
              </div>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.avg}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.hr}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right",fontWeight:600}}>{p.ops}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.green,textAlign:"right",fontWeight:800}}>{p.war}</span>
            </div>
          ))}
        </div>
        <div style={{fontSize:8,color:C.muted,fontFamily:F,marginTop:6,textAlign:"right"}}>via FanGraphs</div>
      </Panel>
      <Panel title="LIVE fWAR LEADERS" sub="2026 season — pitchers." style={{borderTop:`3px solid ${C.green}`}}>
        <div style={{display:"flex",flexDirection:"column",gap:0}}>
          <div style={{display:"grid",gridTemplateColumns:"24px 1fr 50px 34px 44px 44px",gap:4,padding:"4px 6px",borderBottom:`1px solid ${C.border}33`}}>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>#</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Player</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>ERA</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>K</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>IP</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>fWAR</span>
          </div>
          {pitchers.map((p,i)=>(
            <div key={p.name} onClick={()=>searchAndPick(p.name)}
              style={{display:"grid",gridTemplateColumns:"24px 1fr 50px 34px 44px 44px",gap:4,padding:"6px 6px",borderBottom:i<4?`1px solid ${C.border}15`:"none",cursor:"pointer",transition:"background 0.1s"}}
              onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
              onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:11,color:C.muted,fontFamily:F,fontWeight:600}}>{i+1}</span>
              <div>
                <span style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.name}</span>
                <span style={{fontSize:9,color:C.muted,fontFamily:F,marginLeft:5}}>{p.tm}</span>
              </div>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.era}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.k}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.ip}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.green,textAlign:"right",fontWeight:800}}>{p.war}</span>
            </div>
          ))}
        </div>
        <div style={{fontSize:8,color:C.muted,fontFamily:F,marginTop:6,textAlign:"right"}}>via FanGraphs</div>
      </Panel>
    </div>
  );
}

'''

# Insert component before PLAYER OF THE DAY section
marker = "// ── PLAYER OF THE DAY"
if marker in src:
    src = src.replace(marker, component + marker)
    changes += 1
    print("1. Added LiveWARBoard component")

# 2. Insert the component on the landing page between projection boards and prospects
old_insert = """            {/* Top Prospects + What Is VIAcast */}"""
new_insert = """            {/* Live fWAR Leaderboard */}
            <LiveWARBoard onSelect={pick}/>

            {/* Top Prospects + What Is VIAcast */}"""

if old_insert in src:
    src = src.replace(old_insert, new_insert)
    changes += 1
    print("2. Added LiveWARBoard to landing page layout")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
