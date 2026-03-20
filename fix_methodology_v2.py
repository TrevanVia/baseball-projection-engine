#!/usr/bin/env python3
"""Redesign Methodology page. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

start_marker = "function MethodPanel() {"
end_marker = "// ── PLAYER OF THE DAY"

si = src.find(start_marker)
ei = src.find(end_marker)

if si == -1 or ei == -1:
    print(f"ERROR: markers not found (start={si}, end={ei})")
    exit(1)

# The function ends with "}\n\n\n" before the POTD marker
# Find the last "}" before end_marker
before_potd = src[si:ei]
# Find the last closing brace
last_brace = before_potd.rfind("}")
old_method = src[si:si+last_brace+1]

new_method = r'''function MethodPanel() {
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

    {/* 3. PROJECTION METHODOLOGY \u2014 two columns */}
    <Panel title="PROJECTION METHODOLOGY">
      <p style={{margin:"0 0 14px",fontSize:12,color:C.dim,lineHeight:1.6,fontFamily:F}}>VIAcast projects hitters and pitchers through separate Statcast-powered engines. Both use 3 years of data (2023{"\u2013"}2025) weighted 55/30/15% with sample-size reliability scaling. Players below the Statcast threshold use the Marcel fallback with MiLB translation.</p>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(320px,1fr))",gap:16}}>

        {/* HITTER COLUMN */}
        <div style={{fontSize:12,color:C.dim,lineHeight:1.7,fontFamily:F}}>
          <div style={{fontSize:11,fontWeight:800,color:C.accent,letterSpacing:".1em",textTransform:"uppercase",marginBottom:10,paddingBottom:6,borderBottom:`2px solid ${C.accent}20`,fontFamily:F}}>HITTER ENGINE (7 LAYERS)</div>

          {h4(C.blue,"L1: Contact Quality (40%)")}
          {pp("xwOBA anchor weighted across 3 seasons. Supported by avg exit velocity, EV50, barrel rate, and hard-hit rate from Statcast.")}

          {h4(C.purple,"L2: Plate Discipline (25%)")}
          {pp("K% and BB% from FanGraphs. Chase rate, zone contact, and swinging-strike rate feed a selectivity index for pitch recognition.")}

          {h4("#ec4899","L3: Swing Mechanics (10%)")}
          {pp("Bat speed and squared-up rate from Statcast bat tracking. YoY bat speed trends detect early aging signals.")}

          {h4(C.green,"L4: Baserunning (10%)")}
          {pp("Statcast BsR (Baserunning Run Value) for 252 MLB players. Measures actual runs from SB, extra bases taken, and decisions. Fallback: sprint speed tiers.")}

          {h4(C.orange,"L5: Defense")}
          {pp("OAA at 0.5 runs per OAA. Defensive peaks: SS/CF at 26, corners at 28. Decays 6%/yr past peak.")}

          {h4(C.text,"L6: Aging Curves")}
          {pp("Additive wRC+ adjustment. Pre-peak: +1.5/yr. Peak\u201332: \u22121.5/yr. 33+: \u22123.0/yr. Peaks: SS/2B/3B 28, CF 27, C 27, 1B 29, DH 30.")}

          {h4(C.blue,"L7: Trend Weighting")}
          {pp("Multi-year improvers get +30% trend credit. Chase rate improvements, EV50 breakouts, and bat speed declines feed momentum adjustments.")}

          {h4(C.green,"WAR Construction")}
          {pp("xwOBA \u2192 wRC+ (4.5 pts per .010 xwOBA). Batting runs + defense (OAA \u00d7 0.5) + BsR + positional adj + replacement (20 runs/600 PA) \u00f7 9.5 RPW. HR: barrel% \u00d7 BBE \u00d7 0.45 + PA \u00d7 0.010 baseline.")}
        </div>

        {/* PITCHER COLUMN */}
        <div style={{fontSize:12,color:C.dim,lineHeight:1.7,fontFamily:F}}>
          <div style={{fontSize:11,fontWeight:800,color:C.accent,letterSpacing:".1em",textTransform:"uppercase",marginBottom:10,paddingBottom:6,borderBottom:`2px solid ${C.accent}20`,fontFamily:F}}>PITCHER ENGINE (5 LAYERS)</div>

          {h4(C.blue,"L1: ERA Anchor \u2014 Layered (35%)")}
          {pp("Falls through in order of predictive accuracy: SIERA \u2192 xFIP \u2192 xERA \u2192 FIP \u2192 K-BB \u2192 ERA. SIERA from FanGraphs is primary for 815 pitchers, accounting for K/BB/GB interactions. Pitchers without FG data fall back to xERA from Statcast.")}

          {h4(C.purple,"L2: Command (25%)")}
          {pp("K% and BB% sourced from FanGraphs for 815 pitchers. Fallback: whiff% \u00d7 1.05. FIP computed with HR allowed estimated from IP \u00d7 1.2 HR/9 scaled by barrel% allowed.")}

          {h4(C.orange,"L3: Velocity (15%)")}
          {pp("Fastball velocity trends across seasons. Velocity loss is the strongest predictor of pitcher decline. Arsenal mix effectiveness weights pitch-type performance.")}

          {h4(C.text,"L4: Aging Curves")}
          {pp("Pre-peak: \u22121.5% ERA/yr. Peak\u201333: +1.5%/yr. 33+: +3%/yr. SP peak at 27, RP peak at 28.")}

          {h4(C.green,"L5: IP Projection")}
          {pp("Best full season (100+ IP) from FanGraphs data with age adjustment: \u226427 \u00d7 1.03, 28\u201330 \u00d7 1.00, 31\u201333 \u00d7 0.97, 34+ \u00d7 0.93. Capped at 210 IP. Reliever IP capped at 75.")}

          {h4(C.green,"WAR Construction")}
          {pp("(Replacement level \u2212 projected ERA) \u00f7 9.5 RPW \u00d7 IP/9. SP replacement: 5.34, RP replacement: 4.49. Starter detection checks entire career history for injury returns.")}

          <div style={{marginTop:8,padding:"10px 14px",background:`${C.accent}06`,border:`1px solid ${C.accent}15`,borderRadius:8}}>
            <div style={{fontSize:10,fontWeight:700,color:C.accent,fontFamily:F,marginBottom:4}}>MARCEL FALLBACK</div>
            <div style={{fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Players below 250 Statcast PA use Marcel with MiLB translation (AAA 0.82x, AA 0.68x, A+ 0.58x, A 0.50x). HR translated by level factor, projected via games-based rate. Prospect PA: projected games {"\u00d7"} 4.0 PA/G.</div>
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
          {n:"Baseball Savant",d:"Statcast: xwOBA, xERA, barrel%, exit velocity, whiff%, sprint speed, OAA, bat speed, BsR. 900+ hitters, 1200+ pitchers (2023-2025).",c:C.accent,s:"STATIC"},
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
}'''

src = src[:si] + new_method + src[si+last_brace+1:]
open(APP, "w").write(src)
print("Replaced MethodPanel with redesigned version")
print()
print("New order: FV Scale > VpD Scale > Projection (2-col) > MiLB Translation > Data Sources")
