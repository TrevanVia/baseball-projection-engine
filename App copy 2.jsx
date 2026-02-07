import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell, ComposedChart
} from "recharts";
import _ from "lodash";

// ── MLB STATS API ────────────────────────────────────────────────────────────
const API = "https://statsapi.mlb.com/api/v1";
const SPORT_IDS = { MLB: 1, AAA: 11, AA: 12, "A+": 13, A: 14, ROK: 16 };
const LEVEL_NAMES = { 1: "MLB", 11: "AAA", 12: "AA", 13: "A+", 14: "A", 16: "ROK" };
const LEVEL_ORDER = ["ROK", "A", "A+", "AA", "AAA", "MLB"];

// Translation factors: how MiLB stats convert to MLB equivalents
const LEVEL_TRANSLATION = {
  ROK: { factor: 0.40, wrcAdj: -35, reliability: 0.15, label: "Rookie" },
  A:   { factor: 0.50, wrcAdj: -25, reliability: 0.25, label: "Single-A" },
  "A+":{ factor: 0.58, wrcAdj: -18, reliability: 0.35, label: "High-A" },
  AA:  { factor: 0.68, wrcAdj: -10, reliability: 0.50, label: "Double-A" },
  AAA: { factor: 0.82, wrcAdj: -4,  reliability: 0.62, label: "Triple-A" },
  MLB: { factor: 1.00, wrcAdj: 0,   reliability: 0.80, label: "MLB" },
};

async function searchPlayers(query) {
  try {
    const res = await fetch(`${API}/people/search?names=${encodeURIComponent(query)}&sportIds=1,11,12,13,14,16&hydrate=currentTeam`);
    const data = await res.json();
    return (data.people || []).filter(p => p.primaryPosition?.code !== "1").slice(0, 25);
  } catch { return []; }
}

async function getPlayerStats(playerId) {
  try {
    const res = await fetch(`${API}/people/${playerId}?hydrate=currentTeam`);
    const data = await res.json();
    return data.people?.[0] || null;
  } catch { return null; }
}

async function getPlayerCareer(playerId) {
  // The MLB Stats API yearByYear endpoint only returns stats for one sportId at a time.
  // We query ALL levels in parallel and merge the results.
  const sportIds = [1, 11, 12, 13, 14, 16]; // MLB, AAA, AA, A+, A, ROK
  try {
    const promises = sportIds.map(sid =>
      fetch(`${API}/people/${playerId}/stats?stats=yearByYear&group=hitting&gameType=R&sportId=${sid}`)
        .then(r => r.json())
        .then(d => {
          const splits = d.stats?.[0]?.splits || [];
          // Tag each split with the sport info so we can detect the level
          return splits.map(s => ({ ...s, _sportId: sid }));
        })
        .catch(() => [])
    );
    const allResults = await Promise.all(promises);
    return allResults.flat();
  } catch { return []; }
}

async function getTeams(sportId = 1) {
  try {
    const res = await fetch(`${API}/teams?sportId=${sportId}&season=2025`);
    const data = await res.json();
    return (data.teams || []).sort((a, b) => a.name.localeCompare(b.name));
  } catch { return []; }
}

async function getTeamRoster(teamId) {
  try {
    const res = await fetch(`${API}/teams/${teamId}/roster/fullSeason?season=2025`);
    const data = await res.json();
    return data.roster || [];
  } catch { return []; }
}

async function getMiLBAffiliate(mlbTeamId) {
  try {
    const res = await fetch(`${API}/teams/affiliates?teamIds=${mlbTeamId}&season=2025&sportIds=11,12,13,14,16`);
    const data = await res.json();
    return (data.teams || []).sort((a, b) => (a.sport?.id || 99) - (b.sport?.id || 99));
  } catch { return []; }
}

// ── PROJECTION ENGINE ────────────────────────────────────────────────────────
const AGING_PARAMS = {
  C:  { peak: 27, dr: 0.042, pa: -12.5, dd: 0.06 },
  "1B":{ peak: 28, dr: 0.032, pa: -12.5, dd: 0.02 },
  "2B":{ peak: 27, dr: 0.038, pa: 2.5,   dd: 0.05 },
  "3B":{ peak: 27, dr: 0.035, pa: 2.5,   dd: 0.04 },
  SS: { peak: 26, dr: 0.040, pa: 7.5,   dd: 0.055 },
  LF: { peak: 28, dr: 0.033, pa: -7.5,  dd: 0.035 },
  CF: { peak: 27, dr: 0.037, pa: 2.5,   dd: 0.05 },
  RF: { peak: 28, dr: 0.034, pa: -7.5,  dd: 0.04 },
  DH: { peak: 29, dr: 0.030, pa: -17.5, dd: 0.0 },
};

