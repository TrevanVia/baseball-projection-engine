#!/usr/bin/env python3
"""Add retry logic for leaderboard loading + fix Julio. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Add retry logic to fetchPlayerSeasonStats
old_fetch = """async function fetchPlayerSeasonStats(playerId) {
  // Fetch most recent 3 seasons across all levels
  const sportIds = [1, 11, 12, 13, 14, 16];
  try {
    const promises = sportIds.map(sid =>
      fetch(`${API}/people/${playerId}/stats?stats=yearByYear&group=hitting&gameType=R&sportId=${sid}`)
        .then(r => r.json())
        .then(d => (d.stats?.[0]?.splits || []).map(s => ({ ...s, _sportId: sid })))
        .catch(() => [])
    );
    const all = await Promise.all(promises);
    return all.flat();
  } catch { return []; }
}"""

new_fetch = """async function fetchPlayerSeasonStats(playerId) {
  const sportIds = [1, 11, 12, 13, 14, 16];
  const fetchWithRetry = async (url, retries = 2) => {
    for (let r = 0; r <= retries; r++) {
      try {
        if (r > 0) await new Promise(ok => setTimeout(ok, 500 * r));
        const resp = await fetch(url);
        if (!resp.ok && r < retries) continue;
        return await resp.json();
      } catch { if (r === retries) return null; }
    }
    return null;
  };
  try {
    const promises = sportIds.map(async sid => {
      const d = await fetchWithRetry(`${API}/people/${playerId}/stats?stats=yearByYear&group=hitting&gameType=R&sportId=${sid}`);
      return d ? (d.stats?.[0]?.splits || []).map(s => ({ ...s, _sportId: sid })) : [];
    });
    const all = await Promise.all(promises);
    return all.flat();
  } catch { return []; }
}"""

if old_fetch in src:
    src = src.replace(old_fetch, new_fetch)
    changes += 1
    print("1. Added retry logic to fetchPlayerSeasonStats")

# 2. Same for pitcher stats
old_pfetch = """async function fetchPlayerPitchingStats(playerId) {
  const sportIds = [1, 11, 12, 13, 14, 16];
  try {
    const promises = sportIds.map(sid =>
      fetch(`${API}/people/${playerId}/stats?stats=yearByYear&group=pitching&gameType=R&sportId=${sid}`)
        .then(r => r.json())
        .then(d => (d.stats?.[0]?.splits || []).map(s => ({...s, _sportId: sid})))
        .catch(() => [])
    );"""

new_pfetch = """async function fetchPlayerPitchingStats(playerId) {
  const sportIds = [1, 11, 12, 13, 14, 16];
  const fetchWithRetry = async (url, retries = 2) => {
    for (let r = 0; r <= retries; r++) {
      try {
        if (r > 0) await new Promise(ok => setTimeout(ok, 500 * r));
        const resp = await fetch(url);
        if (!resp.ok && r < retries) continue;
        return await resp.json();
      } catch { if (r === retries) return null; }
    }
    return null;
  };
  try {
    const promises = sportIds.map(async sid => {
      const d = await fetchWithRetry(`${API}/people/${playerId}/stats?stats=yearByYear&group=pitching&gameType=R&sportId=${sid}`);
      return d ? (d.stats?.[0]?.splits || []).map(s => ({...s, _sportId: sid})) : [];
    });"""

if old_pfetch in src:
    src = src.replace(old_pfetch, new_pfetch)
    changes += 1
    print("2. Added retry logic to fetchPlayerPitchingStats")

# 3. Add a small delay between batches to avoid rate limiting
old_batch_end = """      const valid = batchResults.filter(Boolean);
      results.push(...valid);
      setPlayers(prev => [...prev, ...valid]);
      setProgress({ done: Math.min(i + BATCH, hitters.length), total: hitters.length + pitcherList.length });
    }"""

new_batch_end = """      const valid = batchResults.filter(Boolean);
      results.push(...valid);
      setPlayers(prev => [...prev, ...valid]);
      setProgress({ done: Math.min(i + BATCH, hitters.length), total: hitters.length + pitcherList.length });
      // Small delay between batches to avoid API rate limiting
      if (i + BATCH < hitters.length) await new Promise(ok => setTimeout(ok, 200));
    }"""

if old_batch_end in src:
    src = src.replace(old_batch_end, new_batch_end, 1)
    changes += 1
    print("3. Added rate-limit delay between hitter batches")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
