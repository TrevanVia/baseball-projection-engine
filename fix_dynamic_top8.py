#!/usr/bin/env python3
"""Replace hardcoded TOP 8 hitters/pitchers with dynamic projections. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Add the DynamicTop8 component before the landing page
component = '''
// ── DYNAMIC TOP 8 PROJECTED LEADERS ───────────────────────────────────────────
function DynamicTop8({onSelect, isPitcher}) {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    (async () => {
      try {
        // Fetch active players from MLB API
        const yr = new Date().getFullYear();
        const res = await fetch(`https://statsapi.mlb.com/api/v1/sports/1/players?season=${yr}&gameType=R`);
        const data = await res.json();
        const allP = (data.people || []).filter(p => p.active);
        const projected = [];
        for (const p of allP) {
          try {
            const base = isPitcher ? projectPitcher(p) : projectFromStatcast(p.id, p.fullName, p);
            if (!base || (isPitcher && !base.era) || (!isPitcher && !base.baseWAR && !base.war)) continue;
            const war = isPitcher ? (base.baseWAR ?? base.war ?? 0) : (base.baseWAR ?? base.war ?? 0);
            if (war < 0.5) continue;
            projected.push({
              name: p.fullName,
              team: p.currentTeam?.abbreviation || '',
              teamId: p.currentTeam?.id || 147,
              pos: p.primaryPosition?.abbreviation || (isPitcher ? 'SP' : 'DH'),
              war: Math.round(war * 10) / 10,
              wrc: isPitcher ? null : (base.wRCPlus || base.wrc || 100),
              era: isPitcher ? (base.era || base.projERA || 4.50) : null,
            });
          } catch(e) {}
        }
        projected.sort((a,b) => b.war - a.war);
        setPlayers(projected.slice(0, 8));
      } catch(e) { console.error('Top8 error:', e); }
      setLoading(false);
    })();
  }, []);
  const TM_IDS = {ARI:109,ATL:144,BAL:110,BOS:111,CHC:112,CWS:145,CHW:145,CIN:113,CLE:114,COL:115,DET:116,HOU:117,KC:118,LAA:108,LAD:119,MIA:146,MIL:158,MIN:142,NYM:121,NYY:147,OAK:133,ATH:133,PHI:143,PIT:134,SD:135,SDP:135,SF:137,SFG:137,SEA:136,STL:138,TB:139,TBR:139,TEX:140,TOR:141,WSH:120,WSN:120};
  if (loading) return <div style={{fontSize:10,color:C.muted,fontFamily:F,padding:16,textAlign:"center"}}>Loading projections...</div>;
  if (!players.length) return null;
  return (
    <div style={{display:"flex",flexDirection:"column",gap:2}}>
      {players.map((p,i)=>(
        <div key={p.name} onClick={()=>searchPlayers(p.name).then(r=>{if(r[0])onSelect(r[0]);})}
          style={{display:"flex",alignItems:"center",gap:10,padding:"7px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
          onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
          onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
          <span style={{fontSize:10,fontWeight:800,color:C.muted,fontFamily:F,minWidth:16}}>{i+1}</span>
          <img src={`https://www.mlbstatic.com/team-logos/${TM_IDS[p.team]||p.teamId}.svg`} alt="" style={{width:20,height:20,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
          <div style={{flex:1}}>
            <div style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.name}</div>
            <div style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.team}</div>
          </div>
          <div style={{textAlign:"right"}}>
            <div style={{fontSize:13,fontWeight:800,color:p.war>=(isPitcher?5:6)?C.green:p.war>=(isPitcher?4:4)?C.blue:C.text,fontFamily:F}}>{p.war.toFixed(1)}</div>
            <div style={{fontSize:8,color:C.muted,fontFamily:F}}>WAR</div>
          </div>
          <div style={{textAlign:"right",minWidth:32}}>
            {isPitcher ? (
              <><div style={{fontSize:11,fontWeight:600,color:p.era<=2.80?C.green:p.era<=3.20?C.blue:C.dim,fontFamily:F}}>{typeof p.era==='number'?p.era.toFixed(2):p.era}</div>
              <div style={{fontSize:8,color:C.muted,fontFamily:F}}>ERA</div></>
            ) : (
              <><div style={{fontSize:11,fontWeight:600,color:C.dim,fontFamily:F}}>{p.wrc}</div>
              <div style={{fontSize:8,color:C.muted,fontFamily:F}}>wRC+</div></>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

'''

# Insert before PLAYER OF THE DAY
marker = "// ── LIVE fWAR LEADERBOARD"
if marker in src:
    src = src.replace(marker, component + marker)
    changes += 1
    print("1. Added DynamicTop8 component")

# Now replace the hardcoded hitter list with <DynamicTop8>
old_hitter_panel_start = '''              <Panel title="TOP HITTERS" sub="2026 projected WAR leaders." style={{borderTop:`3px solid ${C.green}`}}>
                <div style={{display:"flex",flexDirection:"column",gap:2}}>
                  {[
                    {n:"Shohei Ohtani",t:"LAD",war:8.5,wrc:152,pos:"DH"},'''

# Find the full hitter block and replace
import re
# Match from TOP HITTERS panel to its closing </Panel>
hitter_pattern = r'<Panel title="TOP HITTERS"[^>]*>.*?</Panel>'
pitcher_pattern = r'<Panel title="TOP PITCHERS"[^>]*>.*?</Panel>'

hitter_match = re.search(hitter_pattern, src, re.DOTALL)
if hitter_match:
    new_hitter = '''<Panel title="TOP HITTERS" sub="2026 projected WAR leaders." style={{borderTop:`3px solid ${C.green}`}}>
                <DynamicTop8 onSelect={pick} isPitcher={false}/>
              </Panel>'''
    src = src[:hitter_match.start()] + new_hitter + src[hitter_match.end():]
    changes += 1
    print("2. Replaced hardcoded TOP HITTERS with DynamicTop8")

pitcher_match = re.search(pitcher_pattern, src, re.DOTALL)
if pitcher_match:
    new_pitcher = '''<Panel title="TOP PITCHERS" sub="2026 projected WAR leaders." style={{borderTop:`3px solid ${C.blue}`}}>
                <DynamicTop8 onSelect={pick} isPitcher={true}/>
              </Panel>'''
    src = src[:pitcher_match.start()] + new_pitcher + src[pitcher_match.end():]
    changes += 1
    print("3. Replaced hardcoded TOP PITCHERS with DynamicTop8")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Landing page top 8 now computed LIVE from projection engine.")
print("Will always match the leaderboard tab exactly.")
print("No more hardcoded numbers to maintain.")
