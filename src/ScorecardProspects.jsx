// Scorecard + Prospects panels. Rendered by App.jsx, which passes in its shared
// UI pieces (Panel, FVBadge, theme colors C, font F) so the look stays identical.
import { useState, useMemo } from "react";
import scorecardJson from "./scorecard_2026.json";
import prospectsJson from "./prospects.json";
import precomputedJson from "./precomputed_leaderboard.json";

const SC = scorecardJson.default || scorecardJson;
const PROS = prospectsJson.default || prospectsJson;
const PRE = precomputedJson.default || precomputedJson;

// Hand-written scouting notes kept from the old home-page list.
const NOTES = {
  "Jesús Made": "Made it to Double-A at 18. One of the best pure athletes in the minors with ridiculous range, body control, and enormous power projection.",
  "Leo De Vries": "Premium international SS. Plus tools across the board with advanced instincts at a young age.",
  "Aidan Miller": "Uncommon power for a prospect who slid to 27th overall. Smooth swing with natural feel to hit.",
  "Walker Jenkins": "Top 5 pick in the 2023 draft. Plus-plus speed, above-average arm, plus contact skills, above-average raw power.",
};

const fmt = (v, d = 1) => (v == null ? "—" : Number(v).toFixed(d));
const sign = (v, d = 1) => (v == null ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(d));

function Tile({ C, F, value, label, sub, color }) {
  return (
    <div style={{ flex: "1 1 140px", minWidth: 0, background: C.bg, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 14px" }}>
      <div style={{ fontSize: 22, fontWeight: 800, color: color || C.navy, fontFamily: F, lineHeight: 1.1 }}>{value}</div>
      <div style={{ fontSize: 9, fontWeight: 700, color: C.muted, fontFamily: F, textTransform: "uppercase", letterSpacing: ".06em", marginTop: 4 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: C.dim, fontFamily: F, marginTop: 4, lineHeight: 1.4 }}>{sub}</div>}
    </div>
  );
}

function PlayerRows({ C, F, rows, onPick, right }) {
  return (
    <div>
      {rows.map(r => (
        <div key={r.name} onClick={() => onPick(r.name)}
          style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 4px", borderBottom: `1px solid ${C.border}40`, cursor: "pointer" }}
          onMouseEnter={e => (e.currentTarget.style.background = `${C.accent}06`)}
          onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: C.text, fontFamily: F }}>{r.name}</span>
            <span style={{ fontSize: 9, color: C.muted, fontFamily: F, marginLeft: 6 }}>{r.team}</span>
          </div>
          {right(r)}
        </div>
      ))}
    </div>
  );
}

function ProjVsActual({ C, F, proj, act, extra }) {
  return (
    <div style={{ display: "flex", gap: 10, alignItems: "baseline", fontFamily: F, flexShrink: 0 }}>
      {extra}
      <span style={{ fontSize: 10, color: C.muted }}>proj <b style={{ color: C.dim }}>{fmt(proj)}</b></span>
      <span style={{ fontSize: 10, color: C.muted }}>actual <b style={{ color: C.text }}>{fmt(act)}</b></span>
    </div>
  );
}

function Tag({ C, F, children, color }) {
  return <span style={{ fontSize: 8, fontWeight: 700, padding: "2px 6px", borderRadius: 4, fontFamily: F, textTransform: "uppercase", letterSpacing: ".05em", background: `${color}18`, color }}>{children}</span>;
}

