import requests
from bs4 import BeautifulSoup
import json
import re

# FanGraphs Auction Calculator has contract data
url = "https://www.fangraphs.com/roster-resource/payroll/yankees"  # Start with Yankees

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# Actually, let's try a different approach - use a public API or CSV
# RosterResource has team payrolls in a simpler format

teams = ['yankees', 'dodgers', 'mets', 'padres', 'phillies', 'braves', 'astros', 
         'rangers', 'blue-jays', 'red-sox', 'giants', 'angels', 'cubs', 'cardinals',
         'mariners', 'orioles', 'twins', 'guardians', 'white-sox', 'royals',
         'tigers', 'brewers', 'reds', 'pirates', 'diamondbacks', 'rockies',
         'marlins', 'nationals', 'athletics', 'rays']

all_contracts = {}

for team in teams[:5]:  # Test with first 5 teams
    url = f"https://www.fangraphs.com/roster-resource/payroll/{team}"
    print(f"Scraping {team}...")
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"  Failed: {response.status_code}")
        continue
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for payroll table
    # FanGraphs uses specific table IDs
    table = soup.find('table', {'class': re.compile('payroll|roster', re.I)})
    if not table:
        table = soup.find('table')
    
    if table:
        print(f"  Found table with {len(table.find_all('tr'))} rows")
        
        for row in table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                player_cell = cells[0]
                # Salary is usually in last few columns
                for cell in reversed(cells):
                    text = cell.get_text(strip=True)
                    if '$' in text and ',' in text:
                        player_name = player_cell.get_text(strip=True)
                        salary_text = text.replace('$', '').replace(',', '').strip()
                        try:
                            salary = int(re.findall(r'\d+', salary_text.replace(',', ''))[0])
                            all_contracts[player_name] = salary
                            print(f"    {player_name}: ${salary:,}")
                            break
                        except:
                            pass
    else:
        print(f"  No table found")

print(f"\n\nTotal contracts scraped: {len(all_contracts)}")

if all_contracts:
    with open('src/scraped_contracts.json', 'w') as f:
        json.dump(all_contracts, f, indent=2)
    print("Saved to src/scraped_contracts.json")
