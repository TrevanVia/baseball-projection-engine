#!/usr/bin/env python3
"""Remove Cards tab + update Methodology. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. REMOVE CARDS TAB
# ═══════════════════════════════════════════════════════════════
old_tabs = """const TABS=[
  {k:"player",l:"Projections",icon:"⚾"},
  {k:"leaders",l:"Leaderboard",icon:"🏆"},
  {k:"roster",l:"Rosters",icon:"📋"},
  {k:"compare",l:"Compare",icon:"⚖️"},
  {k:"cost",l:"Value/Dollar",icon:"💲"},
  {k:"cards",l:"Cards",icon:"🃏"},
  {k:"method",l:"Methodology",icon:"📊"},
];"""

new_tabs = """const TABS=[
  {k:"player",l:"Projections",icon:"⚾"},
  {k:"leaders",l:"Leaderboard",icon:"🏆"},
  {k:"roster",l:"Rosters",icon:"📋"},
  {k:"compare",l:"Compare",icon:"⚖️"},
  {k:"cost",l:"Value/Dollar",icon:"💲"},
  {k:"method",l:"Methodology",icon:"📊"},
];"""

if old_tabs in src:
    src = src.replace(old_tabs, new_tabs)
    changes += 1
    print("1. Removed Cards tab from TABS array")

# Remove the Cards tab rendering
old_cards_render = '{tab==="cards"&&<CardMarketplace onSelect={pick}/>}'
new_cards_render = ''
if old_cards_render in src:
    src = src.replace(old_cards_render, new_cards_render)
    changes += 1
    print("2. Removed Cards tab render")

# ═══════════════════════════════════════════════════════════════
# 2. REWRITE METHODOLOGY
# ═══════════════════════════════════════════════════════════════
old_method_start = '''    <Panel title="PROJECTION METHODOLOGY">
      <div style={{fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F}}>

        <h4 style={{color:C.accent,fontSize:13,margin:"0 0 4px"}}>VIAcast Statcast Engine (MLB Players)</h4>
        <p style={{margin:"0 0 12px"}}>For MLB players with Statcast data (900+ players), VIAcast uses a 7-layer projection system built on 3 years of Baseball Savant and FanGraphs data. This replaces the traditional Marcel approach with process-based metrics that better predict future performance.</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Layer 1: Contact Quality (40%)</h4>
        <p style={{margin:"0 0 12px"}}>Expected wOBA (xwOBA) is the projection anchor. Weighted across 3 seasons (55/30/15%) with PA reliability scaling. Supported by avg exit velocity, EV50, barrel rate, and hard-hit rate.</p>

        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Layer 2: Plate Discipline (25%)</h4>
        <p style={{margin:"0 0 12px"}}>K% and BB% are the strongest predictive signals. Chase rate (O-Swing%), zone contact, and swinging-strike rate from FanGraphs. Selectivity index (Z-Swing/O-Swing) identifies elite pitch recognition.</p>

        <h4 style={{color:"#ec4899",fontSize:13,margin:"0 0 4px"}}>Layer 3: Swing Mechanics (10%)</h4>
        <p style={{margin:"0 0 12px"}}>Bat speed and squared-up rate from Statcast bat tracking. Year-over-year bat speed trends detect early aging signals before traditional stats reflect it.</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>Layer 4: Speed & Baserunning (10%)</h4>
        <p style={{margin:"0 0 12px"}}>Sprint speed (ft/s) with age-adjusted decay (-0.15 ft/s per year after 28). Tiers from elite (30+ ft/s, +5 runs) to below-average (sub-25.5, -4 runs).</p>

        <h4 style={{color:C.orange,fontSize:13,margin:"0 0 4px"}}>Layer 5: Defense</h4>
        <p style={{margin:"0 0 12px"}}>OAA from Statcast, regressed 40% toward zero. ~1.5 runs per OAA with position-specific aging (SS/CF peak 26, corners 28).</p>

        <h4 style={{color:C.text,fontSize:13,margin:"0 0 4px"}}>Layer 6: Aging Curves</h4>
        <p style={{margin:"0 0 12px"}}>Pre-peak +2%/yr. Gradual decline -1.5%/yr through 32, steeper -3%/yr after 33. Position-specific peaks (SS 26, CF 27, corners 28, DH 29).</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Layer 7: Trend Weighting</h4>
        <p style={{margin:"0 0 12px"}}>Consistent multi-year improvers get amplified trend credit. Chase rate improvement, EV50 breakouts, and bat speed declines feed momentum adjustments that catch breakouts early.</p>

        <h4 style={{color:C.accent,fontSize:13,margin:"12px 0 4px"}}>Marcel Fallback (MiLB Players)</h4>
        <p style={{margin:"0 0 12px"}}>Players without Statcast data use PA-weighted Marcel: 3 seasons weighted 5/4/3 with MiLB-to-MLB translation (AAA 87%, AA 80%, A+ 72%). Blended with FV grade benchmarks by sample size.</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>WAR Construction</h4>
        <p style={{margin:"0 0 12px"}}>xwOBA to wRC+ (0.010 xwOBA = 3.2 wRC+). Batting runs + defense + baserunning + positional adj + replacement, divided by 9.5 runs/win.</p>

        <h4 style={{color:C.orange,fontSize:13,margin:"0 0 4px"}}>Value per Dollar (VpD)</h4>
        <p style={{margin:"0 0 8px"}}>Projected WAR per $1M salary. A+ (4.0+) to F (below 0.08). Salary data from Spotrac and MLB Trade Rumors.</p>

        <h4 style={{color:C.muted,fontSize:13,margin:"8px 0 4px"}}>Data Sources</h4>
        <p style={{margin:0}}>Baseball Savant (xwOBA, EV, barrels, sprint speed, OAA, bat speed) | FanGraphs (discipline, wRC+, WAR) | MLB Stats API (rosters, splits) | Spotrac/MLBTR (contracts). Pipeline covers 2023-2025.</p>
      </div>

    </Panel>'''

new_method_start = '''    <Panel title="PROJECTION METHODOLOGY">
      <div style={{fontSize:12,color:C.dim,lineHeight:1.8,fontFamily:F}}>

        <h4 style={{color:C.accent,fontSize:13,margin:"0 0 4px"}}>VIAcast Statcast Engine (Hitters)</h4>
        <p style={{margin:"0 0 12px"}}>For MLB hitters with 250+ career Statcast PA (900+ players), VIAcast uses a 7-layer projection system anchored on 3 years of Baseball Savant data (2023-2025). Players below the 250 PA threshold use the Marcel fallback, which incorporates MiLB data and FV grades.</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Layer 1: Contact Quality (40%)</h4>
        <p style={{margin:"0 0 12px"}}>Expected wOBA (xwOBA) is the primary projection anchor, weighted across 3 seasons (55/30/15%) with PA reliability scaling. Supported by avg exit velocity, EV50, barrel rate, and hard-hit rate from Statcast.</p>

        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Layer 2: Plate Discipline (25%)</h4>
        <p style={{margin:"0 0 12px"}}>K% and BB% from FanGraphs plate discipline data. When unavailable, K% is estimated from Statcast whiff rate (K% \u2248 whiff% \u00d7 0.80). Chase rate (O-Swing%), zone contact, and swinging-strike rate feed a selectivity index that identifies elite pitch recognition.</p>

        <h4 style={{color:"#ec4899",fontSize:13,margin:"0 0 4px"}}>Layer 3: Swing Mechanics (10%)</h4>
        <p style={{margin:"0 0 12px"}}>Bat speed and squared-up rate from Statcast bat tracking. Year-over-year bat speed trends detect early aging signals before traditional stats reflect it.</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>Layer 4: Speed & Baserunning (10%)</h4>
        <p style={{margin:"0 0 12px"}}>Sprint speed (ft/s) with age-adjusted decay (-0.15 ft/s per year after 28). For MiLB players without sprint speed, baserunning is derived from SB/CS/G with efficiency multipliers.</p>

        <h4 style={{color:C.orange,fontSize:13,margin:"0 0 4px"}}>Layer 5: Defense</h4>
        <p style={{margin:"0 0 12px"}}>OAA from Statcast, regressed 40% toward zero. Approximately 1.5 runs per OAA with position-specific aging curves (SS/CF peak at 26, corners at 28).</p>

        <h4 style={{color:C.text,fontSize:13,margin:"0 0 4px"}}>Layer 6: Aging Curves (Hitters)</h4>
        <p style={{margin:"0 0 12px"}}>Single-year forward adjustment applied to wRC+ (not multiplicative xwOBA). Pre-peak: +1.5 wRC+ per year. Ages 28-32: -1.5 wRC+/yr. Ages 33+: -3.0 wRC+/yr. Position-specific peaks: SS 26, CF 27, 2B/3B 27, 1B/DH/OF 28.</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Layer 7: Trend Weighting</h4>
        <p style={{margin:"0 0 12px"}}>Consistent multi-year improvers get amplified trend credit (+30% for same-direction trends). Chase rate improvements, EV50 breakouts, and bat speed declines feed momentum adjustments.</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>WAR Construction (Hitters)</h4>
        <p style={{margin:"0 0 12px"}}>xwOBA \u2192 wRC+ at 4.5 points per .010 xwOBA (league avg .315 xwOBA = 100 wRC+), plus discipline bonus. Batting runs + defense + baserunning + positional adjustment + replacement level, divided by 9.5 runs per win.</p>

        <h4 style={{color:C.accent,fontSize:13,margin:"16px 0 4px"}}>VIAcast Statcast Engine (Pitchers)</h4>
        <p style={{margin:"0 0 12px"}}>5-layer pitcher projection system using Baseball Savant data. WAR is calculated from projected xERA against replacement level, which is more reliable than FIP when K%/BB% data is incomplete.</p>

        <h4 style={{color:C.blue,fontSize:13,margin:"0 0 4px"}}>Pitcher Layer 1: Stuff Quality (35%)</h4>
        <p style={{margin:"0 0 12px"}}>xERA is the projection anchor, weighted across 3 seasons (55/30/15%). Barrel rate allowed and hard-hit rate provide quality-of-contact validation.</p>

        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Pitcher Layer 2: Command (25%)</h4>
        <p style={{margin:"0 0 12px"}}>K% estimated from whiff rate (whiff% \u00d7 0.80) when FanGraphs data is unavailable. BB% and swinging-strike rate round out the command profile.</p>

        <h4 style={{color:C.orange,fontSize:13,margin:"0 0 4px"}}>Pitcher Layer 3: Velocity (15%)</h4>
        <p style={{margin:"0 0 12px"}}>Fastball velocity trends across seasons. Velocity loss is the strongest predictor of pitcher decline. Arsenal mix effectiveness weights pitch-type performance.</p>

        <h4 style={{color:C.text,fontSize:13,margin:"0 0 4px"}}>Pitcher Aging & WAR</h4>
        <p style={{margin:"0 0 12px"}}>Pre-peak: -1.5% ERA improvement/yr. Post-peak to 33: +1.5% ERA rise/yr. After 33: +3%/yr. Pitcher WAR uses xERA vs. replacement level (5.34 for starters, 4.49 for relievers). Starter detection requires 100+ IP or 450+ BFP. Reliever IP capped at 75.</p>

        <h4 style={{color:C.accent,fontSize:13,margin:"16px 0 4px"}}>Marcel Engine (MiLB & Small-Sample Players)</h4>
        <p style={{margin:"0 0 12px"}}>Players with fewer than 250 Statcast PA use PA-weighted Marcel across all levels. Best 3 seasons weighted 5/4/3 with recency multipliers (1.0/0.85/0.70). Stats translated using level-specific conversion factors (AAA 0.82x, AA 0.68x, A+ 0.58x, A 0.50x).</p>

        <h4 style={{color:C.green,fontSize:13,margin:"0 0 4px"}}>FV Grade Integration</h4>
        <p style={{margin:"0 0 12px"}}>Prospects with FanGraphs FV grades and fewer than 400 MLB PA get a weighted blend of their translated stats and FV benchmark OPS. The blend weights scale by sample size: small samples trust FV heavily, larger samples trust stats more. This ensures elite prospects like top FV 65+ players are not penalized by brief MLB callups.</p>

        <h4 style={{color:C.purple,fontSize:13,margin:"0 0 4px"}}>Value per Dollar (VpD)</h4>
        <p style={{margin:"0 0 8px"}}>Projected WAR per $1M salary. Grades from A+ (4.0+) through F (below 0.08). Pre-arbitration players at league minimum ($0.8M) naturally receive top grades when projecting positive WAR. Salary data from Spotrac and MLB Trade Rumors.</p>

        <h4 style={{color:C.muted,fontSize:13,margin:"8px 0 4px"}}>Data Pipeline</h4>
        <p style={{margin:0}}>Baseball Savant: xwOBA, xERA, xBA, barrel%, exit velocity, whiff%, sprint speed, OAA, bat speed (2023-2025, 900+ hitters, 1200+ pitchers). FanGraphs: plate discipline, FV grades, career fWAR. MLB Stats API: rosters, career splits, all MiLB levels. Spotrac/MLBTR: 2026 contract data.</p>
      </div>

    </Panel>'''

if old_method_start in src:
    src = src.replace(old_method_start, new_method_start)
    changes += 1
    print("3. Updated Methodology panel")

# Also update the Data Sources panel
old_savant_source = '{n:"Baseball Savant",d:"Statcast: xwOBA, barrel%, exit velocity, sprint speed. Full integration planned.",c:C.accent,s:"PLANNED"}'
new_savant_source = '{n:"Baseball Savant",d:"Statcast: xwOBA, xERA, barrel%, exit velocity, whiff%, sprint speed, OAA. 2023-2025 pipeline.",c:C.accent,s:"LIVE"}'
if old_savant_source in src:
    src = src.replace(old_savant_source, new_savant_source)
    changes += 1
    print("4. Updated Baseball Savant data source to LIVE")

# Update Statcast/TrackMan description
old_trackman = '{n:"Statcast/TrackMan",d:"Batted ball data: avg EV, max EV, barrel% for top prospects. Hardcoded from MiLB TrackMan.",c:C.purple,s:"STATIC"}'
new_trackman = '{n:"Pitcher Savant Data",d:"Pitcher Statcast: xERA, barrel% allowed, velocity trends, arsenal effectiveness. 1200+ pitchers.",c:C.purple,s:"LIVE"}'
if old_trackman in src:
    src = src.replace(old_trackman, new_trackman)
    changes += 1
    print("5. Updated pitcher data source")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
