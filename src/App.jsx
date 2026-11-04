import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell, ComposedChart
} from "recharts";
import _ from "lodash";
import { ScorecardPanel, ProspectsPanel } from "./ScorecardProspects.jsx";
import prospectsData from "./prospects.json";

import {
  gradePitch, getLatestArsenal, PRECOMPUTED, LIVE_LB, TEAM_ID_BY_ABBREV, PITCHER_PCTL,
  pctlLookup, getCareerWAR, API, LEVEL_NAMES, LEVEL_ORDER, LEVEL_TRANSLATION,
  getPlayerFV, getFVStyle, getVpdGradeGlobal, getStatcast, searchPlayers, getPlayerStats,
  getPlayerCareer, getTeams, getTeamRoster, getMiLBAffiliate, AGING_PARAMS, getAP,
  posLabel, detectLevel, projectPlayer, projectPitcher, projectPitcherForward, projectForward,
  projectOPSTrajectory,
  PROJ_SEASON, projAge,
} from "./engine.js";
import { inject } from "@vercel/analytics";
inject();

const VPD_BG={"A+":"linear-gradient(135deg,#10b981,#059669)","A":"linear-gradient(135deg,#22c55e,#16a34a)","A-":"linear-gradient(135deg,#84cc16,#65a30d)","B+":"linear-gradient(135deg,#eab308,#ca8a04)","B":"linear-gradient(135deg,#f59e0b,#d97706)","B-":"linear-gradient(135deg,#fb923c,#ea580c)","C+":"linear-gradient(135deg,#fbbf24,#d97706)","C":"linear-gradient(135deg,#94a3b8,#64748b)","D":"linear-gradient(135deg,#ef4444,#dc2626)","F":"linear-gradient(135deg,#dc2626,#991b1b)"};
const VpDBadge = ({war, salary}) => {
  if (!war || !salary || salary <= 0) return null;
  const g = getVpdGradeGlobal(war / (salary / 1000000));
  return (<span style={{fontSize:10,fontWeight:800,padding:"3px 10px",borderRadius:5,fontFamily:F,background:VPD_BG[g.grade]||VPD_BG["C"],color:g.grade==="C+"?"#78350f":"#fff",display:"inline-block",letterSpacing:".04em"}}>{g.grade} VpD</span>);
};
let _contractCache = null;
async function getContractData() {
  if (_contractCache) return _contractCache;
  try { const m = await import("./contract_data.json"); _contractCache = m.default||m; return _contractCache; } catch { return {}; }
}
function getPlayerSalary(name) { return _contractCache ? (_contractCache[name]||null) : null; }

const LIGHT = {
  bg:"#f5f0e6", panel:"#ffffff", border:"#d4c9b5", hover:"#efe9dd",
  accent:"#c8102e", blue:"#1a3668", green:"#2d6a4f", red:"#c8102e",
  yellow:"#d4a017", purple:"#5b2c8e", cyan:"#0077b6", pink:"#c44569",
  orange:"#e17726",
  text:"#1b1b1b", dim:"#4a4540", muted:"#8c8272", grid:"#ddd5c5",
  navy:"#1a3668", leather:"#8b5e3c",
};
const DARK = {
  bg:"#0d1117", panel:"#161b22", border:"#30363d", hover:"#1c2128",
  accent:"#e5534b", blue:"#58a6ff", green:"#3fb950", red:"#e5534b",
  yellow:"#d29922", purple:"#bc8cff", cyan:"#39d2c0", pink:"#f778ba",
  orange:"#e3b341",
  text:"#e6edf3", dim:"#b1bac4", muted:"#7d8590", grid:"#21262d",
  navy:"#58a6ff", leather:"#c69963",
};
// Theme state — initialized from localStorage, defaults to light
let _theme = "light";
try { _theme = localStorage.getItem("via-theme") || "light"; } catch {}
let C = _theme === "dark" ? { ...DARK } : { ...LIGHT };
const F = "'IBM Plex Mono', monospace";
const LEVEL_COLORS = { ROK:"#9ca3af", A:"#0077b6", "A+":"#1a3668", AA:"#5b2c8e", AAA:"#d4a017", MLB:"#2d6a4f", PROJ:"#c8102e" };

// ── COMPONENTS ───────────────────────────────────────────────────────────────
const Panel = ({children,title,sub,style={},onClick,onMouseEnter,onMouseLeave}) => (
  <div className="via-panel" onClick={onClick} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:12,padding:"18px 22px",boxShadow:"0 1px 3px rgba(26,54,104,0.04)",...style}}>
    {title&&<div style={{marginBottom:sub?0:14}}>
      <h3 style={{margin:0,fontSize:12,fontWeight:700,color:C.text,letterSpacing:".08em",fontFamily:F,textTransform:"uppercase"}}>{title}</h3>
      {sub&&<p style={{margin:"4px 0 12px",fontSize:11,color:C.muted,lineHeight:1.5,fontFamily:F}}>{sub}</p>}
    </div>}
    {children}
  </div>
);
const Stat = ({label,value,color=C.accent,sub}) => (
  <div className="via-stat" style={{padding:"10px 14px",background:`${color}06`,borderRadius:10,border:`1px solid ${color}15`,minWidth:72,textAlign:"center",cursor:"default"}}>
    <div style={{fontSize:22,fontWeight:800,color,fontFamily:F,lineHeight:1.1}}>{value}</div>
    <div style={{fontSize:7.5,color:C.muted,marginTop:3,textTransform:"uppercase",letterSpacing:".1em",fontFamily:F,fontWeight:600}}>{label}</div>
    {sub&&<div style={{fontSize:7.5,color:C.dim,fontFamily:F,marginTop:1}}>{sub}</div>}
  </div>
);
const Pill = ({label,active,onClick,color=C.accent}) => (
  <button className="via-pill" onClick={onClick} style={{padding:"6px 16px",border:"none",borderRadius:8,cursor:"pointer",fontSize:11,fontWeight:active?700:500,fontFamily:F,background:active?color:C.hover,color:active?"#fff":C.muted,letterSpacing:".02em"}}>{label}</button>
);
const LevelBadge = ({level}) => (
  <span className="via-badge" style={{fontSize:9,fontWeight:700,padding:"3px 8px",borderRadius:5,fontFamily:F,background:`${LEVEL_COLORS[level]||C.muted}15`,color:LEVEL_COLORS[level]||C.muted,letterSpacing:".04em"}}>{level}</span>
);

const FVBadge = ({fv}) => {
  if (!fv) return null;
  const s = getFVStyle(fv);
  return (
    <span style={{
      fontSize:10, fontWeight:800, padding:"4px 11px", borderRadius:6, fontFamily:F,
      background: s.bg, color: s.color, display:"inline-block", letterSpacing:".04em",
      boxShadow: s.glow ? "0 0 12px rgba(192,132,252,.4), 0 0 24px rgba(96,165,250,.2)" : "none",
      animation: s.glow ? "fvGlow 2s ease-in-out infinite alternate" : "none",
    }}>{s.label}</span>
  );
};

const Spinner = ({msg="Loading..."}) => (
  <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:10,padding:32,color:C.dim,fontFamily:F,fontSize:12,animation:"fadeIn 0.3s ease"}}>
    <div style={{width:18,height:18,border:`2px solid ${C.border}`,borderTopColor:C.accent,borderRadius:"50%",animation:"spin .7s linear infinite"}}/>
    {msg}
    <style>{`@keyframes spin{to{transform:rotate(360deg)}} @keyframes fvGlow{from{box-shadow:0 0 8px rgba(192,132,252,.3),0 0 16px rgba(96,165,250,.15)}to{box-shadow:0 0 16px rgba(251,146,60,.4),0 0 28px rgba(192,132,252,.25)}}`}</style>
  </div>
);
const Tip = ({active,payload,label}) => {
  if(!active||!payload?.length) return null;
  return <div style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:8,padding:"8px 12px",boxShadow:"0 8px 24px rgba(0,0,0,.12)"}}>
    <div style={{fontSize:10,color:C.dim,marginBottom:4,fontFamily:F}}>{label}</div>
    {payload.filter(p=>p.value!=null).map((p,i)=><div key={i} style={{fontSize:11,color:p.color||C.text,fontFamily:F,margin:"1px 0"}}>{p.name}: <strong>{typeof p.value==="number"&&p.value<5?p.value.toFixed(3):p.value}</strong></div>)}
  </div>;
};

// ── PLAYER SEARCH ────────────────────────────────────────────────────────────
function PlayerSearch({onSelect}) {
  const [q,setQ]=useState(""); const [results,setResults]=useState([]); const [show,setShow]=useState(false);
  const ref=useRef(); const search=useMemo(()=>_.debounce(async v=>{if(v.length<2){setResults([]);return;}const r=await searchPlayers(v);setResults(r);setShow(true);},300),[]);
  useEffect(()=>{const h=e=>{if(ref.current&&!ref.current.contains(e.target))setShow(false);};document.addEventListener("mousedown",h);return()=>document.removeEventListener("mousedown",h);},[]);
  return (
    <div ref={ref} style={{position:"relative",width:260}}>
      <input value={q} onChange={e=>{setQ(e.target.value);search(e.target.value);}} placeholder="Search player..."
        className="via-search-input" style={{width:"100%",padding:"10px 14px",borderRadius:10,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:12,fontFamily:F,outline:"none"}}
        onFocus={()=>results.length&&setShow(true)}/>
      {show&&results.length>0&&<div className="via-search-dropdown" style={{position:"absolute",top:"100%",left:0,right:0,background:C.panel,border:`1px solid ${C.border}`,borderRadius:12,marginTop:6,maxHeight:320,overflowY:"auto",zIndex:999,boxShadow:"0 16px 48px rgba(26,54,104,.12)"}}>
        {results.map(p=>{
          const fv = getPlayerFV(p.id, p.fullName);
          return <div key={p.id} onClick={()=>{onSelect(p);setShow(false);setQ(p.fullName);}}
            style={{padding:"8px 12px",cursor:"pointer",borderBottom:`1px solid ${C.border}30`,display:"flex",alignItems:"center",justifyContent:"space-between"}}
            onMouseEnter={e=>e.currentTarget.style.background=C.hover} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
            <div>
              <div style={{fontSize:12,fontWeight:600,color:C.text,fontFamily:F}}>{p.fullName}</div>
              <div style={{fontSize:10,color:C.muted,fontFamily:F}}>
                {posLabel(p.primaryPosition?.code)} &middot; {p.currentTeam?.name||"Free Agent"}
                {p.currentTeam?.sport?.id&&p.currentTeam.sport.id!==1&&<> &middot; <LevelBadge level={LEVEL_NAMES[p.currentTeam.sport.id]||"MiLB"}/></>}
              </div>
            </div>
            {fv && <FVBadge fv={fv}/>}
          </div>;
        })}
      </div>}
    </div>
  );
}

