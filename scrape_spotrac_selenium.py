from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

print("Starting Chrome...")
driver = webdriver.Chrome(options=chrome_options)

try:
    url = "https://www.spotrac.com/mlb/rankings/2026/base"
    print(f"Loading {url}...")
    driver.get(url)
    
    # Wait for table to load
    print("Waiting for table...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "table"))
    )
    
    # Give it extra time for JS to render
    time.sleep(3)
    
    # Find all table rows
    rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
    print(f"Found {len(rows)} rows")
    
    contracts = {}
    for row in rows[1:]:  # Skip header
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= 3:
            try:
                player_name = cells[1].text.strip()
                salary_text = cells[-1].text.strip()
                
                # Parse salary
                salary = salary_text.replace('$', '').replace(',', '').strip()
                salary_num = int(salary)
                
                contracts[player_name] = salary_num
                print(f"{player_name}: ${salary_num:,}")
            except Exception as e:
                continue
    
    print(f"\nScraped {len(contracts)} contracts")
    
    if contracts:
        with open('src/spotrac_contracts.json', 'w') as f:
            json.dump(contracts, f, indent=2)
        print("Saved to src/spotrac_contracts.json")
    
finally:
    driver.quit()
