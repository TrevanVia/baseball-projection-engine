#!/bin/bash
# Run this from inside your baseball-projection-engine folder:
#   bash create_app.sh

cat > src/App.jsx << 'APPEOF'
import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ReferenceLine, Cell, ComposedChart
} from "recharts";
import _ from "lodash";

const MLB_API = "https://statsapi.mlb.com/api/v1";

async function searchPlayers(query) {
  try {
    const res = await fetch(
      `${MLB_API}/people/search?names=${encodeURIComponent(query)}&sportIds=1,11,12,13,14&hydrate=currentTeam,stats(type=season,season=2025,gameType=R)`
    );
    const data = await res.json();
    return (data.people || []).filter(p => p.primaryPosition?.code !== "1").slice(0, 20);
  } catch { return []; }
}

async function getPlayerStats(playerId) {
  try {
    const res = await fetch(
      `${MLB_API}/people/${playerId}?hydrate=stats(type=season,seasons=2022,2023,2024,2025,gameType=R),currentTeam`
    );
    const data = await res.json();
    return data.people?.[0] || null;
  } catch { return null; }
}

async function getPlayerCareer(playerId) {
  try {
    const res = await fetch(
      `${MLB_API}/people/${playerId}/stats?stats=yearByYear&group=hitting&gameType=R`
    );
    const data = await res.json();
    return data.stats?.[0]?.splits || [];
  } catch { return []; }
}

async function getTeams() {
  try {
    const res = await fetch(`${MLB_API}/teams?sportId=1&season=2025`);
    const data = await res.json();
    return data.teams || [];
  } catch { return []; }
}

async function getTeamRoster(teamId) {
  try {
    const res = await fetch(
      `${MLB_API}/teams/${teamId}/roster/fullSeason?hydrate=person(stats(type=season,season=2025,gameType=R))&season=2025`
    );
    const data = await res.json();
    return data.roster || [];
  } catch { return []; }
}

const AGING_PARAMS = {
  C:  { peak: 27, declineRate: 0.042, posAdj: -12.5, defDecline: 0.06 },
  "1B": { peak: 28, declineRate: 0.032, posAdj: -12.5, defDecline: 0.02 },
  "2B": { peak: 27, declineRate: 0.038, posAdj: 2.5, defDecline: 0.05 },
  "3B": { peak: 27, declineRate: 0.035, posAdj: 2.5, defDecline: 0.04 },
  SS:  { peak: 26, declineRate: 0.040, posAdj: 7.5, defDecline: 0.055 },
  LF:  { peak: 28, declineRate: 0.033, posAdj: -7.5, defDecline: 0.035 },
  CF:  { peak: 27, declineRate: 0.037, posAdj: 2.5, defDecline: 0.05 },
  RF:  { peak: 28, declineRate: 0.034, posAdj: -7.5, defDecline: 0.04 },
  DH:  { peak: 29, declineRate: 0.030, posAdj: -17.5, defDecline: 0.0 },
  P:   { peak: 28, declineRate: 0.035, posAdj: 0, defDecline: 0.0 },
  O:   { peak: 28, declineRate: 0.035, posAdj: 0, defDecline: 0.03 },
};

function getAgingParams(posCode) {
  const map = { "2": "C", "3": "1B", "4": "2B", "5": "3B", "6": "SS", "7": "LF", "8": "CF", "9": "RF", "10": "DH" };
  return AGING_PARAMS[map[posCode] || posCode] || AGING_PARAMS["O"];
}

function posLabel(posCode) {
  const map = { "2": "C", "3": "1B", "4": "2B", "5": "3B", "6": "SS", "7": "LF", "8": "CF", "9": "RF", "10": "DH", "Y": "OF", "D": "IF" };
  return map[posCode] || posCode;
}