// ── PLAYER CARD ──────────────────────────────────────────────────────────────
function PlayerCard({player}) {
  const [career,setCareer]=useState([]); const [pitchCareer,setPitchCareer]=useState([]); const [loading,setLoading]=useState(true); const [projTab,setProjTab]=useState("war");
  useEffect(()=>{
    setLoading(true);
    setCareer([]);
    setPitchCareer([]);
    const isPitch = player.primaryPosition?.code === "1";
    const isTwoWay = player.primaryPosition?.code === "Y";
    if (isTwoWay) {
      // Two-way player: fetch BOTH hitting and pitching careers
      Promise.all([
        getPlayerCareer(player.id, "hitting").catch(() => []),
        getPlayerCareer(player.id, "pitching").catch(() => []),
      ]).then(([h, p]) => { setCareer(h); setPitchCareer(p); setLoading(false); });
    } else if (isPitch) {
      getPlayerCareer(player.id, "pitching").then(s=>{setPitchCareer(s);setLoading(false);}).catch(()=>setLoading(false));
    } else {
      getPlayerCareer(player.id, "hitting").then(s=>{setCareer(s);setLoading(false);}).catch(()=>setLoading(false));
    }
  },[player.id]);

  const fv = getPlayerFV(player.id, player.fullName);
  const sc = getStatcast(player.fullName);
  const [salary, setSalary] = useState(null);
  useEffect(() => { getContractData().then(() => setSalary(getPlayerSalary(player.fullName))); }, [player.fullName]);

  const seasons = useMemo(()=>{const CUR_YR=new Date().getFullYear();return career.filter(s=>s.stat?.plateAppearances>0).map(s=>{
    const lvl = detectLevel(s);
    return {
      season:s.season, age:player.currentAge-(CUR_YR-parseInt(s.season)),
      avg:parseFloat(s.stat.avg||0), obp:parseFloat(s.stat.obp||0), slg:parseFloat(s.stat.slg||0), ops:parseFloat(s.stat.ops||0),
      hr:s.stat.homeRuns||0, pa:s.stat.plateAppearances||0, r:s.stat.runs||0, rbi:s.stat.rbi||0,
      bb:s.stat.baseOnBalls||0, so:s.stat.strikeOuts||0, sb:s.stat.stolenBases||0,
      team:s.team?.abbreviation||"", level:lvl,
    };
  }).sort((a,b)=>{const sy=parseInt(a.season)-parseInt(b.season);if(sy!==0)return sy;return LEVEL_ORDER.indexOf(a.level)-LEVEL_ORDER.indexOf(b.level);});},[career,player]);

  
  const pitchSeasons = useMemo(()=>{const CUR_YR=new Date().getFullYear();return pitchCareer.filter(s=>parseFloat(s.stat?.inningsPitched||0)>0).map(s=>{
    const lvl = detectLevel(s);
    const st = s.stat;
    return {
      season:s.season, age:player.currentAge-(CUR_YR-parseInt(s.season)),
      era:parseFloat(st.era||0), ip:parseFloat(st.inningsPitched||0),
      k9:parseFloat(st.strikeoutsPer9Inn||0), bb9:parseFloat(st.walksPer9Inn||0),
      whip:parseFloat(st.whip||0), fip:parseFloat(st.era||0),
      w:parseInt(st.wins||0), l:parseInt(st.losses||0), sv:parseInt(st.saves||0),
      so:parseInt(st.strikeOuts||0), bb:parseInt(st.baseOnBalls||0),
      hr:parseInt(st.homeRuns||0), gs:parseInt(st.gamesStarted||0), g:parseInt(st.gamesPlayed||0),
      team:s.team?.abbreviation||"", level:lvl,
    };
  }).sort((a,b)=>{const sy=parseInt(a.season)-parseInt(b.season);if(sy!==0)return sy;return LEVEL_ORDER.indexOf(a.level)-LEVEL_ORDER.indexOf(b.level);});},[pitchCareer,player]);

  const isPitcher = player.primaryPosition?.code === "1";
  const isTwoWay = player.primaryPosition?.code === "Y";
  useEffect(()=>{if(isPitcher)setProjTab("war");},[isPitcher]);
  const base = useMemo(() => {
    if (isPitcher) {
      return pitchCareer.length ? projectPitcher(pitchCareer, projAge(player), player.fullName, player.id) : null;
    }
    // Hitter projection — uses same router as leaderboard & compare
    let hitProj = career.length
      ? projectPlayer(career.filter(s => s.stat?.plateAppearances > 0), projAge(player), player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id)
      : null;
    if (!hitProj) return null;

    // Two-way: add pitching WAR with workload discount
    // A two-way player can't play full-time hitting AND pitch full-time.
    // Ohtani 2023 (best two-way season): 599 PA + 132 IP = ~92% hitting, ~73% pitching.
    // Discount both sides to reflect realistic two-way workload.
    if (isTwoWay) {
      let pitchWAR = 0;
      const pProj = projectPitcher(pitchCareer, projAge(player), player.fullName, player.id);
      if (pProj) {
        pitchWAR = pProj.baseWAR * 0.72;  // ~130 IP vs 180 IP full-season
        hitProj._pitchProj = pProj;
      }
      if (pitchWAR > 0) {
        const hitDiscount = 0.92;  // ~600 PA vs 650 full-season DH
        hitProj._hitWAR = Math.round(hitProj.baseWAR * hitDiscount * 10) / 10;
        hitProj._pitchWAR = Math.round(pitchWAR * 10) / 10;
        hitProj.baseWAR = Math.round((hitProj._hitWAR + hitProj._pitchWAR) * 10) / 10;
        hitProj._isTwoWay = true;
      }
    }
    return hitProj;
  }, [career, pitchCareer, player, isPitcher, isTwoWay]);
  const forward = useMemo(() => {
    if (!base) return [];
    if (isPitcher) return projectPitcherForward(base, projAge(player));
    const hitFwd = projectForward(base, projAge(player), player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code);
    // Two-way: add pitching trajectory to each year
    if (base._isTwoWay && base._pitchProj) {
      const pitchFwd = projectPitcherForward(base._pitchProj, projAge(player));
      return hitFwd.map((h, i) => ({
        ...h,
        war: Math.round((h.war + (pitchFwd[i]?.war || 0)) * 10) / 10,
        _hitWar: h.war,
        _pitchWar: pitchFwd[i]?.war || 0,
      }));
    }
    return hitFwd;
  }, [base, player, isPitcher]);
  const peak = forward.length?{age:getAP(player.primaryPosition?.code).peak}:null;
  const cWAR = getCareerWAR(player.id, player.fullName);
  const cum = forward.reduce((s,d)=>s+Math.max(0,d.war),0);
  const isMiLB = seasons.length>0 && !seasons.some(s=>s.level==="MLB");

  const opsTrajectory = useMemo(()=>
    projectOPSTrajectory(seasons, base, projAge(player), player.primaryPosition?.code, player.fullName)
  ,[seasons, base, player]);

  if(loading) return <Spinner msg="Pulling career stats from MLB Stats API..."/>;

  return (
    <div style={{display:"flex",flexDirection:"column",gap:16}}>
      {/* Header */}
      <Panel style={{background:`linear-gradient(180deg, ${C.panel} 0%, ${C.bg} 100%)`,borderTop:`3px solid ${C.accent}`}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:12}}>
          <div>
            <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
              <h2 style={{margin:0,fontSize:24,fontWeight:800,color:C.text,fontFamily:F,letterSpacing:"-0.01em"}}>{player.fullName}</h2>
              {fv && <FVBadge fv={fv}/>}
              {!fv && isMiLB && <LevelBadge level={base?.highestLevel||"MiLB"}/>}
              {salary && base?.baseWAR && <VpDBadge war={base.baseWAR} salary={salary}/>}
            </div>
            <p style={{margin:"3px 0 0",fontSize:12,color:C.dim,fontFamily:F}}>
              {posLabel(player.primaryPosition?.code)} &middot; {player.currentTeam?.name||"Free Agent"} &middot; Age {player.currentAge}
              {isPitcher?(player.pitchHand?.code?` \u00b7 Throws: ${player.pitchHand.code}`:""):(player.batSide?.code?` \u00b7 Bats: ${player.batSide.code}`:"")}
              {player.height?` \u00b7 ${player.height}`:""}
              {player.weight?` / ${player.weight} lbs`:""}
            </p>
            {(player.draftYear || player.education) && (
              <p style={{margin:"2px 0 0",fontSize:11,color:C.muted,fontFamily:F}}>
                {player.draftYear ? `Draft: ${player.draftYear}${player.draftRound ? `, Rd. ${player.draftRound}` : ""}${player.draftPickNumber ? `, No. ${player.draftPickNumber}` : ""}${player.draftTeam?.abbreviation ? `, ${player.draftTeam.abbreviation}` : ""}` : ""}
                {player.draftYear && player.education ? " \u00b7 " : ""}
                {player.education?.school?.name || player.education?.highSchool?.name || ""}
              </p>
            )}
          </div>
          <div className="via-stat-row" style={{display:"flex",gap:6,flexWrap:"wrap"}}>
            {base&&isPitcher&&<>
              {cWAR!==null&&<Stat label="Career fWAR" value={cWAR.toFixed(1)} color={cWAR>=30?C.green:cWAR>=15?C.blue:C.accent} sub="FanGraphs"/>}
          </>}
          {base&&!isPitcher&&<>
              {cWAR!==null&&<Stat label="Career fWAR" value={cWAR.toFixed(1)} color={cWAR>=30?C.green:cWAR>=15?C.blue:C.accent} sub="FanGraphs"/>}
              {base._isTwoWay&&<>
                <Stat label="Hit fWAR" value={base._hitWAR?.toFixed(1)} color={C.blue} sub="Batting"/>
                <Stat label="Pitch fWAR" value={base._pitchWAR?.toFixed(1)} color={C.accent} sub="Pitching"/>
              </>}
            </>}
          </div>
        </div>
      </Panel>

      {/* Most recent season stats */}
      {(() => {
        const cur26 = seasons.find(s => s.season === String(PROJ_SEASON - 1) && s.level === "MLB");
        const pit26 = pitchSeasons.find(s => s.season === String(PROJ_SEASON - 1) && s.level === "MLB");
        if (!cur26 && !pit26) return null;
        return (
          <Panel title={`${PROJ_SEASON - 1} SEASON`} sub="Season stats via MLB Stats API." style={{borderTop:`3px solid ${C.green}`}}>
            {cur26 && (
              <div className="via-table-wrap" style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,fontFamily:F}}>
                  <thead>
                    <tr style={{borderBottom:`2px solid ${C.green}20`}}>
                      {["G","PA","AVG","OBP","SLG","OPS","HR","RBI","SB","BB","SO"].map(h=>(
                        <th key={h} style={{padding:"6px 10px",fontSize:10,fontWeight:700,color:C.green,textAlign:"right",fontFamily:F,letterSpacing:".04em"}}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{Math.round(cur26.pa / 4.1) || "—"}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{cur26.pa}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:cur26.avg>=.300?C.green:C.text,fontFamily:F}}>{cur26.avg.toFixed(3)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:cur26.obp>=.370?C.green:C.text,fontFamily:F}}>{cur26.obp.toFixed(3)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:cur26.slg>=.500?C.green:C.text,fontFamily:F}}>{cur26.slg.toFixed(3)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:800,color:cur26.ops>=.900?C.green:cur26.ops>=.750?C.accent:C.text,fontFamily:F}}>{cur26.ops.toFixed(3)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:cur26.hr>=5?C.accent:C.text,fontFamily:F}}>{cur26.hr}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{cur26.rbi}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:cur26.sb>=5?C.cyan:C.text,fontFamily:F}}>{cur26.sb}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.dim,fontFamily:F}}>{cur26.bb}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.dim,fontFamily:F}}>{cur26.so}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
            {pit26 && (
              <div className="via-table-wrap" style={{overflowX:"auto",marginTop:cur26?8:0}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,fontFamily:F}}>
                  <thead>
                    <tr style={{borderBottom:`2px solid ${C.green}20`}}>
                      {["W-L","ERA","IP","SO","BB","WHIP","K/9","BB/9","GS",pit26.sv>0?"SV":null,"HR"].filter(Boolean).map(h=>(
                        <th key={h} style={{padding:"6px 10px",fontSize:10,fontWeight:700,color:C.green,textAlign:"right",fontFamily:F,letterSpacing:".04em"}}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{pit26.w}-{pit26.l}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:pit26.era<=3.00?C.green:pit26.era<=4.00?C.accent:C.text,fontFamily:F}}>{pit26.era.toFixed(2)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{pit26.ip.toFixed(1)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:pit26.so>=20?C.accent:C.text,fontFamily:F}}>{pit26.so}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.dim,fontFamily:F}}>{pit26.bb}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:pit26.whip<=1.10?C.green:C.text,fontFamily:F}}>{pit26.whip.toFixed(2)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:pit26.k9>=10?C.green:C.text,fontFamily:F}}>{pit26.k9.toFixed(1)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:pit26.bb9<=2.5?C.green:C.dim,fontFamily:F}}>{pit26.bb9.toFixed(1)}</td>
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{pit26.gs}</td>
                      {pit26.sv>0&&<td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.accent,fontFamily:F}}>{pit26.sv}</td>}
                      <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.dim,fontFamily:F}}>{pit26.hr}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        );
      })()}

      {/* Season Projection Table */}
      {base && !isPitcher && (
        <Panel title={`${PROJ_SEASON} SEASON PROJECTION`} sub="Projected counting stats for the upcoming season." style={{borderTop:`3px solid ${C.navy}`}}>
          <div className="via-table-wrap" style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,fontFamily:F}}>
              <thead>
                <tr style={{borderBottom:`2px solid ${C.navy}20`}}>
                  {["G","PA","HR","AVG","OBP","SLG","OPS","wRC+","fWAR"].map(h=>(
                    <th key={h} style={{padding:"6px 10px",fontSize:10,fontWeight:700,color:C.navy,textAlign:"right",fontFamily:F,letterSpacing:".04em"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.projGames||Math.round((base.estPA||550)/4.1)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.estPA||"—"}</td>
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

      {/* Pitcher Season Projection Table */}
      {base && isPitcher && (
        <Panel title={`${PROJ_SEASON} SEASON PROJECTION`} sub="Projected pitching stats for the upcoming season." style={{borderTop:`3px solid ${C.navy}`}}>
          <div className="via-table-wrap" style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12,fontFamily:F}}>
              <thead>
                <tr style={{borderBottom:`2px solid ${C.navy}20`}}>
                  {["W","L","ERA","FIP","WHIP","K/9","BB/9","IP","K","fWAR"].map(h=>(
                    <th key={h} style={{padding:"6px 10px",fontSize:10,fontWeight:700,color:C.navy,textAlign:"right",fontFamily:F,letterSpacing:".04em"}}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.w||Math.round((base.ip||150)/9*(1-base.era/9.5)*0.55+5)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{base.l||Math.round((base.ip||150)/9*(base.era/9.5)*0.55+4)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.era<=3.00?C.green:base.era<=3.80?"#1a6b3c":C.text,fontFamily:F}}>{base.era?.toFixed(2)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.fip<=3.00?C.green:base.fip<=3.80?"#1a6b3c":C.text,fontFamily:F}}>{base.fip?.toFixed(2)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.whip<=1.05?C.green:base.whip<=1.20?"#1a6b3c":C.text,fontFamily:F}}>{base.whip?.toFixed(2)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.k9>=10?C.green:base.k9>=8.5?"#1a6b3c":C.text,fontFamily:F}}>{base.k9?.toFixed(1)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.bb9<=2.5?C.green:base.bb9<=3.5?"#1a6b3c":C.text,fontFamily:F}}>{base.bb9?.toFixed(1)||"—"}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:base.ip>=180?C.green:base.ip>=140?"#1a6b3c":C.text,fontFamily:F}}>{base.ip}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:700,color:C.text,fontFamily:F}}>{Math.round((base.k9||8)*(base.ip||150)/9)}</td>
                  <td style={{padding:"8px 10px",textAlign:"right",fontWeight:800,color:base.baseWAR>=5?C.green:base.baseWAR>=3?"#1a6b3c":C.text,fontFamily:F}}>{base.baseWAR?.toFixed(1)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Panel>
      )}

            {/* Statcast Batted Ball Data — Savant-style percentile bars */}
      {base && !isPitcher && base._statcast && (
        <Panel title={base._statcast.milb_source ? `MiLB STATCAST PROFILE (${base._statcast.milb_level})` : "STATCAST PROFILE"} sub={base._statcast.milb_source ? "Prospect Savant data. Percentiles compared to MLB league-wide averages." : "Weighted Baseball Savant data (2024\u20132026). Updated nightly. Percentiles are league-wide."}>
          <div style={{display:"flex",flexDirection:"column",gap:1}}>
            {[
              {label:"xwOBA",      val:base._statcast.xwoba,   fmt:v=>v.toFixed(3), min:.240, max:.420, avg:.310, higher:true},
              {label:"Avg EV",     val:base._statcast.projEV,  fmt:v=>v.toFixed(1)+" mph", min:83, max:94, avg:88.5, higher:true},
              {label:"Max EV",     val:base._statcast.maxEV,   fmt:v=>v.toFixed(1)+" mph", min:102, max:118, avg:110, higher:true},
              {label:"EV50",       val:base._statcast.ev50,    fmt:v=>v.toFixed(1)+" mph", min:82, max:100, avg:90, higher:true},
              {label:"Barrel%",    val:base._statcast.projBarrel, fmt:v=>v.toFixed(1)+"%", min:2, max:18, avg:7.5, higher:true},
              {label:"Hard Hit%",  val:base._statcast.hardHit,  fmt:v=>v.toFixed(1)+"%", min:25, max:55, avg:38, higher:true},
              {label:"K%",         val:base._statcast.projK,   fmt:v=>v.toFixed(1)+"%", min:10, max:35, avg:22.5, higher:false},
              {label:"BB%",        val:base._statcast.projBB,  fmt:v=>v.toFixed(1)+"%", min:3, max:18, avg:8.5, higher:true},
              {label:"Chase%",     val:base._statcast.chase,   fmt:v=>v.toFixed(1)+"%", min:18, max:38, avg:28, higher:false},
              {label:"Whiff%",     val:base._statcast.whiff,   fmt:v=>v.toFixed(1)+"%", min:15, max:40, avg:25, higher:false},
              {label:"Sprint Spd", val:base._statcast.sprintSpeed, fmt:v=>v.toFixed(1)+" ft/s", min:23, max:31, avg:27, higher:true},
              {label:"OAA",        val:base._statcast.oaa,     fmt:v=>String(v), min:-15, max:20, avg:0, higher:true},
            ].filter(m=>m.val!=null).map(m=>{
              const pct = m.higher
                ? Math.max(1, Math.min(99, Math.round(((m.val - m.min) / (m.max - m.min)) * 100)))
                : Math.max(1, Math.min(99, Math.round(((m.max - m.val) / (m.max - m.min)) * 100)));
              const barColor = pct >= 90 ? C.red : pct >= 75 ? "#e17726" : pct >= 60 ? "#eab308" : pct >= 40 ? "#94a3b8" : pct >= 25 ? "#3b82f6" : "#2563eb";
              return (
                <div key={m.label} style={{display:"flex",alignItems:"center",gap:8,padding:"6px 0",borderBottom:`1px solid ${C.border}20`}}>
                  <div style={{width:72,fontSize:10,fontWeight:600,color:C.dim,fontFamily:F,textAlign:"right",flexShrink:0}}>{m.label}</div>
                  <div style={{flex:1,height:8,background:`${C.border}30`,borderRadius:4,position:"relative",overflow:"hidden"}}>
                    <div style={{width:`${pct}%`,height:"100%",background:barColor,borderRadius:4,transition:"width 0.5s ease"}}/>
                  </div>
                  <div style={{width:40,fontSize:11,fontWeight:700,color:barColor,fontFamily:F,textAlign:"center",flexShrink:0}}>{pct}</div>
                  <div style={{width:72,fontSize:10,fontWeight:600,color:C.text,fontFamily:F,textAlign:"left",flexShrink:0}}>{m.fmt(m.val)}</div>
                </div>
              );
            })}
          </div>
          {base._statcast.trendBoost!=null&&base._statcast.trendBoost!==0&&(
            <div style={{marginTop:8,textAlign:"center",fontSize:10,color:base._statcast.trendBoost>0?C.green:C.red,fontFamily:F}}>
              {base._statcast.trendBoost>0?"▲":"▼"} Trend: {base._statcast.trendBoost>0?"+":""}{(base._statcast.trendBoost*1000).toFixed(0)} xwOBA points
            </div>
          )}
        </Panel>
      )}
      {/* Statcast Pitching Profile — Savant-style percentile bars */}
      {base && isPitcher && base._statcast && (
        <Panel title="STATCAST PROFILE" sub={`Three years of weighted Baseball Savant data (${PROJ_SEASON - 3}\u2013${PROJ_SEASON - 1}). Percentiles are league-wide.`}>
          <div style={{display:"flex",flexDirection:"column",gap:1}}>
            {[
              {label:"xwOBA vs",   val:base._statcast.xwoba,   fmt:v=>v.toFixed(3), pctKey:"xwoba", higher:false},
              {label:"xERA",       val:base._statcast.xera,    fmt:v=>v.toFixed(2), pctKey:"xera", higher:false},
              {label:"FB Velo",    val:base._statcast.fbVelo,  fmt:v=>v.toFixed(1)+" mph", pctKey:"velo", higher:true},
              {label:"Barrel% vs", val:base._statcast.projBarrelAgainst, fmt:v=>v.toFixed(1)+"%", pctKey:"barrel", higher:false},
              {label:"EV vs",      val:base._statcast.projEVAgainst, fmt:v=>v.toFixed(1)+" mph", pctKey:"ev", higher:false},
              {label:"Whiff%",     val:base._statcast.swStr,   fmt:v=>v.toFixed(1)+"%", pctKey:"whiff", higher:true},
            ].filter(m=>m.val!=null).map(m=>{
              const pct = PITCHER_PCTL[m.pctKey]
                ? pctlLookup(m.val, PITCHER_PCTL[m.pctKey], m.higher)
                : (m.higher
                  ? Math.max(1, Math.min(99, Math.round(((m.val - 0) / (100 - 0)) * 100)))
                  : Math.max(1, Math.min(99, Math.round(((100 - m.val) / (100 - 0)) * 100))));
              const barColor = pct >= 90 ? C.red : pct >= 75 ? "#e17726" : pct >= 60 ? "#eab308" : pct >= 40 ? "#94a3b8" : pct >= 25 ? "#3b82f6" : "#2563eb";
              return (
                <div key={m.label} style={{display:"flex",alignItems:"center",gap:8,padding:"6px 0",borderBottom:`1px solid ${C.border}20`}}>
                  <div style={{width:72,fontSize:10,fontWeight:600,color:C.dim,fontFamily:F,textAlign:"right",flexShrink:0}}>{m.label}</div>
                  <div style={{flex:1,height:8,background:`${C.border}30`,borderRadius:4,position:"relative",overflow:"hidden"}}>
                    <div style={{width:`${pct}%`,height:"100%",background:barColor,borderRadius:4,transition:"width 0.5s ease"}}/>
                  </div>
                  <div style={{width:40,fontSize:11,fontWeight:700,color:barColor,fontFamily:F,textAlign:"center",flexShrink:0}}>{pct}</div>
                  <div style={{width:72,fontSize:10,fontWeight:600,color:C.text,fontFamily:F,textAlign:"left",flexShrink:0}}>{m.fmt(m.val)}</div>
                </div>
              );
            })}
          </div>
          {base._statcast.veloTrend!=null&&base._statcast.veloTrend!==0&&(
            <div style={{marginTop:8,textAlign:"center",fontSize:10,color:base._statcast.veloTrend>0?C.green:C.red,fontFamily:F}}>
              {base._statcast.veloTrend>0?"▲":"▼"} Velo trend: {base._statcast.veloTrend>0?"+":""}{base._statcast.veloTrend.toFixed(1)} mph
            </div>
          )}
        </Panel>
      )}

      {/* Pitch Arsenal Grades — per-pitch letter grades from Savant data */}
      {base && isPitcher && ((() => {
        const ars = getLatestArsenal(player?.id, player?.fullName);
        if (!ars || !ars.pitches.length) return null;
        return (
          <Panel title={`PITCH ARSENAL (${ars.year})`} sub="Per-pitch grades from Baseball Savant run values, whiff rates, and expected stats.">
            <div className="via-arsenal-grid" style={{display:"flex",flexDirection:"column",gap:2}}>
              {/* Header row */}
              <div className="via-arsenal-row" style={{display:"grid",gridTemplateColumns:"minmax(90px,1fr) 46px 48px 48px 48px 48px 48px",gap:3,padding:"4px 6px",borderBottom:`1px solid ${C.border}40`}}>
                <span style={{fontSize:9,fontWeight:700,color:C.muted,fontFamily:F}}>Pitch</span>
                <span style={{fontSize:9,fontWeight:700,color:C.muted,fontFamily:F,textAlign:"center"}}>Grade</span>
                <span style={{fontSize:9,fontWeight:700,color:C.muted,fontFamily:F,textAlign:"right"}}>Usage</span>
                <span className="via-arsenal-hide-sm" style={{fontSize:9,fontWeight:700,color:C.muted,fontFamily:F,textAlign:"right"}}>RV/100</span>
                <span style={{fontSize:9,fontWeight:700,color:C.muted,fontFamily:F,textAlign:"right"}}>Whiff%</span>
                <span style={{fontSize:9,fontWeight:700,color:C.muted,fontFamily:F,textAlign:"right"}}>xwOBA</span>
                <span className="via-arsenal-hide-sm" style={{fontSize:9,fontWeight:700,color:C.muted,fontFamily:F,textAlign:"right"}}>K%</span>
              </div>
              {ars.pitches.map((pitch, i) => {
                const g = gradePitch(pitch);
                if (!g) return null;
                return (
                  <div key={i} className="via-arsenal-row" style={{display:"grid",gridTemplateColumns:"minmax(90px,1fr) 46px 48px 48px 48px 48px 48px",gap:3,padding:"5px 6px",borderBottom:i < ars.pitches.length - 1 ? `1px solid ${C.border}15` : "none"}}>
                    <div style={{display:"flex",alignItems:"center",gap:6}}>
                      <span style={{fontSize:11,fontWeight:600,color:C.text,fontFamily:F}}>{pitch.name || pitch.type}</span>
                    </div>
                    <div style={{display:"flex",justifyContent:"center",alignItems:"center"}}>
                      <span style={{fontSize:12,fontWeight:800,color:g.color,fontFamily:F,background:`${g.color}12`,padding:"1px 8px",borderRadius:4,border:`1px solid ${g.color}30`}}>{g.grade}</span>
                    </div>
                    <span style={{fontSize:11,color:C.dim,fontFamily:F,textAlign:"right"}}>{pitch.usage?.toFixed(1)}%</span>
                    <span className="via-arsenal-hide-sm" style={{fontSize:11,fontWeight:600,color:pitch.rv100 >= 1.5 ? C.green : pitch.rv100 >= 0 ? "#1a6b3c" : pitch.rv100 >= -1 ? C.dim : "#ef4444",fontFamily:F,textAlign:"right"}}>{pitch.rv100?.toFixed(1)}</span>
                    <span style={{fontSize:11,fontWeight:600,color:pitch.whiff >= 35 ? C.green : pitch.whiff >= 25 ? "#1a6b3c" : C.dim,fontFamily:F,textAlign:"right"}}>{pitch.whiff?.toFixed(1)}%</span>
                    <span style={{fontSize:11,fontWeight:600,color:parseFloat(pitch.xwoba) <= 0.250 ? C.green : parseFloat(pitch.xwoba) <= 0.310 ? "#1a6b3c" : C.dim,fontFamily:F,textAlign:"right"}}>{pitch.xwoba}</span>
                    <span className="via-arsenal-hide-sm" style={{fontSize:11,color:C.dim,fontFamily:F,textAlign:"right"}}>{pitch.k_pct?.toFixed(1)}%</span>
                  </div>
                );
              })}
            </div>
            {/* Overall arsenal grade */}
            {(() => {
              const graded = ars.pitches.map(p => ({...p, g: gradePitch(p)})).filter(p => p.g);
              if (!graded.length) return null;
              const totalUsage = graded.reduce((s, p) => s + (p.usage || 0), 0);
              const weightedComposite = graded.reduce((s, p) => s + (p.g.composite * (p.usage || 0)), 0) / (totalUsage || 1);
              let overallGrade, overallColor;
              if (weightedComposite >= 72) { overallGrade = "A+"; overallColor = "#10b981"; }
              else if (weightedComposite >= 62) { overallGrade = "A"; overallColor = "#22c55e"; }
              else if (weightedComposite >= 54) { overallGrade = "B+"; overallColor = "#84cc16"; }
              else if (weightedComposite >= 46) { overallGrade = "B"; overallColor = "#eab308"; }
              else if (weightedComposite >= 38) { overallGrade = "C+"; overallColor = "#f59e0b"; }
              else if (weightedComposite >= 30) { overallGrade = "C"; overallColor = "#fb923c"; }
              else if (weightedComposite >= 22) { overallGrade = "D"; overallColor = "#ef4444"; }
              else { overallGrade = "F"; overallColor = "#dc2626"; }
              return (
                <div style={{marginTop:10,display:"flex",justifyContent:"space-between",alignItems:"center",padding:"8px 12px",background:`${overallColor}08`,border:`1px solid ${overallColor}20`,borderRadius:8}}>
                  <span style={{fontSize:11,fontWeight:600,color:C.dim,fontFamily:F}}>Overall Arsenal Grade</span>
                  <div style={{display:"flex",alignItems:"center",gap:8}}>
                    <span style={{fontSize:10,color:C.muted,fontFamily:F}}>Score: {Math.round(weightedComposite)}</span>
                    <span style={{fontSize:16,fontWeight:800,color:overallColor,fontFamily:F}}>{overallGrade}</span>
                  </div>
                </div>
              );
            })()}
          </Panel>
        );
      })())}

      {/* Translation factors (MiLB only) */}
      {isMiLB&&<Panel title="MINOR LEAGUE TRANSLATION FACTORS" sub="How stats at each level translate to MLB equivalents. Lower levels get heavier regression to the mean.">
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:6}}>
          {LEVEL_ORDER.map(lvl=>{const t=LEVEL_TRANSLATION[lvl];return(
            <div key={lvl} style={{padding:"10px 12px",background:`${LEVEL_COLORS[lvl]}08`,border:`1px solid ${LEVEL_COLORS[lvl]}${base?.highestLevel===lvl?"40":"15"}`,borderRadius:6}}>
              <div style={{fontSize:14,fontWeight:800,color:LEVEL_COLORS[lvl],fontFamily:F}}>{lvl}</div>
              <div style={{fontSize:9,color:C.muted,fontFamily:F,marginTop:4}}>Factor: <span style={{color:C.text}}>{Math.round(t.factor*100)}%</span></div>
              <div style={{fontSize:9,color:C.muted,fontFamily:F}}>wRC+ adj: <span style={{color:C.text}}>{t.wrcAdj}</span></div>
              <div style={{fontSize:9,color:C.muted,fontFamily:F}}>Reliability: <span style={{color:C.text}}>{Math.round(t.reliability*100)}%</span></div>
            </div>
          );})}
        </div>
      </Panel>}

      {/* Career Stats — moved to bottom */}
      {!isPitcher&&seasons.length>0&&<Panel title="CAREER STATS" sub={isMiLB?"Minor league stats shown with level indicators. Translation factors applied in projections.":"Year-by-year from MLB Stats API."}>
        <div className="via-table-wrap" style={{overflowX:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
              {["Year","Age","Tm","Lvl","PA","AVG","OBP","SLG","OPS","HR","R","RBI","BB","SO","SB"].map(h=>
                <th key={h} style={{padding:"5px 7px",textAlign:["Year","Tm","Lvl"].includes(h)?"left":"right",color:C.muted,fontWeight:600,fontSize:9,letterSpacing:".04em"}}>{h}</th>
              )}
            </tr></thead>
            <tbody>{seasons.map((s,i)=>(
              <tr key={i} style={{borderBottom:`1px solid ${C.border}40`,background:i%2===0?C.hover:"transparent"}}>
                <td style={{padding:"4px 7px",color:C.text,fontWeight:600}}>{s.season}</td>
                <td style={{padding:"4px 7px",color:C.dim,textAlign:"right"}}>{s.age}</td>
                <td style={{padding:"4px 7px",color:C.dim}}>{s.team}</td>
                <td style={{padding:"4px 7px"}}><LevelBadge level={s.level}/></td>
                <td style={{padding:"4px 7px",color:C.text,textAlign:"right"}}>{s.pa}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.avg>=.300?C.green:C.text,fontWeight:600}}>{s.avg.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.obp>=.370?C.green:C.text}}>{s.obp.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.slg>=.500?C.green:C.text}}>{s.slg.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",fontWeight:700,color:s.ops>=.900?C.green:s.ops>=.750?C.accent:C.text}}>{s.ops.toFixed(3)}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.hr>=20?C.accent:C.text}}>{s.hr}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.text}}>{s.r}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.text}}>{s.rbi}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.bb}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:C.dim}}>{s.so}</td>
                <td style={{padding:"4px 7px",textAlign:"right",color:s.sb>=15?C.cyan:C.dim}}>{s.sb}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Panel>}
    </div>
  );
}

// ── ROSTER BROWSER (MLB + MiLB) ─────────────────────────────────────────────
function RosterBrowser({onSelect}) {
  const [teams,setTeams]=useState([]); const [selTeam,setSelTeam]=useState(null);
  const [affiliates,setAffiliates]=useState([]); const [selAffiliate,setSelAffiliate]=useState(null);
  const [roster,setRoster]=useState([]); const [loading,setLoading]=useState(false);
  const [viewLevel,setViewLevel]=useState("MLB");

  useEffect(()=>{getTeams(1).then(setTeams);},[]);

  const pickTeam = (team) => {
    setSelTeam(team); setSelAffiliate(null); setRoster([]); setViewLevel("MLB"); setLoading(true);
    Promise.all([getTeamRoster(team.id), getMiLBAffiliate(team.id)])
      .then(([r, a]) => { setRoster(r); setAffiliates(a); setLoading(false); });
  };

  const pickAffiliate = (aff) => {
    setSelAffiliate(aff); setViewLevel(LEVEL_NAMES[aff.sport?.id]||"MiLB"); setLoading(true);
    getTeamRoster(aff.id).then(r=>{setRoster(r);setLoading(false);});
  };

  const showMLB = () => {
    if(!selTeam) return;
    setSelAffiliate(null); setViewLevel("MLB"); setLoading(true);
    getTeamRoster(selTeam.id).then(r=>{setRoster(r);setLoading(false);});
  };

  return (
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      <Panel title="SELECT MLB ORGANIZATION" sub="All 30 teams listed alphabetically.">
        <div className="via-roster-grid" style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))",gap:6}}>
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
      </Panel>

      {selTeam&&affiliates.length>0&&<Panel title={`${selTeam.name.toUpperCase()} SYSTEM`} sub="Click a level to browse that affiliate's roster.">
        <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
          <button onClick={showMLB} style={{padding:"6px 14px",borderRadius:6,cursor:"pointer",border:`2px solid ${viewLevel==="MLB"?C.green:C.border}`,background:viewLevel==="MLB"?`${C.green}15`:"transparent",color:viewLevel==="MLB"?C.green:C.muted,fontSize:11,fontWeight:700,fontFamily:F}}>
            MLB &middot; {selTeam.abbreviation}
          </button>
          {affiliates.map(a=>{
            const lvl=LEVEL_NAMES[a.sport?.id]||"MiLB";
            const active=selAffiliate?.id===a.id;
            return <button key={a.id} onClick={()=>pickAffiliate(a)} style={{
              padding:"6px 14px",borderRadius:6,cursor:"pointer",fontSize:11,fontWeight:700,fontFamily:F,
              border:`2px solid ${active?LEVEL_COLORS[lvl]:C.border}`,
              background:active?`${LEVEL_COLORS[lvl]}15`:"transparent",
              color:active?LEVEL_COLORS[lvl]:C.muted,
            }}>{lvl} &middot; {a.shortName||a.abbreviation}</button>;
          })}
        </div>
      </Panel>}

      {loading&&<Spinner msg={`Loading ${viewLevel} roster...`}/>}

      {!loading&&roster.length>0&&<Panel title={`${selAffiliate?.name||selTeam?.name||""} ROSTER`} sub="Click a player to load their projection.">
        <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12}}>
          <LevelBadge level={viewLevel}/>
          <span style={{fontSize:11,color:C.dim,fontFamily:F}}>{roster.filter(r=>r.position?.code!=="1").length} position players</span>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(190px,1fr))",gap:5}}>
          {roster.filter(r=>r.person&&r.position?.code!=="1").map(r=>{
            const rfv = getPlayerFV(r.person.id, r.person.fullName);
            return <div key={r.person.id} onClick={()=>onSelect(r.person)}
              style={{padding:"7px 11px",background:C.hover,borderRadius:6,cursor:"pointer",border:`1px solid ${C.border}`,transition:"border-color .1s",display:"flex",justifyContent:"space-between",alignItems:"center"}}
              onMouseEnter={e=>e.currentTarget.style.borderColor=LEVEL_COLORS[viewLevel]||C.accent}
              onMouseLeave={e=>e.currentTarget.style.borderColor=C.border}>
              <div>
                <div style={{fontSize:12,fontWeight:700,color:C.text,fontFamily:F}}>{r.person.fullName}</div>
                <div style={{fontSize:10,color:C.muted,fontFamily:F}}>{posLabel(r.position?.code)} &middot; #{r.jerseyNumber||"\u2014"}</div>
              </div>
              {rfv && <FVBadge fv={rfv}/>}
            </div>;
          })}
        </div>
      </Panel>}
    </div>
  );
}

// ── LEADERBOARD ─────────────────────────────────────────────────────────────
// Fetches all active MLB position players via the sports_players endpoint,
// pulls 2025 season stats in bulk, runs projections, and shows a sortable table.

async function fetchAllMLBPlayers() {
  const TEAMS = {108:'LAA',109:'AZ',110:'BAL',111:'BOS',112:'CHC',113:'CIN',114:'CLE',115:'COL',116:'DET',117:'HOU',118:'KC',119:'LAD',120:'WSH',121:'NYM',133:'OAK',134:'PIT',135:'SD',136:'SEA',137:'SF',138:'STL',139:'TB',140:'TEX',141:'TOR',142:'MIN',143:'PHI',144:'ATL',145:'CWS',146:'MIA',147:'NYY',158:'MIL'};
  try {
    const allPlayers = [];
    const ids = Object.keys(TEAMS);
    const BATCH = 6;
    for (let i = 0; i < ids.length; i += BATCH) {
      const batch = ids.slice(i, i + BATCH);
      const results = await Promise.all(batch.map(async tid => {
        try {
          const res = await fetch(`${API}/teams/${tid}/roster?rosterType=40Man&hydrate=person`);
          const data = await res.json();
          return (data.roster || []).map(r => {
            const p = r.person || {};
            p._teamAbbr = TEAMS[tid];
            return p;
          });
        } catch { return []; }
      }));
      allPlayers.push(...results.flat());
    }
    // Deduplicate by player ID
    const seen = new Set();
    return allPlayers.filter(p => { if (seen.has(p.id)) return false; seen.add(p.id); return true; });
  } catch(e) { console.error(e); return []; }
}

async function fetchPlayerPitchingStats(playerId) {
  const sportIds = [1, 11, 12, 13, 14, 16];
  const fetchWithRetry = async (url, retries = 2) => {
    for (let r = 0; r <= retries; r++) {
      try {
        if (r > 0) await new Promise(ok => setTimeout(ok, 500 * r));
        const resp = await fetch(url);
        if (!resp.ok && r < retries) continue;
        return await resp.json();
      } catch { if (r === retries) return null; }
    }
    return null;
  };
  try {
    const promises = sportIds.map(async sid => {
      const d = await fetchWithRetry(`${API}/people/${playerId}/stats?stats=yearByYear&group=pitching&gameType=R&sportId=${sid}`);
      return d ? (d.stats?.[0]?.splits || []).map(s => ({...s, _sportId: sid})) : [];
    });
    return (await Promise.all(promises)).flat();
  } catch { return []; }
}

