#!/usr/bin/env python3
"""
generate_war_data_v2.py - Pulls career WAR for ALL active MLB players (hitters + pitchers)
"""
import json, time, requests
from pybaseball import batting_stats, pitching_stats
import pandas as pd

def get_mlb_api_players():
    print("  Fetching from MLB Stats API...")
    url = "https://statsapi.mlb.com/api/v1/sports/1/players?season=2025&gameType=R&hydrate=currentTeam"
    data = requests.get(url).json()
    players = {}
    for p in data.get("people", []):
        name = p["fullName"]
        players[name] = {
            "id": p["id"],
            "name": name,
            "pos_code": p.get("primaryPosition", {}).get("code", ""),
        }
    return players

def get_fangraphs_war():
    print("  Fetching FanGraphs stats (2015-2025)...")
    all_players = {}
    
    # Hitters
    for year in range(2015, 2026):
        try:
            print(f"    Batting {year}...", end=" ", flush=True)
            df = batting_stats(year, qual=0)
            count = 0
            for _, row in df.iterrows():
                name = str(row.get("Name", ""))
                war = float(row.get("WAR", 0))
                pa = int(row.get("PA", 0))
                if pa < 10 or not name: continue
                if name not in all_players:
                    all_players[name] = {"war": 0, "type": "hitter"}
                all_players[name]["war"] += war
                count += 1
            print(f"{count} hitters")
            time.sleep(2)
        except Exception as e:
            print(f"FAILED: {e}")
    
    # Pitchers
    for year in range(2015, 2026):
        try:
            print(f"    Pitching {year}...", end=" ", flush=True)
            df = pitching_stats(year, qual=0)
            count = 0
            for _, row in df.iterrows():
                name = str(row.get("Name", ""))
                war = float(row.get("WAR", 0))
                ip = float(row.get("IP", 0))
                if ip < 5 or not name: continue
                if name not in all_players:
                    all_players[name] = {"war": 0, "type": "pitcher"}
                all_players[name]["war"] += war
                count += 1
            print(f"{count} pitchers")
            time.sleep(2)
        except Exception as e:
            print(f"FAILED: {e}")
    
    return all_players

def match_players(mlb_players, fg_data):
    lookup = {}
    matched = 0
    for name, mlb_info in mlb_players.items():
        mlbam_id = str(mlb_info["id"])
        if name in fg_data:
            lookup[mlbam_id] = {"name": name, "careerWAR": round(fg_data[name]["war"], 1)}
            matched += 1
            continue
        parts = name.split()
        if len(parts) >= 2:
            for fg_name, fg_info in fg_data.items():
                fg_parts = fg_name.split()
                if len(fg_parts) >= 2:
                    if (parts[-1].lower() == fg_parts[-1].lower() and 
                        parts[0][0].lower() == fg_parts[0][0].lower()):
                        lookup[mlbam_id] = {"name": name, "careerWAR": round(fg_info["war"], 1)}
                        matched += 1
                        break
    return lookup, matched

def main():
    print("=" * 60)
    print("VIAcast WAR Data Generator v2 (Hitters + Pitchers)")
    print("=" * 60)
    mlb_players = get_mlb_api_players()
    print(f"  Found {len(mlb_players)} total players")
    fg_data = get_fangraphs_war()
    print(f"  Found {len(fg_data)} unique players")
    lookup, matched = match_players(mlb_players, fg_data)
    print(f"  Matched: {matched} / {len(mlb_players)}")
    with open("src/war_data.json", "w") as f:
        json.dump(lookup, f)
    print(f"\nWrote {len(lookup)} players to src/war_data.json")
    top = sorted(lookup.values(), key=lambda x: x["careerWAR"], reverse=True)[:25]
    print("\nTop 25 by Career fWAR:")
    for i, p in enumerate(top):
        print(f"  {i+1:2d}. {p['name']:<28s} {p['careerWAR']:5.1f}")

if __name__ == "__main__":
    main()
