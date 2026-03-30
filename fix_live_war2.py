#!/usr/bin/env python3
"""Update live fWAR leaderboard: top 8, team logos, reordered columns. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Find and replace the entire LiveWARBoard component
old_start = "// ── LIVE fWAR LEADERBOARD"
old_end = "// ── PLAYER OF THE DAY"

idx_start = src.find(old_start)
idx_end = src.find(old_end)

if idx_start >= 0 and idx_end > idx_start:
    new_component = '''// ── LIVE fWAR LEADERBOARD ─────────────────────────────────────────────────────
const FG_TEAM_IDS = {ARI:109,ATL:144,BAL:110,BOS:111,CHC:112,CHW:145,CIN:113,CLE:114,COL:115,DET:116,HOU:117,KC:118,LAA:108,LAD:119,MIA:146,MIL:158,MIN:142,NYM:121,NYY:147,ATH:133,PHI:143,PIT:134,SD:135,SF:137,SEA:136,STL:138,TB:139,TEX:140,TOR:141,WSN:120};
function LiveWARBoard({onSelect}) {
  const [hitters, setHitters] = useState([]);
  const [pitchers, setPitchers] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const yr = new Date().getFullYear();
    Promise.all([
      fetch(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=bat&lg=all&qual=0&season=${yr}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`).then(r=>r.json()),
      fetch(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=pit&lg=all&qual=0&season=${yr}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`).then(r=>r.json()),
    ]).then(([batData, pitData]) => {
      const parseTm = t => (t||'').replace(/<[^>]+>/g,'').trim();
      setHitters((batData.data||[]).slice(0,8).map(p=>({name:p.PlayerName,tm:parseTm(p.Team),war:p.WAR?.toFixed(1),hr:Math.round(p.HR||0),wrc:Math.round(p['wRC+']||0)})));
      setPitchers((pitData.data||[]).slice(0,8).map(p=>({name:p.PlayerName,tm:parseTm(p.Team),war:p.WAR?.toFixed(1),era:(p.ERA||0).toFixed(2),k9:(p['K/9']||0).toFixed(1),ip:(p.IP||0).toFixed(1)})));
      setLoading(false);
    }).catch(()=>setLoading(false));
  }, []);
  const searchAndPick = (name) => { searchPlayers(name).then(r=>{if(r&&r[0])onSelect(r[0]);}); };
  if (loading) return null;
  if (!hitters.length && !pitchers.length) return null;
  const tmLogo = (tm) => `https://www.mlbstatic.com/team-logos/${FG_TEAM_IDS[tm]||147}.svg`;
  return (
    <div className="via-landing-2col" style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Panel title="LIVE fWAR LEADERS" sub="2026 season \\u2014 hitters." style={{borderTop:`3px solid ${C.green}`}}>
        <div style={{display:"flex",flexDirection:"column",gap:0}}>
          <div style={{display:"grid",gridTemplateColumns:"20px 22px 1fr 44px 36px 44px",gap:4,padding:"4px 6px",borderBottom:`1px solid ${C.border}33`}}>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>#</span>
            <span></span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Player</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>fWAR</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>HR</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>wRC+</span>
          </div>
          {hitters.map((p,i)=>(
            <div key={p.name+i} onClick={()=>searchAndPick(p.name)}
              style={{display:"grid",gridTemplateColumns:"20px 22px 1fr 44px 36px 44px",gap:4,padding:"5px 6px",borderBottom:i<7?`1px solid ${C.border}15`:"none",cursor:"pointer",transition:"background 0.1s"}}
              onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
              onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:11,color:C.muted,fontFamily:F,fontWeight:600}}>{i+1}</span>
              <img src={tmLogo(p.tm)} alt="" style={{width:18,height:18,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
              <div style={{overflow:"hidden",whiteSpace:"nowrap"}}>
                <span style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.name}</span>
                <span style={{fontSize:9,color:C.muted,fontFamily:F,marginLeft:4}}>{p.tm}</span>
              </div>
              <span style={{fontSize:11,fontFamily:F,color:C.green,textAlign:"right",fontWeight:800}}>{p.war}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.hr}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right",fontWeight:600}}>{p.wrc}</span>
            </div>
          ))}
        </div>
        <div style={{fontSize:8,color:C.muted,fontFamily:F,marginTop:6,textAlign:"right"}}>via FanGraphs</div>
      </Panel>
      <Panel title="LIVE fWAR LEADERS" sub="2026 season \\u2014 pitchers." style={{borderTop:`3px solid ${C.green}`}}>
        <div style={{display:"flex",flexDirection:"column",gap:0}}>
          <div style={{display:"grid",gridTemplateColumns:"20px 22px 1fr 44px 40px 40px 44px",gap:4,padding:"4px 6px",borderBottom:`1px solid ${C.border}33`}}>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>#</span>
            <span></span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Player</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>fWAR</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>IP</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>K/9</span>
            <span style={{fontSize:8,color:C.muted,fontFamily:F,textAlign:"right"}}>ERA</span>
          </div>
          {pitchers.map((p,i)=>(
            <div key={p.name+i} onClick={()=>searchAndPick(p.name)}
              style={{display:"grid",gridTemplateColumns:"20px 22px 1fr 44px 40px 40px 44px",gap:4,padding:"5px 6px",borderBottom:i<7?`1px solid ${C.border}15`:"none",cursor:"pointer",transition:"background 0.1s"}}
              onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
              onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:11,color:C.muted,fontFamily:F,fontWeight:600}}>{i+1}</span>
              <img src={tmLogo(p.tm)} alt="" style={{width:18,height:18,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
              <div style={{overflow:"hidden",whiteSpace:"nowrap"}}>
                <span style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.name}</span>
                <span style={{fontSize:9,color:C.muted,fontFamily:F,marginLeft:4}}>{p.tm}</span>
              </div>
              <span style={{fontSize:11,fontFamily:F,color:C.green,textAlign:"right",fontWeight:800}}>{p.war}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.ip}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right"}}>{p.k9}</span>
              <span style={{fontSize:11,fontFamily:F,color:C.text,textAlign:"right",fontWeight:600}}>{p.era}</span>
            </div>
          ))}
        </div>
        <div style={{fontSize:8,color:C.muted,fontFamily:F,marginTop:6,textAlign:"right"}}>via FanGraphs</div>
      </Panel>
    </div>
  );
}

'''
    src = src[:idx_start] + new_component + src[idx_end:]
    changes += 1
    print("1. Replaced LiveWARBoard: top 8, team logos, reordered columns")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Hitters: # | Logo | Name/Team | fWAR | HR | wRC+")
print("Pitchers: # | Logo | Name/Team | fWAR | IP | K/9 | ERA")
print("Top 8 on each side, team logos from mlbstatic.com")
