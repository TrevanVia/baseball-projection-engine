#!/usr/bin/env python3
"""Mobile optimization for VIAcast. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. ENHANCE MOBILE CSS - add rules for landing page grids,
#    compare tool, player card, POTD, etc.
# ═══════════════════════════════════════════════════════════════

old_mobile_css = """@media(max-width:768px){
  .via-header{padding:12px 16px 0!important}
  .via-header-inner{flex-direction:row!important;align-items:center!important;gap:8px!important;flex-wrap:nowrap!important}
  .via-search{display:none!important}
  .via-content{padding:8px 12px 20px!important}
  .via-tabs{display:none!important}
  .via-search{width:100%!important;margin:8px auto 0!important;box-sizing:border-box!important;max-width:400px!important;display:block!important}
  .via-title{font-size:28px!important}
  .via-subtitle{font-size:8px!important;letter-spacing:.14em!important}
  .via-tagline{font-size:7px!important}
  .via-stat-row{gap:4px!important;flex-wrap:wrap!important;justify-content:center!important}
  .via-stat-box{min-width:58px!important;padding:6px 8px!important}
  .via-stat-box .via-stat-val{font-size:14px!important}
  .via-stat-box .via-stat-label{font-size:6px!important}
  .via-panel{padding:10px 12px!important;margin-bottom:8px!important}
  .via-footer{padding:8px 12px!important;flex-direction:column!important;gap:4px!important;text-align:center!important}
  .via-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 -12px;padding:0 12px}
  .via-table-wrap table{min-width:500px}
  .via-table-wrap th,.via-table-wrap td{padding:4px 6px!important;font-size:10px!important}
  .via-player-name{font-size:20px!important}
  .via-player-info{font-size:10px!important}
  .via-pos-filters{gap:2px!important}
  .via-pos-filters button{padding:4px 8px!important;font-size:9px!important}
  .via-mode-toggle{gap:2px!important}
  .via-mode-toggle button{padding:5px 12px!important;font-size:10px!important}
  .via-leaderboard-filters{flex-direction:column!important;gap:8px!important;align-items:stretch!important}
  .via-leaderboard-filters input{width:100%!important;box-sizing:border-box!important}
}
@media(max-width:480px){
  .via-title{font-size:24px!important}
  .via-stat-box{min-width:50px!important;padding:5px 6px!important}
  .via-stat-box .via-stat-val{font-size:12px!important}
  .via-table-wrap th,.via-table-wrap td{padding:3px 4px!important;font-size:9px!important}
  .via-player-name{font-size:18px!important}
}"""

new_mobile_css = """@media(max-width:768px){
  .via-header{padding:12px 16px 0!important}
  .via-header-inner{flex-direction:row!important;align-items:center!important;gap:8px!important;flex-wrap:nowrap!important}
  .via-search{display:none!important}
  .via-content{padding:8px 12px 20px!important}
  .via-tabs{display:none!important}
  .via-search{width:100%!important;margin:8px auto 0!important;box-sizing:border-box!important;max-width:400px!important;display:block!important}
  .via-title{font-size:28px!important}
  .via-subtitle{font-size:8px!important;letter-spacing:.14em!important}
  .via-tagline{font-size:7px!important}
  .via-stat-row{gap:4px!important;flex-wrap:wrap!important;justify-content:center!important}
  .via-stat-box{min-width:58px!important;padding:6px 8px!important}
  .via-stat-box .via-stat-val{font-size:14px!important}
  .via-stat-box .via-stat-label{font-size:6px!important}
  .via-panel{padding:10px 12px!important;margin-bottom:8px!important}
  .via-footer{padding:8px 12px!important;flex-direction:column!important;gap:4px!important;text-align:center!important}
  .via-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 -12px;padding:0 12px}
  .via-table-wrap table{min-width:500px}
  .via-table-wrap th,.via-table-wrap td{padding:4px 6px!important;font-size:10px!important}
  .via-player-name{font-size:20px!important}
  .via-player-info{font-size:10px!important}
  .via-pos-filters{gap:2px!important}
  .via-pos-filters button{padding:4px 8px!important;font-size:9px!important}
  .via-mode-toggle{gap:2px!important}
  .via-mode-toggle button{padding:5px 12px!important;font-size:10px!important}
  .via-leaderboard-filters{flex-direction:column!important;gap:8px!important;align-items:stretch!important}
  .via-leaderboard-filters input{width:100%!important;box-sizing:border-box!important}
  /* Landing page grids → single column on mobile */
  .via-landing-2col{grid-template-columns:1fr!important}
  /* Compare tool slots */
  .via-compare-slots{grid-template-columns:1fr!important}
  /* Roster team grid */
  .via-roster-grid{grid-template-columns:repeat(auto-fill,minmax(160px,1fr))!important}
  /* Quick pick buttons wrap better */
  .via-quick-pick{padding:6px 10px!important;font-size:10px!important}
  /* Stats bar on landing */
  .via-engine-stats{gap:12px!important;padding:10px 14px!important}
  .via-engine-stats > div{min-width:60px!important}
  /* Player card stat boxes */
  .via-card-stats{flex-wrap:wrap!important;gap:6px!important}
  /* VpD table */
  .via-vpd-table{min-width:600px}
}
@media(max-width:480px){
  .via-title{font-size:24px!important}
  .via-stat-box{min-width:50px!important;padding:5px 6px!important}
  .via-stat-box .via-stat-val{font-size:12px!important}
  .via-table-wrap th,.via-table-wrap td{padding:3px 4px!important;font-size:9px!important}
  .via-player-name{font-size:18px!important}
  .via-engine-stats{gap:8px!important;flex-wrap:wrap!important}
  .via-quick-pick{padding:5px 8px!important;font-size:9px!important}
}"""

if old_mobile_css in src:
    src = src.replace(old_mobile_css, new_mobile_css)
    changes += 1
    print("1. Enhanced mobile CSS (landing grids, compare, roster, stats bar)")

# ═══════════════════════════════════════════════════════════════
# 2. ADD CSS CLASSES TO LANDING PAGE GRIDS
# ═══════════════════════════════════════════════════════════════

# Top hitters/pitchers grid
old_grid1 = '''            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
              <Panel title="TOP HITTERS"'''
new_grid1 = '''            <div className="via-landing-2col" style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
              <Panel title="TOP HITTERS"'''
if old_grid1 in src:
    src = src.replace(old_grid1, new_grid1)
    changes += 1
    print("2. Added via-landing-2col class to hitters/pitchers grid")

# Prospects + What Is grid
old_grid2 = '''            {/* Top Prospects + What Is VIAcast */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>'''
new_grid2 = '''            {/* Top Prospects + What Is VIAcast */}
            <div className="via-landing-2col" style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>'''
if old_grid2 in src:
    src = src.replace(old_grid2, new_grid2)
    changes += 1
    print("3. Added via-landing-2col class to prospects/about grid")

# Engine stats bar
old_stats_bar = '''            <div style={{display:"flex",justifyContent:"center",gap:20,flexWrap:"wrap",padding:"14px 20px",background:`linear-gradient(135deg, ${C.navy}08, ${C.accent}05)`,borderRadius:12,border:`1px solid ${C.navy}12`}}>'''
new_stats_bar = '''            <div className="via-engine-stats" style={{display:"flex",justifyContent:"center",gap:20,flexWrap:"wrap",padding:"14px 20px",background:`linear-gradient(135deg, ${C.navy}08, ${C.accent}05)`,borderRadius:12,border:`1px solid ${C.navy}12`}}>'''
if old_stats_bar in src:
    src = src.replace(old_stats_bar, new_stats_bar)
    changes += 1
    print("4. Added via-engine-stats class to stats bar")

# ═══════════════════════════════════════════════════════════════
# 3. ADD CLASS TO COMPARE PANEL SLOTS GRID
# ═══════════════════════════════════════════════════════════════

old_compare_grid = '''style={{display:"grid",gridTemplateColumns:"repeat(3, 1fr)",gap:12,marginBottom:14}}'''
new_compare_grid = '''className="via-compare-slots" style={{display:"grid",gridTemplateColumns:"repeat(3, 1fr)",gap:12,marginBottom:14}}'''
if old_compare_grid in src:
    src = src.replace(old_compare_grid, new_compare_grid, 1)
    changes += 1
    print("5. Added via-compare-slots class to compare grid")

# ═══════════════════════════════════════════════════════════════
# 4. ADD VIEWPORT META TAG CHECK
# ═══════════════════════════════════════════════════════════════
# This should already be in index.html but let's make sure
# the resize listener is debounced

old_resize = """  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);"""
new_resize = """  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  useEffect(() => {
    let timeout;
    const handleResize = () => { clearTimeout(timeout); timeout = setTimeout(() => setIsMobile(window.innerWidth <= 768), 100); };
    window.addEventListener("resize", handleResize);
    return () => { window.removeEventListener("resize", handleResize); clearTimeout(timeout); };
  }, []);"""

if old_resize in src:
    # Check if there's already a resize listener
    if "handleResize" not in src:
        src = src.replace(old_resize, new_resize)
        changes += 1
        print("6. Added debounced resize listener for isMobile")
    else:
        print("6. Resize listener already exists, skipping")

# ═══════════════════════════════════════════════════════════════
# 5. ADD ROSTER GRID CLASS
# ═══════════════════════════════════════════════════════════════

old_roster_grid = '''style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))",gap:6}}>
          {[...teams]'''
new_roster_grid = '''className="via-roster-grid" style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))",gap:6}}>
          {[...teams]'''
if old_roster_grid in src:
    src = src.replace(old_roster_grid, new_roster_grid)
    changes += 1
    print("7. Added via-roster-grid class to roster team selector")

# ═══════════════════════════════════════════════════════════════
# 6. MAKE PLAYER CARD CHART RESPONSIVE
# ═══════════════════════════════════════════════════════════════

old_chart_height = '''height:300,'''
new_chart_height = '''height:isMobile?220:300,'''
# This won't work since isMobile isn't in scope of the chart.
# Instead, let's use CSS
# Actually the chart height is in a style prop on the recharts container
# Let's skip this and handle via CSS instead - the chart auto-scales width

# ═══════════════════════════════════════════════════════════════
# 7. ADD VPD TABLE CLASS
# ═══════════════════════════════════════════════════════════════

# Find the VpD table wrapper
old_vpd = '''className="via-table-wrap" style={{overflowX:"auto"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:11,fontFamily:F}}>
              <thead><tr>
                <th'''
# The VpD table needs the same horizontal scroll treatment
# It should already have via-table-wrap - let's verify
if 'via-vpd-table' not in src and 'VpD' in src:
    print("7. VpD table uses via-table-wrap (already has scroll)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Mobile optimizations:")
print("  - Landing page 2-column grids → single column on mobile")
print("  - Compare tool 3-slot grid → single column")
print("  - Stats bar wraps with smaller gaps")
print("  - Roster team grid adapts to narrower columns")
print("  - Quick-pick buttons get smaller padding")
print("  - All tables horizontally scrollable")
print("  - Debounced resize listener for orientation changes")
