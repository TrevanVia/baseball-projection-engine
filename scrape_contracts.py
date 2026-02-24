import requests
import json

# Try Cot's Baseball Contracts - they have CSV/JSON exports
# Or we can try Baseball Reference salary page
url = "https://www.baseball-reference.com/leagues/majors/2026-payroll.shtml"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

# Look for table data in comments (BBRef puts tables in HTML comments)
import re
from bs4 import BeautifulSoup, Comment

soup = BeautifulSoup(response.text, 'html.parser')

# BBRef hides tables in comments to avoid scraping
comments = soup.find_all(string=lambda text: isinstance(text, Comment))
for comment in comments:
    if 'table' in comment and 'salary' in comment.lower():
        print("Found table in comment!")
        table_soup = BeautifulSoup(comment, 'html.parser')
        table = table_soup.find('table')
        if table:
            print("Parsing table...")
            break

# If that doesn't work, try visible tables
if not 'table' in locals():
    table = soup.find('table', {'id': re.compile('payroll|salary', re.I)})

if table:
    print("Found table, parsing...")
    # Will parse in next iteration
else:
    print("No table found")
    print("Page title:", soup.find('title').get_text() if soup.find('title') else "N/A")
