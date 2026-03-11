#!/usr/bin/env python3
"""Add URL routing for shareable links. Run from project root."""
import json

APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# ═══════════════════════════════════════════════════════════════
# 1. UPDATE VERCEL.JSON
# ═══════════════════════════════════════════════════════════════
vc = json.load(open("vercel.json"))
if "rewrites" not in vc:
    vc["rewrites"] = [{"source": "/(.*)", "destination": "/index.html"}]
    json.dump(vc, open("vercel.json", "w"), indent=2)
    changes += 1
    print("1. Added SPA rewrite to vercel.json")
else:
    print("1. vercel.json already has rewrites")

# ═══════════════════════════════════════════════════════════════
# 2. ADD URL PARSING + STATE INIT
# ═══════════════════════════════════════════════════════════════

old_state = '  const [tab,setTab]=useState("player");'
new_state = '''  // URL routing
  const parseURL = () => {
    const path = window.location.pathname;
    const m = path.match(/^\\/player\\/([^/]+?)(?:-(\\d+))?$/);
    if (m) return { tab: "player", playerId: m[2] || null };
    if (path === "/leaderboard") return { tab: "leaders" };
    if (path === "/rosters") return { tab: "roster" };
    if (path === "/compare") return { tab: "compare" };
    if (path === "/value") return { tab: "cost" };
    if (path === "/methodology") return { tab: "method" };
    return { tab: "player" };
  };
  const initRoute = parseURL();
  const [tab,setTab]=useState(initRoute.tab);'''

if 'parseURL' not in src:
    src = src.replace(old_state, new_state)
    changes += 1
    print("2. Added URL parsing for initial route")
else:
    print("2. URL parsing already exists")

# ═══════════════════════════════════════════════════════════════
# 3. UPDATE pick() AND goHome() TO PUSH URL
# ═══════════════════════════════════════════════════════════════

old_pick = '  const pick=useCallback(p=>{setSelPlayer(p);setLp(true);setTab("player");getPlayerStats(p.id).then(d=>{setDetail(d||p);setLp(false);});},[]);'
new_pick = '''  const slugify = (name) => (name||"player").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  const pick=useCallback(p=>{setSelPlayer(p);setLp(true);setTab("player");window.history.pushState({},"",`/player/${slugify(p.fullName||p.name)}-${p.id}`);getPlayerStats(p.id).then(d=>{setDetail(d||p);setLp(false);});},[]);'''

if 'slugify' not in src:
    src = src.replace(old_pick, new_pick)
    changes += 1
    print("3. pick() now pushes player URL")
else:
    print("3. pick() already has URL support")

old_home = '  const goHome = useCallback(()=>{setSelPlayer(null);setDetail(null);setLp(false);setTab("player");},[]);'
new_home = '  const goHome = useCallback(()=>{setSelPlayer(null);setDetail(null);setLp(false);setTab("player");window.history.pushState({},"","/");},[]);'

if 'pushState' not in src or 'goHome' not in src.split('pushState')[0].split('\n')[-1]:
    src = src.replace(old_home, new_home)
    changes += 1
    print("4. goHome() now pushes / URL")
else:
    print("4. goHome() already has URL support")

# ═══════════════════════════════════════════════════════════════
# 4. UPDATE switchTab() TO PUSH URL
# ═══════════════════════════════════════════════════════════════

old_switch = '  const switchTab = useCallback((k) => { setTab(k); setMenuOpen(false); }, []);'
new_switch = '''  const tabPaths = {player:"/",leaders:"/leaderboard",roster:"/rosters",compare:"/compare",cost:"/value",method:"/methodology"};
  const switchTab = useCallback((k) => { setTab(k); setMenuOpen(false); window.history.pushState({},"",tabPaths[k]||"/"); }, []);'''

if 'tabPaths' not in src:
    src = src.replace(old_switch, new_switch)
    changes += 1
    print("5. switchTab() now pushes tab URLs")
else:
    print("5. switchTab() already has URL support")

# ═══════════════════════════════════════════════════════════════
# 5. ADD POPSTATE + DEEP LINK LOADING
# ═══════════════════════════════════════════════════════════════

old_scrolled = '  const [scrolled, setScrolled] = useState(false);'
new_scrolled = '''  const [scrolled, setScrolled] = useState(false);

  // Browser back/forward support
  useEffect(() => {
    const onPop = () => {
      const r = parseURL();
      setTab(r.tab);
      if (r.playerId) {
        setLp(true);
        getPlayerStats(parseInt(r.playerId)).then(d => { if(d){setSelPlayer(d);setDetail(d);} setLp(false); });
      } else if (r.tab === "player") { setSelPlayer(null); setDetail(null); }
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  // Deep link: load player from URL on mount
  useEffect(() => {
    const r = parseURL();
    if (r.playerId) {
      setLp(true);
      getPlayerStats(parseInt(r.playerId)).then(d => { if(d){setSelPlayer(d);setDetail(d);} setLp(false); }).catch(() => setLp(false));
    }
  }, []);'''

if 'onPop' not in src:
    src = src.replace(old_scrolled, new_scrolled, 1)
    changes += 1
    print("6. Added popstate listener + deep link loader")
else:
    print("6. Popstate already exists")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("URLs:")
print("  /player/bobby-witt-jr-677951  -> Witt's card")
print("  /leaderboard                  -> Leaderboard")
print("  /rosters                      -> Rosters")
print("  /compare                      -> Compare")
print("  /value                        -> Value/Dollar")
print("  /methodology                  -> Methodology")
