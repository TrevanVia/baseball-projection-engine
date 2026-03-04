#!/usr/bin/env python3
"""Fix leaderboard crash. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Replace dynamic import() with fetch() - more reliable across bundlers
old_import = '''  // Try loading precomputed projections on mount
  useEffect(() => {
    import("./precomputed_leaderboard.json")
      .then(mod => {
        const data = mod.default || mod;
        if (data?.hitters?.length) {
          // Add _player stubs for click-to-project compatibility
          const h = data.hitters.map(p => ({
            ...p,
            _player: { id: p.id, fullName: p.name, currentAge: p.age,
              primaryPosition: { code: p.pos === "C" ? "2" : p.pos === "1B" ? "3" : p.pos === "2B" ? "4" : p.pos === "3B" ? "5" : p.pos === "SS" ? "6" : p.pos === "LF" ? "7" : p.pos === "CF" ? "8" : p.pos === "RF" ? "9" : p.pos === "DH" ? "10" : "10",
                abbreviation: p.pos },
              currentTeam: { abbreviation: p.team }, _teamAbbr: p.team },
          }));
          setPlayers(h);
          setPitchers((data.pitchers || []).map(p => ({
            ...p,
            fullData: { id: p.id, fullName: p.name, currentAge: p.age,
              primaryPosition: { code: "1", abbreviation: "P" },
              currentTeam: { abbreviation: p.team }, _teamAbbr: p.team },
          })));
          setPrecomputed(true);
          setPrecomputedDate(data.generated);
          setStarted(true);
        }
      })
      .catch(() => { /* No precomputed data available, user can load live */ });
  }, []);'''

new_import = '''  // Try loading precomputed projections on mount
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
  }, []);'''

if old_import in src:
    src = src.replace(old_import, new_import)
    changes += 1
    print("1. Replaced dynamic import() with fetch() for precomputed data")
    print("   Also added _player stub to pitchers (was only fullData)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
