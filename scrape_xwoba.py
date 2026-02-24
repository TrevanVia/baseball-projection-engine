import requests
import re
import json

url = "https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=batter&year=2025&position=&team=&min=100"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)

match = re.search(r'var data = (\[.*?\]);', response.text, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    
    xwoba_lookup = {}
    for player in data:
        name = player.get('entity_name', '')
        if ',' in name:
            last, first = name.split(',', 1)
            name = f"{first.strip()} {last.strip()}"
        
        est_woba = player.get('est_woba')
        est_ba = player.get('est_ba')
        est_slg = player.get('est_slg')
        
        if name and est_woba:
            xwoba_lookup[name] = {
                'xwoba': float(est_woba),
                'xba': float(est_ba) if est_ba else 0,
                'xslg': float(est_slg) if est_slg else 0
            }
    
    with open('src/xwoba_data.json', 'w') as f:
        json.dump(xwoba_lookup, f, indent=2)
    
    print(f"Saved {len(xwoba_lookup)} players")
    
    # Show some key players
    for name in ['Fernando Tatis Jr.', 'Aaron Judge', 'Juan Soto', 'Bobby Witt Jr.']:
        if name in xwoba_lookup:
            print(f"{name}: xwOBA {xwoba_lookup[name]['xwoba']}")
else:
    print("Could not find data")
