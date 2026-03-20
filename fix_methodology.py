#!/usr/bin/env python3
"""Redesign Methodology page: reorder sections, two-column hitter/pitcher, add VpD scale. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

old_method = '''function MethodPanel() {
  return <div style={{display:"flex",flexDirection:"column",gap:14}}>
    <Panel title="DATA SOURCES">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8}}>
        {[
          {n:"MLB Stats API",d:"Player search, career stats, MiLB rosters across all levels (ROK→AAA). Free, no auth.",c:C.blue,s:"LIVE"},
          {n:"FanGraphs FV",d:"Future Value grades for top 100+ prospects. Hardcoded lookup table, updated seasonally.",c:C.green,s:"STATIC"},
          {n:"Pitcher Savant Data",d:"Pitcher Statcast: xERA, barrel% allowed, velocity trends, arsenal effectiveness. 1200+ pitchers.",c:C.purple,s:"LIVE"},
          {n:"Baseball Savant",d:"Statcast: xwOBA, xERA, barrel%, exit velocity, whiff%, sprint speed, OAA. 2023-2025 pipeline.",c:C.accent,s:"LIVE"},
          {n:"Contract Data",d:"2026 salary data for 190+ MLB players. Sources: Spotrac, MLB Trade Rumors, Cot's Baseball Contracts.",c:C.orange,s:"STATIC"},
        ].map(s=><div key={s.n} style={{padding:"12px 14px",background:`${s.c}06`,border:`1px solid ${s.c}18`,borderRadius:8}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:4}}>
            <span style={{fontSize:12,fontWeight:700,color:s.c,fontFamily:F}}>{s.n}</span>
            <span style={{fontSize:7,fontWeight:700,padding:"2px 5px",borderRadius:3,fontFamily:F,background:s.s==="LIVE"?`${C.green}20`:s.s==="STATIC"?`${C.blue}20`:`${C.yellow}20`,color:s.s==="LIVE"?C.green:s.s==="STATIC"?C.blue:C.yellow}}>{s.s}</span>
          </div>
          <p style={{margin:0,fontSize:10,color:C.dim,lineHeight:1.5,fontFamily:F}}>{s.d}</p>
        </div>)}
      </div>
    </Panel>
    <Panel title="FUTURE VALUE SCALE">
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))",gap:6}}>
        {[70,65,60,55,50,45,40].map(fv=>{const s=getFVStyle(fv);return(
          <div key={fv} style={{padding:"10px 12px",borderRadius:6,border:`1px solid ${C.border}`}}>
            <div style={{marginBottom:6}}><FVBadge fv={fv}/></div>
            <div style={{fontSize:9,color:C.muted,fontFamily:F}}>
              {fv>=70?"Franchise Player":fv>=65?"Perennial All-Star":fv>=60?"All-Star upside":fv>=55?"Above-avg regular":fv>=50?"Avg regular":fv>=45?"Solid backup":fv>=40?"Fringe MLB":"—"}
            </div>
          </div>
        );})}
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

        <h4 style={{color:C.accent,fontSize:13,margin:"0 0 4px"}}>VIAcast Statcast Engine (Hitters)</h4>
        <p style={{margin:"0 0 12px"}}>For MLB hitters with 250+ career Statcast PA (900+ players), VIAcast uses a 7-layer projection system anchored on 3 years of Baseball Savant data (2023-2025). Players below the 250 PA threshold use the Marcel fallback, which incorporates MiLB data and FV grades.</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Layer 1: Contact Quality (40%)</h4>
        <p style={{margin:"0 0 12px"}}>Expected wOBA (xwOBA) is the primary projection anchor, weighted across 3 seasons (55/30/15%) with PA reliability scaling. Supported by avg exit velocity, EV50, barrel rate, and hard-hit rate from Statcast.</p>

        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Layer 2: Plate Discipline (25%)</h4>
        <p style={{margin:"0 0 12px"}}>K% and BB% from FanGraphs plate discipline data. When unavailable, K% is estimated from Statcast whiff rate (K% ≈ whiff% × 0.80). Chase rate (O-Swing%), zone contact, and swinging-strike rate feed a selectivity index that identifies elite pitch recognition.</p>

        <h4 style={{color:"#ec4899",fontSize:13,margin:"0 0 4px"}}>Layer 3: Swing Mechanics (10%)</h4>
        <p style={{margin:"0 0 12px"}}>Bat speed and squared-up rate from Statcast bat tracking. Year-over-year bat speed trends detect early aging signals before traditional stats reflect it.</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>Layer 4: Speed & Baserunning (10%)</h4>
        <p style={{margin:"0 0 12px"}}>Statcast Baserunning Run Value (BsR) for 252 MLB players, measuring actual runs created via stolen bases, extra bases taken, and baserunner decisions. BsR maps directly to WAR (divide by 9.5). Players without BsR data fall back to sprint speed tiers. For MiLB players, baserunning is derived from SB/CS rates.</p>

        <h4 style={{color:C.orange,fontSize:13,margin:"0 0 4px"}}>Layer 5: Defense</h4>
        <p style={{margin:"0 0 12px"}}>Outs Above Average (OAA) from Statcast, converted at 0.5 runs per OAA with position-specific aging curves. Defensive peaks: SS/CF at 26, corners at 28. Defense decays at 6% per year past peak.</p>

        <h4 style={{color:C.text,fontSize:13,margin:"0 0 4px"}}>Layer 6: Aging Curves (Hitters)</h4>
        <p style={{margin:"0 0 12px"}}>Single-year forward adjustment applied to wRC+ (not multiplicative xwOBA). Pre-peak: +1.5 wRC+ per year. Ages 28-32: -1.5 wRC+/yr. Ages 33+: -3.0 wRC+/yr. Offensive peaks based on research (Fair 2025, Bradbury, FanGraphs): SS/2B/3B 28, CF 27, C 27, LF/RF 28, 1B 29, DH 30.</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Layer 7: Trend Weighting</h4>
        <p style={{margin:"0 0 12px"}}>Consistent multi-year improvers get amplified trend credit (+30% for same-direction trends). Chase rate improvements, EV50 breakouts, and bat speed declines feed momentum adjustments.</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>WAR Construction (Hitters)</h4>
        <p style={{margin:"0 0 12px"}}>xwOBA \u2192 wRC+ at 4.5 points per .010 xwOBA (league avg .315 xwOBA = 100 wRC+), plus discipline bonus. Batting runs + defense + baserunning + positional adjustment + replacement level, divided by 9.5 runs per win.</p>

        <h4 style={{color:C.accent,fontSize:13,margin:"16px 0 4px"}}>VIAcast Statcast Engine (Pitchers)</h4>
        <p style={{margin:"0 0 12px"}}>5-layer pitcher projection system using Baseball Savant and FanGraphs data. WAR is calculated using a layered ERA anchor based on Peter Appel's predictive ranking: SIERA (primary) \u2192 xFIP \u2192 xERA \u2192 FIP \u2192 K-BB \u2192 ERA. FanGraphs data provides SIERA, xFIP, K%, BB%, and GB% for 815 pitchers across 2023-2025.</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Pitcher Layer 1: Stuff Quality (35%)</h4>
        <p style={{margin:"0 0 12px"}}>SIERA (Skill-Interactive ERA) is the primary projection anchor from FanGraphs, weighted across 3 seasons (55/30/15%) with IP-based reliability scaling. SIERA accounts for K%, BB%, and ground ball rate interactions, making it the most predictive single ERA estimator. Falls back to xFIP, then xERA from Statcast for pitchers without FG data.</p>

        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Pitcher Layer 2: Command (25%)</h4>
        <p style={{margin:"0 0 12px"}}>K% and BB% sourced directly from FanGraphs for 815 pitchers (2023-2025). When FG data is unavailable, K% is estimated from Statcast whiff rate (whiff% \u00d7 1.05). FIP is computed using these rates with HR allowed estimated from IP and barrel rate (league avg 1.2 HR/9, scaled by pitcher barrel% allowed).</p>

        <h4 style={{color:C.orange,fontSize:13,margin:"0 0 4px"}}>Pitcher Layer 3: Velocity (15%)</h4>
        <p style={{margin:"0 0 12px"}}>Fastball velocity trends across seasons. Velocity loss is the strongest predictor of pitcher decline. Arsenal mix effectiveness weights pitch-type performance.</p>

        <h4 style={{color:C.text,fontSize:13,margin:"0 0 4px"}}>Pitcher Aging & WAR</h4>
        <p style={{margin:"0 0 12px"}}>Pre-peak: -1.5% ERA improvement/yr. Post-peak to 33: +1.5% ERA rise/yr. After 33: +3%/yr. Pitcher WAR uses the SIERA-based layered anchor vs. replacement level (5.34 for starters, 4.49 for relievers). Starter detection checks entire career history for injury returns. IP projection uses the best full season (100+ IP) from FanGraphs data with an age-based workload adjustment: \u226427 \u00d7 1.03 (trending up), 28-30 \u00d7 1.00 (peak workload), 31-33 \u00d7 0.97, 34+ \u00d7 0.93. Capped at 210 IP. Reliever IP capped at 75.</p>

        <h4 style={{color:C.accent,fontSize:13,margin:"16px 0 4px"}}>Marcel Engine (MiLB & Small-Sample Players)</h4>
        <p style={{margin:"0 0 12px"}}>Players with fewer than 250 Statcast PA use PA-weighted Marcel across all levels. Best 3 seasons weighted 5/4/3 with recency multipliers (1.0/0.85/0.70). Stats translated using level-specific conversion factors (AAA 0.82x, AA 0.68x, A+ 0.58x, A 0.50x). HR are also translated by level factor and projected using games-based rate (HR/G x projected games). Players with fewer than 400 MLB PA use prospect PA estimation (projected games x 4.0 PA/G).</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>FV Grade Integration</h4>
        <p style={{margin:"0 0 12px"}}>Prospects with FanGraphs FV grades and fewer than 400 MLB PA get a weighted blend of their translated stats and FV benchmark OPS. Higher FV grades get more FV weight (70 FV +20%, 65 +12%, 60 +6%). WAR floor is 50% of FV benchmark (70 FV = 4.0 WAR min). Slash line scales proportionally with FV-boosted OPS so wRC+ and OPS are always consistent. HR scales with the SLG boost.</p>

        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Value per Dollar (VpD)</h4>
        <p style={{margin:"0 0 8px"}}>Projected WAR per $1M salary. Grades from A+ (4.0+) through F (below 0.08). Pre-arbitration players at league minimum ($0.8M) naturally receive top grades when projecting positive WAR. Salary data from Spotrac and MLB Trade Rumors.</p>

        <h4 style={{color:C.muted,fontSize:13,margin:"8px 0 4px"}}>Data Pipeline</h4>
        <p style={{margin:0}}>Baseball Savant: xwOBA, xERA, xBA, barrel%, exit velocity, whiff%, sprint speed, OAA, bat speed, Baserunning Run Value (2023-2025, 900+ hitters, 1200+ pitchers, 252 BsR players). FanGraphs: SIERA, xFIP, FIP, K%, BB%, GB%, IP for 815 pitchers (2023-2025), plus plate discipline, FV grades, career fWAR. MLB Stats API: rosters, career splits, all MiLB levels. Spotrac/MLBTR: 2026 contract data.</p>
      </div>

    </Panel>
      </div>


}'''

new_method = '''function MethodPanel() {
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
              {fv>=70?"Franchise Player":fv>=65?"Perennial All-Star":fv>=60?"All-Star upside":fv>=55?"Above-avg regular":fv>=50?"Avg regular":fv>=45?"Solid backup":fv>=40?"Fringe MLB":"\\u2014"}
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
          {g:"A+",t:"4.0+",c:"#10b981"},{g:"A",t:"2.0\\u20134.0",c:"#22c55e"},{g:"A-",t:"1.0\\u20132.0",c:"#84cc16"},
          {g:"B+",t:"0.60\\u20131.0",c:"#eab308"},{g:"B",t:"0.40\\u20130.60",c:"#f59e0b"},{g:"B-",t:"0.25\\u20130.40",c:"#fb923c"},
          {g:"C+",t:"0.18\\u20130.25",c:"#fbbf24"},{g:"C",t:"0.13\\u20130.18",c:"#94a3b8"},
          {g:"D",t:"0.08\\u20130.13",c:"#ef4444"},{g:"F",t:"< 0.08",c:"#dc2626"},
        ].map(v=><div key={v.g} style={{padding:"8px 10px",borderRadius:6,border:`1px solid ${v.c}30`,background:`${v.c}08`}}>
          <div style={{fontSize:16,fontWeight:800,color:v.c,fontFamily:F}}>{v.g}</div>
          <div style={{fontSize:9,color:C.muted,fontFamily:F,marginTop:2}}>{v.t} WAR/$M</div>
        </div>)}
      </div>
      <p style={{margin:"10px 0 0",fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Projected WAR per $1M salary. Pre-arb players at league minimum ($0.8M) naturally receive top grades. Salary data from Spotrac, MLB Trade Rumors, and Cot\\u2019s Baseball Contracts.</p>
    </Panel>

    {/* 3. PROJECTION METHODOLOGY — two columns */}
    <Panel title="PROJECTION METHODOLOGY">
      <p style={{margin:"0 0 14px",fontSize:12,color:C.dim,lineHeight:1.6,fontFamily:F}}>VIAcast projects hitters and pitchers through separate Statcast-powered engines. Both use 3 years of data (2023\\u20132025) weighted 55/30/15% with sample-size reliability scaling. Players below the Statcast threshold use the Marcel fallback with MiLB translation.</p>
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
          {pp("Additive wRC+ adjustment. Pre-peak: +1.5/yr. Peak\\u201332: \\u22121.5/yr. 33+: \\u22123.0/yr. Peaks: SS/2B/3B 28, CF 27, C 27, 1B 29, DH 30.")}

          {h4(C.blue,"L7: Trend Weighting")}
          {pp("Multi-year improvers get +30% trend credit. Chase rate improvements, EV50 breakouts, and bat speed declines feed momentum adjustments.")}

          {h4(C.green,"WAR Construction")}
          {pp("xwOBA \\u2192 wRC+ (4.5 pts per .010 xwOBA). Batting runs + defense (OAA \\u00d7 0.5) + BsR + positional adj + replacement (20 runs/600 PA) \\u00f7 9.5 RPW. HR: barrel% \\u00d7 BBE \\u00d7 0.45 + PA \\u00d7 0.010 baseline.")}
        </div>

        {/* PITCHER COLUMN */}
        <div style={{fontSize:12,color:C.dim,lineHeight:1.7,fontFamily:F}}>
          <div style={{fontSize:11,fontWeight:800,color:C.accent,letterSpacing:".1em",textTransform:"uppercase",marginBottom:10,paddingBottom:6,borderBottom:`2px solid ${C.accent}20`,fontFamily:F}}>PITCHER ENGINE (5 LAYERS)</div>

          {h4(C.blue,"L1: ERA Anchor \\u2014 Layered (35%)")}
          {pp("Falls through in order of predictive accuracy: SIERA \\u2192 xFIP \\u2192 xERA \\u2192 FIP \\u2192 K-BB \\u2192 ERA. SIERA from FanGraphs is primary for 815 pitchers, accounting for K/BB/GB interactions. Pitchers without FG data fall back to xERA from Statcast.")}

          {h4(C.purple,"L2: Command (25%)")}
          {pp("K% and BB% sourced from FanGraphs for 815 pitchers. Fallback: whiff% \\u00d7 1.05. FIP computed with HR allowed estimated from IP \\u00d7 1.2 HR/9 scaled by barrel% allowed.")}

          {h4(C.orange,"L3: Velocity (15%)")}
          {pp("Fastball velocity trends across seasons. Velocity loss is the strongest predictor of pitcher decline. Arsenal mix effectiveness weights pitch-type performance.")}

          {h4(C.text,"L4: Aging Curves")}
          {pp("Pre-peak: \\u22121.5% ERA/yr. Peak\\u201333: +1.5%/yr. 33+: +3%/yr. SP peak at 27, RP peak at 28.")}

          {h4(C.green,"L5: IP Projection")}
          {pp("Best full season (100+ IP) from FanGraphs data with age adjustment: \\u226427 \\u00d7 1.03, 28\\u201330 \\u00d7 1.00, 31\\u201333 \\u00d7 0.97, 34+ \\u00d7 0.93. Capped at 210 IP. Reliever IP capped at 75.")}

          {h4(C.green,"WAR Construction")}
          {pp("(Replacement level \\u2212 projected ERA) \\u00f7 9.5 RPW \\u00d7 IP/9. SP replacement: 5.34, RP replacement: 4.49. Starter detection checks entire career history for injury returns.")}

          <div style={{marginTop:8,padding:"10px 14px",background:`${C.accent}06`,border:`1px solid ${C.accent}15`,borderRadius:8}}>
            <div style={{fontSize:10,fontWeight:700,color:C.accent,fontFamily:F,marginBottom:4}}>MARCEL FALLBACK</div>
            <div style={{fontSize:11,color:C.dim,lineHeight:1.6,fontFamily:F}}>Players below 250 Statcast PA use Marcel with MiLB translation (AAA 0.82x, AA 0.68x, A+ 0.58x, A 0.50x). HR translated by level factor, projected via games-based rate. Prospect PA: projected games \\u00d7 4.0 PA/G.</div>
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
          {n:"MLB Stats API",d:"Player search, career stats, MiLB rosters across all levels (ROK\\u2192AAA). Free, no auth required.",c:C.blue,s:"LIVE"},
          {n:"Contract Data",d:"2026 salary data for 190+ MLB players. Sources: Spotrac, MLB Trade Rumors, Cot\\u2019s Baseball Contracts.",c:C.orange,s:"STATIC"},
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

if old_method in src:
    src = src.replace(old_method, new_method)
    open(APP, "w").write(src)
    print("Replaced entire MethodPanel with redesigned version")
    print()
    print("New section order:")
    print("  1. Future Value Scale (with FV blend explanation)")
    print("  2. Value per Dollar Scale (NEW - full grade table)")
    print("  3. Projection Methodology (two-column: Hitter | Pitcher)")
    print("  4. MiLB Translation")
    print("  5. Data Sources (consolidated, FG expanded)")
    print()
    print("Appel credit: removed")
    print("Pitcher engine: SIERA-first, FG K%/BB%, IP from best full season")
else:
    print("ERROR: Could not find MethodPanel to replace")
    # Debug
    if "function MethodPanel()" in src:
        print("  Found function declaration but content didn't match")
    else:
        print("  Function not found at all")
