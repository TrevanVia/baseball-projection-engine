from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import time
import re

# Load existing contracts
with open('src/contract_data.json', 'r') as f:
    existing = json.load(f)

print(f"Scraping Spotrac for {len(existing)} players...")

chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    url = "https://www.spotrac.com/mlb/rankings/2026/base"
    print(f"Loading {url}...")
    driver.get(url)
    
    time.sleep(5)
    
    # Look for player rows - Spotrac uses divs/spans
    print("Looking for player salary data...")
    
    # Try to find all rows with player data
    # Look for patterns like "Player Name ... $XX,XXX,XXX"
    page_text = driver.page_source
    
    # Parse using regex to find Player: Salary patterns
    # Spotrac typically has structure like: player name followed by salary
    
    # Try finding by class or data attributes
    player_rows = driver.find_elements(By.XPATH, "//tr[contains(@class, 'player') or contains(@data-player, '')]")
    
    if not player_rows:
        # Try a different approach - find all divs/rows with both name and salary
        print("Trying alternative parsing...")
        
        # Get all text content
        body = driver.find_element(By.TAG_NAME, "body")
        full_text = body.text
        
        # Look for pattern: Name (possibly team/position) $XX,XXX,XXX
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:[A-Z]{2,3}\s+)?(?:[A-Z]{1,2}\s+)?\$([0-9,]+)'
        matches = re.findall(pattern, full_text)
        
        updated = {}
        for name, salary in matches:
            name = name.strip()
            salary_clean = salary.replace(',', '')
            try:
                salary_num = int(salary_clean)
                if salary_num > 500000:  # Filter out noise
                    updated[name] = salary_num
                    print(f"  {name}: ${salary_num:,}")
            except:
                pass
        
        print(f"\n✓ Found {len(updated)} contracts")
        
        if updated:
            existing.update(updated)
            
            with open('src/contract_data.json', 'w') as f:
                json.dump(existing, f, indent=2)
            
            print(f"Total contracts in database: {len(existing)}")
    else:
        print(f"Found {len(player_rows)} player rows")
        # Parse the rows
        updated = {}
        for row in player_rows:
            try:
                text = row.text
                # Extract name and salary from row text
                parts = text.split('$')
                if len(parts) >= 2:
                    name_part = parts[0].strip()
                    salary_part = parts[1].split()[0].replace(',', '')
                    
                    # Extract player name (usually first part before team/position)
                    name = name_part.split()[0:2]
                    player_name = ' '.join(name)
                    
                    salary_num = int(salary_part)
                    updated[player_name] = salary_num
                    print(f"  {player_name}: ${salary_num:,}")
            except:
                pass
    
finally:
    driver.quit()
