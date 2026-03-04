#!/usr/bin/env python3
"""VIAcast UI Overhaul — smoother, more refined interface. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. INJECT GLOBAL CSS — transitions, animations, smooth scrolls
# ═══════════════════════════════════════════════════════════════
# Find the first <link> tag in the return and inject CSS before it
CSS_BLOCK = '''
      <style>{`
        @keyframes spin { to { transform: rotate(360deg) } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(12px) } to { opacity:1; transform:translateY(0) } }
        @keyframes fadeIn { from { opacity:0 } to { opacity:1 } }
        @keyframes shimmer { 0% { background-position: -400px 0 } 100% { background-position: 400px 0 } }
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
          background: #ffffff !important;
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
          background: linear-gradient(90deg, #efe9dd 25%, #f5f0e6 50%, #efe9dd 75%);
          background-size: 800px 100%;
          animation: shimmer 1.5s infinite;
          border-radius: 6px;
        }

        /* Scrollbar styling */
        .via-table-wrap::-webkit-scrollbar { height: 6px; }
        .via-table-wrap::-webkit-scrollbar-track { background: #f5f0e6; border-radius: 3px; }
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
          .via-content { padding: 12px 14px 32px !important; }
          .via-header-inner { gap: 10px !important; }
          .via-stat-row { gap: 4px !important; }
        }
      `}</style>'''

# Insert right after <div style={{minHeight:"100vh"
old_app_start = '''    <div style={{minHeight:"100vh",background:C.bg,color:C.text,fontFamily:F}}>
      <link href'''
new_app_start = '''    <div style={{minHeight:"100vh",background:C.bg,color:C.text,fontFamily:F}}>''' + CSS_BLOCK + '''
      <link href'''
if old_app_start in src:
    src = src.replace(old_app_start, new_app_start, 1)
    changes += 1
    print("1. Injected global CSS (animations, transitions, polish)")


# ═══════════════════════════════════════════════════════════════
# 2. UPGRADE Panel COMPONENT — smooth entrance, subtle depth
# ═══════════════════════════════════════════════════════════════
old_panel = '''const Panel = ({children,title,sub,style={}}) => (
  <div style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:10,padding:"16px 20px",...style}}>
    {title&&<div style={{marginBottom:sub?4:12}}>
      <h3 style={{margin:0,fontSize:13,fontWeight:700,color:C.text,letterSpacing:".06em",fontFamily:F}}>{title}</h3>
      {sub&&<p style={{margin:"3px 0 10px",fontSize:11,color:C.muted,lineHeight:1.4,fontFamily:F}}>{sub}</p>}'''

new_panel = '''const Panel = ({children,title,sub,style={}}) => (
  <div className="via-panel" style={{background:C.panel,border:`1px solid ${C.border}`,borderRadius:12,padding:"18px 22px",boxShadow:"0 1px 3px rgba(26,54,104,0.04)",...style}}>
    {title&&<div style={{marginBottom:sub?0:14}}>
      <h3 style={{margin:0,fontSize:12,fontWeight:700,color:C.text,letterSpacing:".08em",fontFamily:F,textTransform:"uppercase"}}>{title}</h3>
      {sub&&<p style={{margin:"4px 0 12px",fontSize:11,color:C.muted,lineHeight:1.5,fontFamily:F}}>{sub}</p>}'''

if old_panel in src:
    src = src.replace(old_panel, new_panel)
    changes += 1
    print("2. Upgraded Panel component (smoother, subtle shadow)")


# ═══════════════════════════════════════════════════════════════
# 3. UPGRADE Stat COMPONENT — hover lift, smoother feel
# ═══════════════════════════════════════════════════════════════
old_stat = '''const Stat = ({label,value,color=C.accent,sub}) => (
  <div style={{padding:"8px 12px",background:`${color}08`,borderRadius:8,border:`1px solid ${color}20`,minWidth:70,textAlign:"center"}}>
    <div style={{fontSize:20,fontWeight:800,color,fontFamily:F}}>{value}</div>
    <div style={{fontSize:8,color:C.muted,marginTop:1,textTransform:"uppercase",letterSpacing:".08em",fontFamily:F}}>{label}</div>
    {sub&&<div style={{fontSize:8,color:C.dim,fontFamily:F}}>{sub}</div>}'''

new_stat = '''const Stat = ({label,value,color=C.accent,sub}) => (
  <div className="via-stat" style={{padding:"10px 14px",background:`${color}06`,borderRadius:10,border:`1px solid ${color}15`,minWidth:72,textAlign:"center",cursor:"default"}}>
    <div style={{fontSize:22,fontWeight:800,color,fontFamily:F,lineHeight:1.1}}>{value}</div>
    <div style={{fontSize:7.5,color:C.muted,marginTop:3,textTransform:"uppercase",letterSpacing:".1em",fontFamily:F,fontWeight:600}}>{label}</div>
    {sub&&<div style={{fontSize:7.5,color:C.dim,fontFamily:F,marginTop:1}}>{sub}</div>}'''

if old_stat in src:
    src = src.replace(old_stat, new_stat)
    changes += 1
    print("3. Upgraded Stat component (lift on hover, refined spacing)")


# ═══════════════════════════════════════════════════════════════
# 4. UPGRADE Pill/Tab BUTTONS — smoother transitions
# ═══════════════════════════════════════════════════════════════
old_pill = '''const Pill = ({label,active,onClick,color=C.accent}) => (
  <button onClick={onClick} style={{padding:"5px 14px",border:"none",borderRadius:6,cursor:"pointer",fontSize:11,fontWeight:active?700:500,fontFamily:F,background:active?color:"#efe9dd",color:active?"#fff":C.muted}}>{label}</button>'''

new_pill = '''const Pill = ({label,active,onClick,color=C.accent}) => (
  <button className="via-pill" onClick={onClick} style={{padding:"6px 16px",border:"none",borderRadius:8,cursor:"pointer",fontSize:11,fontWeight:active?700:500,fontFamily:F,background:active?color:"#efe9dd",color:active?"#fff":C.muted,letterSpacing:".02em"}}>{label}</button>'''

if old_pill in src:
    src = src.replace(old_pill, new_pill)
    changes += 1
    print("4. Upgraded Pill buttons (smooth transitions)")


# ═══════════════════════════════════════════════════════════════
# 5. UPGRADE Spinner — smoother loading state
# ═══════════════════════════════════════════════════════════════
old_spinner = '''const Spinner = ({msg="Loading..."}) => (
  <div style={{display:"flex",alignItems:"center",gap:8,padding:20,color:C.dim,fontFamily:F,fontSize:12}}>
    <div style={{width:16,height:16,border:`2px solid ${C.border}`,borderTopColor:C.accent,borderRadius:"50%",animation:"spin .8s linear infinite"}}/>'''

new_spinner = '''const Spinner = ({msg="Loading..."}) => (
  <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:10,padding:32,color:C.dim,fontFamily:F,fontSize:12,animation:"fadeIn 0.3s ease"}}>
    <div style={{width:18,height:18,border:`2px solid ${C.border}`,borderTopColor:C.accent,borderRadius:"50%",animation:"spin .7s linear infinite"}}/>'''

if old_spinner in src:
    src = src.replace(old_spinner, new_spinner)
    changes += 1
    print("5. Upgraded Spinner (smoother, centered)")


# ═══════════════════════════════════════════════════════════════
# 6. UPGRADE Search input — focus ring, smoother dropdown
# ═══════════════════════════════════════════════════════════════
old_search_input = '''style={{width:"100%",padding:"8px 12px",borderRadius:8,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:12,fontFamily:F,outline:"none"}}'''

new_search_input = '''className="via-search-input" style={{width:"100%",padding:"10px 14px",borderRadius:10,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:12,fontFamily:F,outline:"none"}}'''

c = src.count(old_search_input)
if c > 0:
    src = src.replace(old_search_input, new_search_input)
    changes += 1
    print("6. Upgraded search inputs (%d instances)" % c)

# Search dropdown
old_dropdown = '''style={{position:"absolute",top:"100%",left:0,right:0,background:C.panel,border:`1px solid ${C.border}`,borderRadius:8,marginTop:4,maxHeight:320,overflowY:"auto",zIndex:999,boxShadow:"0 12px 36px rgba(0,0,0,.12)"}}'''

new_dropdown = '''className="via-search-dropdown" style={{position:"absolute",top:"100%",left:0,right:0,background:C.panel,border:`1px solid ${C.border}`,borderRadius:12,marginTop:6,maxHeight:320,overflowY:"auto",zIndex:999,boxShadow:"0 16px 48px rgba(26,54,104,.12)"}}'''

if old_dropdown in src:
    src = src.replace(old_dropdown, new_dropdown)
    changes += 1
    print("7. Upgraded search dropdown (glass effect, smoother)")


# ═══════════════════════════════════════════════════════════════
# 8. UPGRADE Header — sticky with scroll shadow
# ═══════════════════════════════════════════════════════════════
old_header = '''<div className="via-header" style={{padding:"14px 24px 0",borderBottom:`2px solid ${C.navy}`,background:"linear-gradient(180deg, #ffffff 0%, #f9f5ed 100%)"}}>'''

new_header = '''<div className="via-header" style={{padding:"14px 24px 0",borderBottom:`1.5px solid ${C.navy}20`,background:"linear-gradient(180deg, #ffffff 0%, #faf6ee 100%)",backdropFilter:"blur(12px)"}}>'''

if old_header in src:
    src = src.replace(old_header, new_header)
    changes += 1
    print("8. Upgraded header (softer border, blur backdrop)")


# ═══════════════════════════════════════════════════════════════
# 9. UPGRADE Tab bar — add via-tab class for smooth underlines
# ═══════════════════════════════════════════════════════════════
old_tab_btn = '''            {TABS.map(t=><button key={t.k} onClick={()=>switchTab(t.k)} style={{
              padding:"7px 14px",border:"none",cursor:"pointer",fontSize:10,fontWeight:tab===t.k?700:500,fontFamily:F,
              background:tab===t.k?C.panel:"transparent",color:tab===t.k?C.navy:C.muted,
              borderRadius:"6px 6px 0 0",borderBottom:tab===t.k?`2px solid ${C.accent}`:"2px solid transparent",
              whiteSpace:"nowrap",transition:"all 0.15s ease",
            }}
            onMouseEnter={e=>{if(tab!==t.k){e.target.style.color=C.navy;e.target.style.background=C.hover;}}}
            onMouseLeave={e=>{if(tab!==t.k){e.target.style.color=C.muted;e.target.style.background="transparent";}}}
            >{t.l}</button>)}'''

new_tab_btn = '''            {TABS.map(t=><button key={t.k} className={`via-tab ${tab===t.k?"via-tab-active":""}`} onClick={()=>switchTab(t.k)} style={{
              padding:"8px 16px",border:"none",cursor:"pointer",fontSize:10,fontWeight:tab===t.k?700:500,fontFamily:F,
              background:tab===t.k?C.panel:"transparent",color:tab===t.k?C.navy:C.muted,
              borderRadius:"8px 8px 0 0",borderBottom:"2px solid transparent",
              whiteSpace:"nowrap",letterSpacing:".03em",
            }}
            onMouseEnter={e=>{if(tab!==t.k){e.target.style.color=C.navy;e.target.style.background=C.hover;}}}
            onMouseLeave={e=>{if(tab!==t.k){e.target.style.color=C.muted;e.target.style.background="transparent";}}}
            >{t.l}</button>)}'''

if old_tab_btn in src:
    src = src.replace(old_tab_btn, new_tab_btn)
    changes += 1
    print("9. Upgraded tab bar (smooth underline animation)")


# ═══════════════════════════════════════════════════════════════
# 10. UPGRADE Quick-pick buttons on home screen
# ═══════════════════════════════════════════════════════════════
old_quickpick = '''style={{padding:"5px 12px",borderRadius:6,border:`1px solid ${C.border}`,background:"transparent",color:C.dim,fontSize:11,fontFamily:F,cursor:"pointer"}}
                  onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.color=C.accent;}}
                  onMouseLeave={e=>{e.target.style.borderColor=C.border;e.target.style.color=C.dim;}}'''

new_quickpick = '''className="via-quick-pick" style={{padding:"6px 14px",borderRadius:8,border:`1px solid ${C.border}`,background:"transparent",color:C.dim,fontSize:11,fontFamily:F,cursor:"pointer"}}'''

if old_quickpick in src:
    src = src.replace(old_quickpick, new_quickpick)
    changes += 1
    print("10. Upgraded quick-pick buttons (CSS transitions)")


# ═══════════════════════════════════════════════════════════════
# 11. UPGRADE Player card layout — more breathing room
# ═══════════════════════════════════════════════════════════════
old_card_gap = '''    <div style={{display:"flex",flexDirection:"column",gap:14}}>
      {/* Header */}'''

new_card_gap = '''    <div style={{display:"flex",flexDirection:"column",gap:16}}>
      {/* Header */}'''

if old_card_gap in src:
    src = src.replace(old_card_gap, new_card_gap, 1)
    changes += 1
    print("11. Increased card spacing (16px gap)")


# ═══════════════════════════════════════════════════════════════
# 12. UPGRADE Content padding + max-width for readability
# ═══════════════════════════════════════════════════════════════
old_content = '''<div className="via-content" style={{padding:"16px 24px 40px"}}>'''

new_content = '''<div className="via-content" style={{padding:"20px 28px 48px",maxWidth:1280,margin:"0 auto"}}>'''

if old_content in src:
    src = src.replace(old_content, new_content, 1)
    changes += 1
    print("12. Upgraded content area (centered, more padding)")


# ═══════════════════════════════════════════════════════════════
# 13. UPGRADE LevelBadge — pop-in animation
# ═══════════════════════════════════════════════════════════════
old_lvl = '''<LevelBadge level={base?.highestLevel||"MiLB"}/>'''
# No change needed here, but let's upgrade the badge component itself
old_lvl_comp = '''  <span style={{fontSize:9,fontWeight:700,padding:"2px 7px",borderRadius:4,fontFamily:F,background:`${LEVEL_COLORS[level]||C.muted}20`,color:LEVEL_COLORS[level]||C.muted}}>{level}</span>'''

new_lvl_comp = '''  <span className="via-badge" style={{fontSize:9,fontWeight:700,padding:"3px 8px",borderRadius:5,fontFamily:F,background:`${LEVEL_COLORS[level]||C.muted}15`,color:LEVEL_COLORS[level]||C.muted,letterSpacing:".04em"}}>{level}</span>'''

if old_lvl_comp in src:
    src = src.replace(old_lvl_comp, new_lvl_comp)
    changes += 1
    print("13. Upgraded LevelBadge (pop-in animation)")


# ═══════════════════════════════════════════════════════════════
# 14. UPGRADE Player name + info styling
# ═══════════════════════════════════════════════════════════════
old_name = '''<h2 style={{margin:0,fontSize:22,fontWeight:800,color:C.text,fontFamily:F}}>{player.fullName}</h2>'''

new_name = '''<h2 style={{margin:0,fontSize:24,fontWeight:800,color:C.text,fontFamily:F,letterSpacing:"-0.01em"}}>{player.fullName}</h2>'''

if old_name in src:
    src = src.replace(old_name, new_name)
    changes += 1
    print("14. Upgraded player name typography")


# ═══════════════════════════════════════════════════════════════
# 15. UPGRADE FVBadge — pop-in + smoother
# ═══════════════════════════════════════════════════════════════
old_fv_style = '''      fontSize:10, fontWeight:800, padding:"3px 10px", borderRadius:5, fontFamily:F,'''

new_fv_style = '''      fontSize:10, fontWeight:800, padding:"4px 11px", borderRadius:6, fontFamily:F,'''

if old_fv_style in src:
    src = src.replace(old_fv_style, new_fv_style)
    changes += 1
    print("15. Upgraded FVBadge sizing")


# ═══════════════════════════════════════════════════════════════
# 16. ADD scroll listener to header for shadow on scroll
# ═══════════════════════════════════════════════════════════════
# Add a useEffect for scroll detection after the existing useEffect
old_mobile_eff = '''  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);'''

new_mobile_eff = '''  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);'''

if old_mobile_eff in src:
    src = src.replace(old_mobile_eff, new_mobile_eff)
    changes += 1
    print("16. Added scroll shadow detection")

# Apply scrolled class to header
old_header_cls = '''<div className="via-header"'''
new_header_cls = '''<div className={`via-header ${scrolled?"via-header-scrolled":""}`}'''
if old_header_cls in src:
    src = src.replace(old_header_cls, new_header_cls, 1)
    changes += 1
    print("17. Connected scroll shadow to header")


# ═══════════════════════════════════════════════════════════════
# 18. UPGRADE Leaderboard table header styling
# ═══════════════════════════════════════════════════════════════
old_home_panel = '''<Panel style={{textAlign:"center",padding:50}}>
            <div style={{fontSize:44,marginBottom:12}}>&#9918;</div>
            <h3 style={{margin:0,fontSize:16,color:C.text,fontFamily:F}}>Search any MLB or minor league player</h3>'''

new_home_panel = '''<Panel style={{textAlign:"center",padding:"56px 32px"}}>
            <div style={{fontSize:48,marginBottom:16,filter:"drop-shadow(0 2px 4px rgba(0,0,0,0.1))"}}>&#9918;</div>
            <h3 style={{margin:0,fontSize:17,color:C.text,fontFamily:F,letterSpacing:"-0.01em"}}>Search any MLB or minor league player</h3>'''

if old_home_panel in src:
    src = src.replace(old_home_panel, new_home_panel, 1)
    changes += 1
    print("18. Upgraded home panel")


# ═══════════════════════════════════════════════════════════════
# 19. UPGRADE Chart panel - more height, smoother tooltip
# ═══════════════════════════════════════════════════════════════
old_chart = '''<ResponsiveContainer width="100%" height={280}>'''
new_chart = '''<ResponsiveContainer width="100%" height={300}>'''
c = src.count(old_chart)
if c > 0:
    src = src.replace(old_chart, new_chart)
    changes += 1
    print("19. Taller charts (%d instances)" % c)


# ═══════════════════════════════════════════════════════════════
# 20. Upgrade projection pill bar background
# ═══════════════════════════════════════════════════════════════
old_pill_bar = '''<div style={{display:"flex",gap:4,background:"#efe9dd",borderRadius:8,padding:3,width:"fit-content"}}>'''
new_pill_bar = '''<div style={{display:"flex",gap:4,background:"#efe9dd",borderRadius:10,padding:4,width:"fit-content"}}>'''
c = src.count(old_pill_bar)
if c > 0:
    src = src.replace(old_pill_bar, new_pill_bar)
    changes += 1
    print("20. Upgraded pill bar container (%d instances)" % c)


open(APP, "w").write(src)
print("\n" + "=" * 60)
print("Applied %d UI changes" % changes)
print("=" * 60)
