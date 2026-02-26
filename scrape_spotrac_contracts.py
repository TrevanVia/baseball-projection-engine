import requests
from bs4 import BeautifulSoup
import json
import time

# Load existing contracts to get player list
with open('src/contract_data.json', 'r') as f:
    existing = json.load(f)

player_names = list(existing.keys())
print(f"Scraping contracts for {len(player_names)} players from Spotrac...")

# Spotrac's main salary rankings page
url = "https://www.spotrac.com/mlb/rankings/2026/base"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Spotrac uses table class "datatable"
    table = soup.find('table', class_='datatable')
    
    if not table:
        # Try any table
        table = soup.find('table')
    
    if table:
        print(f"Found table, parsing...")
        
        updated = {}
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # Skip header
            cols = row.find_all('td')
            if len(cols) >= 3:
                # Typical format: Rank | Player | Team | Salary
                player_cell = cols[1] if len(cols) > 1 else cols[0]
                salary_cell = cols[-1]  # Last column usually salary
                
                player_name = player_cell.get_text(strip=True)
                salary_text = salary_cell.get_text(strip=True)
                
                # Clean salary text
                salary_clean = salary_text.replace('$', '').replace(',', '').strip()
                
                try:
                    salary_num = int(salary_clean)
                    updated[player_name] = salary_num
                    print(f"  {player_name}: ${salary_num:,}")
                except:
                    pass
        
        if updated:
            # Merge with existing
            existing.update(updated)
            
            with open('src/contract_data.json', 'w') as f:
                json.dump(existing, f, indent=2)
            
            print(f"\n✓ Updated {len(updated)} contracts")
            print(f"Total contracts: {len(existing)}")
        else:
            print("! No contracts found - page structure may have changed")
            print("Saving HTML for inspection...")
            with open('spotrac_debug.html', 'w') as f:
                f.write(response.text)
    else:
        print("! No table found")
        with open('spotrac_debug.html', 'w') as f:
            f.write(response.text)
else:
    print(f"! Request failed: {response.status_code}")
