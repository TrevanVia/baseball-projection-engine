#!/usr/bin/env python3
"""Patch App.jsx to add VpD badges on player cards and search bar on VpD tab."""

with open("src/App.jsx", "r") as f:
    code = f.read()

# ── PATCH 1: Add VpD helpers after getFVStyle ──
old1 = '  return FV_STYLES[40];\n}\n\n// __ STATCAST LOOKUP'
new1 = '''  return FV_STYLES[40];
}

// __ VpD GRADE + BADGE (module-level) _________________________________________
function getVpdGradeGlobal(warPerM) {
  if (warPerM >= 2.00) return { grade: "A+", color: "#10b981" };
  if (warPerM >= 1.00) return { grade: "A", color: "#22c55e" };
  if (warPerM >= 0.60) return { grade: "A-", color: "#84cc16" };
  if (warPerM >= 0.40) return { grade: "B+", color: "#eab308" };
  if (warPerM >= 0.25) return { grade: "B", color: "#f59e0b" };
  if (warPerM >= 0.18) return { grade: "B-", color: "#fb923c" };
  if (warPerM >= 0.13) return { grade: "C+", color: "#fbbf24" };
  if (warPerM >= 0.10) return { grade: "C", color: "#94a3b8" };
  if (warPerM >= 0.07) return { grade: "D", color: "#ef4444" };
  return { grade: "F", color: "#dc2626" };
}
const VPD_BG={"A+":"linear-gradient(135deg,#10b981,#059669)","A":"linear-gradient(135deg,#22c55e,#16a34a)","A-":"linear-gradient(135deg,#84cc16,#65a30d)","B+":"linear-gradient(135deg,#eab308,#ca8a04)","B":"linear-gradient(135deg,#f59e0b,#d97706)","B-":"linear-gradient(135deg,#fb923c,#ea580c)","C+":"linear-gradient(135deg,#fbbf24,#d97706)","C":"linear-gradient(135deg,#94a3b8,#64748b)","D":"linear-gradient(135deg,#ef4444,#dc2626)","F":"linear-gradient(135deg,#dc2626,#991b1b)"};
const VpDBadge = ({war, salary}) => {
  if (!war || !salary || salary <= 0) return null;
  const g = getVpdGradeGlobal(war / (salary / 1000000));
  return (<span style={{fontSize:10,fontWeight:800,padding:"3px 10px",borderRadius:5,fontFamily:F,background:VPD_BG[g.grade]||VPD_BG["C"],color:g.grade==="C+"?"#78350f":"#fff",display:"inline-block",letterSpacing:".04em"}}>{g.grade} VpD</span>);
};
let _contractCache = null;
async function getContractData() {
  if (_contractCache) return _contractCache;
  try { const m = await import("./contract_data.json"); _contractCache = m.default||m; return _contractCache; } catch { return {}; }
}
function getPlayerSalary(name) { return _contractCache ? (_contractCache[name]||null) : null; }

// __ STATCAST LOOKUP'''