export function ScorecardPanel({ Panel, C, F, onPickName }) {
  const [side, setSide] = useState("hitters");
  const h = SC.hitters, p = SC.pitchers;
  const sideTabs = (
    <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
      {["hitters", "pitchers"].map(k => (
        <button key={k} onClick={() => setSide(k)} style={{ padding: "5px 12px", borderRadius: 6, cursor: "pointer", fontFamily: F, fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em",
          border: `1px solid ${side === k ? C.navy : C.border}`, background: side === k ? C.navy : "transparent", color: side === k ? "#fff" : C.dim }}>{k}</button>
      ))}
    </div>
  );
  const maxBias = Math.max(...[...SC.ageBias.hitters, ...SC.ageBias.pitchers].map(r => Math.abs(r.bias)), 1);
  const date = new Date(SC.projectedOn + "T12:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <Panel style={{ padding: "26px 24px 20px", background: `linear-gradient(180deg, ${C.bg} 0%, ${C.panel} 100%)` }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".15em", color: C.accent, fontFamily: F, textTransform: "uppercase", marginBottom: 6 }}>{SC.season} Scorecard</div>
        <h2 style={{ margin: 0, fontSize: 22, color: C.navy, fontFamily: F, lineHeight: 1.3, letterSpacing: "-0.02em" }}>How our {SC.season} projections held up</h2>
        <p style={{ margin: "8px 0 0", fontSize: 11, color: C.dim, fontFamily: F, maxWidth: 640, lineHeight: 1.6 }}>
          Every projection we published on {date} — {h.n} hitters and {p.n} pitchers — graded against final {SC.season} results.
          The good calls, the bad misses, and what we changed because of them. WAR is FanGraphs fWAR; anyone who didn't play counts as 0.
        </p>
      </Panel>

      <Panel title="The grades" sub="Correlation runs from 0 (no relationship) to 1 (we had everyone in exactly the right order).">
        <div style={{ fontSize: 10, fontWeight: 700, color: C.navy, fontFamily: F, textTransform: "uppercase", letterSpacing: ".08em", margin: "2px 0 8px" }}>Hitters</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 14 }}>
          <Tile C={C} F={F} value={fmt(h.r, 2)} label="WAR correlation" />
          <Tile C={C} F={F} value={`${h.within1}%`} label="Within 1 WAR" sub={`${h.within2}% within 2`} />
          <Tile C={C} F={F} value={fmt(h.mae, 2)} label="Avg miss (WAR)" />
          <Tile C={C} F={F} value={`${h.top25}/25`} label="Top-25 overlap" sub="Projected top 25 who finished top 25" color={h.top25 < 8 ? C.accent : C.navy} />
        </div>
        <div style={{ fontSize: 10, fontWeight: 700, color: C.navy, fontFamily: F, textTransform: "uppercase", letterSpacing: ".08em", margin: "2px 0 8px" }}>Pitchers</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          <Tile C={C} F={F} value={fmt(p.r, 2)} label="WAR correlation" />
          <Tile C={C} F={F} value={`${p.within1}%`} label="Within 1 WAR" sub={`${p.within2}% within 2`} />
          <Tile C={C} F={F} value={fmt(p.mae, 2)} label="Avg miss (WAR)" />
          <Tile C={C} F={F} value={`${p.top25}/25`} label="Top-25 overlap" sub="Projected top 25 who finished top 25" />
        </div>
      </Panel>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 14 }}>
        <Panel title="Nailed it" sub="3+ WAR players we projected within 0.3 WAR." style={{ flex: "1 1 320px", borderTop: `3px solid ${C.green}` }}>
          <PlayerRows C={C} F={F} onPick={onPickName} rows={[...SC.nailed.pitchers, ...SC.nailed.hitters].sort((a, b) => b.act - a.act)}
            right={r => <ProjVsActual C={C} F={F} proj={r.proj} act={r.act} />} />
        </Panel>
        <Panel title="Called the move" sub="Big changes from 2025 we saw coming, and landed within 1 WAR." style={{ flex: "1 1 320px", borderTop: `3px solid ${C.green}` }}>
          {sideTabs}
          <PlayerRows C={C} F={F} onPick={onPickName} rows={SC.calls[side].slice(0, 6)}
            right={r => <ProjVsActual C={C} F={F} proj={r.proj} act={r.act}
              extra={<span style={{ fontSize: 10, color: C.muted }}>'25 <b style={{ color: C.dim }}>{fmt(r.w25)}</b> {r.dir === "up" ? "▲" : "▼"}</span>} />} />
        </Panel>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 14 }}>
        <Panel title="Biggest misses — too low" sub="Players who blew past us. Mostly young players: our aging curve was too pessimistic on them." style={{ flex: "1 1 320px", borderTop: `3px solid ${C.accent}` }}>
          {sideTabs}
          <PlayerRows C={C} F={F} onPick={onPickName} rows={SC.misses.under[side]}
            right={r => <ProjVsActual C={C} F={F} proj={r.proj} act={r.act} extra={<Tag C={C} F={F} color={C.accent}>{sign(r.err)}</Tag>} />} />
        </Panel>
        <Panel title="Biggest misses — too high" sub="Players who fell short. Injuries and lost playing time explain a lot of these." style={{ flex: "1 1 320px", borderTop: `3px solid ${C.accent}` }}>
          {sideTabs}
          <PlayerRows C={C} F={F} onPick={onPickName} rows={SC.misses.over[side]}
            right={r => <ProjVsActual C={C} F={F} proj={r.proj} act={r.act}
              extra={r.why === "Playing time" ? <Tag C={C} F={F} color={C.yellow}>{side === "hitters" ? `${r.pt} PA` : `${Math.round(r.pt)} IP`}</Tag> : <Tag C={C} F={F} color={C.accent}>{sign(r.err)}</Tag>} />} />
          <p style={{ margin: "10px 0 0", fontSize: 10, color: C.muted, fontFamily: F, lineHeight: 1.5 }}>
            Of the {SC.missBreakdown.hitterOverMisses} hitters who fell 1.5+ WAR short, {SC.missBreakdown.ofThoseUnder300PA} got fewer than 300 PA.
          </p>
        </Panel>
      </div>

      <Panel title="Rate stats" sub="Full-time players only, so playing time doesn't muddy the comparison. 'Typical miss' is the average gap between projection and result.">
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F, fontSize: 11 }}>
            <thead><tr>{["Stat", "Players", "Correlation", "Typical miss"].map(t => <th key={t} style={{ textAlign: t === "Stat" ? "left" : "right", padding: "6px 8px", borderBottom: `2px solid ${C.border}`, color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: ".05em" }}>{t}</th>)}</tr></thead>
            <tbody>
              {Object.entries(SC.rates).map(([k, v]) => (
                <tr key={k}>
                  <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, fontWeight: 700, color: C.text }}>{k}</td>
                  <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, textAlign: "right", color: C.dim }}>{v.n} <span style={{ fontSize: 9, color: C.muted }}>{v.who.replace("hitters with ", "").replace("pitchers with ", "")}</span></td>
                  <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, textAlign: "right", color: C.text }}>{fmt(v.r, 2)}</td>
                  <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, textAlign: "right", color: C.text }}>{k === "OPS" ? fmt(v.mae, 3) : fmt(v.mae, k === "wRC+" ? 0 : 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ margin: "10px 0 0", fontSize: 10, color: C.muted, fontFamily: F, lineHeight: 1.5 }}>
          Left off on purpose: home runs and K/9. Both had bugs in the version we published (HR came in about 11 short per full-time hitter; every pitcher's K/9 was stuck at 13.5). Both are fixed below.
        </p>
      </Panel>

      <Panel title="Where we were biased" sub="Actual WAR minus projected WAR, by age (full-time players). Green = we were too low; red = too high.">
        {["hitters", "pitchers"].map(k => (
          <div key={k} style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.navy, fontFamily: F, textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>{k}</div>
            {SC.ageBias[k].map(r => {
              const w = Math.abs(r.bias) / maxBias * 50;
              const col = r.bias >= 0 ? C.green : C.accent;
              return (
                <div key={r.age} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, fontFamily: F }}>
                  <span style={{ width: 78, fontSize: 10, color: C.dim, flexShrink: 0 }}>{r.age}</span>
                  <div style={{ flex: 1, position: "relative", height: 14 }}>
                    <div style={{ position: "absolute", left: "50%", top: 0, bottom: 0, width: 1, background: C.border }} />
                    <div style={{ position: "absolute", top: 2, height: 10, borderRadius: 3, background: col, opacity: 0.85,
                      left: r.bias >= 0 ? "50%" : `${50 - w}%`, width: `${w}%` }} />
                  </div>
                  <span style={{ width: 44, fontSize: 10, fontWeight: 700, color: col, textAlign: "right", flexShrink: 0 }}>{sign(r.bias, 2)}</span>
                  <span style={{ width: 34, fontSize: 9, color: C.muted, textAlign: "right", flexShrink: 0 }}>n={r.n}</span>
                </div>
              );
            })}
          </div>
        ))}
        <p style={{ margin: "4px 0 0", fontSize: 10, color: C.muted, fontFamily: F, lineHeight: 1.5 }}>
          Young players beat us across the board, and hitters in their mid-30s fell short. The aging curve was too gentle on decline and too stingy on growth.
        </p>
      </Panel>

      <Panel title={`What we changed for ${SC.season + 1}`} sub={`The retuned engine, re-run as if it were March ${SC.season} (only data through ${SC.season - 1}), on the same ${SC.upgrade.nH} hitters and ${SC.upgrade.nP} pitchers.`} style={{ borderTop: `3px solid ${C.navy}` }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: F, fontSize: 11 }}>
            <thead><tr>{["", `Published ${SC.season}`, "Retuned engine", ""].map((t, i) => <th key={i} style={{ textAlign: i === 0 ? "left" : "right", padding: "6px 8px", borderBottom: `2px solid ${C.border}`, color: C.muted, fontSize: 9, textTransform: "uppercase", letterSpacing: ".05em" }}>{t}</th>)}</tr></thead>
            <tbody>
              {SC.upgrade.rows.map(r => {
                const better = r.better === "lower" ? r.new < r.old : r.better === "higher" ? r.new > r.old : Math.abs(r.new) < Math.abs(r.old);
                const same = Math.abs(r.new - r.old) <= Math.max(0.01, 0.03 * Math.abs(r.old));
                return (
                  <tr key={r.metric}>
                    <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, color: C.text }}>{r.metric}</td>
                    <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, textAlign: "right", color: C.dim }}>{r.old > 0 && r.better === "zero" ? "+" : ""}{r.old}</td>
                    <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, textAlign: "right", fontWeight: 700, color: C.text }}>{r.new > 0 && r.better === "zero" ? "+" : ""}{r.new}</td>
                    <td style={{ padding: "8px", borderBottom: `1px solid ${C.border}40`, textAlign: "right", width: 60 }}>
                      {same ? <Tag C={C} F={F} color={C.muted}>Flat</Tag> : better ? <Tag C={C} F={F} color={C.green}>Better</Tag> : <Tag C={C} F={F} color={C.accent}>Worse</Tag>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <ul style={{ margin: "14px 0 0", paddingLeft: 18, fontSize: 11, color: C.dim, fontFamily: F, lineHeight: 1.7 }}>
          <li><b style={{ color: C.text }}>One engine.</b> The leaderboard used a stripped-down copy of the model. Now the leaderboard, player pages and home page all run the same engine.</li>
          <li><b style={{ color: C.text }}>Home runs</b> now come from barrel rate and contact rate, and slugging is fit to real hitters, so power bats aren't shortchanged.</li>
          <li><b style={{ color: C.text }}>K/9</b> unit bug fixed; strikeout rates now track reality.</li>
          <li><b style={{ color: C.text }}>Aging:</b> more credit for growth before the peak, decline starting at 31 instead of 32 and falling faster.</li>
          <li><b style={{ color: C.text }}>Regression:</b> extreme projections are pulled toward average more — one great season isn't treated as the new normal.</li>
          <li><b style={{ color: C.text }}>Playing time:</b> projections now expect the ~125 PA a typical player loses to injuries, platoons and slumps, and starters' innings are realistic.</li>
          <li><b style={{ color: C.text }}>Honest gap:</b> pitcher <i>ranking</i> didn't improve. Getting the order of pitchers right is the main target for next year.</li>
        </ul>
      </Panel>
    </div>
  );
}