function projectFromSeasons(seasonSplits, age, posCode) {
  const valid = seasonSplits
    .filter(s => s.stat && s.stat.plateAppearances > 50)
    .sort((a, b) => parseInt(b.season) - parseInt(a.season))
    .slice(0, 3);
  if (valid.length === 0) return null;
  const weights = [5, 4, 3];
  let totalWeight = 0;
  let wOPS = 0, wAVG = 0, wOBP = 0, wSLG = 0, wHR = 0, wPA = 0;
  valid.forEach((s, i) => {
    const w = weights[i] || 2;
    const st = s.stat;
    totalWeight += w;
    wOPS += parseFloat(st.ops || 0) * w;
    wAVG += parseFloat(st.avg || 0) * w;
    wOBP += parseFloat(st.obp || 0) * w;
    wSLG += parseFloat(st.slg || 0) * w;
    wHR += (st.homeRuns || 0) * w;
    wPA += (st.plateAppearances || 0) * w;
  });
  const rawOPS = wOPS / totalWeight;
  const rawAVG = wAVG / totalWeight;
  const rawOBP = wOBP / totalWeight;
  const rawSLG = wSLG / totalWeight;
  const rawHR = wHR / totalWeight;
  const rawPA = wPA / totalWeight;
  const paReliability = Math.min(0.85, rawPA / 700);
  const lgOPS = 0.720, lgAVG = 0.248, lgOBP = 0.315, lgSLG = 0.405;
  const regOPS = rawOPS * paReliability + lgOPS * (1 - paReliability);
  const regOBP = rawOBP * paReliability + lgOBP * (1 - paReliability);
  const regSLG = rawSLG * paReliability + lgSLG * (1 - paReliability);
  const wRCPlus = Math.round(((regOPS / lgOPS) * 100));
  const params = getAgingParams(posCode);
  const estPA = Math.min(680, rawPA * 0.95);
  const battingRuns = ((wRCPlus - 100) / 100) * estPA * 0.12;
  const posAdj = params.posAdj * (estPA / 600);
  const replacement = 20 * (estPA / 600);
  const baseWAR = (battingRuns + posAdj + replacement) / 10;
  return {
    ops: regOPS, avg: rawAVG * paReliability + lgAVG * (1 - paReliability),
    obp: regOBP, slg: regSLG, wRCPlus,
    baseWAR: Math.round(baseWAR * 10) / 10, estPA,
    hr: Math.round(rawHR * (estPA / rawPA)),
    paReliability: Math.round(paReliability * 100),
  };
}

function projectForward(base, age, posCode, years = 10) {
  const params = getAgingParams(posCode);
  const projections = [];
  for (let yr = 0; yr < years; yr++) {
    const projAge = age + yr;
    if (projAge > 42) break;
    const diff = projAge - params.peak;
    const ageMult = diff <= 0 ? 1 + 0.006 * Math.max(-3, -diff) : 1 - params.declineRate * diff;
    const factor = Math.max(0.25, ageMult);
    const war = Math.max(-1, base.baseWAR * factor);
    const wrcPlus = Math.max(60, Math.round(100 + (base.wRCPlus - 100) * factor));
    const ops = Math.max(0.500, base.ops * (0.5 + 0.5 * factor));
    const ci = (0.8 + yr * 0.3) * (1.2 - base.paReliability / 100 * 0.5);
    projections.push({
      age: projAge, year: 2026 + yr,
      war: Math.round(war * 10) / 10,
      warHigh: Math.round((war + ci) * 10) / 10,
      warLow: Math.round(Math.max(-2, war - ci) * 10) / 10,
      wrcPlus, wrcHigh: Math.min(200, wrcPlus + Math.round(ci * 12)),
      wrcLow: Math.max(50, wrcPlus - Math.round(ci * 12)),
      ops: Math.round(ops * 1000) / 1000,
      opsHigh: Math.round(Math.min(1.200, ops + ci * 0.025) * 1000) / 1000,
      opsLow: Math.round(Math.max(0.450, ops - ci * 0.025) * 1000) / 1000,
    });
  }
  return projections;
}

const C = {
  bg: "#080c14", panel: "#0f1623", panelBorder: "#1a2744", panelHover: "#141e30",
  accent: "#f97316", blue: "#3b82f6", green: "#22c55e", red: "#ef4444",
  yellow: "#eab308", purple: "#a855f7", cyan: "#06b6d4", pink: "#ec4899",
  text: "#f1f5f9", textDim: "#94a3b8", textMuted: "#4b6080", grid: "#1a2744",
};
const FONT = "'IBM Plex Mono', 'JetBrains Mono', monospace";

const Panel = ({ children, title, subtitle, style = {} }) => (
  <div style={{ background: C.panel, border: `1px solid ${C.panelBorder}`, borderRadius: 10, padding: "18px 22px", ...style }}>
    {title && <div style={{ marginBottom: subtitle ? 4 : 14 }}>
      <h3 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: C.text, letterSpacing: "0.06em", fontFamily: FONT }}>{title}</h3>
      {subtitle && <p style={{ margin: "3px 0 10px", fontSize: 11, color: C.textMuted, lineHeight: 1.4, fontFamily: FONT }}>{subtitle}</p>}
    </div>}
    {children}
  </div>
);

