#!/usr/bin/env python3
"""Remove broken precomputed loading. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# Remove the broken precomputed state and useEffect entirely
old_precomputed_block = """  const [precomputed, setPrecomputed] = useState(null);
  const [precomputedDate, setPrecomputedDate] = useState(null);

  // Try loading precomputed projections on mount
  useEffect(() => {
    fetch(new URL("./precomputed_leaderboard.json", import.meta.url))
      .then(r => { if (!r.ok) throw new Error("No precomputed data"); return r.json(); })
      .then(data => {
        if (!data?.hitters?.length) return;
        const posToCode = { C:"2", "1B":"3", "2B":"4", "3B":"5", SS:"6", LF:"7", CF:"8", RF:"9", DH:"10", TWP:"10", OF:"7" };
        // Build _player stubs for click-to-project compatibility
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
      })
      .catch(() => { /* No precomputed data, user can load live */ });
  }, []);"""

new_precomputed_block = ""

if old_precomputed_block in src:
    src = src.replace(old_precomputed_block, new_precomputed_block)
    changes += 1
    print("1. Removed broken precomputed loading block")

# Also remove the precomputedDate badge reference in the header
old_badge = """        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>
          {precomputedDate && <span style={{fontSize:9,color:C.muted,fontFamily:F,padding:"2px 6px",borderRadius:4,background:`${C.green}10`,border:`1px solid ${C.green}20`}}>Updated {new Date(precomputedDate).toLocaleDateString()}</span>}
        </div>"""

new_badge = """        <h3 style={{ margin: 0, fontSize: 16, color: C.text, fontFamily: F }}>MLB Leaderboard</h3>"""

if old_badge in src:
    src = src.replace(old_badge, new_badge)
    changes += 1
    print("2. Removed precomputedDate badge (variable no longer exists)")

# Fix the button text back
old_btn = "Load All Players &amp; Project (Live)"
new_btn = "Load All Players &amp; Project"
if old_btn in src:
    src = src.replace(old_btn, new_btn)
    changes += 1
    print("3. Restored button text")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print("Leaderboard should work again (back to live loading)")