async function fetchPlayerSeasonStats(playerId) {
  const sportIds = [1, 11, 12, 13, 14, 16];
  const fetchWithRetry = async (url, retries = 2) => {
    for (let r = 0; r <= retries; r++) {
      try {
        if (r > 0) await new Promise(ok => setTimeout(ok, 500 * r));
        const resp = await fetch(url);
        if (!resp.ok && r < retries) continue;
        return await resp.json();
      } catch { if (r === retries) return null; }
    }
    return null;
  };
  try {
    const promises = sportIds.map(async sid => {
      const d = await fetchWithRetry(`${API}/people/${playerId}/stats?stats=yearByYear&group=hitting&gameType=R&sportId=${sid}`);
      return d ? (d.stats?.[0]?.splits || []).map(s => ({ ...s, _sportId: sid })) : [];
    });
    const all = await Promise.all(promises);
    return all.flat();
  } catch { return []; }
}

const PITCHER_COLS = [
  { k: "name",     l: "Player",      fmt: v => v, align: "left", sortDir: 1 },
  { k: "team",     l: "Team",        fmt: v => v, align: "left", sortDir: 1 },
  { k: "age",      l: "Age",         fmt: v => v, align: "right", sortDir: -1 },
  { k: "projWAR",  l: "Proj fWAR",    fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "careerWAR",l: "Career fWAR", fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "cumWAR",   l: "10yr fWAR",    fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "projERA",  l: "Proj ERA",    fmt: v => v?.toFixed(2) ?? "—", align: "right", sortDir: 1 },
  { k: "projFIP",  l: "Proj FIP",    fmt: v => v?.toFixed(2) ?? "—", align: "right", sortDir: 1 },
  { k: "projWHIP", l: "Proj WHIP",   fmt: v => v?.toFixed(2) ?? "—", align: "right", sortDir: 1 },
  { k: "projK9",   l: "Proj K/9",    fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "projBB9",  l: "Proj BB/9",   fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: 1 },
  { k: "projIP",   l: "Proj IP",     fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "projW",    l: "Proj W",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "projSV",   l: "Proj SV",     fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastERA",  l: "'25 ERA",     fmt: v => v?.toFixed(2) ?? "—", align: "right", sortDir: 1 },
  { k: "lastIP",   l: "'25 IP",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastSO",   l: "'25 SO",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "fv",       l: "FV",          fmt: v => v ?? "—", align: "right", sortDir: -1 },
];

const LEADER_COLS = [
  { k: "name",     l: "Player",      fmt: v => v, align: "left", sortDir: 1 },
  { k: "team",     l: "Team",        fmt: v => v, align: "left", sortDir: 1 },
  { k: "pos",      l: "Pos",         fmt: v => v, align: "left", sortDir: 1 },
  { k: "age",      l: "Age",         fmt: v => v, align: "right", sortDir: -1 },
  { k: "projWAR",  l: "Proj fWAR",    fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "careerWAR",l: "Career fWAR",  fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "cumWAR",   l: "10yr fWAR",     fmt: v => v?.toFixed(1) ?? "—", align: "right", sortDir: -1 },
  { k: "projWRC",  l: "Proj wRC+",   fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "projOPS",  l: "Proj OPS",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projAVG",  l: "Proj AVG",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projOBP",  l: "Proj OBP",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projSLG",  l: "Proj SLG",    fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "projHR",   l: "Proj HR",     fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastAVG",  l: "'25 AVG",     fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "lastOPS",  l: "'25 OPS",     fmt: v => v?.toFixed(3) ?? "—", align: "right", sortDir: -1 },
  { k: "lastHR",   l: "'25 HR",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastSB",   l: "'25 SB",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "lastPA",   l: "'25 PA",      fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "peakAge",  l: "Peak Age",    fmt: v => v ?? "—", align: "right", sortDir: -1 },
  { k: "fv",       l: "FV",          fmt: v => v ?? "—", align: "right", sortDir: -1 },
];

function Leaderboard({ onSelect }) {
  const [players, setPlayers] = useState([]);
  const [pitchers, setPitchers] = useState([]);
  const [mode, setMode] = useState("hitters");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [sortCol, setSortCol] = useState("projWAR");
  const [sortAsc, setSortAsc] = useState(false);
  const [posFilter, setPosFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [started, setStarted] = useState(false);


  const loadAll = useCallback(async () => {
    setStarted(true);
    setLoading(true);
    setPlayers([]);
    setPitchers([]);

    // Step 1: fetch all active MLB players
    const allPeople = await fetchAllMLBPlayers();
    const hitters = allPeople.filter(p => p.primaryPosition?.code !== "1");
    const pitcherList = allPeople.filter(p => p.primaryPosition?.code === "1");
    setProgress({ done: 0, total: hitters.length + pitcherList.length });

    // Step 2: fetch stats and project in batches of 15
    const results = [];
    const BATCH = 15;
    for (let i = 0; i < hitters.length; i += BATCH) {
      const batch = hitters.slice(i, i + BATCH);
      const batchResults = await Promise.all(batch.map(async (p) => {
        try {
          const splits = await fetchPlayerSeasonStats(p.id);
          if (!splits.length) return null;

          const base = projectPlayer(splits, projAge(p), p.primaryPosition?.code, p.fullName, p.id);
          if (!base) return null;

          const forward = projectForward(base, projAge(p), p.primaryPosition?.code);
          const cum = forward.reduce((s, d) => s + Math.max(0, d.war), 0);
          const fv = getPlayerFV(p.id, p.fullName);

          // Find 2025 stats
          const s25 = splits
            .filter(s => s.season === String(PROJ_SEASON - 1) && s.stat?.plateAppearances > 0)
            .sort((a, b) => (b.stat?.plateAppearances || 0) - (a.stat?.plateAppearances || 0));
          const best25 = s25[0]?.stat;

          // Two-way WAR: compute pitching contribution separately
          let twoWayBonus = 0;
          if (p.primaryPosition?.code === "Y") {
            try {
              const pitchSplits = await fetchPlayerPitchingStats(p.id);
              const pp = pitchSplits.length ? projectPitcher(pitchSplits, projAge(p), p.fullName, p.id) : null;
              if (pp && pp.baseWAR > 0) {
                const hitDiscount = base.baseWAR * 0.92;
                const pitchDiscount = pp.baseWAR * 0.72;
                twoWayBonus = Math.round((hitDiscount + pitchDiscount) * 10) / 10 - base.baseWAR;
              }
            } catch {}
          }

          return {
            id: p.id,
            name: p.fullName,
            team: p._teamAbbr || p.currentTeam?.abbreviation || "FA",
            pos: posLabel(p.primaryPosition?.code),
            age: projAge(p),
            projWAR: base.baseWAR + twoWayBonus,
            careerWAR: getCareerWAR(p.id, p.fullName),
            cumWAR: Math.round(cum * 10) / 10,
            projWRC: base.wRCPlus,
            projOPS: base.ops,
            projAVG: base.avg,
            projOBP: base.obp,
            projSLG: base.slg,
            projHR: base.hr,
            lastAVG: best25 ? parseFloat(best25.avg || 0) : null,
            lastOPS: best25 ? parseFloat(best25.ops || 0) : null,
            lastHR: best25 ? best25.homeRuns : null,
            lastSB: best25 ? best25.stolenBases : null,
            lastPA: best25 ? best25.plateAppearances : null,
            peakAge: getAP(p.primaryPosition?.code).peak,
            fv: fv,
            _player: p,
          };
        } catch { return null; }
      }));

      const valid = batchResults.filter(Boolean);
      results.push(...valid);
      setPlayers(prev => [...prev, ...valid]);
      setProgress({ done: Math.min(i + BATCH, hitters.length), total: hitters.length + pitcherList.length });
      // Small delay between batches to avoid API rate limiting
      if (i + BATCH < hitters.length) await new Promise(ok => setTimeout(ok, 200));
    }

    // Now process pitchers
    try {
    for (let i = 0; i < pitcherList.length; i += BATCH) {
      const batch = pitcherList.slice(i, i + BATCH);
      const batchResults = await Promise.all(batch.map(async p => {
        try {
          const splits = await fetchPlayerPitchingStats(p.id);
          if (!splits.length) return null;
          let base = projectPitcher(splits, projAge(p), p.fullName, p.id);
          if (!base) return null;
          const fwd = projectPitcherForward(base, projAge(p));
          const cum = fwd.reduce((s, d) => s + Math.max(0, d.war), 0);
          const last = splits.find(s => s.season === String(PROJ_SEASON - 1) && s._sportId === 1);
          const lst = last?.stat || {};
          return {
            id: p.id, name: p.fullName, fullData: p,
            team: p._teamAbbr || p.currentTeam?.abbreviation || "FA",
            pos: base.isReliever ? "RP" : "SP", age: projAge(p),
            projWAR: base.baseWAR, careerWAR: getCareerWAR(p.id, p.fullName),
            cumWAR: Math.round(cum * 10) / 10,
            projERA: base.era, projFIP: base.fip, projWHIP: base.whip,
            projK9: base.k9, projBB9: base.bb9, projIP: base.ip,
            projW: base.w, projSV: base.sv,
            lastERA: lst.era ? parseFloat(lst.era) : null,
            lastIP: lst.inningsPitched ? parseFloat(lst.inningsPitched) : null,
            lastSO: lst.strikeOuts ? parseInt(lst.strikeOuts) : null,
            fv: getPlayerFV(p.id, p.fullName),
          };
        } catch { return null; }
      }));
      setPitchers(prev => [...prev, ...batchResults.filter(Boolean)]);
      setProgress({ done: results.length + i + BATCH, total: hitters.length + pitcherList.length });
    }
    } catch(e) { console.error("Pitcher loading error:", e); }

    setLoading(false);
  }, []);

  const sorted = useMemo(() => {
    let filtered = (mode === "pitchers" ? pitchers : players);
    if (posFilter !== "ALL") filtered = filtered.filter(p => p.pos === posFilter);
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(p => p.name.toLowerCase().includes(q) || p.team.toLowerCase().includes(q));
    }
    const activeCols = mode === "pitchers" ? PITCHER_COLS : LEADER_COLS;
    const col = activeCols.find(c => c.k === sortCol);
    const dir = sortAsc ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = a[sortCol], bv = b[sortCol];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string") return av.localeCompare(bv) * dir;
      return (av - bv) * dir;
    });
  }, [players, pitchers, mode, sortCol, sortAsc, posFilter, search]);

  const toggleSort = (k) => {
    if (sortCol === k) setSortAsc(!sortAsc);
    else { setSortCol(k); setSortAsc(false); }
  };

  const positions = ["ALL", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH", "OF"];
  const pitcherPositions = ["ALL", "SP", "RP"];

  if (!started) {
    return (
      <Panel style={{ textAlign: "center", padding: 50 }}>
        <div style={{ fontSize: 44, marginBottom: 12 }}>&#128202;</div>
        <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>
        <p style={{ margin: "8px auto 0", fontSize: 12, color: C.muted, fontFamily: F, maxWidth: 520, lineHeight: 1.6 }}>
          Load every active MLB position player, run projections on all of them, and sort by any stat.
          This fetches ~400+ players from the MLB Stats API — takes about 60-90 seconds.
        </p>
        <button onClick={loadAll} style={{
          marginTop: 20, padding: "10px 28px", borderRadius: 8, border: "none", cursor: "pointer",
          background: C.accent, color: "#fff", fontSize: 13, fontWeight: 700, fontFamily: F,
        }}>Load All Players &amp; Project</button>
      </Panel>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Progress */}
      {loading && <Panel>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 16, height: 16, border: `2px solid ${C.border}`, borderTopColor: C.accent, borderRadius: "50%", animation: "spin .8s linear infinite" }} />
          <span style={{ fontSize: 12, color: C.dim, fontFamily: F }}>
            Loading players... {progress.done}/{progress.total} ({players.length} hitters, {pitchers.length} pitchers projected)
          </span>
        </div>
        <div style={{ marginTop: 8, height: 4, background: C.border, borderRadius: 2, overflow: "hidden" }}>
          <div style={{ height: "100%", background: C.accent, borderRadius: 2, width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%`, transition: "width .3s" }} />
        </div>
      </Panel>}

      {/* Filters */}
      {(players.length > 0 || pitchers.length > 0) && <Panel>
        <div className="via-mode-toggle" style={{display:"flex",gap:4,marginBottom:10}}>
          <button onClick={()=>{setMode("hitters");setSortCol("projWAR");setSortAsc(false);setPosFilter("ALL");}}
            style={{padding:"6px 16px",border:"none",cursor:"pointer",fontSize:11,fontWeight:mode==="hitters"?700:500,fontFamily:F,
              background:mode==="hitters"?C.navy:"transparent",color:mode==="hitters"?"#fff":C.muted,borderRadius:6}}>Hitters</button>
          <button onClick={()=>{setMode("pitchers");setSortCol("projWAR");setSortAsc(false);setPosFilter("ALL");}}
            style={{padding:"6px 16px",border:"none",cursor:"pointer",fontSize:11,fontWeight:mode==="pitchers"?700:500,fontFamily:F,
              background:mode==="pitchers"?C.navy:"transparent",color:mode==="pitchers"?"#fff":C.muted,borderRadius:6}}>Pitchers</button>
        </div>
        <div className="via-leaderboard-filters" style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Filter by name or team..."
            style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${C.border}`, background: C.panel, color: C.text, fontSize: 11, fontFamily: F, outline: "none", width: 200 }} />
          <div className="via-pos-filters" style={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
            {(mode === "pitchers" ? pitcherPositions : positions).map(p => (
              <button key={p} onClick={() => setPosFilter(p)} style={{
                padding: "4px 10px", fontSize: 10, fontWeight: 600, fontFamily: F, borderRadius: 4, cursor: "pointer", border: "none",
                background: posFilter === p ? C.accent : C.hover, color: posFilter === p ? "#fff" : C.muted,
              }}>{p}</button>
            ))}
          </div>
          <span style={{ fontSize: 10, color: C.muted, fontFamily: F, marginLeft: "auto" }}>{sorted.length} players</span>
        </div>
      </Panel>}

      {/* Table */}
      {(players.length > 0 || pitchers.length > 0) && <Panel>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F, fontSize: 10 }}>
            <thead>
              <tr style={{ borderBottom: `2px solid ${C.border}` }}>
                <th style={{ padding: "6px 4px", textAlign: "right", color: C.muted, fontWeight: 600, fontSize: 8, width: 30 }}>#</th>
                {(mode === "pitchers" ? PITCHER_COLS : LEADER_COLS).map(col => (
                  <th key={col.k} onClick={() => toggleSort(col.k)} style={{
                    padding: "6px 6px", textAlign: col.align, color: sortCol === col.k ? C.accent : C.muted,
                    fontWeight: 600, fontSize: 8, letterSpacing: ".04em", cursor: "pointer", userSelect: "none", whiteSpace: "nowrap",
                  }}>
                    {col.l} {sortCol === col.k ? (sortAsc ? "▲" : "▼") : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.slice(0, 200).map((p, i) => (
                <tr key={p.id}
                  onClick={() => onSelect(p._player)}
                  style={{
                    borderBottom: `1px solid ${C.border}40`,
                    background: i % 2 === 0 ? C.hover : "transparent",
                    cursor: "pointer",
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = `${C.accent}08`}
                  onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? C.hover : "transparent"}>
                  <td style={{ padding: "5px 4px", textAlign: "right", color: C.muted, fontSize: 9 }}>{i + 1}</td>
                  {(mode === "pitchers" ? PITCHER_COLS : LEADER_COLS).map(col => {
                    const val = p[col.k];
                    const display = col.fmt(val);
                    let color = C.text;
                    if (col.k === "projWAR") color = val >= 4 ? C.green : val >= 2 ? C.blue : val >= 0 ? C.text : C.red;
                    if (col.k === "projOPS") color = val >= .850 ? C.green : val >= .720 ? C.blue : C.text;
                    if (col.k === "projWRC") color = val >= 120 ? C.green : val >= 100 ? C.blue : C.text;
                    if (col.k === "fv" && val) color = val >= 60 ? C.accent : val >= 50 ? C.yellow : C.muted;
                    if (col.k === "name") color = C.text;
                    return (
                      <td key={col.k} style={{
                        padding: "5px 6px", textAlign: col.align, color,
                        fontWeight: col.k === "name" || col.k === "projWAR" || col.k === "projOPS" ? 700 : 400,
                        whiteSpace: "nowrap",
                      }}>{display}</td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {sorted.length > 200 && <p style={{ fontSize: 10, color: C.muted, fontFamily: F, marginTop: 8, textAlign: "center" }}>Showing top 200 of {sorted.length}. Use filters to narrow.</p>}
      </Panel>}
    </div>
  );
}

// ── AGING CURVES ─────────────────────────────────────────────────────────────
function AgingPanel() {
  const [sel,setSel]=useState(["SS","CF","1B","C"]); const [bw,setBw]=useState(4);
  const posC = {C:C.red,"1B":C.yellow,"2B":C.green,"3B":C.accent,SS:C.blue,LF:C.purple,CF:C.cyan,RF:C.pink,DH:C.muted};
  const data=useMemo(()=>{
    const m={};
    sel.forEach(pos=>{const p=AGING_PARAMS[pos];for(let age=20;age<=40;age++){if(!m[age])m[age]={age};const d=age-p.peak;const off=d<=0?1-.015*d*d*.3:1-p.dr*d*d*.25;const def=age<=p.peak?1:1-p.dd*(age-p.peak);m[age][pos]=Math.round(Math.max(-.5,bw*off*Math.max(.4,def)+p.pa/10*Math.max(.3,def))*10)/10;}});
    return Object.values(m).sort((a,b)=>a.age-b.age);
  },[sel,bw]);
  return (
    <Panel title="POSITION AGING CURVES" sub="Offensive (quadratic) + defensive (linear) decline.">
      <div style={{display:"flex",flexWrap:"wrap",gap:5,marginBottom:14}}>
        {Object.keys(AGING_PARAMS).map(pos=><button key={pos} onClick={()=>setSel(p=>p.includes(pos)?p.filter(x=>x!==pos):[...p,pos])} style={{padding:"5px 12px",borderRadius:5,cursor:"pointer",fontSize:11,fontWeight:700,fontFamily:F,border:`2px solid ${sel.includes(pos)?posC[pos]:C.border}`,background:sel.includes(pos)?`${posC[pos]}18`:"transparent",color:sel.includes(pos)?posC[pos]:C.muted}}>{pos}</button>)}
        <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:8}}>
          <span style={{fontSize:10,color:C.muted,fontFamily:F}}>BASE WAR</span>
          <input type="range" min="1" max="8" step=".5" value={bw} onChange={e=>setBw(+e.target.value)} style={{width:100,accentColor:C.accent}}/>
          <span style={{fontSize:13,fontWeight:700,color:C.accent,fontFamily:F}}>{bw}</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={data} margin={{top:10,right:30,left:0,bottom:0}}>
          <CartesianGrid strokeDasharray="3 3" stroke={C.grid}/><XAxis dataKey="age" stroke={C.muted} fontSize={10} fontFamily={F}/><YAxis stroke={C.muted} fontSize={10} fontFamily={F}/><Tooltip content={<Tip/>}/><ReferenceLine y={0} stroke={C.muted} strokeDasharray="5 5"/>
          {sel.map(pos=><Line key={pos} type="monotone" dataKey={pos} stroke={posC[pos]} strokeWidth={2.5} dot={false} name={pos}/>)}
        </LineChart>
      </ResponsiveContainer>
    </Panel>
  );
}

// ── METHODOLOGY ──────────────────────────────────────────────────────────────
function VpDPanel() {
  const [loading, setLoading] = useState(true);
  const [players, setPlayers] = useState([]);
  const [sort, setSort] = useState({ key: "warPerM", dir: -1 });
  const [contractData, setContractData] = useState({});
  const [vpdSearch, setVpdSearch] = useState("");


  function getVpdGrade(warPerM) {
    if (warPerM >= 4.00) return { grade: "A+", color: "#10b981", label: "Elite" };
    if (warPerM >= 2.00) return { grade: "A", color: "#22c55e", label: "Excellent" };
    if (warPerM >= 1.00) return { grade: "A-", color: "#84cc16", label: "Great" };
    if (warPerM >= 0.60) return { grade: "B+", color: "#eab308", label: "Very Good" };
    if (warPerM >= 0.40) return { grade: "B", color: "#f59e0b", label: "Good" };
    if (warPerM >= 0.25) return { grade: "B-", color: "#fb923c", label: "Above Avg" };
    if (warPerM >= 0.18) return { grade: "C+", color: "#fbbf24", label: "Fair" };
    if (warPerM >= 0.13) return { grade: "C", color: "#94a3b8", label: "Below Avg" };
    if (warPerM >= 0.08) return { grade: "D", color: "#ef4444", label: "Poor Value" };
    return { grade: "F", color: "#dc2626", label: "Overpaid" };
  }


  useEffect(() => {
    async function loadData() {
      try {
        const contracts = await import("./contract_data.json");
        const cMap = contracts.default || contracts;
        setContractData(cMap);
        _contractCache = cMap;
        
        const playerPromises = Object.keys(contracts.default || contracts).filter(name => (contracts.default || contracts)[name] > 0).map(async (name) => {
          try {
            const results = await searchPlayers(name);
            if (results && results[0]) {
              const player = await getPlayerStats(results[0].id);
              if (!player) return null;
              const isPitcher = player.primaryPosition?.code === "1";
              const career = await getPlayerCareer(player.id, isPitcher ? "pitching" : "hitting");
              let base;
              if (isPitcher) {
                base = projectPitcher(career, projAge(player), player.fullName, player.id);
              } else {
                const splits = career.filter(s => s.stat?.plateAppearances > 0);
                base = projectPlayer(splits, projAge(player), player.primaryPosition?.code, player.fullName, player.id);
              }
              
              if (base && base.baseWAR) {
                const salary = (contracts.default || contracts)[name];
                return {
                  name: player.fullName,
                  salary: salary,
                  war: base.baseWAR,
                  warPerM: base.baseWAR / (salary / 1000000),
                  pos: player.primaryPosition?.code,
                  team: player.currentTeam?.abbreviation || player.currentTeam?.name || "FA"
                };
              }
            }
          } catch (e) {
            console.error(`Failed to load ${name}:`, e);
          }
          return null;
        });
        const results = await Promise.all(playerPromises);
        const validResults = results.filter(Boolean);
        const top100 = validResults.sort((a, b) => b.warPerM - a.warPerM);
        setPlayers(top100);
        setLoading(false);
      } catch (e) {
        console.error("Failed to load contract data:", e);
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const sorted = useMemo(() => {
    let filtered = [...players];
    if (vpdSearch.trim()) { const q = vpdSearch.toLowerCase(); filtered = filtered.filter(p => p.name.toLowerCase().includes(q) || (p.team||"").toLowerCase().includes(q)); }
    return filtered.sort((a, b) => {
      const aVal = a[sort.key];
      const bVal = b[sort.key];
      if (typeof aVal === "string") return aVal.localeCompare(bVal) * sort.dir;
      return (aVal - bVal) * sort.dir;
    });
  }, [players, sort, vpdSearch]);

  return (
    <div>
      <Panel title="VALUE PER DOLLAR (VpD)" sub="Most cost-efficient players based on projected WAR vs. 2026 salary">
        <div style={{marginBottom:12}}><input type="text" placeholder="Search players or teams..." value={vpdSearch} onChange={e=>setVpdSearch(e.target.value)} style={{width:"100%",maxWidth:360,padding:"8px 12px",borderRadius:6,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:12,fontFamily:F,outline:"none",boxSizing:"border-box"}} onFocus={e=>e.target.style.borderColor=C.accent} onBlur={e=>e.target.style.borderColor=C.border}/>{!loading&&<span style={{marginLeft:10,fontSize:10,color:C.muted,fontFamily:F}}>{sorted.length} players</span>}</div>
        {loading && <Spinner msg="Loading contract data and projections..."/>}
        {!loading && players.length === 0 && <p style={{color:C.muted,fontSize:11,fontFamily:F}}>No data available</p>}
        {!loading && players.length > 0 && (
          <div style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:11,fontFamily:F}}>
              <thead><tr>
                <th style={{padding:"8px",borderBottom:`2px solid ${C.border}`,textAlign:"left",cursor:"pointer",fontWeight:700,color:C.muted,fontSize:9}} onClick={() => setSort({key:"name",dir:sort.key==="name"?-sort.dir:-1})}>PLAYER</th>
                <th style={{padding:"8px",borderBottom:`2px solid ${C.border}`,textAlign:"center",cursor:"pointer",fontWeight:700,color:C.muted,fontSize:9}} onClick={() => setSort({key:"pos",dir:sort.key==="pos"?-sort.dir:-1})}>POS</th>
                <th style={{padding:"8px",borderBottom:`2px solid ${C.border}`,textAlign:"center",cursor:"pointer",fontWeight:700,color:C.muted,fontSize:9}} onClick={() => setSort({key:"team",dir:sort.key==="team"?-sort.dir:-1})}>TEAM</th>
                <th style={{padding:"8px",borderBottom:`2px solid ${C.border}`,textAlign:"right",cursor:"pointer",fontWeight:700,color:C.muted,fontSize:9}} onClick={() => setSort({key:"war",dir:sort.key==="war"?-sort.dir:-1})}>PROJ WAR</th>
                <th style={{padding:"8px",borderBottom:`2px solid ${C.border}`,textAlign:"right",cursor:"pointer",fontWeight:700,color:C.muted,fontSize:9}} onClick={() => setSort({key:"salary",dir:sort.key==="salary"?-sort.dir:-1})}>2026 SALARY</th>
                <th style={{padding:"8px",borderBottom:`2px solid ${C.border}`,textAlign:"right",cursor:"pointer",fontWeight:700,color:C.muted,fontSize:9}} onClick={() => setSort({key:"warPerM",dir:sort.key==="warPerM"?-sort.dir:-1})}>VpD GRADE</th>
              </tr></thead>
              <tbody>
                {sorted.map((p, i) => (
                  <tr key={i} style={{borderBottom:`1px solid ${C.border}22`}}>
                    <td style={{padding:"8px",fontWeight:600,color:C.text}}>{p.name}</td>
                    <td style={{padding:"8px",textAlign:"center",color:C.muted,fontSize:10}}>{posLabel(p.pos) || "—"}</td>
                    <td style={{padding:"8px",textAlign:"center",color:C.muted,fontSize:10}}>{p.team || "—"}</td>
                    <td style={{padding:"8px",textAlign:"right",color:C.accent,fontWeight:600}}>{p.war.toFixed(1)}</td>
                    <td style={{padding:"8px",textAlign:"right",color:C.text}}>${(p.salary/1000000).toFixed(1)}M</td>
                    <td style={{padding:"8px",textAlign:"center"}}>{
                      (() => {
                        const g = getVpdGrade(p.warPerM);
                        return <span style={{display:"inline-block",padding:"2px 8px",borderRadius:4,background:`${g.color}20`,color:g.color,fontWeight:700,fontSize:11}}>{g.grade}</span>;
                      })()
                    }</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}

function CardMarketplace({ onSelect }) {
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [projection, setProjection] = useState(null);
  const [loadingPlayer, setLoadingPlayer] = useState(false);
  const [cardType, setCardType] = useState("RC");
  const [psaGrade, setPsaGrade] = useState("raw");
  const [parallel, setParallel] = useState("base");
  const [currentPrice, setCurrentPrice] = useState("");
  const [showProjection, setShowProjection] = useState(false);

  const CARD_TYPES = [
    { k: "RC", l: "Rookie Card" },
    { k: "auto", l: "Auto" },
    { k: "auto_rc", l: "Auto RC" },
    { k: "base", l: "Base" },
    { k: "refractor", l: "Refractor" },
  ];

  const PSA_GRADES = [
    { k: "raw", l: "Raw", mult: 1.0 },
    { k: "psa8", l: "PSA 8", mult: 1.8 },
    { k: "psa9", l: "PSA 9", mult: 3.2 },
    { k: "psa10", l: "PSA 10", mult: 7.5 },
    { k: "bgs95", l: "BGS 9.5", mult: 5.0 },
    { k: "bgs10", l: "BGS 10", mult: 12.0 },
  ];

  const PARALLELS = [
    { k: "base", l: "Base", mult: 1.0 },
    { k: "prizm_silver", l: "Prizm Silver", mult: 2.5 },
    { k: "prizm_color", l: "Prizm Color", mult: 4.0 },
    { k: "optic", l: "Optic", mult: 1.8 },
    { k: "superfractor", l: "Superfractor 1/1", mult: 25.0 },
    { k: "numbered_25", l: "/25 Numbered", mult: 8.0 },
    { k: "numbered_10", l: "/10 Numbered", mult: 15.0 },
    { k: "auto_card", l: "Auto Variation", mult: 5.0 },
  ];

  const CARD_TYPE_MULT = { RC: 1.0, auto: 3.5, auto_rc: 6.0, base: 0.4, refractor: 1.8 };

  useEffect(() => {
    if (!search.trim()) { setSearchResults([]); return; }
    const t = setTimeout(() => {
      searchPlayers(search).then(r => setSearchResults(r.slice(0, 6)));
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const selectPlayer = async (p) => {
    setSearch("");
    setSearchResults([]);
    setLoadingPlayer(true);
    setShowProjection(false);
    try {
      const full = await getPlayerStats(p.id);
      const player = full || p;
      const isPitcher = player.primaryPosition?.code === "1";
      const career = await getPlayerCareer(player.id, isPitcher ? "pitching" : "hitting");
      let base, forward;
      if (isPitcher) {
        base = projectPitcher(career, projAge(player), player.fullName, player.id);
        forward = base ? projectPitcherForward(base, projAge(player)) : [];
      } else {
        const splits = career.filter(s => s.stat?.plateAppearances > 0);
        base = projectPlayer(splits, projAge(player), player.primaryPosition?.code, player.fullName, player.id);
        forward = base ? projectForward(base, projAge(player), player.primaryPosition?.code) : [];
      }
      const fv = getPlayerFV(player.id, player.fullName);
      setSelectedPlayer({ ...player, fv });
      setProjection({ base, forward });
    } catch(e) { console.error(e); }
    setLoadingPlayer(false);
  };

  const projectCardValue = () => {
    if (!projection || !currentPrice) return null;
    const price = parseFloat(currentPrice);
    if (isNaN(price) || price <= 0) return null;

    const psaMult = PSA_GRADES.find(g => g.k === psaGrade)?.mult || 1;
    const parallelMult = PARALLELS.find(p => p.k === parallel)?.mult || 1;
    const typeMult = CARD_TYPE_MULT[cardType] || 1;
    const fvBonus = selectedPlayer?.fv ? (selectedPlayer.fv >= 70 ? 2.5 : selectedPlayer.fv >= 65 ? 2.0 : selectedPlayer.fv >= 60 ? 1.6 : selectedPlayer.fv >= 55 ? 1.3 : 1.1) : 1.0;

    const baseWAR = projection.base?.baseWAR || 0;
    const peakWAR = projection.forward?.length ? Math.max(...projection.forward.map(f => f?.war || 0)) : baseWAR;

    return (projection.forward || []).slice(0, 6).map((f, i) => {
      if (!f) return null;
      const yr = PROJ_SEASON + i;
      const war = f.war || 0;

      // Exponential star premium - WAR > 4 gets huge multiplier
      const warMult = war <= 0 ? 0.5 :
        war < 2 ? 0.7 + war * 0.15 :
        war < 4 ? 1.0 + (war - 2) * 0.3 :
        war < 6 ? 1.6 + Math.pow(war - 4, 1.8) * 0.8 :
        1.6 + Math.pow(war - 4, 1.8) * 0.8 + Math.pow(war - 6, 2) * 1.2;

      // Peak proximity bonus - cards peak in value ~1yr before player peaks
      const isPeakYear = Math.abs(war - peakWAR) < 0.3;
      const peakBonus = isPeakYear ? 1.25 : 1.0;

      // FV prospect premium decays as player proves themselves
      const fvDecay = Math.max(1.0, fvBonus - i * 0.15);

      const projectedPrice = price * warMult * peakBonus * fvDecay;

      return {
        year: yr,
        age: (projAge(selectedPlayer) || 25) + i,
        war,
        price: projectedPrice,
        change: ((projectedPrice - price) / price) * 100,
        isPeak: isPeakYear,
      };
    }).filter(Boolean);
  };

  const cardValues = showProjection ? projectCardValue() : null;
  const rec = cardValues ? (
    cardValues[0]?.change > 30 ? { l: "STRONG BUY", c: C.green } :
    cardValues[0]?.change > 10 ? { l: "BUY", c: "#22c55e" } :
    cardValues[0]?.change > -10 ? { l: "HOLD", c: C.accent } :
    { l: "SELL", c: "#ef4444" }
  ) : null;

  return (
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      <Panel title="CARD MARKETPLACE" sub="Project the future value of baseball cards using WAR trajectories">
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
          {/* Left: Player Search */}
          <div>
            <div style={{fontSize:10,fontWeight:700,color:C.muted,fontFamily:F,marginBottom:6}}>PLAYER</div>
            <div style={{position:"relative"}}>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder={selectedPlayer ? selectedPlayer.fullName : "Search player..."}
                style={{width:"100%",padding:"8px 12px",borderRadius:6,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:12,fontFamily:F,outline:"none",boxSizing:"border-box"}}
              />
              {searchResults.length > 0 && (
                <div style={{position:"absolute",top:"100%",left:0,right:0,zIndex:100,background:"#fff",border:`1px solid ${C.border}`,borderRadius:6,boxShadow:"0 4px 12px rgba(0,0,0,0.1)"}}>
                  {searchResults.map(p => (
                    <div key={p.id} onClick={() => selectPlayer(p)}
                      style={{padding:"8px 12px",cursor:"pointer",fontSize:11,fontFamily:F,borderBottom:`1px solid ${C.border}22`,color:C.text}}
                      onMouseOver={e=>e.currentTarget.style.background=C.hover}
                      onMouseOut={e=>e.currentTarget.style.background="transparent"}>
                      {p.fullName} <span style={{color:C.muted,fontSize:9}}>{posLabel(p.primaryPosition?.code)} · {p.currentTeam?.abbreviation||"FA"}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {loadingPlayer && <div style={{fontSize:10,color:C.muted,fontFamily:F,marginTop:6}}>Loading player data...</div>}
            {selectedPlayer && !loadingPlayer && (
              <div style={{marginTop:8,padding:"10px 12px",background:`${C.accent}08`,borderRadius:6,border:`1px solid ${C.accent}20`}}>
                <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
                  <span style={{fontSize:13,fontWeight:700,color:C.text,fontFamily:F}}>{selectedPlayer.fullName}</span>
                  {selectedPlayer.fv && <FVBadge fv={selectedPlayer.fv}/>}
                </div>
                <div style={{fontSize:10,color:C.muted,fontFamily:F}}>
                  {posLabel(selectedPlayer.primaryPosition?.code)} · {selectedPlayer.currentTeam?.name||"FA"} · Age {selectedPlayer.currentAge}
                </div>
                {projection?.base && (
                  <div style={{marginTop:6,display:"flex",gap:12}}>
                    <div><span style={{fontSize:9,color:C.muted,fontFamily:F}}>PROJ WAR</span><div style={{fontSize:13,fontWeight:700,color:C.accent,fontFamily:F}}>{projection.base.baseWAR?.toFixed(1)}</div></div>
                    <div><span style={{fontSize:9,color:C.muted,fontFamily:F}}>PEAK AGE</span><div style={{fontSize:13,fontWeight:700,color:C.blue,fontFamily:F}}>{projection.base.peakAge||"—"}</div></div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right: Card Details */}
          <div>
            <div style={{fontSize:10,fontWeight:700,color:C.muted,fontFamily:F,marginBottom:6}}>CARD DETAILS</div>
            <div style={{display:"flex",flexDirection:"column",gap:8}}>
              <div>
                <div style={{fontSize:9,color:C.muted,fontFamily:F,marginBottom:3}}>CARD TYPE</div>
                <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>
                  {CARD_TYPES.map(t => (
                    <button key={t.k} onClick={() => setCardType(t.k)}
                      style={{padding:"4px 8px",borderRadius:4,border:`1px solid ${cardType===t.k?C.accent:C.border}`,background:cardType===t.k?`${C.accent}15`:"transparent",color:cardType===t.k?C.accent:C.muted,fontSize:9,fontFamily:F,cursor:"pointer",fontWeight:cardType===t.k?700:400}}>
                      {t.l}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <div style={{fontSize:9,color:C.muted,fontFamily:F,marginBottom:3}}>GRADE</div>
                <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>
                  {PSA_GRADES.map(g => (
                    <button key={g.k} onClick={() => setPsaGrade(g.k)}
                      style={{padding:"4px 8px",borderRadius:4,border:`1px solid ${psaGrade===g.k?C.blue:C.border}`,background:psaGrade===g.k?`${C.blue}15`:"transparent",color:psaGrade===g.k?C.blue:C.muted,fontSize:9,fontFamily:F,cursor:"pointer",fontWeight:psaGrade===g.k?700:400}}>
                      {g.l}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <div style={{fontSize:9,color:C.muted,fontFamily:F,marginBottom:3}}>PARALLEL / VARIATION</div>
                <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>
                  {PARALLELS.map(p => (
                    <button key={p.k} onClick={() => setParallel(p.k)}
                      style={{padding:"4px 8px",borderRadius:4,border:`1px solid ${parallel===p.k?C.purple:C.border}`,background:parallel===p.k?`${C.purple}15`:"transparent",color:parallel===p.k?C.purple:C.muted,fontSize:9,fontFamily:F,cursor:"pointer",fontWeight:parallel===p.k?700:400}}>
                      {p.l}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <div style={{fontSize:9,color:C.muted,fontFamily:F,marginBottom:3}}>CURRENT PRICE ($)</div>
                <input
                  type="number"
                  value={currentPrice}
                  onChange={e => setCurrentPrice(e.target.value)}
                  placeholder="e.g. 150"
                  style={{width:"100%",padding:"7px 10px",borderRadius:6,border:`1px solid ${C.border}`,background:"#fff",color:C.text,fontSize:12,fontFamily:F,outline:"none",boxSizing:"border-box"}}
                />
              </div>
              <button
                onClick={() => setShowProjection(true)}
                disabled={!selectedPlayer || !currentPrice}
                style={{padding:"8px 16px",borderRadius:6,border:"none",background:(!selectedPlayer||!currentPrice)?C.border:C.accent,color:"#fff",fontSize:11,fontWeight:700,fontFamily:F,cursor:(!selectedPlayer||!currentPrice)?"not-allowed":"pointer"}}>
                PROJECT VALUE
              </button>
            </div>
          </div>
        </div>

        {/* Projection Results */}
        {showProjection && cardValues && (
          <div style={{marginTop:16,borderTop:`1px solid ${C.border}`,paddingTop:16}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:12}}>
              <div style={{fontSize:12,fontWeight:700,color:C.text,fontFamily:F}}>5-YEAR VALUE PROJECTION</div>
              {rec && <div style={{padding:"4px 12px",borderRadius:4,background:`${rec.c}20`,color:rec.c,fontSize:10,fontWeight:700,fontFamily:F}}>{rec.l}</div>}
            </div>
            <div style={{display:"grid",gridTemplateColumns:"repeat(6,1fr)",gap:8,marginBottom:16}}>
              {cardValues.map((v,i) => (
                <div key={i} style={{padding:"10px 8px",borderRadius:8,border:`1px solid ${v.isPeak?C.accent:C.border}`,background:v.isPeak?`${C.accent}08`:"transparent",textAlign:"center"}}>
                  {v.isPeak && <div style={{fontSize:7,fontWeight:700,color:C.accent,fontFamily:F,marginBottom:2}}>PEAK</div>}
                  <div style={{fontSize:9,color:C.muted,fontFamily:F}}>{v.year}</div>
                  <div style={{fontSize:9,color:C.muted,fontFamily:F,marginBottom:4}}>Age {v.age}</div>
                  <div style={{fontSize:14,fontWeight:700,color:C.text,fontFamily:F}}>${v.price < 1000 ? v.price.toFixed(0) : (v.price/1000).toFixed(1)+"k"}</div>
                  <div style={{fontSize:9,fontWeight:600,color:v.change>=0?C.green:"#ef4444",fontFamily:F}}>{v.change>=0?"+":""}{v.change.toFixed(0)}%</div>
                  <div style={{fontSize:8,color:C.muted,fontFamily:F,marginTop:2}}>{v.war.toFixed(1)} WAR</div>
                </div>
              ))}
            </div>
            <div style={{fontSize:9,color:C.muted,fontFamily:F,lineHeight:1.6,padding:"8px 12px",background:`${C.border}30`,borderRadius:6}}>
              ⚠️ Card value projections are speculative estimates based on WAR trajectory, player age curves, and market premiums. Not financial advice. Card markets are volatile and influenced by many factors beyond on-field performance.
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}


// ── RESEARCH / BLOG ─────────────────────────────────────────────────────────

const BLOG_POSTS = [
  {
    id: "building-viacast",
    date: "March 2026",
    title: "Building VIAcast: A Statcast-Powered Projection Engine",
    tags: ["methodology", "statcast", "projections"],
    summary: "How VIAcast uses 3 years of Baseball Savant data to project every MLB and MiLB player — and what I learned about aging curves, prospect valuation, and the gap between expected stats and outcomes.",
    content: `VIAcast started as a simple question: what if you built a projection engine entirely on Statcast data instead of traditional stats?

Most public projection systems — ZiPS, Steamer, Marcel — anchor on results-based metrics: batting average, ERA, home runs. These are noisy. A hitter can have an identical approach from one year to the next and see his batting average swing by 30 points based on BABIP variance. A pitcher can throw the exact same pitches and watch his ERA balloon because three more fly balls happened to land in seats.

Statcast's expected stats strip away that noise. Expected wOBA (xwOBA) measures the quality of contact and plate discipline directly — what a hitter SHOULD have produced based on exit velocity, launch angle, and barrel rate, regardless of what actually happened. It's the signal underneath the noise.

VIAcast's 7-layer projection system is built on this foundation:

LAYER 1: CONTACT QUALITY (40% weight) — xwOBA is the primary anchor, weighted across 3 seasons at 55/30/15%. Supported by average exit velocity, EV50 (top-half exit velocity), barrel rate, and hard-hit rate. These metrics are among the most stable year-to-year stats in baseball.

LAYER 2: PLATE DISCIPLINE (25%) — K% and BB% from FanGraphs, supplemented by chase rate, zone contact, and swinging-strike rate. When FanGraphs data isn't available, K% is estimated from Statcast whiff rate (K% ≈ whiff% × 0.80). The selectivity index (Z-Swing / O-Swing) identifies elite pitch recognition.

LAYER 3: SWING MECHANICS (10%) — Bat speed and squared-up rate from Statcast bat tracking. Year-over-year bat speed trends detect early aging signals before traditional stats reflect it.

LAYER 4: SPEED & BASERUNNING (10%) — Statcast Baserunning Run Value (BsR) directly measures runs created on the basepaths, accounting for stolen bases, extra bases taken, and the specific pitcher/catcher matchup. For MiLB players, baserunning is derived from SB/CS rates.

LAYER 5: DEFENSE — Outs Above Average (OAA) from Statcast, converted at 0.5 runs per OAA with position-specific aging curves.

LAYER 6: AGING — Single-year forward adjustment applied to wRC+, not multiplicative xwOBA. The key insight: a player's weighted xwOBA already reflects their current age. We only need to project one year of aging delta, not cumulative decline since peak.

LAYER 7: TREND WEIGHTING — Consistent multi-year improvers get amplified trend credit. Chase rate improvements, exit velocity breakouts, and bat speed declines feed momentum adjustments.

For pitchers, WAR is calculated from projected xERA against replacement level (5.34 for starters, 4.49 for relievers), which is more reliable than FIP when K%/BB% data is incomplete.

For MiLB players with fewer than 250 MLB plate appearances, VIAcast uses a Marcel-based engine with level-specific translation factors (AAA 0.82x, AA 0.68x, etc.) blended with FanGraphs Future Value grades. Higher FV prospects get more weight on their grade — a 70 FV like Konnor Griffin isn't going to be dragged down by translated A-ball stats.

VALIDATION: Backtesting against 2025 actual results, VIAcast's wRC+ RMSE of 26.3 is within the ZiPS/Steamer range of 22-28. The xwOBA projection RMSE of 0.034 is at industry standard (0.025-0.035). The engine is systematically conservative — it's strongest on established stars and weakest on breakout candidates, which is a known limitation of regression-based systems.

This is version 1. The roadmap includes rest-of-season projections for the 2026 season, expanded pitcher analytics, and a more sophisticated aging model that accounts for player type (power vs. contact) rather than just position.`
  },
  {
    id: "aging-curves-revisited",
    date: "March 2026",
    title: "Why Shortstops Peak Later Than You Think",
    tags: ["aging", "research", "shortstop"],
    summary: "The conventional wisdom says shortstops peak at 26. Our research — and players like Lindor, Seager, and Turner — suggest the offensive peak is closer to 28.",
    content: `The traditional sabermetric aging curve puts the overall WAR peak for shortstops at age 26. This makes sense when you combine offense and defense — a shortstop's glove peaks early (around 25-26) as speed and range decline, even while the bat continues to develop.

But VIAcast projects offensive performance separately from defense. And when you look at OFFENSIVE peak for shortstops, the picture changes dramatically.

Consider the evidence:

Corey Seager posted a 146 wRC+ at age 28 (2022) and 131 at age 29. Trea Turner hit .298/.343/.466 at age 28. Francisco Lindor had his best OPS season (.809) at age 28. Carlos Correa posted a 145 wRC+ at age 27.

The research supports this. FanGraphs' own aging curve data shows wRC+ peaking around 26-27, but that's heavily influenced by survivor bias — the players who are still playing at 30+ are disproportionately good, which makes the average look like it peaks earlier than it actually does for individual players. Baseball Prospectus research from Bradbury found that hitters overall peak at 29, with slugging peaking at 28.6.

Ray Fair's 2025 study at Yale found the peak age for batters using OPS is 27.49. Not 26.

VIAcast uses the following offensive peaks:
- SS: 28 (was 26 — the biggest change)
- 2B: 28 (was 27)
- 3B: 28 (was 27)
- CF: 27 (unchanged — speed decline is more relevant to CF offense)
- C: 27 (catchers wear down earliest)
- 1B: 29 (pure offense position, late peak)
- DH: 30 (no defensive drain at all)

The impact is significant. Under the old SS peak of 26, a player like Gunnar Henderson (age 24) was projected to peak in just 2 years and start declining. Under peak 28, he gets 4 years of projected improvement — which maps much better to what we actually see from elite young shortstops.

Defense is tracked separately in VIAcast's WAR calculation, with SS/CF defensive peaks set at 26. So the total WAR trajectory still reflects declining range and arm strength. But the bat — the biggest component of WAR for most shortstops — gets the room to develop that the evidence says it should.`
  },
  {
    id: "baserunning-gap",
    date: "March 2026",
    title: "The Baserunning Gap: Why BsR Changes Everything",
    tags: ["methodology", "baserunning", "statcast"],
    summary: "Replacing sprint speed tiers with Statcast Baserunning Run Value reshuffled our WAR leaderboard. Here's who won and who lost.",
    content: `For most of VIAcast's development, baserunning value was estimated using sprint speed tiers. If you ran 29+ ft/s, you got +3.5 runs. Under 26 ft/s, you got -2 runs. Simple, fast, and wrong.

The problem with sprint speed tiers is that they measure capacity, not production. A guy who runs 30 ft/s but never attempts a stolen base and makes poor baserunning decisions isn't actually creating value on the bases. Meanwhile, a 28 ft/s runner with elite instincts and aggressive coaching might be worth more.

Statcast's Baserunning Run Value (BsR) solves this. It measures actual runs created — or lost — via two channels: stolen base value and extra-bases-taken value. Each steal attempt is contextualized against the specific pitcher-catcher battery. Each baserunning opportunity is evaluated against the outfielder's arm strength and the runner's position.

When we integrated BsR data for 252 MLB players, the WAR leaderboard shifted meaningfully.

THE WINNERS

Bobby Witt Jr. jumped the most. His +7.4 BsR translates to roughly 0.8 WAR from baserunning alone. Under the old sprint speed system, he was getting about 0.4 WAR — the BsR integration nearly doubled his baserunning contribution. Witt doesn't just run fast; he runs smart, takes extra bases aggressively, and rarely gets thrown out.

Elly De La Cruz (+8.9 BsR, ~0.9 WAR) and Corbin Carroll (+10.1 BsR, ~1.1 WAR) also saw significant boosts. Carroll leads all of baseball in BsR, and it's not just stolen bases — his extra-bases-taken value is elite, meaning he consistently turns singles into scoring position.

Gunnar Henderson (+6.8 BsR, ~0.7 WAR) was a surprise gainer. He's not typically thought of as a speed threat, but his baserunning decisions are consistently positive.

THE LOSERS

Aaron Judge dropped. His -3.6 BsR costs him roughly 0.4 WAR. Under the old sprint speed system, his 27.5 ft/s speed put him in a neutral tier. In reality, he's a below-average baserunner who occasionally gets thrown out trying to take extra bases, and his size makes him a poor stolen base threat.

The broader pattern: speed doesn't equal value. BsR captures the difference between players who convert their athleticism into runs and those who don't. For a projection engine trying to estimate total player value, that distinction matters.

THE FALLBACK

For MiLB players without BsR data, VIAcast still uses sprint speed tiers as a proxy. It's imperfect, but until Statcast tracking expands to all minor league parks, it's the best available option. As more BsR data becomes available, the fallback will apply to fewer players.

The takeaway: baserunning is a meaningful component of player value, and measuring it correctly can swing a projection by nearly a full win. That's the difference between a 5 WAR player and a 6 WAR player — which is the difference between an All-Star and an MVP candidate.`
  },
  {
    id: "prospect-fv-blend",
    date: "March 2026",
    title: "Projecting Prospects: How VIAcast Blends Stats and Scouting Grades",
    tags: ["prospects", "methodology", "FV"],
    summary: "A 70 FV prospect with 118 MLB plate appearances shouldn't project like a league-average player. Here's how VIAcast solves the small-sample problem.",
    content: `The hardest problem in baseball projection is the prospect problem.

Take Samuel Basallo. He's a 65 FV prospect — FanGraphs' scouting department says he profiles as a perennial All-Star. He hit 23 HR with a .966 OPS in AAA at age 20. Then he got called up to Baltimore and posted a .286 xwOBA in 118 plate appearances.

If you only look at the MLB stats, Basallo projects as a below-average hitter. If you only look at the scouting grade, he projects as a star. The truth is somewhere in between, but figuring out exactly where requires a framework.

VIAcast uses what we call the FV Blend — a weighted combination of translated statistical performance and FanGraphs Future Value benchmarks.

HOW THE BLEND WORKS

For any player with an FV grade and fewer than 400 MLB plate appearances, VIAcast computes two OPS estimates:

1. Stats OPS: Career MiLB stats translated to MLB equivalents using level-specific factors (AAA 0.82x, AA 0.68x, etc.), regressed toward league average based on sample size.

2. FV Benchmark OPS: The historical MLB outcome for that FV tier. A 65 FV projects to .880 OPS at peak. A 60 FV projects to .830. A 70 FV projects to .960.

The final OPS is a weighted blend: finalOPS = statsOPS × statWeight + benchOPS × fvWeight.

The key innovation: higher FV grades get more FV weight. A 70 FV prospect like Konnor Griffin gets 20% additional FV weight because scouting consensus at that tier is extremely predictive. A 55 FV gets no additional boost — the grade carries less certainty.

WHY THE SLASH LINE HAS TO MATCH

Early versions of VIAcast had a bug where wRC+ was boosted by the FV blend but the displayed OBP/SLG weren't. You'd see a prospect with 120 wRC+ but .712 OPS — numbers that can't coexist. A 120 wRC+ implies roughly .790-.800 OPS.

The fix: when the FV blend boosts OPS, the slash line now scales proportionally. The boost splits 40/60 between OBP and SLG, reflecting that prospect upside is more power-driven than patience-driven. HR also scales with the SLG increase.

THE WAR FLOOR

The other piece of the FV puzzle is the WAR clamp. Without it, a 70 FV prospect with a terrible 50-PA MLB sample could project for 1.0 WAR — which contradicts what the scouting grade means.

VIAcast sets the WAR floor at 50% of the FV benchmark:
- 70 FV: 4.0 WAR minimum (benchmark: 8.0)
- 65 FV: 2.8 WAR minimum (benchmark: 5.5)
- 60 FV: 2.0 WAR minimum (benchmark: 4.0)
- 55 FV: 1.4 WAR minimum (benchmark: 2.8)

These floors are conservative — they represent the low end of what a player at that tier should produce. But they prevent the embarrassing outcome of projecting the best prospect in baseball for 1.2 WAR because he had a rough 30-game audition.

WHAT THIS MEANS FOR SPECIFIC PLAYERS

Basallo (65 FV): His translated MiLB stats are strong, and the 65 FV benchmark pulls his projection to ~120 wRC+ with a .790 OPS. The WAR floor of 2.8 provides a safety net, but his stats-based projection actually exceeds it.

Konnor Griffin (70 FV): With no MLB data at all, his projection is almost entirely FV-driven. The .960 benchmark OPS and 4.0 WAR floor reflect the scouting consensus that he's the best prospect in baseball.

Jackson Holliday (60 FV, ~850 MLB PA): With more MLB data, the blend trusts his stats more and the FV less. He's transitioning from prospect to established player in the engine's eyes.

The FV blend isn't perfect. Scouting grades are subjective, and FanGraphs occasionally misses. But for small-sample prospects, it's far better than pure statistical regression, which would project every 100-PA callup as a league-average hitter.`
  },
  {
    id: "xera-vs-fip",
    date: "March 2026",
    title: "Why VIAcast Uses xERA Instead of FIP for Pitcher WAR",
    tags: ["pitching", "methodology", "statcast"],
    summary: "Most projection systems anchor pitcher WAR on FIP. VIAcast uses xERA instead. Here's the case for expected ERA as a better projection anchor.",
    content: `FIP (Fielding Independent Pitching) has been the gold standard for pitcher evaluation for over a decade. It strips out the things a pitcher can't control — defense, sequencing, luck on balls in play — and focuses on strikeouts, walks, and home runs.

For historical evaluation, FIP is excellent. But for projection, it has a blind spot that matters: it ignores contact quality.

Two pitchers can have identical K%, BB%, and HR rates but be vastly different pitchers. One might induce weak grounders and lazy fly balls. The other might get hit hard but have the ball land in gloves. FIP treats them the same. The market shouldn't.

This is where xERA (Expected ERA) comes in.

WHAT xERA CAPTURES THAT FIP DOESN'T

xERA is built on Statcast's expected stats framework. It takes every batted ball a pitcher allows and assigns an expected outcome based on exit velocity and launch angle. A 110 mph line drive is expected to be a hit. A 75 mph grounder is expected to be an out. The pitcher gets credit or blame for the quality of contact they allow, regardless of what actually happened.

This means xERA captures:
- Contact management (barrel% allowed, hard-hit%, avg EV against)
- Ground ball tendency (which suppresses HR independent of HR/FB rate)
- Quality of weak contact (not all outs are created equal)

FIP captures none of this. A pitcher who allows a .250 xBA on contact and a .350 xBA on contact look identical in FIP if their K/BB/HR rates match.

THE PRACTICAL DIFFERENCE

In VIAcast's pitcher projections, the choice of anchor matters most for pitchers with elite contact management. Adrian Morejon is the poster child: his 2025 xERA was 1.71 (1st in baseball), driven by a 2.7% barrel rate and 25.4% hard-hit rate — both best in MLB. His FIP was good but not historic, because his strikeout rate was merely above-average.

A FIP-based system would project Morejon as a solid mid-rotation arm. An xERA-based system sees one of the most effective run preventers in the sport.

The reverse also applies. A pitcher with a great K rate but who gets barreled frequently will have a better FIP than xERA. VIAcast would project them for regression — which is usually correct.

THE K%/BB% DATA GAP

There's a practical reason too. VIAcast's Statcast data pipeline doesn't always have clean K% and BB% data from FanGraphs (the primary source for plate discipline metrics). For many pitchers, K% has to be estimated from whiff rate (K% ≈ whiff% × 0.80). Since FIP requires precise K and BB counts, an estimated FIP is less reliable than xERA, which comes directly from Statcast's batted ball data.

WHERE FIP STILL SHOWS UP

VIAcast does compute FIP for every pitcher — it's displayed on the player card alongside xERA-based WAR. This gives users the full picture: the xERA projection tells you what VIAcast thinks will happen, and the FIP provides a cross-reference from the traditional framework.

For the Marcel engine (which handles pitchers without Statcast data), FIP is actually the WAR anchor, since translated MiLB data doesn't include batted ball quality metrics. This is a known limitation — as Statcast expands to more minor league parks, the xERA advantage will extend to prospect pitchers too.

The bottom line: for MLB pitchers with Statcast data, contact quality is too important to ignore. xERA captures it. FIP doesn't. That's why VIAcast builds pitcher WAR on expected ERA.`
  },
  {
    id: "defense-tax",
    date: "March 2026",
    title: "The Defense Tax: How OAA Reshuffles the WAR Leaderboard",
    tags: ["defense", "methodology", "statcast"],
    summary: "At 0.5 runs per OAA, defense can swing a player's WAR by 1-2 wins. Here's how VIAcast handles the most volatile component of player value.",
    content: `Defense is the noisiest component of WAR. A hitter's wRC+ is relatively stable year-to-year. A pitcher's xERA regresses predictably. But a fielder's OAA can swing wildly — and even one season of elite or terrible defense can dramatically change a projection.

VIAcast converts Outs Above Average at 0.5 runs per OAA. This is deliberately conservative. Some models use higher conversion rates (0.7-0.9 runs per OAA), but we found those rates inflate defensive contributions beyond what the data supports when backtested against full-season WAR.

THE CALIBRATION PROBLEM

Our original defense formula used OAA × 0.6 × 1.5, which works out to 0.9 runs per OAA. For Bobby Witt Jr. (21.9 OAA), that produced 19.7 defensive runs — over 2 full WAR from defense alone. His total projection hit 8.6 WAR, which would make him the best position player in baseball by a wide margin.

That didn't pass the smell test. Witt is an elite defender, but 2.1 dWAR from a single season's OAA is historically rare. Andrelton Simmons at his peak managed about 3.0-3.5 dWAR, and he's considered one of the best defensive shortstops ever measured.

Dropping to 0.5 runs per OAA brought Witt's defensive contribution to 11.0 runs (1.2 dWAR). His total projection landed at 7.8 WAR — still the top position player in our system, but driven by a realistic combination of offense, baserunning, and defense rather than defense alone.

DEFENSIVE AGING

Defense ages faster than offense. VIAcast tracks defensive peaks separately from offensive peaks:
- SS and CF peak defensively at 26
- Corner infielders at 27
- Corner outfielders at 28

After the defensive peak, fielding value decays at 6% per year. A shortstop who was +15 OAA at age 26 would be projected at roughly +12 OAA by age 28 and +9 by age 30 — even if their offensive peak hasn't arrived yet.

This creates interesting projection dynamics. A 24-year-old shortstop like Gunnar Henderson is still improving offensively (peak at 28) but will start declining defensively soon (peak at 26). His total WAR trajectory reflects both curves, which is why his projected WAR peaks around age 27 — the sweet spot where both offense and defense are near their best.

WHO BENEFITS, WHO DOESN'T

The biggest defensive beneficiaries in VIAcast's system are premium-position players with plus OAA: Witt (+1.2 dWAR), Henderson, Francisco Lindor, and Elly De La Cruz all get meaningful WAR boosts from their glove work.

The biggest losers are bat-first players at premium positions with negative OAA. CJ Abrams (-13.4 OAA) loses about 0.7 WAR from defense. Juan Soto (-9.2 OAA) takes a similar hit — partly offset by playing a less demanding position.

DH-only players like Yordan Alvarez and designated hitters receive no defensive value but also no defensive penalty. However, the DH positional adjustment (-17.5 runs per 600 PA) is the harshest in the system, reflecting the opportunity cost of a roster spot that contributes nothing in the field.

Defense remains the component of WAR that we're least confident in projecting forward. OAA can be volatile, and a single season's data is noisier than three years of Statcast batting data. But ignoring it entirely — as some simpler projection models do — systematically undervalues elite defenders and overvalues poor ones. The 0.5 conversion rate is our current best estimate of the signal-to-noise ratio.`
  },
  {
    id: "counting-stats-approach",
    date: "March 2026",
    title: "Counting Stats for Prospects: A Games-First Approach",
    tags: ["prospects", "methodology", "HR"],
    summary: "Why VIAcast projects games played first and derives plate appearances and home runs from there — and how MiLB HR translation prevents power inflation.",
    content: `Early versions of VIAcast had a counting-stat problem. Samuel Basallo — a 65 FV catcher with 23 HR in AAA — was projecting for 15 HR in his first full MLB season. Jackson Merrill and Jackson Chourio, despite very different barrel rates, both projected for exactly 28 HR.

These numbers didn't pass scrutiny. Basallo's HR total was too low for his power profile. Merrill and Chourio converging to the same number suggested a formula artifact, not a real projection. Both problems had different root causes, but the fix for each started with the same principle: project playing time first, then derive counting stats from rate stats.

THE GAMES-FIRST APPROACH

Instead of projecting PA from career averages and then scaling HR to match, VIAcast now projects games played based on position and level:
- Catchers: 120 games (catchers need rest days)
- Position players: 140 games (typical for a projected starter)
- Established MLB players: based on actual recent game history

Plate appearances are then derived: PA = projected games × 4.0 PA/G (the MLB average). This ensures PA and games are always internally consistent — you won't see a player with 140 games but 170 PA.

THE MiLB HR TRANSLATION

The second piece was translating minor league home runs. A player who hits 23 HR in AA doesn't project for 23 HR in MLB. AA ball has different pitch quality, park factors, and competitive level. VIAcast now applies the same translation factors to HR that it applies to other stats:
- AAA HR × 0.82
- AA HR × 0.68
- High-A HR × 0.58
- Single-A HR × 0.50

So Basallo's 23 AA/AAA HR become roughly 17 translated HR. At a rate of 17 HR per 125 MiLB games, that's 0.136 HR/game. Multiply by 120 projected games (catcher) and you get about 16 base HR. Add the FV SLG boost (his 65 FV grade pushes projected SLG above the baseline) and you land around 22-24 HR — right in line with ZiPS and Steamer.

THE CONVERGENCE FIX

The Chourio/Merrill/Holliday convergence to 28 HR had a different cause. The Statcast HR formula for MLB players uses barrel rate and a non-barrel baseline:

HR = barrel% × BBE × 0.45 + PA × baseline

The original baseline was 0.018 HR per PA — about 11 non-barrel HR per full season. This was too aggressive. It made plate appearances the dominant driver of HR totals, overwhelming the barrel-rate differences between players. A low-barrel guy with lots of PA could match a high-barrel guy with fewer PA.

Reducing the baseline to 0.010 restored barrel rate as the primary differentiator. The non-barrel contribution dropped to about 6-7 HR per season, which is more empirically grounded — most home runs come from barreled balls, and the non-barrel HR rate should be modest.

WHAT THE NUMBERS LOOK LIKE NOW

The games-first approach produces internally consistent projections:
- Basallo: 120G, 480 PA, ~22 HR (was 100G, 170 PA, 15 HR)
- Chourio: 140G, 560 PA, ~23 HR (was 28, same as everyone else)
- Merrill: 140G, 560 PA, ~24 HR (differentiated by higher barrel rate)
- Holliday: 140G, 560 PA, ~23 HR (appropriately lower barrel rate)

These aren't perfect — no preseason projection is. But they're internally consistent, position-appropriate, and differentiated by the underlying skills that drive power production.`
  },

  // ── TrevKnowsBall Archive (July-September 2025) ──
  {
    id: "trent-grisham-rise",
    date: "September 3, 2025",
    title: "The Rise of Trent Grisham",
    tags: ["player analysis", "breakout"],
    summary: "From role player to game-changer. How Grisham's retooled approach turned him into a legitimate contributor.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/09/role-player-to-game-changer-rise-of.html",
  },
  {
    id: "jhoan-duran-closer",
    date: "August 11, 2025",
    title: "Jhoan Duran is The Game's Most Untouchable Closer",
    tags: ["pitching", "statcast", "reliever"],
    summary: "Breaking down Duran's arsenal and why his pitch mix makes him virtually unhittable. Statcast data tells the story.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/jhoan-duran-is-games-most-untouchable.html",
  },
  {
    id: "tatis-just-fine",
    date: "August 9, 2025",
    title: "Fernando Tatis Jr. is Just Fine, Guys",
    tags: ["player analysis", "statcast"],
    summary: "Despite the noise, Tatis's underlying metrics show a player who's still elite. The expected stats back it up.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/fernando-tatis-jr-is-just-fine-guys.html",
  },
  {
    id: "schwarber-nl-mvp",
    date: "August 7, 2025",
    title: "Kyle Schwarber is Your NL MVP",
    tags: ["player analysis", "MVP"],
    summary: "The case for Schwarber as the National League's most valuable player, backed by production and advanced metrics.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/kyle-schwarber-is-your-nl-mvp.html",
  },
  {
    id: "bo-bichette-back",
    date: "August 5, 2025",
    title: "Bo Bichette is Back in Business",
    tags: ["player analysis", "statcast", "breakout"],
    summary: "After a disastrous 2024, Bichette has re-emerged with a 125 wRC+ and career-high 48.7% hard-hit rate. The rebound is real.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/bo-bichette-hasnt-just-bounced-back-hes.html",
  },
  {
    id: "hunter-brown-peaks-valleys",
    date: "August 4, 2025",
    title: "Hunter Brown's Season of Peaks & Valleys",
    tags: ["pitching", "statcast", "breakout"],
    summary: "From 28 consecutive scoreless innings to a July slump and back again. Tracking Brown's 2025 through Statcast.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/hunter-browns-season-of-peaks-valleys.html",
  },
  {
    id: "max-clark-prospect",
    date: "August 2, 2025",
    title: "Max Clark Punches Way Above His Age",
    tags: ["prospects", "scouting"],
    summary: "At age 20, Clark is slashing .323/.386/.581 in Double-A with elite plate discipline. Breaking down why his FV 60 grade might be conservative.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/max-clark-punches-way-above-his-age.html",
  },
  {
    id: "adrian-morejon-dream",
    date: "August 1, 2025",
    title: "Adrian Morej\u00f3n, A Front Office's Dream Player",
    tags: ["pitching", "statcast", "value"],
    summary: "Ranked 1st in xERA, avg EV, xSLG, xwOBA, barrel%, and hard-hit% among pitchers with 80+ IP. At $2M salary, he's the most cost-efficient pitcher in baseball.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/adrian-morejon-is-on-absolute-tear.html",
  },
  {
    id: "will-smith-best-hitter",
    date: "July 31, 2025",
    title: "Will Smith Is The Best Hitter We Don't Talk About",
    tags: ["player analysis", "statcast", "catcher"],
    summary: "Six straight years of 120+ wRC+ from the catcher position. 92nd percentile xwOBA, 83rd percentile chase rate. Smith is quietly elite.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/07/will-smith-is-best-hitter-we-dont-talk.html",
  },
  {
    id: "matthew-boyd-shoving",
    date: "July 30, 2025",
    title: "Matthew Boyd is Shoving, What's Changed?",
    tags: ["pitching", "breakout"],
    summary: "A 34-year-old lefty has become the ace of a first-place Cubs team. The Statcast page confirms this isn't smoke and mirrors.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/07/you-know-i-had-to-squeeze-some-alonso.html",
  },
  {
    id: "langeliers-breakout",
    date: "July 29, 2025",
    title: "Shea Langeliers is Quietly Having His Best Season Yet",
    tags: ["player analysis", "statcast", "catcher"],
    summary: "Career-high power numbers backed by a 11.1% barrel rate and xwOBA matching his actual production. Oakland's cornerstone is arriving.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/07/langeliers-quietly-having-his-best.html",
  },
];

function ResearchPanel() {
  const [selectedPost, setSelectedPost] = useState(null);

  if (selectedPost) {
    const post = BLOG_POSTS.find(p => p.id === selectedPost);
    if (!post) return null;
    return (
      <div style={{display:"flex",flexDirection:"column",gap:14}}>
        <button onClick={() => setSelectedPost(null)} style={{
          alignSelf:"flex-start",padding:"6px 14px",borderRadius:6,border:`1px solid ${C.border}`,
          background:"transparent",color:C.dim,fontSize:11,fontFamily:F,cursor:"pointer",
        }}>&larr; Back to Research</button>
        <Panel>
          <div style={{maxWidth:720,margin:"0 auto"}}>
            <div style={{fontSize:9,color:C.accent,fontFamily:F,fontWeight:700,letterSpacing:".1em",textTransform:"uppercase",marginBottom:8}}>{post.date}</div>
            <h2 style={{margin:"0 0 12px",fontSize:22,color:C.navy,fontFamily:F,lineHeight:1.3}}>{post.title}</h2>
            <div style={{display:"flex",gap:6,marginBottom:20,flexWrap:"wrap"}}>
              {post.tags.map(t => <span key={t} style={{fontSize:9,padding:"3px 8px",borderRadius:4,background:`${C.accent}10`,color:C.accent,fontFamily:F,fontWeight:600}}>{t}</span>)}
            </div>
            <div style={{fontSize:13,color:C.dim,fontFamily:F,lineHeight:2.0,whiteSpace:"pre-wrap"}}>
              {post.content.split("\n\n").map((para, i) => {
                // Check if paragraph is a header-like line (ALL CAPS or starts with specific patterns)
                const isHeader = /^[A-Z][A-Z ]+:/.test(para) || /^LAYER \d/.test(para) || /^VALIDATION:/.test(para);
                if (isHeader) {
                  const [head, ...rest] = para.split(": ");
                  return <p key={i} style={{margin:"20px 0 8px"}}><span style={{fontWeight:800,color:C.navy,fontSize:13}}>{head}:</span> {rest.join(": ")}</p>;
                }
                return <p key={i} style={{margin:"0 0 16px"}}>{para}</p>;
              })}
            </div>
          </div>
        </Panel>
      </div>
    );
  }

  return (
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      <Panel title="RESEARCH" sub="Analysis, methodology deep-dives, and projection insights." style={{borderTop:`3px solid ${C.accent}`}}>
        <p style={{fontSize:12,color:C.dim,fontFamily:F,lineHeight:1.7,margin:"0 0 16px"}}>
          Original research on baseball projections, aging curves, prospect valuation, and Statcast methodology. Written by <span style={{color:C.text,fontWeight:600}}>Trevan Via</span>.
        </p>
      </Panel>
      <div style={{display:"flex",flexDirection:"column",gap:12}}>
        {BLOG_POSTS.map(post => (
          <Panel key={post.id} style={{cursor:"pointer",transition:"all 0.15s"}}
            onClick={() => post.externalUrl ? window.open(post.externalUrl, '_blank') : setSelectedPost(post.id)}
            onMouseEnter={e => {e.currentTarget.style.borderColor=C.accent;e.currentTarget.style.transform="translateY(-1px)";}}
            onMouseLeave={e => {e.currentTarget.style.borderColor=C.border;e.currentTarget.style.transform="none";}}>
            <div style={{display:"flex",gap:16,alignItems:"flex-start"}}>
              <div style={{flex:1}}>
                <div style={{fontSize:9,color:C.accent,fontFamily:F,fontWeight:700,letterSpacing:".1em",textTransform:"uppercase",marginBottom:6}}>{post.date}</div>
                <h3 style={{margin:"0 0 8px",fontSize:16,color:C.navy,fontFamily:F,lineHeight:1.3}}>{post.title}</h3>
                <p style={{margin:"0 0 10px",fontSize:12,color:C.dim,fontFamily:F,lineHeight:1.6}}>{post.summary}</p>
                <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
                  {post.tags.map(t => <span key={t} style={{fontSize:9,padding:"2px 7px",borderRadius:4,background:`${C.accent}08`,color:C.accent,fontFamily:F,fontWeight:600}}>{t}</span>)}
                </div>
              </div>
              <div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:4,paddingTop:4}}>
                <span style={{fontSize:18,color:C.border,fontFamily:F}}>{post.externalUrl ? "↗" : "→"}</span>
                {post.externalUrl && <span style={{fontSize:7,color:C.muted,fontFamily:F,whiteSpace:"nowrap"}}>TrevKnowsBall</span>}
              </div>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}

function MethodPanel() {
  const h4 = (color,text,mt) => <h4 style={{color,fontSize:13,margin:`${mt||0}px 0 4px`,fontFamily:F}}>{text}</h4>;
  const pp = (text,mb) => <p style={{margin:`0 0 ${mb||12}px`,fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F}}>{text}</p>;
  return <div style={{display:"flex",flexDirection:"column",gap:14}}>

    {/* 1. FUTURE VALUE SCALE */}
    <Panel title="FUTURE VALUE SCALE">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:6}}>
        {[70,65,60,55,50,45,40].map(fv=>{const s=getFVStyle(fv);return(
          <div key={fv} style={{padding:"10px 12px",borderRadius:6,border:`1px solid ${C.border}`}}>
            <div style={{marginBottom:6}}><FVBadge fv={fv}/></div>
            <div style={{fontSize:9,color:C.muted,fontFamily:F}}>
              {fv>=70?"Franchise Player":fv>=65?"Perennial All-Star":fv>=60?"All-Star upside":fv>=55?"Above-avg regular":fv>=50?"Avg regular":fv>=45?"Solid backup":fv>=40?"Fringe MLB":"\u2014"}
            </div>
          </div>
        );})}
      </div>
      <p style={{margin:"10px 0 0",fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Prospects with FV grades and fewer than 400 MLB PA get a weighted FV blend. Higher FV grades receive more weight (70 FV +20%, 65 +12%, 60 +6%). WAR floor is set at 50% of the FV benchmark. Slash lines scale proportionally with the FV-boosted OPS.</p>
    </Panel>

    {/* 2. VALUE PER DOLLAR SCALE */}
    <Panel title="VALUE PER DOLLAR (VpD)">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(100px,1fr))",gap:6}}>
        {[
          {g:"A+",t:"4.0+",c:"#10b981"},{g:"A",t:"2.0\u20134.0",c:"#22c55e"},{g:"A-",t:"1.0\u20132.0",c:"#84cc16"},
          {g:"B+",t:"0.60\u20131.0",c:"#eab308"},{g:"B",t:"0.40\u20130.60",c:"#f59e0b"},{g:"B-",t:"0.25\u20130.40",c:"#fb923c"},
          {g:"C+",t:"0.18\u20130.25",c:"#fbbf24"},{g:"C",t:"0.13\u20130.18",c:"#94a3b8"},
          {g:"D",t:"0.08\u20130.13",c:"#ef4444"},{g:"F",t:"< 0.08",c:"#dc2626"},
        ].map(v=><div key={v.g} style={{padding:"8px 10px",borderRadius:6,border:`1px solid ${v.c}30`,background:`${v.c}08`}}>
          <div style={{fontSize:16,fontWeight:800,color:v.c,fontFamily:F}}>{v.g}</div>
          <div style={{fontSize:9,color:C.muted,fontFamily:F,marginTop:2}}>{v.t} WAR/$M</div>
        </div>)}
      </div>
      <p style={{margin:"10px 0 0",fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Projected WAR per $1M salary. Pre-arb players at league minimum ($0.8M) naturally receive top grades. Salary data from Spotrac, MLB Trade Rumors, and Cot{"\u2019"}s Baseball Contracts.</p>
    </Panel>

    {/* 3. PROJECTION METHODOLOGY — two columns */}
    <Panel title="PROJECTION METHODOLOGY">
      <p style={{margin:"0 0 14px",fontSize:12,color:C.dim,lineHeight:1.6,fontFamily:F}}>VIAcast projects hitters and pitchers through separate Statcast-powered engines, calibrated against FanGraphs Depth Charts (ZiPS/Steamer blend) as a benchmark. Both use 3 years of data (2023{"\u2013"}2025) weighted 55/30/15% with sample-size reliability scaling. Players below the Statcast threshold (250 MLB PA) use the Marcel fallback with MiLB translation. Projected WAR is displayed as fWAR for direct comparability with industry-standard systems.</p>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(320px,1fr))",gap:16}}>

        {/* HITTER COLUMN */}
        <div style={{fontSize:12,color:C.dim,lineHeight:1.7,fontFamily:F}}>
          <div style={{fontSize:11,fontWeight:800,color:C.accent,letterSpacing:".1em",textTransform:"uppercase",marginBottom:10,paddingBottom:6,borderBottom:`2px solid ${C.accent}20`,fontFamily:F}}>HITTER ENGINE (7 LAYERS)</div>

          {h4(C.blue,"L1: Contact Quality (40%)")}
          {pp("xwOBA anchor weighted across 3 seasons. Supported by avg exit velocity, EV50, barrel rate, and hard-hit rate from Statcast. xSLG is deflated 5% before regression to correct for Statcast\u2019s systematic overestimation of realized slugging (~5% gap league-wide).")}

          {h4(C.purple,"L2: Plate Discipline (25%)")}
          {pp("K% and BB% from FanGraphs. Chase rate, zone contact, and swinging-strike rate feed a selectivity index (Z-Swing/O-Swing) for pitch recognition. Discipline bonus of up to \u00b15 wRC+ points for elite/poor selectivity.")}

          {h4("#ec4899","L3: Swing Mechanics (10%)")}
          {pp("Bat speed and squared-up rate from Statcast bat tracking. YoY bat speed trends detect early aging signals before traditional stats reflect it.")}

          {h4(C.green,"L4: Baserunning (10%)")}
          {pp("Statcast BsR (Baserunning Run Value) for MLB players, regressed 25% toward league average to dampen single-season volatility. Fallback: sprint speed tiers for MLB, SB/CS rates for MiLB.")}

          {h4(C.orange,"L5: Defense")}
          {pp("OAA (Outs Above Average) at 0.85 runs per OAA (standard Statcast methodology), blended 80/20 with DRS directional (\u00b13 runs). Defensive peaks: SS/CF at 26, corners at 28. Decays 6%/yr past peak.")}

          {h4(C.text,"L6: Aging Curves")}
          {pp("Pre-peak development boost: +0.8% AVG and +1.0% SLG per year to peak (capped at 4%/6%). Post-peak: AVG declines 0.8%/yr past 32, SLG declines 1.5%/yr past 30. Position-specific peaks: SS/2B/3B 28, CF/C 27, 1B 29, DH 30.")}

          {h4(C.blue,"L7: Trend Weighting")}
          {pp("Consistent multi-year improvers get +30% trend credit. Chase rate improvements, EV50 breakouts, and bat speed declines feed momentum adjustments.")}

          {h4(C.green,"fWAR Construction")}
          {pp("Slash line projected from xBA/xSLG with PA-aware regression (15\u201350% toward league avg). xSLG deflated 5% before regression. wOBA estimated via FanGraphs quick formula: (1.7\u00d7OBP + SLG) / 3. wRC+ derived from wOBA \u2192 wRAA \u2192 wRC+ (league avg calibrated to 100). Batting runs = ((wRC+ \u2212 100) / 100) \u00d7 PA \u00d7 0.115. Total: batting + defense + BsR + positional adj + replacement (20 runs/600 PA) \u00f7 9.5 RPW.")}

          <div style={{marginTop:8,padding:"10px 14px",background:`${C.blue}06`,border:`1px solid ${C.blue}15`,borderRadius:8}}>
            <div style={{fontSize:10,fontWeight:700,color:C.blue,fontFamily:F,marginBottom:4}}>NON-FV PROSPECT CEILING</div>
            <div style={{fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Players without FV grades and fewer than 200 MLB PA are capped at 120 wRC+ and .800 OPS. This prevents unconstrained MiLB projections from producing unrealistic star-level projections for ungraded prospects.</div>
          </div>
        </div>

        {/* PITCHER COLUMN */}
        <div style={{fontSize:12,color:C.dim,lineHeight:1.7,fontFamily:F}}>
          <div style={{fontSize:11,fontWeight:800,color:C.accent,letterSpacing:".1em",textTransform:"uppercase",marginBottom:10,paddingBottom:6,borderBottom:`2px solid ${C.accent}20`,fontFamily:F}}>PITCHER ENGINE (5 LAYERS)</div>

          {h4(C.blue,"L1: ERA Anchor \u2014 Layered (35%)")}
          {pp("Falls through in order of predictive accuracy: SIERA \u2192 xFIP \u2192 xERA \u2192 FIP \u2192 K-BB \u2192 ERA. SIERA from FanGraphs is primary, accounting for K/BB/GB interactions. Pitchers without FG data fall back to xERA from Statcast.")}

          {h4(C.purple,"L2: Command (25%)")}
          {pp("K% and BB% sourced from FanGraphs. Fallback: whiff% \u00d7 1.05. FIP computed from projected K, BB, and HR allowed (HR rate derived from barrel% against).")}

          {h4(C.orange,"L3: Velocity (15%)")}
          {pp("Fastball velocity trends across seasons. Velocity loss >1.5 mph adds 0.15 ERA points. Velocity gain >1.0 mph subtracts 0.10.")}

          {h4(C.text,"L4: Aging Curves")}
          {pp("Pre-peak: \u22121.5% ERA/yr. Peak\u201333: +1.5%/yr. 33+: +3%/yr. SP peak at 27, RP peak at 28.")}

          {h4(C.green,"L5: IP Projection")}
          {pp("Best full season (100+ IP) from FanGraphs data with age adjustment. Injury detection: if most recent season was <80 IP (checked in both Savant and FG data), projection capped at 150 IP. Manual IP overrides for known injured pitchers returning from surgery (e.g. Wheeler 120 IP, McClanahan 130 IP).")}

          {h4(C.green,"fWAR Construction \u2014 Blended")}
          {pp("60% xERA-based + 40% FIP-based WAR. xERA captures contact quality (barrel%, hard-hit%) that FIP ignores. FIP captures K/BB/HR skill that xERA can miss in small samples. SP replacement level: 5.34, RP: 4.49, divided by 9.5 RPW.")}

          {h4(C.blue,"Starter Detection")}
          {pp("Pitchers are classified as SP if: career max IP >100, or season BFP >450, or FV grade \u226550. This ensures top pitcher prospects (McLean, Yesavage) project as starters even with limited MLB innings.")}

          <div style={{marginTop:8,padding:"10px 14px",background:`${C.accent}06`,border:`1px solid ${C.accent}15`,borderRadius:8}}>
            <div style={{fontSize:10,fontWeight:700,color:C.accent,fontFamily:F,marginBottom:4}}>MARCEL FALLBACK</div>
            <div style={{fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Players below 250 Statcast PA use Marcel with MiLB translation (AAA 0.82x, AA 0.68x, A+ 0.58x, A 0.50x). wRC+ computed from wOBA via (1.7{"\u00d7"}OBP + SLG) / 3. Established MLB threshold: 250 PA.</div>
          </div>

          <div style={{marginTop:8,padding:"10px 14px",background:`${C.purple}06`,border:`1px solid ${C.purple}15`,borderRadius:8}}>
            <div style={{fontSize:10,fontWeight:700,color:C.purple,fontFamily:F,marginBottom:4}}>TWO-WAY PLAYERS</div>
            <div style={{fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Two-way players (Ohtani) receive a workload discount: 92% of projected hitting PA, 72% of projected pitching IP. Based on Ohtani{"\u2019"}s 2023 actuals (599 PA + 132 IP). Combined fWAR is synced across player card, leaderboard, and landing page.</div>
          </div>
        </div>
      </div>
    </Panel>

    {/* 4. MINOR LEAGUE TRANSLATION */}
    <Panel title="MINOR LEAGUE TRANSLATION">
      <p style={{fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F,margin:"0 0 12px"}}>
        MiLB stats are <span style={{color:C.text}}>not directly comparable</span> to MLB. The system applies level-specific translation factors derived from historical promotion data:
      </p>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(140px,1fr))",gap:6}}>
        {LEVEL_ORDER.map(lvl=>{const t=LEVEL_TRANSLATION[lvl];return <div key={lvl} style={{padding:"10px 12px",background:`${LEVEL_COLORS[lvl]}08`,border:`1px solid ${LEVEL_COLORS[lvl]}20`,borderRadius:6}}>
          <div style={{fontSize:15,fontWeight:800,color:LEVEL_COLORS[lvl],fontFamily:F}}>{lvl}</div>
          <div style={{fontSize:10,color:C.dim,fontFamily:F,marginTop:4}}>{t.label}</div>
          <div style={{fontSize:10,color:C.muted,fontFamily:F,marginTop:2}}>Stat multiplier: <span style={{color:C.text,fontWeight:700}}>{t.factor}x</span></div>
          <div style={{fontSize:10,color:C.muted,fontFamily:F}}>Reliability: <span style={{color:C.text}}>{Math.round(t.reliability*100)}%</span></div>
        </div>;})}
      </div>
    </Panel>

    {/* 5. DATA SOURCES */}
    <Panel title="DATA SOURCES">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8}}>
        {[
          {n:"Baseball Savant",d:"Statcast: xwOBA, xERA, barrel%, exit velocity, whiff%, sprint speed, OAA, bat speed, BsR. 900+ hitters, 1200+ pitchers (2023-2026).",c:C.accent,s:"STATIC"},
          {n:"FanGraphs",d:"SIERA, xFIP, FIP, K%, BB%, GB%, IP for 815 pitchers. Plate discipline, FV grades, career fWAR.",c:C.green,s:"STATIC"},
          {n:"MLB Stats API",d:"Player search, career stats, MiLB rosters across all levels (ROK\u2192AAA). Free, no auth required.",c:C.blue,s:"LIVE"},
          {n:"Contract Data",d:"2026 salary data for 190+ MLB players. Sources: Spotrac, MLB Trade Rumors, Cot\u2019s Baseball Contracts.",c:C.orange,s:"STATIC"},
        ].map(s=><div key={s.n} style={{padding:"12px 14px",background:`${s.c}06`,border:`1px solid ${s.c}18`,borderRadius:8}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:4}}>
            <span style={{fontSize:12,fontWeight:700,color:s.c,fontFamily:F}}>{s.n}</span>
            <span style={{fontSize:7,fontWeight:700,padding:"2px 5px",borderRadius:3,fontFamily:F,background:s.s==="LIVE"?`${C.green}20`:`${C.blue}20`,color:s.s==="LIVE"?C.green:C.blue}}>{s.s}</span>
          </div>
          <p style={{margin:0,fontSize:10,color:C.dim,lineHeight:1.5,fontFamily:F}}>{s.d}</p>
        </div>)}
      </div>
    </Panel>

  </div>
}




// ── LIVE fWAR LEADERBOARD ─────────────────────────────────────────────────────
const FG_TEAM_IDS = {ARI:109,AZ:109,CWS:145,WSH:120,ATL:144,BAL:110,BOS:111,CHC:112,CHW:145,CIN:113,CLE:114,COL:115,DET:116,HOU:117,KC:118,LAA:108,LAD:119,MIA:146,MIL:158,MIN:142,NYM:121,NYY:147,ATH:133,PHI:143,PIT:134,SD:135,SF:137,SEA:136,STL:138,TB:139,TEX:140,TOR:141,WSN:120,KCR:118,SDP:135,SFG:137,TBR:139};
function LiveWARBoard({onSelect}) {
  const [hitters, setHitters] = useState([]);
  const [pitchers, setPitchers] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const parseTm = t => (t||'').replace(/<[^>]+>/g,'').trim();

    // Priority 1: Pre-scraped live data (updated daily at 2am via Playwright)
    if (LIVE_LB?.hitters?.length > 0) {
      setHitters(LIVE_LB.hitters.slice(0,8));
      setPitchers((LIVE_LB.pitchers||[]).slice(0,8));
      setLoading(false);
      return;
    }

    // Priority 2: Client-side FanGraphs fetch (works when not blocked by Cloudflare)
    const yr = new Date().getFullYear();
    const fetchLeaders = (qual) => Promise.all([
      fetch(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=bat&lg=all&qual=${qual}&season=${yr}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`).then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}),
      fetch(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=pit&lg=all&qual=${qual}&season=${yr}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`).then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}),
    ]);
    const applyData = (batData, pitData) => {
      const h = (batData.data||[]).slice(0,8).map(p=>({name:p.PlayerName,tm:parseTm(p.Team),war:p.WAR?.toFixed(1),hr:Math.round(p.HR||0),wrc:Math.round(p['wRC+']||0)}));
      const pt = (pitData.data||[]).slice(0,8).map(p=>({name:p.PlayerName,tm:parseTm(p.Team),war:p.WAR?.toFixed(1),era:(p.ERA||0).toFixed(2),k9:(p['K/9']||0).toFixed(1),ip:(p.IP||0).toFixed(1)}));
      if (h.length > 0) { setHitters(h); setPitchers(pt); setLoading(false); return true; }
      return false;
    };
    fetchLeaders('y')
      .then(([b,p]) => { if (!applyData(b,p)) return fetchLeaders('0').then(([b2,p2]) => applyData(b2,p2)); })
      .catch(() => fetchLeaders('0').then(([b,p]) => applyData(b,p)).catch(() => {}))
      .finally(() => {
        // Priority 3: Precomputed projections as last resort
        setHitters(prev => {
          if (prev.length > 0) return prev;
          if (PRECOMPUTED?.hitters?.length > 0) {
            setPitchers((PRECOMPUTED.pitchers||[]).slice(0,8).map(p=>({name:p.name,tm:parseTm(p.team),war:(p.projWAR||0).toFixed(1),era:(p.projERA||0).toFixed(2),k9:(p.projK9||0).toFixed(1),ip:(p.projIP||0).toFixed(1)})));
            return PRECOMPUTED.hitters.slice(0,8).map(p=>({name:p.name,tm:parseTm(p.team),war:(p.projWAR||0).toFixed(1),hr:Math.round(p.projHR||0),wrc:Math.round(p.projWRC||0)}));
          }
          return prev;
        });
        setLoading(false);
      });
  }, []);
  const searchAndPick = (name) => { searchPlayers(name).then(r=>{if(r&&r[0])onSelect(r[0]);}); };
  if (loading) return null;
  if (!hitters.length && !pitchers.length) return null;
  const tmLogo = (tm) => `https://www.mlbstatic.com/team-logos/${FG_TEAM_IDS[tm]||147}.svg`;
  return (
    <div className="via-landing-2col" style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Panel title="LIVE fWAR LEADERS" sub="Top 8 Hitters" style={{borderTop:`3px solid ${C.navy}`,background:`linear-gradient(180deg, ${C.panel} 0%, ${C.bg} 100%)`}}>
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
      <Panel title="LIVE fWAR LEADERS" sub="Top 8 Pitchers" style={{borderTop:`3px solid ${C.navy}`,background:`linear-gradient(180deg, ${C.panel} 0%, ${C.bg} 100%)`}}>
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

// ── PLAYER OF THE DAY ────────────────────────────────────────────────────────
const POTD_POOL = [
  // Launch week: marquee names
  "Gunnar Henderson","Juan Soto","Bobby Witt Jr.","Shohei Ohtani","Paul Skenes",
  "Aaron Judge","Konnor Griffin","Elly De La Cruz","Corbin Carroll","Julio Rodriguez",
  // Week 2: stars + top prospects
  "Fernando Tatis Jr.","Bryce Harper","Mookie Betts","Samuel Basallo","Kyle Tucker",
  "Ronald Acuña Jr.","Corey Seager","Freddie Freeman","Mike Trout","Roki Sasaki",
  // Week 3: young stars + breakouts
  "Jackson Chourio","Adley Rutschman","Yordan Alvarez","Tarik Skubal","Garrett Crochet",
  "Riley Greene","Jackson Merrill","James Wood","Cal Raleigh","Kevin McGonigle",
  // Week 4+: deep roster
  "Vladimir Guerrero Jr.","Rafael Devers","Jose Ramirez","Francisco Lindor","Kyle Schwarber",
  "Trea Turner","Bo Bichette","Pete Alonso","Willy Adames","Max Clark",
  "Anthony Volpe","CJ Abrams","Jarren Duran","Roman Anthony","JJ Wetherholt",
  "Jackson Holliday","Dylan Crews","Evan Carter","Corbin Burnes","Zack Wheeler",
  "Matt McLain","Dansby Swanson","Marcus Semien","Alex Bregman","Manny Machado",
  "Pete Crow-Armstrong","Steven Kwan","Michael Harris II","Chris Sale","Cole Ragans",
  "Logan Webb","Dylan Cease","Colt Keith","Zach Neto","Matt Olson",
  "Kerry Carpenter","Bryson Stott","Cody Bellinger","Maikel Garcia","Aidan Miller",
  "Grayson Rodriguez","Hunter Brown","Jared Jones","Luis Gil","Tanner Bibee",
];

function getPlayerOfTheDay() {
  const now = new Date();
  const daysSinceEpoch = Math.floor(now.getTime() / 86400000);
  const launchDay = 20518; // March 5, 2026
  const idx = Math.abs(daysSinceEpoch - launchDay) % POTD_POOL.length;
  return POTD_POOL[idx];
}

function PlayerOfTheDay({onSelect}) {
  const [potdData, setPotdData] = useState(null);
  const [loading, setLoading] = useState(true);
  const name = getPlayerOfTheDay();

  useEffect(() => {
    setLoading(true);
    searchPlayers(name).then(async results => {
      if (!results[0]) { setLoading(false); return; }
      const p = results[0];
      try {
        const detail = await getPlayerStats(p.id);
        const player = detail || p;
        const isPitch = player.primaryPosition?.code === "1";
        const career = await getPlayerCareer(player.id, isPitch ? "pitching" : "hitting");
        const splits = isPitch
          ? career.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0)
          : career.filter(s => s.stat?.plateAppearances > 0);
        if (splits.length) {
          const base = isPitch
            ? projectPitcher(splits, projAge(player), player.fullName, player.id)
            : projectPlayer(splits, projAge(player), player.primaryPosition?.code, player.fullName, player.id);
          const fv = getPlayerFV(player.id, player.fullName);
          const cWAR = getCareerWAR(player.id, player.fullName);
          setPotdData({ player, base, fv, cWAR });
        }
      } catch {}
      setLoading(false);
    });
  }, [name]);

  return (
    <div style={{borderRadius:12,border:`1px solid ${C.border}`,borderTop:`3px solid ${C.accent}`,overflow:"hidden",background:`linear-gradient(180deg, ${C.panel} 0%, ${C.bg} 100%)`,boxShadow:`0 1px 3px rgba(26,54,104,0.04)`}}>
      {loading ? (
        <div style={{fontSize:11,color:C.muted,fontFamily:F,textAlign:"center",padding:20}}>Loading...</div>
      ) : potdData ? (
        <div style={{padding:"16px 22px"}}>
          {/* Label */}
          <div style={{textAlign:"center",marginBottom:10}}>
            <span style={{fontSize:8,fontWeight:700,letterSpacing:".14em",color:C.accent,fontFamily:F,textTransform:"uppercase"}}>★ Player of the Day</span>
          </div>
          {/* Centered player name */}
          <div style={{textAlign:"center",marginBottom:12}}>
            <span onClick={()=>onSelect(potdData.player)} style={{fontSize:22,fontWeight:800,color:C.navy,fontFamily:F,cursor:"pointer",lineHeight:1.1}}>{potdData.player.fullName}</span>
            {potdData.fv && <span style={{marginLeft:10,verticalAlign:"middle"}}><FVBadge fv={potdData.fv}/></span>}
            <div style={{fontSize:10,color:C.muted,fontFamily:F,marginTop:4}}>
              {posLabel(potdData.player.primaryPosition?.code)} &middot; {potdData.player.currentTeam?.name||"FA"} &middot; Age {potdData.player.currentAge}
            </div>
          </div>
          {/* Stats row — centered */}
          <div style={{display:"flex",justifyContent:"center",alignItems:"center",gap:16,flexWrap:"wrap"}}>
            {potdData.base && !potdData.base.isPitcher && <>
              <div style={{textAlign:"center"}}>
                <div style={{fontSize:13,fontWeight:600,color:C.dim,fontFamily:F,letterSpacing:".01em"}}>
                  {potdData.base.avg?.toFixed(3)}<span style={{color:C.muted}}> / </span>{potdData.base.obp?.toFixed(3)}<span style={{color:C.muted}}> / </span>{potdData.base.slg?.toFixed(3)}
                </div>
                <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".06em",marginTop:2}}>AVG / OBP / SLG</div>
              </div>
              <div style={{width:1,height:28,background:`${C.border}60`}}/>
              {[
                {v:potdData.base.wRCPlus,l:"wRC+",c:potdData.base.wRCPlus>=120?C.green:C.text},
                {v:potdData.base.hr,l:"HR",c:C.text},
                {v:potdData.base.baseWAR?.toFixed(1),l:"fWAR",c:potdData.base.baseWAR>=4?C.green:potdData.base.baseWAR>=2?C.blue:C.text},
              ].map(s=><div key={s.l} style={{textAlign:"center",minWidth:36}}>
                <div style={{fontSize:20,fontWeight:800,color:s.c,fontFamily:F,lineHeight:1}}>{s.v}</div>
                <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".05em",marginTop:2}}>{s.l}</div>
              </div>)}
              {potdData.cWAR !== null && <>
                <div style={{width:1,height:28,background:`${C.border}60`}}/>
                <div style={{textAlign:"center",minWidth:36}}>
                  <div style={{fontSize:16,fontWeight:800,color:potdData.cWAR>=30?C.green:C.text,fontFamily:F,lineHeight:1}}>{potdData.cWAR.toFixed(1)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".05em",marginTop:2}}>Career fWAR</div>
                </div>
              </>}
            </>}
            {potdData.base && potdData.base.isPitcher && <>
              {[
                {v:potdData.base.era?.toFixed(2),l:"ERA",c:potdData.base.era<=3?C.green:C.text},
                {v:potdData.base.fip?.toFixed(2),l:"FIP",c:potdData.base.fip<=3.5?C.green:C.text},
                {v:Math.round(potdData.base.ip),l:"IP",c:C.text},
                {v:potdData.base.baseWAR?.toFixed(1),l:"fWAR",c:potdData.base.baseWAR>=4?C.green:C.text},
              ].map(s=><div key={s.l} style={{textAlign:"center",minWidth:36}}>
                <div style={{fontSize:20,fontWeight:800,color:s.c,fontFamily:F,lineHeight:1}}>{s.v}</div>
                <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".05em",marginTop:2}}>{s.l}</div>
              </div>)}
              {potdData.cWAR !== null && <>
                <div style={{width:1,height:28,background:`${C.border}60`}}/>
                <div style={{textAlign:"center",minWidth:36}}>
                  <div style={{fontSize:16,fontWeight:800,color:potdData.cWAR>=30?C.green:C.text,fontFamily:F,lineHeight:1}}>{potdData.cWAR.toFixed(1)}</div>
                  <div style={{fontSize:7,color:C.muted,fontFamily:F,textTransform:"uppercase",letterSpacing:".05em",marginTop:2}}>Career fWAR</div>
                </div>
              </>}
            </>}
          </div>
          {/* CTA */}
          <div style={{textAlign:"center",marginTop:12}}>
            <button onClick={()=>onSelect(potdData.player)} style={{padding:"7px 20px",borderRadius:6,background:C.accent,color:"#fff",fontSize:10,fontWeight:700,fontFamily:F,cursor:"pointer",border:"none",transition:"opacity 0.15s"}} onMouseEnter={e=>e.currentTarget.style.opacity="0.85"} onMouseLeave={e=>e.currentTarget.style.opacity="1"}>View Full Projection &rarr;</button>
          </div>
        </div>
      ) : (
        <div style={{fontSize:11,color:C.muted,fontFamily:F,textAlign:"center",padding:16}}>{name}</div>
      )}
    </div>
  );
}
// ── TICKER BAR ──────────────────────────────────────────────────────────────
function TickerBar() {
  const [games, setGames] = useState([]);
  useEffect(() => {
    const today = new Date().toISOString().slice(0,10);
    fetch(`https://statsapi.mlb.com/api/v1/schedule?date=${today}&sportId=1&gameType=R&hydrate=probablePitcher(note),team`)
      .then(r=>r.json())
      .then(data => {
        const g = data.dates?.[0]?.games || [];
        const items = g.map(game => {
          const away = game.teams.away;
          const home = game.teams.home;
          const getLastName = (p) => p?.fullName?.split(" ").pop() || p?.lastName || "TBD";
          return {
            awayAbbr: away.team?.abbreviation || "???",
            homeAbbr: home.team?.abbreviation || "???",
            awayId: away.team?.id || 0,
            homeId: home.team?.id || 0,
            awayP: getLastName(away.probablePitcher),
            homeP: getLastName(home.probablePitcher),
            time: new Date(game.gameDate).toLocaleTimeString("en-US",{hour:"numeric",minute:"2-digit",timeZone:"America/New_York"}),
            status: game.status?.detailedState || "",
          };
        });
        if (items.length > 0) setGames(items);
      }).catch(()=>{});
  }, []);

  const logo = (id) => `https://www.mlbstatic.com/team-logos/${id}.svg`;

  if (games.length === 0) {
    return (
      <div style={{overflow:"hidden",borderRadius:10,background:"#1e3a5f",padding:"10px 0",border:`1px solid #2d5a8a`}}>
        <div className="via-ticker" style={{display:"flex",gap:40,whiteSpace:"nowrap",animation:"ticker 25s linear infinite"}}>
          {[...Array(3)].flatMap((_,dup) => (() => {
            // Offseason fallback, built from current data so it never goes stale.
            const H = PRECOMPUTED.hitters || [], P = PRECOMPUTED.pitchers || [];
            const topHR = [...H].sort((a,b)=>(b.projHR||0)-(a.projHR||0))[0];
            const topPros = (prospectsData.players||[]).find(p=>!p.graduated);
            const lastH = LIVE_LB?.hitters?.[0], lastP = LIVE_LB?.pitchers?.[0];
            return [
              H[0] && {t:H[0].name,s:`${H[0].projWAR} fWAR`,c:"#4ade80",d:`#1 projected hitter for ${PROJ_SEASON}`},
              P[0] && {t:P[0].name,s:`${P[0].projWAR} fWAR`,c:"#4ade80",d:`#1 projected pitcher for ${PROJ_SEASON}`},
              topPros && {t:topPros.name,s:`${topPros.fv} FV`,c:"#fbbf24",d:"top-ranked prospect"},
              topHR && {t:topHR.name,s:`${topHR.projHR} HR`,c:"#c084fc",d:`projected ${PROJ_SEASON} home run leader`},
              lastH && {t:lastH.name,s:`${lastH.war} fWAR`,c:"#60a5fa",d:`led all hitters in ${LIVE_LB.season}`},
              lastP && {t:lastP.name,s:`${lastP.war} fWAR`,c:"#60a5fa",d:`led all pitchers in ${LIVE_LB.season}`},
            ].filter(Boolean);
          })().map((item,i) => (
            <span key={dup+"_"+i} style={{display:"inline-flex",alignItems:"center",gap:6,fontSize:11,fontFamily:F}}>
              <span style={{color:"#fff",fontWeight:700}}>{item.t}</span>
              <span style={{color:item.c,fontWeight:800,fontSize:12}}>{item.s}</span>
              <span style={{color:"#ffffffaa",fontSize:9}}>{item.d}</span>
              <span style={{color:"#ffffff20",margin:"0 10px"}}>|</span>
            </span>
          )))}
        </div>
      </div>
    );
  }

  return (
    <div style={{overflow:"hidden",borderRadius:10,background:"#1e3a5f",padding:"8px 0",border:`1px solid #2d5a8a`}}>
      <div className="via-ticker" style={{display:"flex",gap:0,whiteSpace:"nowrap",animation:`ticker ${Math.max(15, games.length * 1.8)}s linear infinite`}}>
        {[...games, ...games, ...games].map((g, i) => (
          <span key={i} style={{display:"inline-flex",alignItems:"center",gap:0,fontFamily:F,padding:"0 14px",borderRight:"1px solid #ffffff12",flexShrink:0}}>
            <img src={logo(g.awayId)} alt="" style={{width:16,height:16,objectFit:"contain",marginRight:3}} onError={e=>{e.target.style.display="none"}}/>
            <span style={{color:"#fff",fontWeight:800,fontSize:10,marginRight:4}}>{g.awayAbbr}</span>
            <span style={{color:"#ffffff40",fontSize:8,marginRight:4}}>@</span>
            <img src={logo(g.homeId)} alt="" style={{width:16,height:16,objectFit:"contain",marginRight:3}} onError={e=>{e.target.style.display="none"}}/>
            <span style={{color:"#fff",fontWeight:800,fontSize:10,marginRight:8}}>{g.homeAbbr}</span>
            <span style={{color:"#c084fc",fontWeight:600,fontSize:9}}>{g.awayP}</span>
            <span style={{color:"#ffffff40",fontSize:8,margin:"0 3px"}}>vs</span>
            <span style={{color:"#4ade80",fontWeight:600,fontSize:9,marginRight:6}}>{g.homeP}</span>
            <span style={{color:"#fbbf24",fontWeight:700,fontSize:9}}>
              {g.status === "In Progress" ? "LIVE" : g.status === "Final" ? "FINAL" : g.time}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ── MAIN APP ─────────────────────────────────────────────────────────────────
const TABS=[
  {k:"player",l:"Projections",icon:"⚾"},
  {k:"leaders",l:"Leaderboard",icon:"🏆"},
  {k:"prospects",l:"Prospects",icon:"🌱"},
  {k:"roster",l:"Rosters",icon:"📋"},
  // Compare tab hidden for now (ComparePanel still exists below; /compare redirects home).
  {k:"cost",l:"Value/Dollar",icon:"💲"},
  {k:"scorecard",l:"Scorecard",icon:"✅"},
  {k:"research",l:"Research",icon:"📝"},
  {k:"method",l:"Methodology",icon:"📊"},
];

function ComparePanel({ onSelect }) {
  const [slots, setSlots] = useState([null, null, null]);
  const [searches, setSearches] = useState(["", "", ""]);
  const [results, setResults] = useState([[], [], []]);
  const [projections, setProjections] = useState([null, null, null]);
  const [loading, setLoading] = useState([false, false, false]);

  const searchPlayer = async (query, idx) => {
    const newSearches = [...searches];
    newSearches[idx] = query;
    setSearches(newSearches);
    if (query.length < 2) { const nr = [...results]; nr[idx] = []; setResults(nr); return; }
    try {
      const r = await fetch(`${API}/people/search?names=${encodeURIComponent(query)}&sportIds=1,11,12,13,14,16&hydrate=currentTeam,team,primaryPosition&limit=8`);
      const d = await r.json();
      const nr = [...results]; nr[idx] = (d.people || []).slice(0, 6); setResults(nr);
    } catch { }
  };

  const selectPlayer = async (player, idx) => {
    const fullPlayer = await getPlayerStats(player.id);
    const ns = [...slots]; ns[idx] = fullPlayer || player; setSlots(ns);
    console.log("Full player data:", fullPlayer);
    const nr = [...results]; nr[idx] = []; setResults(nr);
    const nsr = [...searches]; nsr[idx] = ""; setSearches(nsr);
    const nl = [...loading]; nl[idx] = true; setLoading(nl);

    try {
      const isPitcher = (fullPlayer || player).primaryPosition?.code === "1";
      const career = await getPlayerCareer((fullPlayer || player).id, isPitcher ? "pitching" : "hitting");
      let base, forward;
      if (isPitcher) {
        base = projectPitcher(career, (fullPlayer || player).currentAge, (fullPlayer || player).fullName, (fullPlayer || player).id);
        forward = base ? projectPitcherForward(base, (fullPlayer || player).currentAge) : [];
      } else {
        const splits = career.filter(s => s.stat?.plateAppearances > 0);
        base = projectPlayer(splits, (fullPlayer || player).currentAge, (fullPlayer || player).primaryPosition?.code, (fullPlayer || player).fullName, (fullPlayer || player).id);
        forward = base ? projectForward(base, (fullPlayer || player).currentAge, (fullPlayer || player).primaryPosition?.code) : [];
      }
      const np = [...projections]; np[idx] = { base, forward, isPitcher }; setProjections(np);
    } catch { }
    const nl2 = [...loading]; nl2[idx] = false; setLoading(nl2);
  };

  const removePlayer = (idx) => {
    const ns = [...slots]; ns[idx] = null; setSlots(ns);
    const np = [...projections]; np[idx] = null; setProjections(np);
  };

  const COLORS = ["#c8102e", "#1a3668", "#059669"];
  const filledSlots = slots.filter(Boolean);
  const allForward = projections.filter(Boolean).map(p => p.forward);
  const maxYears = Math.max(...allForward.map(f => f.length), 0);

  // Build chart data
  const chartData = [];
  for (let y = 0; y < Math.min(maxYears, 8); y++) {
    const point = {};
    slots.forEach((s, i) => {
      if (s && projections[i]?.forward?.[y]) {
        const f = projections[i].forward[y];
        point.season = point.season || ("'" + String(PROJ_SEASON + y).slice(2));
        point[`war${i}`] = f.war;
        point[`name${i}`] = s.fullName;
      }
    });
    if (Object.keys(point).length > 1) chartData.push(point);
  }

  return (
    <div>
      <Panel title="PLAYER COMPARISON" sub="Compare up to 3 players side-by-side with projected WAR curves.">
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:16}}>
          {[0,1,2].map(idx => (
            <div key={idx} style={{flex:"1 1 200px",minWidth:180}}>
              {slots[idx] ? (
                <div style={{padding:12,borderRadius:8,border:`2px solid ${COLORS[idx]}`,background:`${COLORS[idx]}08`}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                    <div>
                      <div style={{fontSize:14,fontWeight:700,color:C.text,fontFamily:F}}>{slots[idx].fullName}</div>
                      <div style={{fontSize:10,color:C.muted,fontFamily:F}}>
                        {posLabel(slots[idx].primaryPosition?.code)} &middot; {slots[idx].currentTeam?.name || "FA"} &middot; Age {slots[idx].currentAge}
                      </div>
                    </div>
                    <button onClick={()=>removePlayer(idx)} style={{background:"none",border:"none",cursor:"pointer",fontSize:16,color:C.muted,padding:4}}>&times;</button>
                  </div>
                  {loading[idx] && <div style={{fontSize:10,color:C.muted,fontFamily:F,marginTop:6}}>Loading projections...</div>}
                  {projections[idx]?.base && (
                    <div style={{display:"flex",gap:8,marginTop:8,flexWrap:"wrap"}}>
                      {projections[idx].isPitcher ? <>
                        <div style={{textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:COLORS[idx],fontFamily:F}}>{projections[idx].base.era?.toFixed(2)}</div><div style={{fontSize:7,color:C.muted,fontFamily:F}}>ERA</div></div>
                        <div style={{textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:COLORS[idx],fontFamily:F}}>{projections[idx].base.k9?.toFixed(1)}</div><div style={{fontSize:7,color:C.muted,fontFamily:F}}>K/9</div></div>
                        <div style={{textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:COLORS[idx],fontFamily:F}}>{projections[idx].base.baseWAR?.toFixed(1)}</div><div style={{fontSize:7,color:C.muted,fontFamily:F}}>fWAR</div></div>
                      </> : <>
                        <div style={{textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:COLORS[idx],fontFamily:F}}>{projections[idx].base.ops?.toFixed(3)}</div><div style={{fontSize:7,color:C.muted,fontFamily:F}}>OPS</div></div>
                        <div style={{textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:COLORS[idx],fontFamily:F}}>{projections[idx].base.hr}</div><div style={{fontSize:7,color:C.muted,fontFamily:F}}>HR</div></div>
                        <div style={{textAlign:"center"}}><div style={{fontSize:16,fontWeight:800,color:COLORS[idx],fontFamily:F}}>{projections[idx].base.baseWAR?.toFixed(1)}</div><div style={{fontSize:7,color:C.muted,fontFamily:F}}>fWAR</div></div>
                      </>}
                    </div>
                  )}
                </div>
              ) : (
                <div style={{padding:12,borderRadius:8,border:`2px dashed ${C.border}`,background:`${C.panel}`}}>
                  <div style={{fontSize:10,color:C.muted,fontFamily:F,marginBottom:6}}>Player {idx + 1}</div>
                  <input
                    value={searches[idx]}
                    onChange={e => searchPlayer(e.target.value, idx)}
                    placeholder="Search player..."
                    style={{width:"100%",padding:"6px 10px",borderRadius:6,border:`1px solid ${C.border}`,background:"#fff",color:C.text,fontSize:11,fontFamily:F,outline:"none",boxSizing:"border-box"}}
                  />
                  {results[idx].length > 0 && (
                    <div style={{marginTop:4,maxHeight:180,overflowY:"auto",borderRadius:6,border:`1px solid ${C.border}`,background:"#fff"}}>
                      {results[idx].map(p => (
                        <div key={p.id} onClick={() => selectPlayer(p, idx)}
                          style={{padding:"6px 10px",cursor:"pointer",fontSize:11,fontFamily:F,borderBottom:`1px solid ${C.border}22`,color:C.text}}
                          onMouseOver={e=>e.currentTarget.style.background=C.hover}
                          onMouseOut={e=>e.currentTarget.style.background="transparent"}>
                          {p.fullName} <span style={{color:C.muted,fontSize:9}}>{posLabel(p.primaryPosition?.code)} &middot; {p.currentTeam?.abbreviation || "FA"}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </Panel>

      {chartData.length > 0 && (
        <Panel title="PROJECTED fWAR COMPARISON" sub="Side-by-side fWAR trajectory over the next 8 seasons.">
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={chartData} margin={{top:10,right:20,left:0,bottom:0}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid}/>
              <XAxis dataKey="season" stroke={C.muted} fontSize={10} fontFamily={F}/>
              <YAxis stroke={C.muted} fontSize={10} fontFamily={F}/>
              <Tooltip content={({active,payload,label}) => {
                if (!active || !payload?.length) return null;
                return <div style={{background:"#fff",border:`1px solid ${C.border}`,borderRadius:8,padding:"8px 12px",boxShadow:"0 4px 12px rgba(0,0,0,.1)"}}>
                  <div style={{fontSize:10,color:C.muted,fontFamily:F,marginBottom:4}}>Season {label}</div>
                  {payload.map((p,i) => <div key={i} style={{fontSize:11,color:p.color,fontFamily:F}}>{p.name}: <strong>{p.value?.toFixed(1)}</strong> WAR</div>)}
                </div>;
              }}/>
              <ReferenceLine y={0} stroke={C.muted} strokeDasharray="5 5"/>
              <ReferenceLine y={2} stroke={C.green} strokeDasharray="3 3" strokeOpacity={.3}/>
              {slots.map((s, i) => s && projections[i] ? (
                <Line key={i} type="monotone" dataKey={`war${i}`} name={s.fullName} stroke={COLORS[i]} strokeWidth={2.5} dot={{fill:COLORS[i],r:4}} activeDot={{r:6}}/>
              ) : null)}
            </ComposedChart>
          </ResponsiveContainer>
        </Panel>
      )}

      {filledSlots.length >= 2 && projections.filter(Boolean).length >= 2 && (
        <Panel title="STAT COMPARISON" sub="Projected season stats side-by-side.">
          <div className="via-table-wrap" style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:11,fontFamily:F}}>
              <thead><tr>
                <th style={{padding:"6px 8px",borderBottom:`2px solid ${C.border}`,textAlign:"left",color:C.muted,fontWeight:700,fontSize:9}}>Stat</th>
                {slots.map((s, i) => s ? <th key={i} style={{padding:"6px 8px",borderBottom:`2px solid ${COLORS[i]}`,textAlign:"right",color:COLORS[i],fontWeight:700,fontSize:9}}>{s.fullName.split(" ").pop()}</th> : null)}
              </tr></thead>
              <tbody>
                {(() => {
                  const anyPitcher = projections.some(p => p?.isPitcher);
                  const anyHitter = projections.some(p => p && !p.isPitcher);
                  const rows = [];
                  if (anyHitter) {
                    [{k:"ops",l:"OPS",fmt:v=>v?.toFixed(3)},{k:"wRCPlus",l:"wRC+",fmt:v=>v},{k:"hr",l:"HR",fmt:v=>v},{k:"avg",l:"AVG",fmt:v=>v?.toFixed(3)},{k:"obp",l:"OBP",fmt:v=>v?.toFixed(3)},{k:"slg",l:"SLG",fmt:v=>v?.toFixed(3)},{k:"baseWAR",l:"Proj fWAR",fmt:v=>v?.toFixed(1)}].forEach(stat => {
                      rows.push(<tr key={stat.k} style={{borderBottom:`1px solid ${C.border}22`}}>
                        <td style={{padding:"5px 8px",fontWeight:600}}>{stat.l}</td>
                        {slots.map((s, i) => s ? <td key={i} style={{padding:"5px 8px",textAlign:"right",fontWeight:600,color:COLORS[i]}}>{projections[i]?.base && !projections[i]?.isPitcher ? stat.fmt(projections[i].base[stat.k]) ?? "—" : "—"}</td> : null)}
                      </tr>);
                    });
                  }
                  if (anyPitcher) {
                    [{k:"era",l:"ERA",fmt:v=>v?.toFixed(2)},{k:"fip",l:"FIP",fmt:v=>v?.toFixed(2)},{k:"whip",l:"WHIP",fmt:v=>v?.toFixed(2)},{k:"k9",l:"K/9",fmt:v=>v?.toFixed(1)},{k:"ip",l:"IP",fmt:v=>v},{k:"baseWAR",l:"Proj fWAR",fmt:v=>v?.toFixed(1)}].forEach(stat => {
                      rows.push(<tr key={"p_"+stat.k} style={{borderBottom:`1px solid ${C.border}22`}}>
                        <td style={{padding:"5px 8px",fontWeight:600}}>{stat.l}</td>
                        {slots.map((s, i) => s ? <td key={i} style={{padding:"5px 8px",textAlign:"right",fontWeight:600,color:COLORS[i]}}>{projections[i]?.base && projections[i]?.isPitcher ? stat.fmt(projections[i].base[stat.k]) ?? "—" : "—"}</td> : null)}
                      </tr>);
                    });
                  }
                  // 10yr WAR for all
                  rows.push(<tr key="cumwar" style={{borderBottom:`1px solid ${C.border}22`,background:`${C.accent}05`}}>
                    <td style={{padding:"5px 8px",fontWeight:700}}>10yr WAR</td>
                    {slots.map((s, i) => s ? <td key={i} style={{padding:"5px 8px",textAlign:"right",fontWeight:800,color:COLORS[i]}}>{projections[i]?.forward ? projections[i].forward.reduce((sum, d) => sum + Math.max(0, d.war), 0).toFixed(1) : "—"}</td> : null)}
                  </tr>);
                  // Career fWAR
                  rows.push(<tr key="cfwar" style={{borderBottom:`1px solid ${C.border}22`}}>
                    <td style={{padding:"5px 8px",fontWeight:600}}>Career fWAR</td>
                    {slots.map((s, i) => s ? <td key={i} style={{padding:"5px 8px",textAlign:"right",fontWeight:600,color:COLORS[i]}}>{(() => { const w = getCareerWAR(s.id, s.fullName); return w !== null ? w.toFixed(1) : "—"; })()}</td> : null)}
                  </tr>);
                  return rows;
                })()}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}

// ── LANDING PAGE TOP LISTS (live from engine) ───────────────────────────────
// Projects a curated set of star players on mount so landing page numbers
// always match the player card and leaderboard engine.
const LANDING_HITTERS = [
  {name:"Shohei Ohtani",pos:"Y"},{name:"Bobby Witt Jr.",pos:"6"},{name:"Juan Soto",pos:"9"},
  {name:"Aaron Judge",pos:"9"},{name:"Gunnar Henderson",pos:"6"},{name:"Fernando Tatis Jr.",pos:"9"},
  {name:"Ronald Acuna Jr.",pos:"9"},{name:"Elly De La Cruz",pos:"6"},{name:"Francisco Lindor",pos:"6"},
  {name:"Corbin Carroll",pos:"9"},{name:"Julio Rodriguez",pos:"8"},{name:"Mookie Betts",pos:"6"},
  {name:"Freddie Freeman",pos:"3"},{name:"Kyle Tucker",pos:"9"},{name:"Corey Seager",pos:"6"},
];
const LANDING_PITCHERS = [
  {name:"Paul Skenes"},{name:"Tarik Skubal"},{name:"Garrett Crochet"},
  {name:"Logan Webb"},{name:"Zack Wheeler"},{name:"Cole Ragans"},
  {name:"Cristopher Sanchez"},{name:"Chris Sale"},{name:"Bryan Woo"},
  {name:"Corbin Burnes"},{name:"Seth Lugo"},{name:"Framber Valdez"},
];

function LandingTopLists({onSelect}) {
  const [topHitters, setTopHitters] = useState([]);
  const [topPitchers, setTopPitchers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      // Project hitters
      const hResults = [];
      for (const h of LANDING_HITTERS) {
        try {
          const results = await searchPlayers(h.name);
          if (!results?.[0]) continue;
          const p = results[0];
          const isPitcher = p.primaryPosition?.code === "1";
          const isTwoWay = p.primaryPosition?.code === "Y";
          const career = await getPlayerCareer(p.id, isPitcher ? "pitching" : "hitting");
          let base;
          if (isPitcher) {
            base = projectPitcher(career, projAge(p), p.fullName, p.id);
          } else {
            const splits = career.filter(s => s.stat?.plateAppearances > 0);
            base = projectPlayer(splits, projAge(p), isTwoWay ? "10" : p.primaryPosition?.code, p.fullName, p.id);
            // Two-way: add pitching WAR
            if (isTwoWay) {
              const pitchCareer = await getPlayerCareer(p.id, "pitching");
              const pProj = projectPitcher(pitchCareer, projAge(p), p.fullName, p.id);
              if (pProj && pProj.baseWAR > 0) {
                base._hitWAR = Math.round(base.baseWAR * 0.92 * 10) / 10;
                base._pitchWAR = Math.round(pProj.baseWAR * 0.72 * 10) / 10;
                base.baseWAR = Math.round((base._hitWAR + base._pitchWAR) * 10) / 10;
              }
            }
          }
          if (base) {
            hResults.push({
              name: p.fullName, team: p.currentTeam?.abbreviation || "FA",
              pos: posLabel(isTwoWay ? "Y" : p.primaryPosition?.code),
              war: base.baseWAR, wrc: base.wRCPlus, _player: p,
            });
          }
        } catch {}
      }
      if (!cancelled) setTopHitters(hResults.sort((a,b) => b.war - a.war).slice(0,8));

      // Project pitchers
      const pResults = [];
      for (const h of LANDING_PITCHERS) {
        try {
          const results = await searchPlayers(h.name);
          if (!results?.[0]) continue;
          const p = results[0];
          const career = await getPlayerCareer(p.id, "pitching");
          const base = projectPitcher(career, projAge(p), p.fullName, p.id);
          if (base) {
            pResults.push({
              name: p.fullName, team: p.currentTeam?.abbreviation || "FA",
              pos: base.isReliever ? "RP" : "SP",
              war: base.baseWAR, era: base.era, _player: p,
            });
          }
        } catch {}
      }
      if (!cancelled) { setTopPitchers(pResults.sort((a,b) => b.war - a.war).slice(0,8)); setLoading(false); }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // While loading, show skeleton from precomputed as placeholder
  const displayHitters = topHitters.length > 0 ? topHitters : (PRECOMPUTED.hitters||[]).sort((a,b)=>b.projWAR-a.projWAR).slice(0,8).map(p=>({name:p.name,team:p.team,pos:p.pos,war:p.projWAR,wrc:p.projWRC}));
  const displayPitchers = topPitchers.length > 0 ? topPitchers : (PRECOMPUTED.pitchers||[]).sort((a,b)=>b.projWAR-a.projWAR).slice(0,8).map(p=>({name:p.name,team:p.team,pos:p.pos,war:p.projWAR,era:p.projERA}));

  return (
    <div className="via-landing-2col" style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Panel title="TOP HITTERS" sub={`${PROJ_SEASON} projected fWAR leaders.${loading?" (updating...)":""}`} style={{borderTop:`3px solid ${C.accent}`,background:`linear-gradient(180deg, ${C.panel} 0%, ${C.bg} 100%)`}}>
        <div style={{display:"flex",flexDirection:"column",gap:2}}>
          {displayHitters.map((p,i)=>(
            <div key={p.name} onClick={()=>p._player?onSelect(p._player):searchPlayers(p.name).then(r=>{if(r[0])onSelect(r[0]);})}
              style={{display:"flex",alignItems:"center",gap:10,padding:"7px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
              onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
              onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:10,fontWeight:800,color:C.muted,fontFamily:F,minWidth:16}}>{i+1}</span>
              <img src={`https://www.mlbstatic.com/team-logos/${TEAM_ID_BY_ABBREV[p.team]||0}.svg`} alt="" style={{width:20,height:20,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
              <div style={{flex:1}}>
                <div style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.name}</div>
                <div style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.team}</div>
              </div>
              <div style={{textAlign:"right"}}>
                <div style={{fontSize:13,fontWeight:800,color:p.war>=6?C.green:p.war>=4?C.blue:C.text,fontFamily:F}}>{p.war.toFixed(1)}</div>
                <div style={{fontSize:8,color:C.muted,fontFamily:F}}>fWAR</div>
              </div>
              <div style={{textAlign:"right",minWidth:32}}>
                <div style={{fontSize:11,fontWeight:600,color:C.dim,fontFamily:F}}>{p.wrc||"—"}</div>
                <div style={{fontSize:8,color:C.muted,fontFamily:F}}>wRC+</div>
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="TOP PITCHERS" sub={`${PROJ_SEASON} projected fWAR leaders.${loading?" (updating...)":""}`} style={{borderTop:`3px solid ${C.accent}`,background:`linear-gradient(180deg, ${C.panel} 0%, ${C.bg} 100%)`}}>
        <div style={{display:"flex",flexDirection:"column",gap:2}}>
          {displayPitchers.map((p,i)=>(
            <div key={p.name} onClick={()=>p._player?onSelect(p._player):searchPlayers(p.name).then(r=>{if(r[0])onSelect(r[0]);})}
              style={{display:"flex",alignItems:"center",gap:10,padding:"7px 10px",borderRadius:6,cursor:"pointer",borderBottom:i<7?`1px solid ${C.border}22`:"none",transition:"background 0.1s"}}
              onMouseEnter={e=>e.currentTarget.style.background=`${C.accent}06`}
              onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontSize:10,fontWeight:800,color:C.muted,fontFamily:F,minWidth:16}}>{i+1}</span>
              <img src={`https://www.mlbstatic.com/team-logos/${TEAM_ID_BY_ABBREV[p.team]||0}.svg`} alt="" style={{width:20,height:20,objectFit:"contain"}} onError={e=>{e.target.style.display="none"}}/>
              <div style={{flex:1}}>
                <div style={{fontSize:11,fontWeight:700,color:C.text,fontFamily:F}}>{p.name}</div>
                <div style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.team}</div>
              </div>
              <div style={{textAlign:"right"}}>
                <div style={{fontSize:13,fontWeight:800,color:p.war>=5?C.green:p.war>=4?C.blue:C.text,fontFamily:F}}>{p.war.toFixed(1)}</div>
                <div style={{fontSize:8,color:C.muted,fontFamily:F}}>fWAR</div>
              </div>
              <div style={{textAlign:"right",minWidth:32}}>
                <div style={{fontSize:11,fontWeight:600,color:p.era<=2.80?C.green:p.era<=3.20?C.blue:C.dim,fontFamily:F}}>{p.era?.toFixed(2)||"—"}</div>
                <div style={{fontSize:8,color:C.muted,fontFamily:F}}>ERA</div>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

export default function App() {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [darkMode, setDarkMode] = useState(_theme === "dark");
  
  // Theme toggle
  const toggleTheme = useCallback(() => {
    const next = darkMode ? "light" : "dark";
    setDarkMode(!darkMode);
    Object.assign(C, next === "dark" ? DARK : LIGHT);
    try { localStorage.setItem("via-theme", next); } catch {}
    _theme = next;
  }, [darkMode]);
  
  // Sync C on mount if dark
  if (darkMode && C.bg !== DARK.bg) Object.assign(C, DARK);
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);
  const [scrolled, setScrolled] = useState(false);

  // Browser back/forward support
  useEffect(() => {
    const onPop = () => {
      const r = parseURL();
      setTab(r.tab);
      if (r.playerId) {
        setLp(true);
        getPlayerStats(parseInt(r.playerId)).then(d => { if(d){setSelPlayer(d);setDetail(d);} setLp(false); });
      } else if (r.tab === "player") { setSelPlayer(null); setDetail(null); }
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  // Deep link: load player from URL on mount
  useEffect(() => {
    const r = parseURL();
    if (r.playerId) {
      setLp(true);
      getPlayerStats(parseInt(r.playerId)).then(d => { if(d){setSelPlayer(d);setDetail(d);} setLp(false); }).catch(() => setLp(false));
    }
  }, []);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // URL routing
  const parseURL = () => {
    const path = window.location.pathname;
    const m = path.match(/^\/player\/([^/]+?)(?:-(\d+))?$/);
    if (m) return { tab: "player", playerId: m[2] || null };
    if (path === "/leaderboard") return { tab: "leaders" };
    if (path === "/rosters") return { tab: "roster" };
    if (path === "/prospects") return { tab: "prospects" };
    if (path === "/scorecard") return { tab: "scorecard" };
    if (path === "/value") return { tab: "cost" };
    if (path === "/methodology") return { tab: "method" };
    if (path === "/research") return { tab: "research" };
    return { tab: "player" };
  };
  const initRoute = parseURL();
  const [tab,setTab]=useState(initRoute.tab);
  const [selPlayer,setSelPlayer]=useState(null);
  const [detail,setDetail]=useState(null);
  const [lp,setLp]=useState(false);
  const [menuOpen,setMenuOpen]=useState(false);

  const slugify = (name) => (name||"player").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  const pick=useCallback(p=>{setSelPlayer(p);setLp(true);setTab("player");window.history.pushState({},"",`/player/${slugify(p.fullName||p.name)}-${p.id}`);getPlayerStats(p.id).then(d=>{setDetail(d||p);setLp(false);});},[]);

  const goHome = useCallback(()=>{setSelPlayer(null);setDetail(null);setLp(false);setTab("player");window.history.pushState({},"","/");},[]);

  const tabPaths = {player:"/",leaders:"/leaderboard",prospects:"/prospects",roster:"/rosters",cost:"/value",scorecard:"/scorecard",research:"/research",method:"/methodology"};
  const pickName = useCallback((name, id) => { if (id) pick({ id, fullName: name }); else searchPlayers(name).then(r => { if (r[0]) pick(r[0]); }); }, [pick]);
  const switchTab = useCallback((k) => { setTab(k); setMenuOpen(false); window.history.pushState({},"",tabPaths[k]||"/"); }, []);

  return (
    <div style={{minHeight:"100vh",background:C.bg,color:C.text,fontFamily:F}}>
      <style>{`
        :root {
          --via-bg: ${C.bg};
          --via-panel: ${C.panel};
          --via-hover: ${C.hover};
          --via-border: ${C.border};
          --via-text: ${C.text};
        }
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(12px) } to { opacity:1; transform:translateY(0) } }
        @keyframes fadeIn { from { opacity:0 } to { opacity:1 } }
        @keyframes shimmer { 0% { background-position: -400px 0 } 100% { background-position: 400px 0 } }
        @keyframes ticker { 0% { transform: translateX(0) } 100% { transform: translateX(-33.33%) } }
        @keyframes pulse { 0%,100% { opacity:0.5 } 50% { opacity:0.8 } }
        @keyframes slideUp { from { opacity:0; transform:translateY(20px) } to { opacity:1; transform:translateY(0) } }
        @keyframes scaleIn { from { opacity:0; transform:scale(0.97) } to { opacity:1; transform:scale(1) } }

        * { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body { margin:0; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

        /* Smooth panel entrances */
        .via-panel {
          animation: fadeUp 0.35s ease-out both;
          transition: box-shadow 0.25s ease, transform 0.2s ease, border-color 0.2s ease;
        }
        .via-panel:hover {
          box-shadow: 0 4px 20px rgba(26,54,104,0.06);
        }

        /* Stagger panels */
        .via-panel:nth-child(1) { animation-delay: 0s; }
        .via-panel:nth-child(2) { animation-delay: 0.06s; }
        .via-panel:nth-child(3) { animation-delay: 0.12s; }
        .via-panel:nth-child(4) { animation-delay: 0.18s; }
        .via-panel:nth-child(5) { animation-delay: 0.24s; }
        .via-panel:nth-child(6) { animation-delay: 0.30s; }

        /* Stat boxes */
        .via-stat {
          transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
        }
        .via-stat:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        /* Buttons and interactive elements */
        .via-pill {
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
          position: relative;
          overflow: hidden;
        }
        .via-pill:hover {
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .via-pill:active {
          transform: translateY(0);
        }

        /* Search input */
        .via-search-input {
          transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease !important;
        }
        .via-search-input:focus {
          border-color: #1a3668 !important;
          box-shadow: 0 0 0 3px rgba(26,54,104,0.08) !important;
          background: var(--via-panel) !important;
        }

        /* Search dropdown */
        .via-search-dropdown {
          animation: scaleIn 0.15s ease-out;
          transform-origin: top center;
          backdrop-filter: blur(8px);
        }

        /* Table rows */
        .via-table-wrap tr {
          transition: background 0.15s ease;
        }
        .via-table-wrap tbody tr:hover {
          background: rgba(200,16,46,0.04) !important;
        }
        .via-table-wrap tbody tr {
          cursor: pointer;
        }

        /* Tab bar */
        .via-tab {
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
          position: relative;
        }
        .via-tab::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          width: 0;
          height: 2px;
          background: #c8102e;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          transform: translateX(-50%);
        }
        .via-tab:hover::after, .via-tab-active::after {
          width: 100%;
        }

        /* Header */
        .via-header {
          backdrop-filter: blur(12px);
          position: sticky;
          top: 0;
          z-index: 100;
          transition: box-shadow 0.3s ease;
        }
        .via-header-scrolled {
          box-shadow: 0 2px 20px rgba(26,54,104,0.08);
        }

        /* Content area smooth entrance */
        .via-content {
          animation: fadeIn 0.3s ease-out;
        }

        /* Quick-pick buttons */
        .via-quick-pick {
          transition: all 0.2s ease !important;
        }
        .via-quick-pick:hover {
          border-color: #c8102e !important;
          color: #c8102e !important;
          transform: translateY(-1px);
          box-shadow: 0 2px 8px rgba(200,16,46,0.12);
        }

        /* Leaderboard filter pills */
        .via-filter-pill {
          transition: all 0.2s ease !important;
        }
        .via-filter-pill:hover {
          transform: scale(1.03);
        }

        /* Skeleton loading */
        .via-skeleton {
          background: linear-gradient(90deg, var(--via-hover) 25%, var(--via-bg) 50%, var(--via-hover) 75%);
          background-size: 800px 100%;
          animation: shimmer 1.5s infinite;
          border-radius: 6px;
        }

        /* Scrollbar styling */
        .via-table-wrap::-webkit-scrollbar { height: 6px; }
        .via-table-wrap::-webkit-scrollbar-track { background: var(--via-bg); border-radius: 3px; }
        .via-table-wrap::-webkit-scrollbar-thumb { background: #d4c9b5; border-radius: 3px; }
        .via-table-wrap::-webkit-scrollbar-thumb:hover { background: #8c8272; }

        /* Chart tooltip animation */
        .recharts-tooltip-wrapper {
          transition: transform 0.15s ease, opacity 0.15s ease !important;
        }

        /* Mobile menu smooth */
        @keyframes slideDown { from { opacity:0; transform:translateY(-10px) } to { opacity:1; transform:translateY(0) } }

        /* Card marketplace hover */
        .via-card-hover {
          transition: transform 0.25s ease, box-shadow 0.25s ease !important;
        }
        .via-card-hover:hover {
          transform: translateY(-4px) scale(1.01);
          box-shadow: 0 8px 30px rgba(26,54,104,0.12);
        }

        /* Focus ring */
        button:focus-visible, input:focus-visible {
          outline: 2px solid #1a3668;
          outline-offset: 2px;
        }

        /* Progress bar smooth */
        .via-progress-bar {
          transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Badge pop-in */
        .via-badge {
          animation: scaleIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) both;
        }

        /* Responsive refinements */
        @media (max-width: 768px) {
          .via-content { padding: 8px 12px 20px !important; }
          .via-header { padding: 12px 16px 0 !important; }
          .via-header-inner { flex-direction: row !important; align-items: center !important; gap: 8px !important; flex-wrap: nowrap !important; }
          .via-tabs { display: none !important; }
          .via-title { font-size: 28px !important; }
          .via-subtitle { font-size: 8px !important; letter-spacing: .14em !important; }
          .via-tagline { font-size: 7px !important; }
          .via-stat-row { gap: 4px !important; flex-wrap: wrap !important; justify-content: center !important; }
          .via-stat-box { min-width: 58px !important; padding: 6px 8px !important; }
          .via-stat-box .via-stat-val { font-size: 14px !important; }
          .via-stat-box .via-stat-label { font-size: 6px !important; }
          .via-panel { padding: 10px 12px !important; margin-bottom: 8px !important; }
          .via-footer { padding: 8px 12px !important; flex-direction: column !important; gap: 4px !important; text-align: center !important; }
          .via-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 0 -12px; padding: 0 12px; }
          .via-table-wrap table { min-width: 500px; }
          .via-table-wrap th, .via-table-wrap td { padding: 4px 6px !important; font-size: 10px !important; }
          .via-player-name { font-size: 20px !important; }
          .via-player-info { font-size: 10px !important; }
          .via-pos-filters { gap: 2px !important; }
          .via-pos-filters button { padding: 4px 8px !important; font-size: 9px !important; }
          .via-mode-toggle { gap: 2px !important; }
          .via-mode-toggle button { padding: 5px 12px !important; font-size: 10px !important; }
          .via-leaderboard-filters { flex-direction: column !important; gap: 8px !important; align-items: stretch !important; }
          .via-leaderboard-filters input { width: 100% !important; box-sizing: border-box !important; }
          /* Landing page grids → single column */
          .via-landing-2col { grid-template-columns: 1fr !important; }
          .via-compare-slots { grid-template-columns: 1fr !important; }
          .via-roster-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)) !important; }
          /* Arsenal grid: hide RV/100 and K% columns, reflow to 5-col */
          .via-arsenal-hide-sm { display: none !important; }
          .via-arsenal-row { grid-template-columns: minmax(80px,1fr) 44px 44px 44px 44px !important; }
          .via-quick-pick { padding: 6px 10px !important; font-size: 10px !important; }
          .via-engine-stats { gap: 12px !important; padding: 10px 14px !important; }
          .via-engine-stats > div { min-width: 60px !important; }
        }
        @media (max-width: 480px) {
          .via-title { font-size: 24px !important; }
          .via-stat-box { min-width: 50px !important; padding: 5px 6px !important; }
          .via-stat-box .via-stat-val { font-size: 12px !important; }
          .via-table-wrap th, .via-table-wrap td { padding: 3px 4px !important; font-size: 9px !important; }
          .via-player-name { font-size: 18px !important; }
          .via-engine-stats { gap: 8px !important; flex-wrap: wrap !important; }
          .via-quick-pick { padding: 5px 8px !important; font-size: 9px !important; }
        }
      `}</style>
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700;800&family=Changa+One&display=swap" rel="stylesheet"/>
      {/* Header */}
      <div className={`via-header ${scrolled?"via-header-scrolled":""}`} style={{padding:"14px 24px 0",borderBottom:`1.5px solid ${C.navy}20`,background:darkMode?C.bg:`linear-gradient(180deg, ${C.panel} 0%, ${C.bg} 100%)`,backdropFilter:"blur(12px)"}}>
        <div className="via-header-inner" style={{display:"flex",alignItems:"center",gap:14,marginBottom:12,flexWrap:"wrap"}}>
          <div onClick={goHome} style={{cursor:"pointer",userSelect:"none"}}>
            <div style={{display:"flex",alignItems:"baseline",gap:6}}>
              <span className="via-title" style={{fontFamily:"'Changa One', cursive",fontSize:38,fontWeight:400,color:C.navy,lineHeight:1,letterSpacing:"-0.02em",textShadow:`2px 2px 0 ${C.accent}30`}}>VIAcast</span>
              <span style={{width:8,height:8,borderRadius:"50%",background:C.accent,display:"inline-block",marginBottom:4}}/>
            </div>
            <p style={{margin:"1px 0 0 2px",fontSize:11,fontWeight:700,color:C.navy,letterSpacing:".06em",fontFamily:F,textTransform:"uppercase"}}>Baseball Projection Engine</p>
            <p style={{margin:"2px 0 0 2px",fontSize:9,color:C.muted,letterSpacing:".04em",fontFamily:F}}>Data-driven MLB &amp; MiLB forecasting</p>
          </div>
          {!isMobile&&<>
            {/* Theme toggle */}
            <button onClick={toggleTheme} style={{
              marginLeft:"auto",background:"none",border:`1.5px solid ${C.navy}30`,borderRadius:6,
              padding:"5px 8px",cursor:"pointer",fontSize:14,lineHeight:1,
              color:C.navy,transition:"all 0.2s",
            }} aria-label="Toggle dark mode" title={darkMode?"Light mode":"Dark mode"}>
              {darkMode?"☀️":"🌙"}
            </button>
            <div className="via-search"><PlayerSearch onSelect={pick}/></div>
          </>}
          {isMobile&&(
            <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:8}}>
              <button onClick={toggleTheme} style={{
                background:"none",border:`1.5px solid ${C.navy}30`,borderRadius:6,
                padding:"5px 8px",cursor:"pointer",fontSize:14,lineHeight:1,
                color:C.navy,
              }} aria-label="Toggle dark mode">
                {darkMode?"☀️":"🌙"}
              </button>
              <button onClick={()=>setMenuOpen(!menuOpen)} style={{
                background:"none",border:`1.5px solid ${C.navy}`,borderRadius:6,
                padding:"6px 10px",cursor:"pointer",display:"flex",flexDirection:"column",gap:3,alignItems:"center",justifyContent:"center",
              }} aria-label="Menu">
              <span style={{width:18,height:2,background:C.navy,borderRadius:1,transition:"all 0.2s",transform:menuOpen?"rotate(45deg) translate(3.5px,3.5px)":"none"}}/>
              <span style={{width:18,height:2,background:C.navy,borderRadius:1,transition:"all 0.2s",opacity:menuOpen?0:1}}/>
              <span style={{width:18,height:2,background:C.navy,borderRadius:1,transition:"all 0.2s",transform:menuOpen?"rotate(-45deg) translate(3.5px,-3.5px)":"none"}}/>
            </button>
            </div>
          )}
        </div>
        {/* Desktop: compact horizontal tabs */}
        {!isMobile&&(
          <div className="via-tabs" style={{display:"flex",gap:2,flexWrap:"nowrap"}}>
            {TABS.map(t=><button key={t.k} className={`via-tab ${tab===t.k?"via-tab-active":""}`} onClick={()=>switchTab(t.k)} style={{
              padding:"8px 16px",border:"none",cursor:"pointer",fontSize:10,fontWeight:tab===t.k?700:500,fontFamily:F,
              background:tab===t.k?C.panel:"transparent",color:tab===t.k?C.navy:C.muted,
              borderRadius:"8px 8px 0 0",borderBottom:"2px solid transparent",
              whiteSpace:"nowrap",letterSpacing:".03em",
            }}
            onMouseEnter={e=>{if(tab!==t.k){e.target.style.color=C.navy;e.target.style.background=C.hover;}}}
            onMouseLeave={e=>{if(tab!==t.k){e.target.style.color=C.muted;e.target.style.background="transparent";}}}
            >{t.l}</button>)}
          </div>
        )}
      {isMobile&&<div style={{display:"flex",justifyContent:"center",padding:"10px 16px",background:C.bg}}><div style={{width:"100%",maxWidth:400}}><PlayerSearch onSelect={pick}/></div></div>}
      </div>
      {/* Mobile: slide-down menu */}
      {isMobile&&menuOpen&&(
        <div style={{
          background:C.panel,borderBottom:`2px solid ${C.border}`,
          boxShadow:"0 4px 16px rgba(0,0,0,0.1)",
          animation:"slideDown 0.2s ease-out",
        }}>
          <style>{`@keyframes slideDown{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}`}</style>
          {TABS.map(t=>(
            <button key={t.k} onClick={()=>switchTab(t.k)} style={{
              display:"flex",alignItems:"center",gap:10,width:"100%",padding:"14px 24px",
              border:"none",cursor:"pointer",fontFamily:F,fontSize:13,fontWeight:tab===t.k?700:500,
              background:tab===t.k?`${C.accent}08`:"transparent",
              color:tab===t.k?C.navy:C.dim,
              borderLeft:tab===t.k?`3px solid ${C.accent}`:"3px solid transparent",
              transition:"all 0.15s ease",
            }}
            onMouseEnter={e=>{if(tab!==t.k)e.target.style.background=C.hover;}}
            onMouseLeave={e=>{if(tab!==t.k)e.target.style.background="transparent";}}
            >
              <span style={{fontSize:16}}>{t.icon}</span>
              {t.l}
            </button>
          ))}
        </div>
      )}
      {/* Click-away overlay for mobile menu */}
      {isMobile&&menuOpen&&(
        <div onClick={()=>setMenuOpen(false)} style={{
          position:"fixed",top:0,left:0,right:0,bottom:0,zIndex:-1,
        }}/>
      )}
      {/* Content */}
      <div className="via-content" style={{padding:"20px 28px 48px",maxWidth:1280,margin:"0 auto"}}>
        {tab==="player"&&<div>
          {!selPlayer&&!lp&&<div style={{display:"flex",flexDirection:"column",gap:14}}>
            {/* Hero */}
            <Panel style={{textAlign:"center",padding:"32px 28px 20px",background:`linear-gradient(180deg, ${C.bg} 0%, ${C.panel} 100%)`}}>
              <div style={{fontSize:11,fontWeight:700,letterSpacing:".15em",color:C.accent,fontFamily:F,textTransform:"uppercase",marginBottom:6}}>{PROJ_SEASON} Projections</div>
              <h2 style={{margin:0,fontSize:22,color:C.navy,fontFamily:F,lineHeight:1.3,letterSpacing:"-0.02em"}}>Statcast-Powered MLB Projections</h2>
              <p style={{margin:"8px auto 0",fontSize:11,color:C.dim,fontFamily:F,maxWidth:520,lineHeight:1.6}}>
                3 years of Baseball Savant data — expected stats, barrel rates, plate discipline, sprint speed. 900+ hitters, 1,200+ pitchers, all MiLB levels.
              </p>
            </Panel>

            {/* Ticker — live from FanGraphs leaders API */}
            <TickerBar/>

            {/* Player of the Day — full width horizontal */}
            <PlayerOfTheDay onSelect={pick}/>

            {/* Top Projections Grid — live from engine */}
            <LandingTopLists onSelect={pick}/>

            {/* Live fWAR Leaderboard */}
            <LiveWARBoard onSelect={pick}/>

            {/* Scorecard + prospects teasers (full versions live in their own tabs) */}
            <div style={{display:"flex",flexWrap:"wrap",gap:14}}>
              <Panel title="How did we do last year?" sub="Our 2026 projections, graded against what actually happened. The hits, the misses, and what we fixed." style={{flex:"1 1 300px",borderTop:`3px solid ${C.green}`,cursor:"pointer"}} onClick={()=>switchTab("scorecard")}>
                <span style={{fontSize:11,fontWeight:700,color:C.accent,fontFamily:F}}>See the 2026 scorecard →</span>
              </Panel>
              <Panel title="Top prospects" sub={`Ranked by FV grade heading into ${PROJ_SEASON}.`} style={{flex:"1 1 300px",borderTop:`3px solid ${C.accent}`}}>
                {(prospectsData.players||[]).filter(p=>!p.graduated).slice(0,5).map((p,i)=>(
                  <div key={p.id} onClick={()=>pickName(p.name,p.id)} style={{display:"flex",alignItems:"center",gap:10,padding:"7px 2px",cursor:"pointer",borderBottom:`1px solid ${C.border}30`}}>
                    <span style={{fontSize:12,fontWeight:800,color:C.muted,fontFamily:F,width:16,textAlign:"right"}}>{i+1}</span>
                    <FVBadge fv={p.fv}/>
                    <span style={{fontSize:12,fontWeight:700,color:C.text,fontFamily:F,flex:1}}>{p.name}</span>
                    <span style={{fontSize:9,color:C.muted,fontFamily:F}}>{p.pos} · {p.org}</span>
                  </div>
                ))}
                <div onClick={()=>switchTab("prospects")} style={{marginTop:10,fontSize:11,fontWeight:700,color:C.accent,fontFamily:F,cursor:"pointer"}}>All prospects →</div>
              </Panel>
            </div>

            {/* Engine Stats — subtle credibility bar */}
            <div style={{display:"flex",justifyContent:"center",gap:24,flexWrap:"wrap",padding:"12px 16px",opacity:0.6}}>
              {[
                {v:"900+",l:"Hitters"},{v:"1,200+",l:"Pitchers"},{v:"3 Years",l:"Savant Data"},{v:"All Levels",l:"ROK → MLB"},{v:"7 Layers",l:"Engine"},
              ].map(s=>(
                <div key={s.l} style={{textAlign:"center"}}>
                  <span style={{fontSize:13,fontWeight:700,color:C.navy,fontFamily:F}}>{s.v}</span>
                  <span style={{fontSize:8,color:C.muted,fontFamily:F,marginLeft:4,textTransform:"uppercase",letterSpacing:".06em"}}>{s.l}</span>
                </div>
              ))}
            </div>


          </div>}
          {lp&&<Spinner msg="Pulling career data..."/>}
          {selPlayer&&!lp&&detail&&<PlayerCard player={detail}/>}
        </div>}
        {tab==="leaders"&&<Leaderboard onSelect={pick}/>}
        {tab==="roster"&&<RosterBrowser onSelect={pick}/>}

        {tab==="prospects"&&<ProspectsPanel Panel={Panel} FVBadge={FVBadge} C={C} F={F} onPickName={pickName}/>}
        {tab==="scorecard"&&<ScorecardPanel Panel={Panel} C={C} F={F} onPickName={pickName}/>}
        {tab==="cost"&&<VpDPanel/>}
        
        {tab==="research"&&<ResearchPanel/>}
        {tab==="method"&&<MethodPanel/>}
      </div>
      <div className="via-footer" style={{padding:"12px 24px",borderTop:`2px solid ${C.navy}`,background:C.bg,display:"flex",justifyContent:"space-between",flexWrap:"wrap",gap:8}}>
        <span style={{fontSize:8,color:C.muted,fontFamily:F}}>VIAcast v2.1 &middot; Data: MLB Stats API &middot; FV: FanGraphs/ESPN consensus &middot; No affiliation with MLB</span>
        <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Methodology: VIAcast 7-layer Statcast engine + Marcel fallback</span>
        <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Questions or inquiries? <a href="mailto:trevanvia@gmail.com" style={{color:C.accent,textDecoration:"none"}}>trevanvia@gmail.com</a></span>
      </div>
    </div>
  );
}