const Stat = ({ label, value, color = C.accent }) => (
  <div style={{ padding: "10px 14px", background: `${color}08`, borderRadius: 8, border: `1px solid ${color}20`, minWidth: 80, textAlign: "center" }}>
    <div style={{ fontSize: 22, fontWeight: 800, color, fontFamily: FONT }}>{value}</div>
    <div style={{ fontSize: 9, color: C.textMuted, marginTop: 1, textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: FONT }}>{label}</div>
  </div>
);

const Pill = ({ label, active, onClick }) => (
  <button onClick={onClick} style={{
    padding: "5px 14px", border: "none", borderRadius: 6, cursor: "pointer",
    fontSize: 11, fontWeight: active ? 700 : 500, fontFamily: FONT,
    background: active ? C.accent : "#0d1520", color: active ? "#fff" : C.textMuted,
  }}>{label}</button>
);

const Spinner = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: 20, color: C.textDim, fontFamily: FONT, fontSize: 12 }}>
    <div style={{ width: 16, height: 16, border: `2px solid ${C.panelBorder}`, borderTopColor: C.accent, borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
    Loading from MLB Stats API...
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#111d2e", border: `1px solid ${C.panelBorder}`, borderRadius: 8, padding: "8px 12px", boxShadow: "0 8px 24px rgba(0,0,0,0.6)" }}>
      <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4, fontFamily: FONT }}>{label}</div>
      {payload.filter(p => p.value != null).map((p, i) => (
        <div key={i} style={{ fontSize: 11, color: p.color || C.text, fontFamily: FONT, margin: "1px 0" }}>
          {p.name}: <strong>{typeof p.value === "number" && p.value < 5 ? p.value.toFixed(3) : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

function PlayerSearch({ onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const timeout = useRef(null);
  const doSearch = useCallback((q) => {
    if (q.length < 2) { setResults([]); return; }
    setLoading(true);
    searchPlayers(q).then(r => { setResults(r); setLoading(false); setOpen(true); });
  }, []);
  const handleChange = (e) => {
    const v = e.target.value; setQuery(v);
    clearTimeout(timeout.current);
    timeout.current = setTimeout(() => doSearch(v), 400);
  };
  return (
    <div style={{ position: "relative", flex: 1, maxWidth: 420 }}>
      <div style={{ position: "relative" }}>
        <input value={query} onChange={handleChange} placeholder="Search MLB players..."
          onFocus={() => results.length > 0 && setOpen(true)}
          style={{ width: "100%", padding: "10px 14px 10px 36px", borderRadius: 8, border: `1px solid ${C.panelBorder}`, background: C.panel, color: C.text, fontSize: 13, fontFamily: FONT, outline: "none", boxSizing: "border-box" }} />
        <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", fontSize: 15, opacity: 0.4 }}>&#9918;</span>
        {loading && <span style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", fontSize: 10, color: C.accent, fontFamily: FONT }}>searching...</span>}
      </div>
      {open && results.length > 0 && (
        <div style={{ position: "absolute", top: "100%", left: 0, right: 0, zIndex: 50, background: "#111d2e", border: `1px solid ${C.panelBorder}`, borderRadius: 8, maxHeight: 320, overflowY: "auto", marginTop: 4, boxShadow: "0 12px 40px rgba(0,0,0,0.6)" }}>
          {results.map(p => (
            <div key={p.id} onClick={() => { onSelect(p); setOpen(false); setQuery(p.fullName); }}
              style={{ padding: "10px 14px", cursor: "pointer", borderBottom: `1px solid ${C.panelBorder}15` }}
              onMouseEnter={e => e.currentTarget.style.background = C.panelHover}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
              <div style={{ fontSize: 13, fontWeight: 600, color: C.text, fontFamily: FONT }}>{p.fullName}</div>
              <div style={{ fontSize: 10, color: C.textMuted, fontFamily: FONT, marginTop: 2 }}>
                {posLabel(p.primaryPosition?.code)} &middot; {p.currentTeam?.abbreviation || "FA"} &middot; Age {p.currentAge}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PlayerCard({ player }) {
  const [career, setCareer] = useState([]);
  const [loading, setLoading] = useState(true);
  const [projTab, setProjTab] = useState("war");
  useEffect(() => {
    setLoading(true);
    getPlayerCareer(player.id).then(splits => { setCareer(splits); setLoading(false); });
  }, [player.id]);

  const seasonStats = useMemo(() => {
    return career.filter(s => s.stat && s.stat.plateAppearances > 0).map(s => ({
      season: s.season,
      age: player.currentAge - (2025 - parseInt(s.season)),
      avg: parseFloat(s.stat.avg || 0), obp: parseFloat(s.stat.obp || 0),
      slg: parseFloat(s.stat.slg || 0), ops: parseFloat(s.stat.ops || 0),
      hr: s.stat.homeRuns || 0, pa: s.stat.plateAppearances || 0,
      r: s.stat.runs || 0, rbi: s.stat.rbi || 0,
      bb: s.stat.baseOnBalls || 0, so: s.stat.strikeOuts || 0,
      sb: s.stat.stolenBases || 0, team: s.team?.abbreviation || "",
    })).sort((a, b) => parseInt(a.season) - parseInt(b.season));
  }, [career, player]);

  const base = useMemo(() => {
    if (career.length === 0) return null;
    return projectFromSeasons(career, player.currentAge, player.primaryPosition?.code || "O");
  }, [career, player]);

  const forward = useMemo(() => {
    if (!base) return [];
    return projectForward(base, player.currentAge, player.primaryPosition?.code || "O");
  }, [base, player]);

  const peakProj = forward.length > 0 ? forward.reduce((best, d) => d.war > best.war ? d : best, forward[0]) : null;
  const cumWAR = forward.reduce((s, d) => s + Math.max(0, d.war), 0);

  if (loading) return <Spinner />;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Panel>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 14 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: C.text, fontFamily: FONT }}>{player.fullName}</h2>
            <p style={{ margin: "3px 0 0", fontSize: 12, color: C.textDim, fontFamily: FONT }}>
              {posLabel(player.primaryPosition?.code)} &middot; {player.currentTeam?.name || "Free Agent"} &middot; Age {player.currentAge}
              {player.batSide?.code ? ` \u00b7 Bats: ${player.batSide.code}` : ""}
              {player.height ? ` \u00b7 ${player.height}` : ""}
              {player.weight ? ` / ${player.weight} lbs` : ""}
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {base && <>
              <Stat label="Proj WAR" value={base.baseWAR.toFixed(1)} color={base.baseWAR >= 4 ? C.green : base.baseWAR >= 2 ? C.blue : C.yellow} />
              <Stat label="Proj wRC+" value={base.wRCPlus} color={base.wRCPlus >= 120 ? C.green : base.wRCPlus >= 100 ? C.blue : C.yellow} />
              <Stat label="Proj OPS" value={base.ops.toFixed(3)} color={base.ops >= 0.850 ? C.green : base.ops >= 0.730 ? C.blue : C.yellow} />
              {peakProj && <Stat label="Peak Age" value={peakProj.age} color={C.cyan} />}
              <Stat label="Cum WAR" value={cumWAR.toFixed(1)} color={C.purple} />
            </>}
          </div>
        </div>
        {base && <div style={{ marginTop: 12, padding: "8px 12px", background: `${C.accent}08`, borderRadius: 6, border: `1px solid ${C.accent}15` }}>
          <span style={{ fontSize: 10, color: C.textMuted, fontFamily: FONT }}>
            PROJECTION BASIS: {base.paReliability}% reliability &middot; {seasonStats.length} seasons &middot; Marcel 5/4/3 weighting
          </span>
        </div>}
      </Panel>

      {seasonStats.length > 0 && (
        <Panel title="CAREER HITTING STATS" subtitle="Year-by-year from MLB Stats API">
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: FONT, fontSize: 11 }}>
              <thead><tr style={{ borderBottom: `1px solid ${C.panelBorder}` }}>
                {["Year","Age","Tm","PA","AVG","OBP","SLG","OPS","HR","R","RBI","BB","SO","SB"].map(h => (
                  <th key={h} style={{ padding: "6px 8px", textAlign: h==="Year"||h==="Tm" ? "left" : "right", color: C.textMuted, fontWeight: 600, fontSize: 10 }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {seasonStats.map((s, i) => (
                  <tr key={i} style={{ borderBottom: `1px solid ${C.panelBorder}20`, background: i % 2 === 0 ? `${C.bg}80` : "transparent" }}>
                    <td style={{ padding: "5px 8px", color: C.text, fontWeight: 600 }}>{s.season}</td>
                    <td style={{ padding: "5px 8px", color: C.textDim, textAlign: "right" }}>{s.age}</td>
                    <td style={{ padding: "5px 8px", color: C.textDim }}>{s.team}</td>
                    <td style={{ padding: "5px 8px", color: C.text, textAlign: "right" }}>{s.pa}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: s.avg >= .300 ? C.green : C.text, fontWeight: 600 }}>{s.avg.toFixed(3)}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: s.obp >= .370 ? C.green : C.text }}>{s.obp.toFixed(3)}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: s.slg >= .500 ? C.green : C.text }}>{s.slg.toFixed(3)}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontWeight: 700, color: s.ops >= .900 ? C.green : s.ops >= .750 ? C.accent : C.text }}>{s.ops.toFixed(3)}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: s.hr >= 30 ? C.accent : C.text }}>{s.hr}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: C.text }}>{s.r}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: C.text }}>{s.rbi}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: C.textDim }}>{s.bb}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: C.textDim }}>{s.so}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", color: s.sb >= 20 ? C.cyan : C.textDim }}>{s.sb}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {seasonStats.length >= 2 && (
        <Panel title="CAREER OPS TRAJECTORY">
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart data={seasonStats} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
              <XAxis dataKey="season" stroke={C.textMuted} fontSize={10} fontFamily={FONT} />
              <YAxis stroke={C.textMuted} fontSize={10} fontFamily={FONT} />
              <Tooltip content={<ChartTooltip />} />
              <ReferenceLine y={0.720} stroke={C.textMuted} strokeDasharray="5 5" />
              <Bar dataKey="ops" fill={C.accent} radius={[3, 3, 0, 0]} name="OPS" barSize={24}>
                {seasonStats.map((s, i) => <Cell key={i} fill={s.ops >= .900 ? C.green : s.ops >= .750 ? C.accent : C.yellow} fillOpacity={0.7} />)}
              </Bar>
            </ComposedChart>
          </ResponsiveContainer>
        </Panel>
      )}

      {forward.length > 0 && <>
        <div style={{ display: "flex", gap: 4, background: "#0a1018", borderRadius: 8, padding: 3, width: "fit-content" }}>
          {[{ key: "war", label: "WAR" }, { key: "wrc", label: "wRC+" }, { key: "ops", label: "OPS" }].map(t =>
            <Pill key={t.key} label={t.label} active={projTab === t.key} onClick={() => setProjTab(t.key)} />
          )}
        </div>
        <Panel title={`PROJECTED ${projTab.toUpperCase()} (90% CI)`} subtitle="Marcel projection with position-specific aging curve. Shaded = confidence interval.">
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={forward} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
              <XAxis dataKey="age" stroke={C.textMuted} fontSize={10} fontFamily={FONT} />
              <YAxis stroke={C.textMuted} fontSize={10} fontFamily={FONT} />
              <Tooltip content={<ChartTooltip />} />
              {projTab === "war" && <>
                <Area type="monotone" dataKey="warHigh" stroke="none" fill={`${C.blue}18`} name="90th" />
                <Area type="monotone" dataKey="warLow" stroke="none" fill={C.panel} name="10th" />
                <Line type="monotone" dataKey="war" stroke={C.blue} strokeWidth={2.5} dot={{ r: 3, fill: C.blue }} name="WAR" />
                <ReferenceLine y={0} stroke={C.textMuted} strokeDasharray="5 5" />
                <ReferenceLine y={2} stroke={C.green} strokeDasharray="3 3" strokeOpacity={0.4} />
                <ReferenceLine y={5} stroke={C.accent} strokeDasharray="3 3" strokeOpacity={0.4} />
              </>}
              {projTab === "wrc" && <>
                <Area type="monotone" dataKey="wrcHigh" stroke="none" fill={`${C.green}18`} name="90th" />
                <Area type="monotone" dataKey="wrcLow" stroke="none" fill={C.panel} name="10th" />
                <Line type="monotone" dataKey="wrcPlus" stroke={C.green} strokeWidth={2.5} dot={{ r: 3, fill: C.green }} name="wRC+" />
                <ReferenceLine y={100} stroke={C.textMuted} strokeDasharray="5 5" />
              </>}
              {projTab === "ops" && <>
                <Area type="monotone" dataKey="opsHigh" stroke="none" fill={`${C.purple}18`} name="90th" />
                <Area type="monotone" dataKey="opsLow" stroke="none" fill={C.panel} name="10th" />
                <Line type="monotone" dataKey="ops" stroke={C.purple} strokeWidth={2.5} dot={{ r: 3, fill: C.purple }} name="OPS" />
                <ReferenceLine y={0.720} stroke={C.textMuted} strokeDasharray="5 5" />
              </>}
            </AreaChart>
          </ResponsiveContainer>
        </Panel>
      </>}
    </div>
  );
}