# The file uses unicode em-dashes in comments, let's check
import re
# Find the actual anchor
m = re.search(r'  return FV_STYLES\[40\];\n\}\n\n// .+ STATCAST LOOKUP', code)
if m:
    old1 = m.group(0)
    new1_header = old1.split('\n')[-1]  # Keep the exact comment line
    new1 = '''  return FV_STYLES[40];
}

// __ VpD GRADE + BADGE (module-level) _________________________________________
function getVpdGradeGlobal(warPerM) {
  if (warPerM >= 2.00) return { grade: "A+", color: "#10b981" };
  if (warPerM >= 1.00) return { grade: "A", color: "#22c55e" };
  if (warPerM >= 0.60) return { grade: "A-", color: "#84cc16" };
  if (warPerM >= 0.40) return { grade: "B+", color: "#eab308" };
  if (warPerM >= 0.25) return { grade: "B", color: "#f59e0b" };
  if (warPerM >= 0.18) return { grade: "B-", color: "#fb923c" };
  if (warPerM >= 0.13) return { grade: "C+", color: "#fbbf24" };
  if (warPerM >= 0.10) return { grade: "C", color: "#94a3b8" };
  if (warPerM >= 0.07) return { grade: "D", color: "#ef4444" };
  return { grade: "F", color: "#dc2626" };
}
const VPD_BG={"A+":"linear-gradient(135deg,#10b981,#059669)","A":"linear-gradient(135deg,#22c55e,#16a34a)","A-":"linear-gradient(135deg,#84cc16,#65a30d)","B+":"linear-gradient(135deg,#eab308,#ca8a04)","B":"linear-gradient(135deg,#f59e0b,#d97706)","B-":"linear-gradient(135deg,#fb923c,#ea580c)","C+":"linear-gradient(135deg,#fbbf24,#d97706)","C":"linear-gradient(135deg,#94a3b8,#64748b)","D":"linear-gradient(135deg,#ef4444,#dc2626)","F":"linear-gradient(135deg,#dc2626,#991b1b)"};
const VpDBadge = ({war, salary}) => {
  if (!war || !salary || salary <= 0) return null;
  const g = getVpdGradeGlobal(war / (salary / 1000000));
  return (<span style={{fontSize:10,fontWeight:800,padding:"3px 10px",borderRadius:5,fontFamily:F,background:VPD_BG[g.grade]||VPD_BG["C"],color:g.grade==="C+"?"#78350f":"#fff",display:"inline-block",letterSpacing:".04em"}}>{g.grade} VpD</span>);
};
let _contractCache = null;
async function getContractData() {
  if (_contractCache) return _contractCache;
  try { const m = await import("./contract_data.json"); _contractCache = m.default||m; return _contractCache; } catch { return {}; }
}
function getPlayerSalary(name) { return _contractCache ? (_contractCache[name]||null) : null; }

''' + new1_header
    code = code.replace(old1, new1, 1)
    print("PATCH 1 OK - VpD helpers added after getFVStyle")
else:
    print("PATCH 1 FAILED - could not find getFVStyle anchor")
    exit(1)

# ── PATCH 2: Add salary state to PlayerCard ──
old2 = '  const fv = getPlayerFV(player.id, player.fullName);\n  const sc = getStatcast(player.fullName);\n\n  const seasons = useMemo('
new2 = '  const fv = getPlayerFV(player.id, player.fullName);\n  const sc = getStatcast(player.fullName);\n  const [salary, setSalary] = useState(null);\n  useEffect(() => { getContractData().then(() => setSalary(getPlayerSalary(player.fullName))); }, [player.fullName]);\n\n  const seasons = useMemo('

if old2 in code:
    code = code.replace(old2, new2, 1)
    print("PATCH 2 OK - salary state added to PlayerCard")
else:
    print("PATCH 2 FAILED")
    exit(1)

# ── PATCH 3: Add VpD badge to player card header ──
old3 = '            <div style={{display:"flex",alignItems:"center",gap:10}}>\n              <h2 style={{margin:0,fontSize:22,fontWeight:800,color:C.text,fontFamily:F}}>{player.fullName}</h2>\n              {fv && <FVBadge fv={fv}/>}\n              {!fv && isMiLB && <LevelBadge level={base?.highestLevel||"MiLB"}/>}\n            </div>'
new3 = '            <div style={{display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>\n              <h2 style={{margin:0,fontSize:22,fontWeight:800,color:C.text,fontFamily:F}}>{player.fullName}</h2>\n              {fv && <FVBadge fv={fv}/>}\n              {!fv && isMiLB && <LevelBadge level={base?.highestLevel||"MiLB"}/>}\n              {salary && base?.baseWAR && <VpDBadge war={base.baseWAR} salary={salary}/>}\n            </div>'

if old3 in code:
    code = code.replace(old3, new3, 1)
    print("PATCH 3 OK - VpD badge added to player card header")