function getAP(code) {
  const m = {"2":"C","3":"1B","4":"2B","5":"3B","6":"SS","7":"LF","8":"CF","9":"RF","10":"DH"};
  return AGING_PARAMS[m[code]||code] || { peak:28, dr:0.035, pa:0, dd:0.03 };
}
function posLabel(c) {
  const m = {"2":"C","3":"1B","4":"2B","5":"3B","6":"SS","7":"LF","8":"CF","9":"RF","10":"DH","Y":"OF","D":"IF"};
  return m[c]||c||"UT";
}

function detectLevel(split) {
  // Use our tagged _sportId first (from the parallel query approach)
  if (split._sportId) return LEVEL_NAMES[split._sportId] || "MLB";
  const sid = split.sport?.id || split.team?.sport?.id;
  return LEVEL_NAMES[sid] || "MLB";
}

function projectFromSeasons(splits, age, posCode) {
  const valid = splits
    .filter(s => s.stat?.plateAppearances > 30)
    .sort((a, b) => parseInt(b.season) - parseInt(a.season))
    .slice(0, 3);
  if (!valid.length) return null;

  const weights = [5, 4, 3];
  let tw = 0, wOPS = 0, wPA = 0, wHR = 0, wAVG = 0, wOBP = 0, wSLG = 0;
  let highestLevel = "ROK";

  valid.forEach((s, i) => {
    const w = weights[i] || 2;
    const st = s.stat;
    const lvl = detectLevel(s);
    if (LEVEL_ORDER.indexOf(lvl) > LEVEL_ORDER.indexOf(highestLevel)) highestLevel = lvl;

    const trans = LEVEL_TRANSLATION[lvl] || LEVEL_TRANSLATION.MLB;
    tw += w;
    wOPS += parseFloat(st.ops || 0) * trans.factor * w;
    wAVG += parseFloat(st.avg || 0) * trans.factor * w;
    wOBP += parseFloat(st.obp || 0) * trans.factor * w;
    wSLG += parseFloat(st.slg || 0) * trans.factor * w;
    wHR += (st.homeRuns || 0) * w;
    wPA += (st.plateAppearances || 0) * w;
  });

  const rawOPS = wOPS / tw;
  const rawPA = wPA / tw;
  const trans = LEVEL_TRANSLATION[highestLevel] || LEVEL_TRANSLATION.MLB;
  const paRel = Math.min(0.85, rawPA / 700) * (trans.reliability / 0.80);
  const lgOPS = 0.720;
  const regOPS = rawOPS * paRel + lgOPS * (1 - paRel);
  const regOBP = (wOBP/tw) * paRel + 0.315 * (1 - paRel);
  const regSLG = (wSLG/tw) * paRel + 0.405 * (1 - paRel);
  const wRCPlus = Math.round((regOPS / lgOPS) * 100) + (trans.wrcAdj * (1 - paRel));
  const ap = getAP(posCode);
  const estPA = highestLevel === "MLB" ? Math.min(680, rawPA * 0.95) : Math.min(600, rawPA * 0.85);
  const batRuns = ((wRCPlus - 100) / 100) * estPA * 0.12;
  const posAdj = ap.pa * (estPA / 600);
  const repl = 20 * (estPA / 600);
  const baseWAR = (batRuns + posAdj + repl) / 10;

  return {
    ops: regOPS, obp: regOBP, slg: regSLG,
    avg: (wAVG/tw) * paRel + 0.248 * (1 - paRel),
    wRCPlus: Math.round(wRCPlus),
    baseWAR: Math.round(baseWAR * 10) / 10,
    estPA: Math.round(estPA),
    hr: Math.round(wHR / tw * (estPA / Math.max(1, rawPA))),
    paReliability: Math.round(paRel * 100),
    highestLevel,
    translationNote: highestLevel !== "MLB"
      ? `Stats translated from ${trans.label} (${Math.round(trans.factor*100)}% factor)`
      : null,
  };
}