export function ProspectsPanel({ Panel, FVBadge, C, F, onPickName }) {
  const [filter, setFilter] = useState("all");
  const [showGrad, setShowGrad] = useState(false);
  const projById = useMemo(() => {
    const m = {};
    for (const x of [...(PRE.hitters || []), ...(PRE.pitchers || [])]) m[x.id] = x;
    return m;
  }, []);
  const live = PROS.players.filter(p => !p.graduated && (filter === "all" || (filter === "pitchers" ? p.isPitcher : !p.isPitcher)));
  const grads = PROS.players.filter(p => p.graduated).map(p => ({ ...p, proj: projById[p.id] }))
    .filter(p => p.proj).sort((a, b) => (b.proj.projWAR || 0) - (a.proj.projWAR || 0));
  const lvlColor = l => (l === "MLB" ? C.green : l === "AAA" ? C.yellow : l === "AA" ? C.purple : C.cyan);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <Panel style={{ padding: "26px 24px 20px", background: `linear-gradient(180deg, ${C.bg} 0%, ${C.panel} 100%)` }}>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: ".15em", color: C.accent, fontFamily: F, textTransform: "uppercase", marginBottom: 6 }}>Prospects</div>
        <h2 style={{ margin: 0, fontSize: 22, color: C.navy, fontFamily: F, lineHeight: 1.3, letterSpacing: "-0.02em" }}>Top prospects heading into {PROS.season}</h2>
        <p style={{ margin: "8px 0 0", fontSize: 11, color: C.dim, fontFamily: F, maxWidth: 640, lineHeight: 1.6 }}>
          Ranked by Future Value (FV) grade. Players past rookie limits (130 MLB at-bats or 50 innings) graduate off the list.
          FV grades are the {PROS.fvSource}; we'll refresh them when the {PROS.season} lists publish.
        </p>
      </Panel>

      <Panel title={`Ranked prospects (${live.length})`} sub="Tap any player for their full projection.">
        <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
          {[["all", "All"], ["hitters", "Hitters"], ["pitchers", "Pitchers"]].map(([k, l]) => (
            <button key={k} onClick={() => setFilter(k)} style={{ padding: "5px 12px", borderRadius: 6, cursor: "pointer", fontFamily: F, fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: ".05em",
              border: `1px solid ${filter === k ? C.navy : C.border}`, background: filter === k ? C.navy : "transparent", color: filter === k ? "#fff" : C.dim }}>{l}</button>
          ))}
        </div>
        {live.map((p, i) => (
          <div key={p.id} onClick={() => onPickName(p.name, p.id)}
            style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 6px", cursor: "pointer", borderBottom: `1px solid ${C.border}40` }}
            onMouseEnter={e => (e.currentTarget.style.background = `${C.accent}06`)}
            onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
            <span style={{ fontSize: 14, fontWeight: 800, color: C.muted, fontFamily: F, width: 24, textAlign: "right", flexShrink: 0 }}>{i + 1}</span>
            <FVBadge fv={p.fv} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: C.text, fontFamily: F }}>{p.name}</span>
                <span style={{ fontSize: 9, color: C.muted, fontFamily: F }}>{p.pos} · {p.org || "—"} · age {p.age} in {PROS.season}</span>
              </div>
              {NOTES[p.name] && <div style={{ fontSize: 10, color: C.dim, fontFamily: F, marginTop: 2, lineHeight: 1.4 }}>{NOTES[p.name]}</div>}
            </div>
            {p.level && <span style={{ fontSize: 9, fontWeight: 700, padding: "3px 7px", borderRadius: 4, fontFamily: F, background: `${lvlColor(p.level)}18`, color: lvlColor(p.level), flexShrink: 0 }}>{p.level}</span>}
          </div>
        ))}
      </Panel>

      <Panel title={`Graduated in ${PROS.season - 1} (${grads.length})`} sub={`Last year's prospects who are now big leaguers, with their ${PROS.season} projection.`}>
        <button onClick={() => setShowGrad(s => !s)} style={{ padding: "5px 12px", borderRadius: 6, cursor: "pointer", fontFamily: F, fontSize: 10, fontWeight: 700, border: `1px solid ${C.border}`, background: "transparent", color: C.dim, marginBottom: showGrad ? 8 : 0 }}>
          {showGrad ? "Hide" : "Show"} graduates
        </button>
        {showGrad && grads.map(p => (
          <div key={p.id} onClick={() => onPickName(p.name, p.id)}
            style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 4px", cursor: "pointer", borderBottom: `1px solid ${C.border}40` }}>
            <FVBadge fv={p.fv} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: C.text, fontFamily: F }}>{p.name}</span>
              <span style={{ fontSize: 9, color: C.muted, fontFamily: F, marginLeft: 6 }}>{p.pos} · {p.proj.team}</span>
            </div>
            <span style={{ fontSize: 12, fontWeight: 800, color: C.navy, fontFamily: F }}>{fmt(p.proj.projWAR)}</span>
            <span style={{ fontSize: 8, color: C.muted, fontFamily: F, textTransform: "uppercase", width: 54 }}>{PROS.season} WAR</span>
          </div>
        ))}
      </Panel>
    </div>
  );
}