else:
    print("PATCH 3 FAILED")
    exit(1)

# ── PATCH 4: Add search state to VpDPanel ──
old4 = '  const [contractData, setContractData] = useState({});\n\n\n  function getVpdGrade'
new4 = '  const [contractData, setContractData] = useState({});\n  const [vpdSearch, setVpdSearch] = useState("");\n\n\n  function getVpdGrade'

if old4 in code:
    code = code.replace(old4, new4, 1)
    print("PATCH 4 OK - vpdSearch state added")
else:
    print("PATCH 4 FAILED")
    exit(1)

# ── PATCH 5: Add search filtering to sorted memo ──
old5 = '  const sorted = useMemo(() => {\n    return [...players].sort((a, b) => {\n      const aVal = a[sort.key];\n      const bVal = b[sort.key];\n      if (typeof aVal === "string") return aVal.localeCompare(bVal) * sort.dir;\n      return (aVal - bVal) * sort.dir;\n    });\n  }, [players, sort]);'
new5 = '  const sorted = useMemo(() => {\n    let filtered = [...players];\n    if (vpdSearch.trim()) { const q = vpdSearch.toLowerCase(); filtered = filtered.filter(p => p.name.toLowerCase().includes(q) || (p.team||"").toLowerCase().includes(q)); }\n    return filtered.sort((a, b) => {\n      const aVal = a[sort.key];\n      const bVal = b[sort.key];\n      if (typeof aVal === "string") return aVal.localeCompare(bVal) * sort.dir;\n      return (aVal - bVal) * sort.dir;\n    });\n  }, [players, sort, vpdSearch]);'

if old5 in code:
    code = code.replace(old5, new5, 1)
    print("PATCH 5 OK - search filtering added to sorted memo")
else:
    print("PATCH 5 FAILED")
    exit(1)

# ── PATCH 6: Add search input above the table ──
old6 = '      <Panel title="VALUE PER DOLLAR (VpD)" sub="Most cost-efficient players based on projected WAR vs. 2026 salary">\n        {loading && <Spinner'
new6 = '      <Panel title="VALUE PER DOLLAR (VpD)" sub="Most cost-efficient players based on projected WAR vs. 2026 salary">\n        <div style={{marginBottom:12}}><input type="text" placeholder="Search players or teams..." value={vpdSearch} onChange={e=>setVpdSearch(e.target.value)} style={{width:"100%",maxWidth:360,padding:"8px 12px",borderRadius:6,border:`1px solid ${C.border}`,background:C.panel,color:C.text,fontSize:12,fontFamily:F,outline:"none",boxSizing:"border-box"}} onFocus={e=>e.target.style.borderColor=C.accent} onBlur={e=>e.target.style.borderColor=C.border}/>{!loading&&<span style={{marginLeft:10,fontSize:10,color:C.muted,fontFamily:F}}>{sorted.length} players</span>}</div>\n        {loading && <Spinner'

if old6 in code:
    code = code.replace(old6, new6, 1)
    print("PATCH 6 OK - search input added to VpD panel")
else:
    print("PATCH 6 FAILED")
    exit(1)

# ── PATCH 7: Populate _contractCache in loadData ──
old7 = '        setContractData(contracts.default || contracts);'
new7 = '        const cMap = contracts.default || contracts;\n        setContractData(cMap);\n        _contractCache = cMap;'

if old7 in code:
    code = code.replace(old7, new7, 1)
    print("PATCH 7 OK - _contractCache populated in loadData")
else:
    print("PATCH 7 FAILED")
    exit(1)

with open("src/App.jsx", "w") as f:
    f.write(code)

lines = code.count('\n') + 1
print(f"\nSUCCESS - All patches applied ({lines} lines)")
print(f"  VpDBadge: {code.count('VpDBadge')}")
print(f"  vpdSearch: {code.count('vpdSearch')}")
print(f"  _contractCache: {code.count('_contractCache')}")