function projectForward(base, age, posCode, years = 10) {
  const ap = getAP(posCode);
  return Array.from({ length: years }, (_, yr) => {
    const a = age + yr;
    if (a > 42) return null;
    const d = a - ap.peak;
    const f = Math.max(0.25, d <= 0 ? 1 + 0.006 * Math.max(-3, -d) : 1 - ap.dr * d);
    const war = Math.max(-1, base.baseWAR * f);
    const wrc = Math.max(60, Math.round(100 + (base.wRCPlus - 100) * f));
    const ops = Math.max(0.500, base.ops * (0.5 + 0.5 * f));
    const ci = (0.8 + yr * 0.3) * (1.2 - base.paReliability / 100 * 0.5);
    return {
      age: a, year: 2026 + yr,
      war: Math.round(war*10)/10, warHigh: Math.round((war+ci)*10)/10, warLow: Math.round(Math.max(-2,war-ci)*10)/10,
      wrcPlus: wrc, wrcHigh: Math.min(200, wrc+Math.round(ci*12)), wrcLow: Math.max(50, wrc-Math.round(ci*12)),
      ops: Math.round(ops*1000)/1000, opsHigh: Math.round(Math.min(1.2,ops+ci*.025)*1000)/1000, opsLow: Math.round(Math.max(.45,ops-ci*.025)*1000)/1000,
    };
  }).filter(Boolean);
}

// ── STYLES ───────────────────────────────────────────────────────────────────
const C = {
  bg:"#0f1729", panel:"#1a2440", border:"#2a3a5c", hover:"#223050",
  accent:"#fb923c", blue:"#60a5fa", green:"#4ade80", red:"#f87171",
  yellow:"#facc15", purple:"#c084fc", cyan:"#22d3ee", pink:"#f472b6",
  text:"#f8fafc", dim:"#cbd5e1", muted:"#7590b8", grid:"#2a3a5c",
};
const F = "'IBM Plex Mono', monospace";
const LEVEL_COLORS = { ROK:"#b0b8c8", A:"#22d3ee", "A+":"#60a5fa", AA:"#c084fc", AAA:"#facc15", MLB:"#4ade80" };

// ── COMPONENTS ───────────────────────────────────────────────────────────────
const Panel = ({children,title,sub,style={}}) => (
  <div style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:10,padding:"16px 20px",...style}}>
    {title&&<div style={{marginBottom:sub?4:12}}>
      <h3 style={{margin:0,fontSize:13,fontWeight:700,color:C.text,letterSpacing:".06em",fontFamily:F}}>{title}</h3>
      {sub&&<p style={{margin:"3px 0 10px",fontSize:11,color:C.muted,lineHeight:1.4,fontFamily:F}}>{sub}</p>}
    </div>}
    {children}
  </div>
);
const Stat = ({label,value,color=C.accent,sub}) => (
  <div style={{padding:"8px 12px",background:`${color}08`,borderRadius:8,border:`1px solid ${color}20`,minWidth:70,textAlign:"center"}}>
    <div style={{fontSize:20,fontWeight:800,color,fontFamily:F}}>{value}</div>
    <div style={{fontSize:8,color:C.muted,marginTop:1,textTransform:"uppercase",letterSpacing:".08em",fontFamily:F}}>{label}</div>
    {sub&&<div style={{fontSize:8,color:C.dim,fontFamily:F}}>{sub}</div>}
  </div>
);
const Pill = ({label,active,onClick,color=C.accent}) => (
  <button onClick={onClick} style={{padding:"5px 14px",border:"none",borderRadius:6,cursor:"pointer",fontSize:11,fontWeight:active?700:500,fontFamily:F,background:active?color:"#152238",color:active?"#fff":C.muted}}>{label}</button>
);
const LevelBadge = ({level}) => (
  <span style={{fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:4,fontFamily:F,background:`${LEVEL_COLORS[level]||C.muted}20`,color:LEVEL_COLORS[level]||C.muted}}>{level}</span>
);
const Spinner = ({msg="Loading..."}) => (
  <div style={{display:"flex",alignItems:"center",gap:8,padding:20,color:C.dim,fontFamily:F,fontSize:12}}>
    <div style={{width:16,height:16,border:`2px solid ${C.border}`,borderTopColor:C.accent,borderRadius:"50%",animation:"spin .8s linear infinite"}}/>
    {msg}
    <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
  </div>
);
const Tip = ({active,payload,label}) => {
  if(!active||!payload?.length) return null;
  return <div style={{background:"#1e3050",border:`1px solid ${C.border}`,borderRadius:8,padding:"8px 12px",boxShadow:"0 8px 24px rgba(0,0,0,.5)"}}>
    <div style={{fontSize:10,color:C.dim,marginBottom:4,fontFamily:F}}>{label}</div>
    {payload.filter(p=>p.value!=null).map((p,i)=><div key={i} style={{fontSize:11,color:p.color||C.text,fontFamily:F,margin:"1px 0"}}>{p.name}: <strong>{typeof p.value==="number"&&p.value<5?p.value.toFixed(3):p.value}</strong></div>)}
  </div>;
};

