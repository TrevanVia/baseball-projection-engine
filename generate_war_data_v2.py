#!/usr/bin/env python3
"""
generate_war_data_v2.py
Pulls career WAR for ALL active MLB players (hitters + pitchers)
from FanGraphs via pybaseball + MLB Stats API for ID mapping.

Usage:
  cd ~/Desktop/baseball-projection-engine
  pip install pybaseball requests
  python3 generate_war_data_v2.py

Output: src/war_data.json
"""

import json
import time
import requests
from pybaseball import batting_stats, pitching_stats
from pybaseball import cache
cache.enable()

def get_mlb_api_players():
    """Fetch ALL active MLB players (hitters + pitchers) from 40-man rosters."""
    print("  Fetching 40-man rosters from MLB Stats API...")
    TEAMS = {108:'LAA',109:'AZ',110:'BAL',111:'BOS',112:'CHC',113:'CIN',
             114:'CLE',115:'COL',116:'DET',117:'HOU',118:'KC',119:'LAD',
             120:'WSH',121:'NYM',133:'OAK',134:'PIT',135:'SD',136:'SEA',
             137:'SF',138:'STL',139:'TB',140:'TEX',141:'TOR',142:'MIN',
             143:'PHI',144:'ATL',145:'CWS',146:'MIA',147:'NYY',158:'MIL'}
    
    players = {}
    seen = set()
    for tid, abbr in TEAMS.items():
        try:
            resp = requests.get(
                f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster?rosterType=40Man&season=2026&hydrate=person",
                timeout=10
            )
            data = resp.json()
            for r in data.get("roster", []):
                p = r.get("person", {})
                pid = p.get("id")
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                players[p["fullName"]] = {
                    "id": pid,
                    "name": p["fullName"],
                    "team": abbr,
                    "pos": p.get("primaryPosition", {}).get("abbreviation", ""),
                    "posCode": p.get("primaryPosition", {}).get("code", ""),
                }
        except Exception as e:
            print(f"    {abbr}: ERROR - {e}")
        time.sleep(0.3)
    
    return players


def get_fangraphs_war():
    """Pull WAR data from FanGraphs for 2015-2025 via pybaseball."""
    print("  Fetching FanGraphs batting + pitching stats...")
    
    all_data = {}  # name -> { war, type }
    
    # Batting WAR
    for year in range(2015, 2026):
        try:
            print(f"    Batting {year}...", end=" ", flush=True)
            df = batting_stats(year, qual=0)
            count = 0
            for _, row in df.iterrows():
                name = str(row.get("Name", ""))
                war = float(row.get("WAR", 0))
                pa = int(row.get("PA", 0))
                if pa < 10 or not name:
                    continue
                if name not in all_data:
                    all_data[name] = {"war": 0, "type": "hitter"}
                all_data[name]["war"] += war
                count += 1
            print(f"{count} players")
            time.sleep(1.5)
        except Exception as e:
            print(f"FAILED: {e}")
    
    # Pitching WAR
    for year in range(2015, 2026):
        try:
            print(f"    Pitching {year}...", end=" ", flush=True)
            df = pitching_stats(year, qual=0)
            count = 0
            for _, row in df.iterrows():
                name = str(row.get("Name", ""))
                war = float(row.get("WAR", 0))
                ip = float(row.get("IP", 0))
                if ip < 5 or not name:
                    continue
                if name not in all_data:
                    all_data[name] = {"war": 0, "type": "pitcher"}
                all_data[name]["war"] += war
                count += 1
            print(f"{count} players")
            time.sleep(1.5)
        except Exception as e:
            print(f"FAILED: {e}")
    
    return all_data


def normalize(name):
    """Normalize name for matching (handle accents, Jr., etc.)"""
    import unicodedata
    n = unicodedata.normalize("NFD", name)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = n.lower().replace("jr.", "").replace("sr.", "").replace("ii", "").replace("iii", "")
    return n.strip()


def match_players(mlb_players, fg_data):
    """Match FanGraphs players to MLBAM IDs."""
    lookup = {}
    matched = 0
    unmatched = []
    
    # Build normalized FG lookup
    fg_norm = {}
    for name, info in fg_data.items():
        fg_norm[normalize(name)] = (name, info)
    
    for name, mlb_info in mlb_players.items():
        mlbam_id = str(mlb_info["id"])
        norm = normalize(name)
        
        # Exact normalized match
        if norm in fg_norm:
            fg_name, fg_info = fg_norm[norm]
            lookup[mlbam_id] = {
                "name": name,
                "careerWAR": round(fg_info["war"], 1),
            }
            matched += 1
            continue
        
        # Fuzzy: last name + first 3 chars
        parts = norm.split()
        found = False
        if len(parts) >= 2:
            for fn, (fg_name, fg_info) in fg_norm.items():
                fp = fn.split()
                if len(fp) >= 2:
                    if (parts[-1] == fp[-1] and parts[0][:3] == fp[0][:3]):
                        lookup[mlbam_id] = {
                            "name": name,
                            "careerWAR": round(fg_info["war"], 1),
                        }
                        matched += 1
                        found = True
                        break
        
        if not found:
            unmatched.append(name)
    
    return lookup, matched, unmatched


def main():
    print("=" * 60)
    print("VIAcast WAR Data Generator v2 (Hitters + Pitchers)")
    print("=" * 60)
    
    print("\n[1/3] Fetching active MLB players...")
    mlb_players = get_mlb_api_players()
    hitters = {n: p for n, p in mlb_players.items() if p["posCode"] != "1"}
    pitchers = {n: p for n, p in mlb_players.items() if p["posCode"] == "1"}
    print(f"  Found {len(hitters)} hitters + {len(pitchers)} pitchers = {len(mlb_players)} total")
    
    print("\n[2/3] Fetching FanGraphs career WAR (2015-2025)...")
    fg_data = get_fangraphs_war()
    print(f"  Found {len(fg_data)} unique players across all seasons")
    
    print("\n[3/3] Matching players...")
    lookup, matched, unmatched = match_players(mlb_players, fg_data)
    print(f"  Matched: {matched} / {len(mlb_players)}")
    if unmatched[:15]:
        print(f"  Sample unmatched: {', '.join(unmatched[:15])}")
    
    # Write output
    output_path = "src/war_data.json"
    with open(output_path, "w") as f:
        json.dump(lookup, f, separators=(",", ":"))
    
    import os
    size_kb = os.path.getsize(output_path) / 1024
    print(f"\nWrote {len(lookup)} players to {output_path} ({size_kb:.0f} KB)")
    
    # Verify key players
    print("\nKey player verification:")
    checks = [
        ("677594", "Julio Rodriguez"),
        ("694973", "Paul Skenes"),
        ("668939", "Shohei Ohtani"),
        ("660271", "Ronald Acuna Jr."),
        ("592450", "Aaron Judge"),
        ("666176", "Gunnar Henderson"),
        ("680757", "Elly De La Cruz"),
    ]
    for pid, name in checks:
        entry = lookup.get(pid)
        if entry:
            print(f"  {name}: {entry['careerWAR']} fWAR")
        else:
            print(f"  {name}: MISSING!")
    
    # Top 25 overall
    print("\nTop 25 by Career fWAR (2015-2025):")
    top = sorted(lookup.values(), key=lambda x: x["careerWAR"], reverse=True)[:25]
    for i, p in enumerate(top):
        print(f"  {i+1:2d}. {p['name']:<28s} {p['careerWAR']:5.1f}")


if __name__ == "__main__":
    main()
