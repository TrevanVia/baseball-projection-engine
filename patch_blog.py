#!/usr/bin/env python3
"""Add Research/Blog section to VIAcast. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. ADD BLOG TAB
# ═══════════════════════════════════════════════════════════════

old_tabs = """const TABS=[
  {k:"player",l:"Projections",icon:"⚾"},
  {k:"leaders",l:"Leaderboard",icon:"🏆"},
  {k:"roster",l:"Rosters",icon:"📋"},
  {k:"compare",l:"Compare",icon:"⚖️"},
  {k:"cost",l:"Value/Dollar",icon:"💲"},
  {k:"method",l:"Methodology",icon:"📊"},
];"""

new_tabs = """const TABS=[
  {k:"player",l:"Projections",icon:"⚾"},
  {k:"leaders",l:"Leaderboard",icon:"🏆"},
  {k:"roster",l:"Rosters",icon:"📋"},
  {k:"compare",l:"Compare",icon:"⚖️"},
  {k:"cost",l:"Value/Dollar",icon:"💲"},
  {k:"research",l:"Research",icon:"📝"},
  {k:"method",l:"Methodology",icon:"📊"},
];"""

if old_tabs in src:
    src = src.replace(old_tabs, new_tabs)
    changes += 1
    print("1. Added Research tab")

# ═══════════════════════════════════════════════════════════════
# 2. ADD URL ROUTE FOR RESEARCH
# ═══════════════════════════════════════════════════════════════

old_paths = """const tabPaths = {player:"/",leaders:"/leaderboard",roster:"/rosters",compare:"/compare",cost:"/value",method:"/methodology"};"""
new_paths = """const tabPaths = {player:"/",leaders:"/leaderboard",roster:"/rosters",compare:"/compare",cost:"/value",research:"/research",method:"/methodology"};"""

if old_paths in src:
    src = src.replace(old_paths, new_paths)
    changes += 1
    print("2. Added /research URL path")

# Add to URL parser
old_parse = '''    if (path === "/methodology") return { tab: "method" };'''
new_parse = '''    if (path === "/methodology") return { tab: "method" };
    if (path === "/research") return { tab: "research" };'''
if old_parse in src:
    src = src.replace(old_parse, new_parse)
    changes += 1
    print("3. Added /research to URL parser")

# Add to popstate handler
old_routes = '''const routes = {"/leaderboard":"leaders","/rosters":"roster","/compare":"compare","/value":"cost","/methodology":"method"};'''
new_routes = '''const routes = {"/leaderboard":"leaders","/rosters":"roster","/compare":"compare","/value":"cost","/research":"research","/methodology":"method"};'''
if old_routes in src:
    src = src.replace(old_routes, new_routes)
    changes += 1
    print("4. Added /research to popstate handler")

# ═══════════════════════════════════════════════════════════════
# 3. ADD RESEARCH PANEL COMPONENT
# ═══════════════════════════════════════════════════════════════

# Insert before MethodPanel
old_method = """function MethodPanel() {"""

blog_component = '''
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
              {post.content.split("\\n\\n").map((para, i) => {
                // Check if paragraph is a header-like line (ALL CAPS or starts with specific patterns)
                const isHeader = /^[A-Z][A-Z ]+:/.test(para) || /^LAYER \\d/.test(para) || /^VALIDATION:/.test(para);
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
            onClick={() => setSelectedPost(post.id)}
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
              <span style={{fontSize:18,color:C.border,fontFamily:F,paddingTop:4}}>&rarr;</span>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}

''' + "function MethodPanel() {"

if old_method in src:
    src = src.replace(old_method, blog_component)
    changes += 1
    print("5. Added ResearchPanel component with 2 initial articles")

# ═══════════════════════════════════════════════════════════════
# 4. ADD TAB RENDER
# ═══════════════════════════════════════════════════════════════

old_render = '        {tab==="method"&&<MethodPanel/>}'
new_render = '''        {tab==="research"&&<ResearchPanel/>}
        {tab==="method"&&<MethodPanel/>}'''

if old_render in src:
    src = src.replace(old_render, new_render)
    changes += 1
    print("6. Added Research tab render")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
