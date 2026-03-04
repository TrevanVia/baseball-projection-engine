#!/usr/bin/env python3
"""Fix leaderboard: static import for precomputed data. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Add static import at the top (next to other JSON imports)
old_imports = 'import warDataJson from "./war_data.json";'
new_imports = '''import warDataJson from "./war_data.json";
let precomputedDataJson = null;
try { precomputedDataJson = await import("./precomputed_leaderboard.json"); } catch {}'''

# Actually, top-level await won't work. Use a simpler approach:
# Import it statically - if the file exists, it works. If not, build fails.
# Since the file DOES exist in the repo, this is fine.

new_imports = '''import warDataJson from "./war_data.json";
import precomputedDataJson from "./precomputed_leaderboard.json";'''

if old_imports in src:
    src = src.replace(old_imports, new_imports, 1)
    changes += 1
    print("1. Added static import for precomputed_leaderboard.json")

# 2. Replace the fetch-based loading with direct use of the imported data
old_fetch = '''  // Try loading precomputed projections on mount
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

new_fetch = '''  // Load precomputed projections on mount (static import, instant)
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
  }, []);'''

if old_fetch in src:
    src = src.replace(old_fetch, new_fetch)
    changes += 1
    print("2. Replaced fetch() with static import reference (instant, no network)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("The precomputed JSON is now bundled directly into the app via static import,")
print("just like war_data.json and xwoba_data.json. No fetch, no async, no failure modes.")