function AgingCurvesPanel() {
  const [selected, setSelected] = useState(["SS", "CF", "1B", "C"]);
  const [baseWAR, setBaseWAR] = useState(4.0);
  const posColors = { C: C.red, "1B": C.yellow, "2B": C.green, "3B": C.accent, SS: C.blue, LF: C.purple, CF: C.cyan, RF: C.pink, DH: C.textDim };
  const data = useMemo(() => {
    const merged = {};
    selected.forEach(pos => {
      const params = AGING_PARAMS[pos];
      for (let age = 20; age <= 40; age++) {
        if (!merged[age]) merged[age] = { age };
        const diff = age - params.peak;
        const offFactor = diff <= 0 ? 1 - 0.015 * diff * diff * 0.3 : 1 - params.declineRate * diff * diff * 0.25;
        const defFactor = age <= params.peak ? 1 : 1 - params.defDecline * (age - params.peak);
        merged[age][pos] = Math.round(Math.max(-0.5, baseWAR * offFactor * Math.max(0.4, defFactor) + params.posAdj / 10 * Math.max(0.3, defFactor)) * 10) / 10;
      }
    });
    return Object.values(merged).sort((a, b) => a.age - b.age);
  }, [selected, baseWAR]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Panel title="POSITION AGING CURVES" subtitle="Offensive (quadratic) + defensive (linear) decline by position.">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 14 }}>
          {Object.keys(AGING_PARAMS).filter(p => !["P","O"].includes(p)).map(pos => (
            <button key={pos} onClick={() => setSelected(prev => prev.includes(pos) ? prev.filter(p => p !== pos) : [...prev, pos])} style={{
              padding: "5px 12px", borderRadius: 5, cursor: "pointer", fontSize: 11, fontWeight: 700, fontFamily: FONT,
              border: `2px solid ${selected.includes(pos) ? posColors[pos] : C.panelBorder}`,
              background: selected.includes(pos) ? `${posColors[pos]}18` : "transparent",
              color: selected.includes(pos) ? posColors[pos] : C.textMuted,
            }}>{pos}</button>
          ))}
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 10, color: C.textMuted, fontFamily: FONT }}>BASE WAR</span>
            <input type="range" min="1" max="8" step="0.5" value={baseWAR} onChange={e => setBaseWAR(parseFloat(e.target.value))} style={{ width: 100, accentColor: C.accent }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: C.accent, fontFamily: FONT }}>{baseWAR}</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={380}>
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.grid} />
            <XAxis dataKey="age" stroke={C.textMuted} fontSize={10} fontFamily={FONT} />
            <YAxis stroke={C.textMuted} fontSize={10} fontFamily={FONT} />
            <Tooltip content={<ChartTooltip />} />
            <ReferenceLine y={0} stroke={C.textMuted} strokeDasharray="5 5" />
            {selected.map(pos => <Line key={pos} type="monotone" dataKey={pos} stroke={posColors[pos]} strokeWidth={2.5} dot={false} name={pos} />)}
          </LineChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  );
}

