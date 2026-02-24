import requests
import json

print("Fetching all active MLB players...")

# Load existing contract data first
existing_contracts = {}
try:
    with open('src/contract_data.json', 'r') as f:
        existing_contracts = json.load(f)
        print(f"Loaded {len(existing_contracts)} existing contracts")
except:
    pass

# Get all 30 MLB teams
teams_url = "https://statsapi.mlb.com/api/v1/teams?sportId=1&season=2025"
teams_response = requests.get(teams_url)
teams = teams_response.json()['teams']

all_players = {}
league_minimum = 760000  # 2026 MLB minimum salary

for team in teams:
    team_id = team['id']
    team_name = team['name']
    
    # Get 40-man roster
    roster_url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?rosterType=40Man"
    try:
        roster_response = requests.get(roster_url)
        roster = roster_response.json()
        
        if 'roster' in roster:
            for player in roster['roster']:
                player_name = player['person']['fullName']
                # Use existing contract if we have it, otherwise league minimum
                all_players[player_name] = existing_contracts.get(player_name, league_minimum)
                
            print(f"{team_name}: {len(roster['roster'])} players")
    except Exception as e:
        print(f"Error fetching {team_name}: {e}")

with open('src/contract_data.json', 'w') as f:
    json.dump(all_players, f, indent=2)

print(f"\nTotal players: {len(all_players)}")
print(f"Known contracts: {len([v for v in all_players.values() if v != league_minimum])}")
print("Saved to src/contract_data.json")
