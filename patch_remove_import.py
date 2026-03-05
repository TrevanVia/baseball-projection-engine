#!/usr/bin/env python3
"""Remove ALL precomputed loading code. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Remove static import line
old = 'import precomputedDataJson from "./precomputed_leaderboard.json";\n'
if old in src:
    src = src.replace(old, '')
    changes += 1
    print("1. Removed static import")

# 2. Remove state variables
old2 = """  const [precomputed, setPrecomputed] = useState(null);
  const [precomputedDate, setPrecomputedDate] = useState(null);

  // Load precomputed projections on mount (static import, instant)
  useEffect(() => {
    try {
      const data = precomputedDataJson;
      if (data?.hitters?.length) {
        const posToCode = { C:"2", "1B":"3", "2B":"4", "3B":"5", SS:"6", LF:"7", CF:"8", RF:"9", DH:"10", TWP:"10", OF:"7" };
        const h = data.hitters.map(p => ({
          ...p,
          _player: { id: p.id, fullName: p.name, currentAge: p.age,
            primaryPosition: { code: posToCode[p.pos] || "10", abbreviation: p.pos },
            currentTeam: { abbreviation: p.team }, _teamAbbr: p.team },
        }));
        const pit = (data.pitchers || []).map(p => ({
          ...p,
          _player: { id: p.id, fullName: p.name, currentAge: p.age,
            primaryPosition: { code: "1", abbreviation: "P" },
            currentTeam: { abbreviation: p.team }, _teamAbbr: p.team },
          fullData: { id: p.id, fullName: p.name, currentAge: p.age,
            primaryPosition: { code: "1", abbreviation: "P" },
            currentTeam: { abbreviation: p.team }, _teamAbbr: p.team },
        }));
        setPlayers(h);
        setPitchers(pit);
        setPrecomputed(true);
        setPrecomputedDate(data.generated);
        setStarted(true);
      }
    } catch(e) { console.warn("No precomputed data:", e); }
  }, []);"""

if old2 in src:
    src = src.replace(old2, '')
    changes += 1
    print("2. Removed precomputed state + useEffect block")

# 3. Remove precomputedDate badge if still present
old3 = """        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>
          {precomputedDate && <span style={{fontSize:9,color:C.muted,fontFamily:F,padding:"2px 6px",borderRadius:4,background:`${C.green}10`,border:`1px solid ${C.green}20`}}>Updated {new Date(precomputedDate).toLocaleDateString()}</span>}
        </div>"""
new3 = """        <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>"""
if old3 in src:
    src = src.replace(old3, new3)
    changes += 1
    print("3. Removed precomputedDate badge")

# 4. Fix button text
src = src.replace("Load All Players &amp; Project (Live)", "Load All Players &amp; Project")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print("All precomputed code removed. Site should load cleanly.")
