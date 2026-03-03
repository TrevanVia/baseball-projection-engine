#!/usr/bin/env python3
"""Update methodology page. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

OLD_MARKER = '<Panel title="PROJECTION METHODOLOGY">'
s = src.find(OLD_MARKER)
# Find the closing </Panel> for this section
pe = src.find('</Panel>', s)
# Then find the next closing </div> } pattern
ce = src.find('\n}\n', pe) + 2

old = src[s:ce]
print("Found block: %d chars" % len(old))

NEW = """<Panel title="PROJECTION METHODOLOGY">
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
        <p style={{margin:"0 0 8px"}}>Projected WAR per $1M salary. A+ (4.0+) to F (<0.08). Salary data from Spotrac and MLB Trade Rumors.</p>

        <h4 style={{color:C.muted,fontSize:13,margin:"8px 0 4px"}}>Data Sources</h4>
        <p style={{margin:0}}>Baseball Savant (xwOBA, EV, barrels, sprint speed, OAA, bat speed) | FanGraphs (discipline, wRC+, WAR) | MLB Stats API (rosters, splits) | Spotrac/MLBTR (contracts). Pipeline covers 2023-2025.</p>
      </div>

    </Panel>
      </div>


}"""

src = src[:s] + NEW + src[ce:]

src = src.replace(
    'Methodology: Marcel (Tango) + level translation + Statcast batted ball adjustments',
    'Methodology: VIAcast 7-layer Statcast engine + Marcel fallback'
)

open(APP, "w").write(src)
print("Done! Lines:", src.count(chr(10)))
