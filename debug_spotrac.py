import requests
from bs4 import BeautifulSoup

url = "https://www.spotrac.com/mlb/rankings/2026/base"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

print("=== All tables found ===")
tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print(f"\nTable {i}: {table.get('class')}")
    rows = table.find_all('tr')[:3]
    for j, row in enumerate(rows):
        print(f"  Row {j}: {[td.text.strip()[:30] for td in row.find_all(['td', 'th'])]}")

with open('spotrac_debug.html', 'w') as f:
    f.write(response.text)
print("\nSaved full HTML to spotrac_debug.html")