// ── PLAYER SEARCH ────────────────────────────────────────────────────────────
function PlayerSearch({onSelect}) {
  const [q,setQ]=useState(""); const [res,setRes]=useState([]); const [loading,setLoading]=useState(false); const [open,setOpen]=useState(false); const t=useRef(null);
  const search=useCallback(v=>{if(v.length<2){setRes([]);return;}setLoading(true);searchPlayers(v).then(r=>{setRes(r);setLoading(false);setOpen(true);});},[]);
  return (
    <div style={{position:"relative",flex:1,maxWidth:440}}>
      <input value={q} onChange={e=>{setQ(e.target.value);clearTimeout(t.current);t.current=setTimeout(()=>search(e.target.value),350);}}
        onFocus={()=>res.length>0&&setOpen(true)} placeholder="Search any MLB or MiLB player..."
        style={{width:"100%",padding:"10px 14px 10px 36px",borderRadius:8,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:13,fontFamily:F,outline:"none",boxSizing:"border-box"}}/>
      <span style={{position:"absolute",left:12,top:"50%",transform:"translateY(-50%)",fontSize:14,opacity:.4}}>&#9918;</span>
      {loading&&<span style={{position:"absolute",right:12,top:"50%",transform:"translateY(-50%)",fontSize:10,color:C.accent,fontFamily:F}}>searching...</span>}
      {open&&res.length>0&&<div style={{position:"absolute",top:"100%",left:0,right:0,zIndex:50,background:"#1e3050",border:`1px solid ${C.border}`,borderRadius:8,maxHeight:360,overflowY:"auto",marginTop:4,boxShadow:"0 12px 40px rgba(0,0,0,.5)"}}>
        {res.map(p=><div key={p.id} onClick={()=>{onSelect(p);setOpen(false);setQ(p.fullName);}} style={{padding:"10px 14px",cursor:"pointer",borderBottom:`1px solid ${C.border}15`}} onMouseEnter={e=>e.currentTarget.style.background=C.hover} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
          <div style={{display:"flex",alignItems:"center",gap:8}}>
            <span style={{fontSize:13,fontWeight:600,color:C.text,fontFamily:F}}>{p.fullName}</span>
            {p.currentTeam?.sport?.id&&p.currentTeam.sport.id!==1&&<LevelBadge level={LEVEL_NAMES[p.currentTeam.sport.id]||"MiLB"}/>}
          </div>
          <div style={{fontSize:10,color:C.muted,fontFamily:F,marginTop:2}}>
            {posLabel(p.primaryPosition?.code)} &middot; {p.currentTeam?.name||"FA"} &middot; Age {p.currentAge}
          </div>
        </div>)}
      </div>}
    </div>
  );
}

