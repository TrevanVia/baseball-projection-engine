import requests
import re
import json

url = "https://www.spotrac.com/mlb/rankings/2026/base"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)

# Look for JSON data in script tags
json_pattern = r'var\s+tableData\s*=\s*(\[.*?\]);'
match = re.search(json_pattern, response.text, re.DOTALL)

if match:
    print("Found tableData!")
    data = json.loads(match.group(1))
    print(f"Found {len(data)} entries")
    print("Sample:", data[0] if data else "None")
else:
    # Try to find any array in the page
    array_pattern = r'\[\s*\{\s*".*?rank.*?salary'
    if re.search(array_pattern, response.text, re.IGNORECASE):
        print("Found array-like structure, trying to extract...")
        # Save full HTML to inspect
        with open('spotrac_page.html', 'w') as f:
            f.write(response.text)
        print("Saved page to spotrac_page.html for inspection")
    else:
        print("No data array found")
        print("\nSearching for 'salary' mentions:")
        salary_mentions = re.findall(r'.{50}salary.{50}', response.text, re.IGNORECASE)[:5]
        for mention in salary_mentions:
            print(f"  ...{mention}...")
