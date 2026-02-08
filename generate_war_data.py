#!/usr/bin/env python3
"""
generate_war_data.py
Pulls career WAR for all active MLB hitters from FanGraphs via pybaseball,
cross-references with MLB Stats API player IDs, and outputs a JSON lookup file.

Usage:
  cd ~/Desktop/baseball-projection-engine
  pip install pybaseball requests
  python generate_war_data.py

Output:
  src/war_data.json — keyed by MLBAM player ID
"""

import json
import time
import requests
from pybaseball import batting_stats, playerid_reverse_lookup
import pandas as pd

def get_mlb_api_players():
    """Fetch all active MLB position players with MLBAM IDs."""
    print("  Fetching from MLB Stats API...")
    url = "https://statsapi.mlb.com/api/v1/sports/1/players?season=2025&gameType=R&hydrate=currentTeam"
    resp = requests.get(url)
    data = resp.json()
    players = {}
    for p in data.get("people", []):
        pos_code = p.get("primaryPosition", {}).get("code", "")
        if pos_code == "1":
            continue
        name = p["fullName"]
        players[name] = {
            "id": p["id"],
            "name": name,
            "team": p.get("currentTeam", {}).get("abbreviation", "FA"),
            "pos": p.get("primaryPosition", {}).get("abbreviation", ""),
            "age": p.get("currentAge", 0),
        }
    return players

def get_fangraphs_war():
    """Pull seasonal batting stats from FanGraphs for 2015-2025 and sum career WAR."""
    print("  Fetching FanGraphs batting stats (this takes 1-2 minutes)...")
    
    all_seasons = {}
    
    for year in range(2015, 2026):
        try:
            print(f"    {year}...", end=" ", flush=True)
            df = batting_stats(year, qual=0)
            count = 0
            
            for _, row in df.iterrows():
                name = str(row.get("Name", ""))
                war = float(row.get("WAR", 0))
                pa = int(row.get("PA", 0))
                
                if pa < 10 or not name:
                    continue
                
                if name not in all_seasons:
                    all_seasons[name] = {
                        "war": 0,
                        "seasons": [],
                        "last_team": str(row.get("Team", "")),
                    }
                
                all_seasons[name]["war"] += war
                all_seasons[name]["seasons"].append({
                    "year": year,
                    "war": round(war, 1),
                    "pa": pa,
                })
                count += 1
            
            print(f"{count} players")
            time.sleep(2)  # be nice to FanGraphs
        except Exception as e:
            print(f"FAILED: {e}")
            continue
    
    return all_seasons

def match_players(mlb_players, fg_data):
    """Match FanGraphs players to MLBAM IDs."""
    lookup = {}
    matched = 0
    unmatched = []
    
    for name, mlb_info in mlb_players.items():
        mlbam_id = str(mlb_info["id"])
        
        # Exact name match
        if name in fg_data:
            lookup[mlbam_id] = {
                "name": name,
                "careerWAR": round(fg_data[name]["war"], 1),
            }
            matched += 1
            continue
        
        # Fuzzy match: last name + first initial
        parts = name.split()
        found = False
        if len(parts) >= 2:
            for fg_name, fg_info in fg_data.items():
                fg_parts = fg_name.split()
                if len(fg_parts) >= 2:
                    if (parts[-1].lower() == fg_parts[-1].lower() and 
                        parts[0][0].lower() == fg_parts[0][0].lower()):
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
    print("VIAcast WAR Data Generator")
    print("=" * 60)
    
    # Step 1
    print("\n[1/3] Fetching active MLB players...")
    mlb_players = get_mlb_api_players()
    print(f"  Found {len(mlb_players)} position players")
    
    # Step 2
    print("\n[2/3] Fetching FanGraphs career WAR (2015-2025)...")
    fg_data = get_fangraphs_war()
    print(f"  Found {len(fg_data)} unique players across all seasons")
    
    # Step 3
    print("\n[3/3] Matching players...")
    lookup, matched, unmatched = match_players(mlb_players, fg_data)
    print(f"  Matched: {matched} / {len(mlb_players)}")
    if unmatched[:10]:
        print(f"  Sample unmatched: {', '.join(unmatched[:10])}")
    
    # Write output
    output_path = "src/war_data.json"
    with open(output_path, "w") as f:
        json.dump(lookup, f)
    
    print(f"\n✅ Wrote {len(lookup)} players to {output_path}")
    print(f"   File size: {len(json.dumps(lookup)) / 1024:.0f} KB")
    
    # Top 25
    print("\n📊 Top 25 by Career fWAR (2015-2025):")
    top = sorted(lookup.values(), key=lambda x: x["careerWAR"], reverse=True)[:25]
    for i, p in enumerate(top):
        print(f"  {i+1:2d}. {p['name']:<28s} {p['careerWAR']:5.1f} WAR")

if __name__ == "__main__":
    main()