// ── PLAYER CARD ──────────────────────────────────────────────────────────────
function PlayerCard({player}) {
  const [career,setCareer]=useState([]); const [loading,setLoading]=useState(true); const [projTab,setProjTab]=useState("war");
  useEffect(()=>{
    setLoading(true);
    getPlayerCareer(player.id).then(s=>{
      console.log("[VIA Debug] Career splits received:", s.length, s.slice(0,2).map(x=>({season:x.season, sportId:x._sportId, pa:x.stat?.plateAppearances})));
      setCareer(s);
      setLoading(false);
    }).catch(err=>{
      console.error("[VIA Debug] getPlayerCareer failed:", err);
      setLoading(false);
    });
  },[player.id]);

  const seasons = useMemo(()=>{
    const result = career.filter(s=>s.stat?.plateAppearances>0).map(s=>{
      const lvl = detectLevel(s);
      return {
        season:s.season, age:player.currentAge-(2025-parseInt(s.season)),
        avg:parseFloat(s.stat.avg||0), obp:parseFloat(s.stat.obp||0), slg:parseFloat(s.stat.slg||0), ops:parseFloat(s.stat.ops||0),
        hr:s.stat.homeRuns||0, pa:s.stat.plateAppearances||0, r:s.stat.runs||0, rbi:s.stat.rbi||0,
        bb:s.stat.baseOnBalls||0, so:s.stat.strikeOuts||0, sb:s.stat.stolenBases||0,
        team:s.team?.abbreviation||"", level:lvl,
      };
    }).sort((a,b)=>parseInt(a.season)-parseInt(b.season));
    console.log("[VIA Debug] Seasons processed:", result.length, result.map(s=>({season:s.season,level:s.level,pa:s.pa})));
    return result;
  },[career,player]);

  const base = useMemo(()=>{
    const result = career.length?projectFromSeasons(career,player.currentAge,player.primaryPosition?.code):null;
    console.log("[VIA Debug] Base projection:", result, "career.length:", career.length, "age:", player.currentAge, "pos:", player.primaryPosition?.code);
    return result;
  },[career,player]);
  const forward = useMemo(()=>base?projectForward(base,player.currentAge,player.primaryPosition?.code):[], [base,player]);
  const peak = forward.length?forward.reduce((b,d)=>d.war>b.war?d:b,forward[0]):null;
  const cum = forward.reduce((s,d)=>s+Math.max(0,d.war),0);
  const isMiLB = seasons.length>0 && !seasons.some(s=>s.level==="MLB");

  if(loading) return <Spinner msg="Pulling career stats from MLB Stats API..."/>;

  return (
    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      {/* Header */}
      <Panel>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:12}}>
          <div>
            <div style={{display:"flex",alignItems:"center",gap:10}}>
              <h2 style={{margin:0,fontSize:22,fontWeight:800,color:C.text,fontFamily:F}}>{player.fullName}</h2>
              {isMiLB&&<LevelBadge level={base?.highestLevel||"MiLB"}/>}
            </div>
            <p style={{margin:"3px 0 0",fontSize:12,color:C.dim,fontFamily:F}}>
              {posLabel(player.primaryPosition?.code)} &middot; {player.currentTeam?.name||"Free Agent"} &middot; Age {player.currentAge}
              {player.batSide?.code?` \u00b7 Bats: ${player.batSide.code}`:""}
              {player.height?` \u00b7 ${player.height}`:""}
              {player.weight?` / ${player.weight} lbs`:""}
            </p>
          </div>
          <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
            {base&&<>
              <Stat label="Proj WAR" value={base.baseWAR.toFixed(1)} color={base.baseWAR>=4?C.green:base.baseWAR>=2?C.blue:C.yellow}/>
              <Stat label="Proj wRC+" value={base.wRCPlus} color={base.wRCPlus>=120?C.green:base.wRCPlus>=100?C.blue:C.yellow}/>
              <Stat label="Proj OPS" value={base.ops.toFixed(3)} color={base.ops>=.85?C.green:base.ops>=.73?C.blue:C.yellow}/>
              {peak&&<Stat label="Peak Age" value={peak.age} color={C.cyan}/>}
              <Stat label="Cum WAR" value={cum.toFixed(1)} color={C.purple}/>
            </>}
          </div>
        </div>
        {base&&<div style={{marginTop:10,padding:"7px 12px",background:`${isMiLB?C.purple:C.accent}08`,borderRadius:6,border:`1px solid ${isMiLB?C.purple:C.accent}15`}}>
          <span style={{fontSize:10,color:C.muted,fontFamily:F}}>
            {base.paReliability}% reliability &middot; {seasons.length} seasons &middot; Marcel 5/4/3 weighting
            {base.translationNote&&<span style={{color:LEVEL_COLORS[base.highestLevel]}}> &middot; {base.translationNote}</span>}
          </span>
        </div>}
      </Panel>

      {/* Career Stats */}
      {seasons.length>0&&<Panel title="CAREER STATS" sub={isMiLB?"Minor league stats shown with level indicators. Translation factors applied in projections.":"Year-by-year from MLB Stats API."}>
        <div style={{overflowX:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11}}>
            <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
              {["Year","Age","Tm","Lvl","PA","AVG","OBP","SLG","OPS","HR","R","RBI","BB","SO","SB"].map(h=>
                <th key={h} style={{padding:"5px 7px",textAlign:["Year","Tm","Lvl"].includes(h)?"left":"right",color:C.muted,fontWeight:600,fontSize:9,letterSpacing:".04em"}}>{h}</th>
              )}
            </tr></thead>
            <tbody>{seasons.map((s,i)=>(
              <tr key={i} style={{borderBottom:`1px solid ${C.border}20`,background:i%2===0?`${C.bg}80`:"transparent"}}>
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

      {/* OPS Chart */}
      {seasons.length>=2&&<Panel title="OPS TRAJECTORY">
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={seasons} margin={{top:10,right:20,left:0,bottom:0}}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.grid}/>
            <XAxis dataKey="season" stroke={C.muted} fontSize={10} fontFamily={F}/>
            <YAxis stroke={C.muted} fontSize={10} fontFamily={F}/>
            <Tooltip content={<Tip/>}/>
            <ReferenceLine y={.720} stroke={C.muted} strokeDasharray="5 5"/>
            <Bar dataKey="ops" radius={[3,3,0,0]} name="OPS" barSize={22}>
              {seasons.map((s,i)=><Cell key={i} fill={LEVEL_COLORS[s.level]||C.accent} fillOpacity={.7}/>)}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
        <div style={{display:"flex",gap:10,marginTop:8,flexWrap:"wrap"}}>
          {Object.entries(LEVEL_COLORS).map(([k,v])=><span key={k} style={{fontSize:9,color:v,fontFamily:F}}>&#9632; {k}</span>)}
        </div>
      </Panel>}

      {/* Projections */}
      {forward.length>0&&<>
        <div style={{display:"flex",gap:4,background:"#121e34",borderRadius:8,padding:3,width:"fit-content"}}>
          {[{k:"war",l:"WAR"},{k:"wrc",l:"wRC+"},{k:"ops",l:"OPS"}].map(t=><Pill key={t.k} label={t.l} active={projTab===t.k} onClick={()=>setProjTab(t.k)}/>)}
        </div>
        <Panel title={`PROJECTED ${projTab.toUpperCase()} (90% CI)`} sub={`Marcel projection${base?.translationNote?` with ${base.highestLevel} translation`:""} + position-specific aging.`}>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={forward} margin={{top:10,right:30,left:0,bottom:0}}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid}/>
              <XAxis dataKey="age" stroke={C.muted} fontSize={10} fontFamily={F}/>
              <YAxis stroke={C.muted} fontSize={10} fontFamily={F}/>
              <Tooltip content={<Tip/>}/>
              {projTab==="war"&&<><Area type="monotone" dataKey="warHigh" stroke="none" fill={`${C.blue}18`} name="90th"/><Area type="monotone" dataKey="warLow" stroke="none" fill={C.panel} name="10th"/><Line type="monotone" dataKey="war" stroke={C.blue} strokeWidth={2.5} dot={{r:3,fill:C.blue}} name="WAR"/><ReferenceLine y={0} stroke={C.muted} strokeDasharray="5 5"/><ReferenceLine y={2} stroke={C.green} strokeDasharray="3 3" strokeOpacity={.4}/></>}
              {projTab==="wrc"&&<><Area type="monotone" dataKey="wrcHigh" stroke="none" fill={`${C.green}18`} name="90th"/><Area type="monotone" dataKey="wrcLow" stroke="none" fill={C.panel} name="10th"/><Line type="monotone" dataKey="wrcPlus" stroke={C.green} strokeWidth={2.5} dot={{r:3,fill:C.green}} name="wRC+"/><ReferenceLine y={100} stroke={C.muted} strokeDasharray="5 5"/></>}
              {projTab==="ops"&&<><Area type="monotone" dataKey="opsHigh" stroke="none" fill={`${C.purple}18`} name="90th"/><Area type="monotone" dataKey="opsLow" stroke="none" fill={C.panel} name="10th"/><Line type="monotone" dataKey="ops" stroke={C.purple} strokeWidth={2.5} dot={{r:3,fill:C.purple}} name="OPS"/><ReferenceLine y={.720} stroke={C.muted} strokeDasharray="5 5"/></>}
            </AreaChart>
          </ResponsiveContainer>
        </Panel>
      </>}

      {/* Translation factors */}
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
      <Panel title="SELECT MLB ORGANIZATION">
        <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
          {teams.map(t=><button key={t.id} onClick={()=>pickTeam(t)} style={{
            padding:"4px 10px",fontSize:10,fontWeight:600,fontFamily:F,borderRadius:4,cursor:"pointer",border:"none",
            background:selTeam?.id===t.id?C.accent:"#152238",color:selTeam?.id===t.id?"#000":C.muted,
          }}>{t.abbreviation}</button>)}
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
          {roster.filter(r=>r.person&&r.position?.code!=="1").map(r=>(
            <div key={r.person.id} onClick={()=>onSelect(r.person)}
              style={{padding:"7px 11px",background:"#121e34",borderRadius:6,cursor:"pointer",border:`1px solid ${C.border}`,transition:"border-color .1s"}}
              onMouseEnter={e=>e.currentTarget.style.borderColor=LEVEL_COLORS[viewLevel]||C.accent}
              onMouseLeave={e=>e.currentTarget.style.borderColor=C.border}>
              <div style={{fontSize:12,fontWeight:700,color:C.text,fontFamily:F}}>{r.person.fullName}</div>
              <div style={{fontSize:10,color:C.muted,fontFamily:F}}>{posLabel(r.position?.code)} &middot; #{r.jerseyNumber||"\u2014"}</div>
            </div>
          ))}
        </div>
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
function MethodPanel() {
  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
    <Panel title="DATA SOURCES">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8}}>
        {[
          {n:"MLB Stats API",d:"Player search, career stats, MiLB rosters across all levels (ROK→AAA). Free, no auth.",c:C.blue,s:"LIVE"},
          {n:"pybaseball",d:"FanGraphs scraper: wRC+, fWAR, Statcast batted-ball data, 300+ cols.",c:C.green,s:"PIPELINE"},
          {n:"FanGraphs MiLB",d:"Minor league leaderboards with advanced stats. CSV export.",c:C.accent,s:"PIPELINE"},
          {n:"Baseball Savant",d:"Statcast: xwOBA, barrel%, exit velocity, sprint speed.",c:C.purple,s:"PLANNED"},
        ].map(s=><div key={s.n} style={{padding:"12px 14px",background:`${s.c}06`,border:`1px solid ${s.c}18`,borderRadius:8}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:4}}>
            <span style={{fontSize:12,fontWeight:700,color:s.c,fontFamily:F}}>{s.n}</span>
            <span style={{fontSize:7,fontWeight:700,padding:"2px 5px",borderRadius:3,fontFamily:F,background:s.s==="LIVE"?`${C.green}20`:`${C.yellow}20`,color:s.s==="LIVE"?C.green:C.yellow}}>{s.s}</span>
          </div>
          <p style={{margin:0,fontSize:10,color:C.dim,lineHeight:1.5,fontFamily:F}}>{s.d}</p>
        </div>)}
      </div>
    </Panel>
    <Panel title="MINOR LEAGUE TRANSLATION">
      <p style={{fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F,margin:"0 0 12px"}}>
        MiLB stats are <span style={{color:C.text}}>not directly comparable</span> to MLB. A .300 hitter in A-ball is not a .300 MLB hitter.
        The system applies level-specific translation factors derived from historical promotion data:
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
    <Panel title="PROJECTION METHODOLOGY">
      <div style={{fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F}}>
        <h4 style={{color:C.accent,fontSize:13,margin:"0 0 4px"}}>Marcel Weighting</h4>
        <p style={{margin:"0 0 12px"}}>3 most recent seasons weighted 5/4/3, regressed to league mean based on PA reliability. MiLB seasons are translated before weighting.</p>
        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>WAR Construction</h4>
        <p style={{margin:"0 0 12px"}}>Batting runs (from wRC+) + positional adjustment (FanGraphs scale) + replacement level, divided by ~10 runs/win.</p>
        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>Aging Curves</h4>
        <p style={{margin:"0 0 12px"}}>Offensive: quadratic decay past peak. Defensive: linear. Position-specific rates. Catchers steepest, DH gentlest.</p>
        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Confidence Intervals</h4>
        <p style={{margin:0}}>90% CIs expand ~30%/yr. MiLB projections have wider CIs due to lower reliability. The distribution matters more than the point estimate.</p>
      </div>
    </Panel>
  </div>;
}

// ── MAIN APP ─────────────────────────────────────────────────────────────────
const TABS=[
  {k:"player",l:"Player Projections"},
  {k:"roster",l:"MLB & MiLB Rosters"},
  {k:"aging",l:"Aging Curves"},
  {k:"method",l:"Methodology"},
];

export default function App() {
  const [tab,setTab]=useState("player");
  const [selPlayer,setSelPlayer]=useState(null);
  const [detail,setDetail]=useState(null);
  const [lp,setLp]=useState(false);

  const pick=useCallback(p=>{setSelPlayer(p);setLp(true);setTab("player");getPlayerStats(p.id).then(d=>{setDetail(d||p);setLp(false);});},[]);

  return (
    <div style={{minHeight:"100vh",background:C.bg,color:C.text,fontFamily:F}}>
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
      {/* Header */}
      <div style={{padding:"16px 24px 0",borderBottom:`1px solid ${C.border}`}}>
        <div style={{display:"flex",alignItems:"center",gap:14,marginBottom:12,flexWrap:"wrap"}}>
          <div>
            <h1 style={{margin:0,fontSize:22,fontWeight:800,letterSpacing:"-.01em",background:`linear-gradient(135deg,${C.accent},${C.yellow})`,WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent"}}>
              VIA PROJECTIONS
            </h1>
            <p style={{margin:"1px 0 0",fontSize:9,color:C.muted,letterSpacing:".06em"}}>MLB &amp; MiLB &middot; MARCEL ENGINE &middot; WAR / wRC+ / OPS &middot; ROOKIE BALL THROUGH THE SHOW</p>
          </div>
          <div style={{marginLeft:"auto"}}><PlayerSearch onSelect={pick}/></div>
        </div>
        <div style={{display:"flex",gap:2}}>
          {TABS.map(t=><button key={t.k} onClick={()=>setTab(t.k)} style={{
            padding:"7px 16px",border:"none",cursor:"pointer",fontSize:11,fontWeight:tab===t.k?700:500,fontFamily:F,
            background:tab===t.k?C.panel:"transparent",color:tab===t.k?C.text:C.muted,
            borderRadius:"6px 6px 0 0",borderBottom:tab===t.k?`2px solid ${C.accent}`:"2px solid transparent",
          }}>{t.l}</button>)}
        </div>
      </div>
      {/* Content */}
      <div style={{padding:"16px 24px 40px"}}>
        {tab==="player"&&<div>
          {!selPlayer&&!lp&&<Panel style={{textAlign:"center",padding:50}}>
            <div style={{fontSize:44,marginBottom:12}}>&#9918;</div>
            <h3 style={{margin:0,fontSize:16,color:C.text,fontFamily:F}}>Search any MLB or minor league player</h3>
            <p style={{margin:"6px auto 0",fontSize:12,color:C.muted,fontFamily:F,maxWidth:520,lineHeight:1.6}}>
              Covers all levels from Rookie ball through the majors. MiLB stats are translated using level-specific conversion factors before projection.
            </p>
            <div style={{marginTop:20,display:"flex",gap:8,justifyContent:"center",flexWrap:"wrap"}}>
              {["Juan Soto","Shohei Ohtani","Julio Rodriguez","Gunnar Henderson","Jackson Holliday","Junior Caminero"].map(n=>
                <button key={n} onClick={()=>searchPlayers(n).then(r=>{if(r[0])pick(r[0]);})}
                  style={{padding:"5px 12px",borderRadius:6,border:`1px solid ${C.border}`,background:"transparent",color:C.dim,fontSize:11,fontFamily:F,cursor:"pointer"}}
                  onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.color=C.accent;}}
                  onMouseLeave={e=>{e.target.style.borderColor=C.border;e.target.style.color=C.dim;}}
                >{n}</button>
              )}
            </div>
          </Panel>}
          {lp&&<Spinner msg="Pulling career data..."/>}
          {selPlayer&&!lp&&detail&&<PlayerCard player={detail}/>}
        </div>}
        {tab==="roster"&&<RosterBrowser onSelect={pick}/>}
        {tab==="aging"&&<AgingPanel/>}
        {tab==="method"&&<MethodPanel/>}
      </div>
      <div style={{padding:"12px 24px",borderTop:`1px solid ${C.border}`,display:"flex",justifyContent:"space-between",flexWrap:"wrap",gap:8}}>
        <span style={{fontSize:8,color:C.muted,fontFamily:F}}>VIA PROJECTIONS &middot; Data: MLB Stats API (statsapi.mlb.com) &middot; No affiliation with MLB</span>
        <span style={{fontSize:8,color:C.muted,fontFamily:F}}>Methodology: Marcel (Tango) + level translation factors</span>
      </div>
    </div>
  );
}