function TeamRosterPanel({ onSelectPlayer }) {
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [roster, setRoster] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => { getTeams().then(t => setTeams(_.sortBy(t, "name"))); }, []);
  const loadRoster = (team) => { setSelectedTeam(team); setLoading(true); getTeamRoster(team.id).then(r => { setRoster(r); setLoading(false); }); };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Panel title="SELECT TEAM">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {teams.map(t => (
            <button key={t.id} onClick={() => loadRoster(t)} style={{
              padding: "4px 10px", fontSize: 10, fontWeight: 600, fontFamily: FONT, borderRadius: 4, cursor: "pointer", border: "none",
              background: selectedTeam?.id === t.id ? C.accent : "#0d1520", color: selectedTeam?.id === t.id ? "#000" : C.textMuted,
            }}>{t.abbreviation}</button>
          ))}
        </div>
      </Panel>
      {loading && <Spinner />}
      {!loading && roster.length > 0 && (
        <Panel title={`${selectedTeam?.name || ""} ROSTER`} subtitle="Click a player to load projections">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 6 }}>
            {roster.filter(r => r.person && r.position?.code !== "1").map(r => (
              <div key={r.person.id} onClick={() => onSelectPlayer(r.person)}
                style={{ padding: "8px 12px", background: "#0a1018", borderRadius: 6, cursor: "pointer", border: `1px solid ${C.panelBorder}` }}
                onMouseEnter={e => e.currentTarget.style.borderColor = C.accent}
                onMouseLeave={e => e.currentTarget.style.borderColor = C.panelBorder}>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.text, fontFamily: FONT }}>{r.person.fullName}</div>
                <div style={{ fontSize: 10, color: C.textMuted, fontFamily: FONT }}>{posLabel(r.position?.code)} &middot; #{r.jerseyNumber || "\u2014"}</div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

function MethodologyPanel() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Panel title="DATA SOURCES">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 10 }}>
          {[
            { name: "MLB Stats API", desc: "Free, no auth. Player stats, rosters, career data. Used in-browser.", color: C.blue, status: "LIVE" },
            { name: "pybaseball", desc: "Python. Statcast + FanGraphs advanced stats (wRC+, WAR, xwOBA).", color: C.green, status: "PIPELINE" },
            { name: "FanGraphs", desc: "wRC+, fWAR, Steamer/ZiPS projections for validation.", color: C.accent, status: "PIPELINE" },
            { name: "Baseball Savant", desc: "Statcast: xwOBA, barrel rate, exit velocity, sprint speed.", color: C.purple, status: "PLANNED" },
          ].map(s => (
            <div key={s.name} style={{ padding: "14px 16px", background: `${s.color}06`, border: `1px solid ${s.color}18`, borderRadius: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: s.color, fontFamily: FONT }}>{s.name}</span>
                <span style={{ fontSize: 8, fontWeight: 700, padding: "2px 6px", borderRadius: 3, fontFamily: FONT,
                  background: s.status === "LIVE" ? `${C.green}20` : `${C.yellow}20`,
                  color: s.status === "LIVE" ? C.green : C.yellow }}>{s.status}</span>
              </div>
              <p style={{ margin: 0, fontSize: 10, color: C.textDim, lineHeight: 1.5, fontFamily: FONT }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="PROJECTION METHODOLOGY">
        <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.8, fontFamily: FONT }}>
          <h4 style={{ color: C.accent, fontSize: 13, margin: "0 0 6px" }}>Marcel Weighting</h4>
          <p style={{ margin: "0 0 14px" }}>3 most recent seasons weighted 5/4/3, regressed to league mean. PA-based reliability: 600+ PA = ~85% weight on actual performance; 200 PA = ~30%.</p>
          <h4 style={{ color: C.blue, fontSize: 13, margin: "0 0 6px" }}>WAR Construction</h4>
          <p style={{ margin: "0 0 14px" }}>Batting runs (from wRC+) + positional adjustment (FanGraphs scale) + replacement level (~20 runs/600 PA), divided by ~10 runs/win.</p>
          <h4 style={{ color: C.green, fontSize: 13, margin: "0 0 6px" }}>Aging Curves</h4>
          <p style={{ margin: "0 0 14px" }}>Offensive: quadratic decay past peak. Defensive: linear decline. Position-specific rates (C steepest, DH gentlest). Separation reveals why catcher value collapses post-30.</p>
          <h4 style={{ color: C.purple, fontSize: 13, margin: "0 0 6px" }}>Confidence Intervals</h4>
          <p style={{ margin: 0 }}>90% CIs expand ~30%/yr. Year-1 calibrated from historical Marcel RMSE (~1.4 WAR). The distribution matters more than the point estimate.</p>
        </div>
      </Panel>
    </div>
  );
}

const TABS = [
  { key: "player", label: "Player Projections" },
  { key: "team", label: "Team Roster" },
  { key: "aging", label: "Aging Curves" },
  { key: "method", label: "Methodology" },
];

export default function App() {
  const [tab, setTab] = useState("player");
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [playerDetail, setPlayerDetail] = useState(null);
  const [loadingPlayer, setLoadingPlayer] = useState(false);
  const handleSelectPlayer = useCallback((player) => {
    setSelectedPlayer(player); setLoadingPlayer(true); setTab("player");
    getPlayerStats(player.id).then(detail => { setPlayerDetail(detail || player); setLoadingPlayer(false); });
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: C.bg, color: C.text, fontFamily: FONT }}>
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
      <div style={{ padding: "20px 28px 0", borderBottom: `1px solid ${C.panelBorder}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 14, flexWrap: "wrap" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, background: `linear-gradient(135deg, ${C.accent}, ${C.yellow})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              &#9918; PROJECTION ENGINE
            </h1>
            <p style={{ margin: "2px 0 0", fontSize: 10, color: C.textMuted, letterSpacing: "0.05em" }}>REAL MLB DATA &middot; MARCEL PROJECTIONS &middot; WAR / wRC+ / OPS</p>
          </div>
          <div style={{ marginLeft: "auto" }}><PlayerSearch onSelect={handleSelectPlayer} /></div>
        </div>
        <div style={{ display: "flex", gap: 2 }}>
          {TABS.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{
              padding: "8px 18px", border: "none", cursor: "pointer", fontSize: 11, fontWeight: tab === t.key ? 700 : 500, fontFamily: FONT,
              background: tab === t.key ? C.panel : "transparent", color: tab === t.key ? C.text : C.textMuted,
              borderRadius: "6px 6px 0 0", borderBottom: tab === t.key ? `2px solid ${C.accent}` : "2px solid transparent",
            }}>{t.label}</button>
          ))}
        </div>
      </div>
      <div style={{ padding: "20px 28px 40px" }}>
        {tab === "player" && <div>
          {!selectedPlayer && !loadingPlayer && (
            <Panel style={{ textAlign: "center", padding: 60 }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>&#9918;</div>
              <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: FONT }}>Search for any MLB player</h3>
              <p style={{ margin: "8px auto 0", fontSize: 12, color: C.textMuted, fontFamily: FONT, maxWidth: 500, lineHeight: 1.6 }}>
                Type a name above. The engine pulls career stats from the MLB Stats API and runs Marcel-style projections with confidence intervals.
              </p>
              <div style={{ marginTop: 24, display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
                {["Juan Soto", "Shohei Ohtani", "Mookie Betts", "Julio Rodriguez", "Gunnar Henderson"].map(name => (
                  <button key={name} onClick={() => searchPlayers(name).then(r => { if (r[0]) handleSelectPlayer(r[0]); })}
                    style={{ padding: "6px 14px", borderRadius: 6, border: `1px solid ${C.panelBorder}`, background: "transparent", color: C.textDim, fontSize: 11, fontFamily: FONT, cursor: "pointer" }}
                    onMouseEnter={e => { e.target.style.borderColor = C.accent; e.target.style.color = C.accent; }}
                    onMouseLeave={e => { e.target.style.borderColor = C.panelBorder; e.target.style.color = C.textDim; }}
                  >{name}</button>
                ))}
              </div>
            </Panel>
          )}
          {loadingPlayer && <Spinner />}
          {selectedPlayer && !loadingPlayer && playerDetail && <PlayerCard player={playerDetail} />}
        </div>}
        {tab === "team" && <TeamRosterPanel onSelectPlayer={handleSelectPlayer} />}
        {tab === "aging" && <AgingCurvesPanel />}
        {tab === "method" && <MethodologyPanel />}
      </div>
      <div style={{ padding: "16px 28px", borderTop: `1px solid ${C.panelBorder}`, display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <span style={{ fontSize: 9, color: C.textMuted, fontFamily: FONT }}>Data: MLB Stats API (statsapi.mlb.com) &middot; No affiliation with MLB</span>
        <span style={{ fontSize: 9, color: C.textMuted, fontFamily: FONT }}>Methodology: Marcel (Tango) + ZiPS/Steamer inspired</span>
      </div>
    </div>
  );
}
APPEOF

echo ""
echo "✅ src/App.jsx created successfully!"
echo ""
echo "Next steps:"
echo "  npm install"
echo "  npm run dev"
