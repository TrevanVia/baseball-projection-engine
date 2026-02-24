import json

# Compiled from Spotrac, MLBTR, and team press releases (Feb 2026)
# All values are 2026 salary (not AAV necessarily, but actual 2026 payment)

contracts_2026 = {
    # $50M+ Club
    "Shohei Ohtani": 70000000,
    "Kyle Tucker": 60000000,
    "Juan Soto": 51000000,
    "Max Scherzer": 43333333,
    "Justin Verlander": 43333333,
    "Aaron Judge": 40000000,
    "Blake Snell": 36400000,
    "Gerrit Cole": 36000000,
    "Carlos Correa": 33333333,
    
    # $30-35M
    "Corey Seager": 32500000,
    "Trea Turner": 27083333,
    "Bryce Harper": 27538462,
    "Mookie Betts": 30416667,
    "Francisco Lindor": 34100000,
    "Manny Machado": 30000000,
    "Rafael Devers": 28000000,
    "Xander Bogaerts": 25400000,
    "Anthony Rendon": 38000000,
    "Mike Trout": 37116667,
    
    # $20-30M
    "Freddie Freeman": 27000000,
    "Matt Olson": 21000000,
    "Vladimir Guerrero Jr.": 19900000,  # Arb estimate
    "Pete Alonso": 20500000,  # Arb estimate
    "Jose Ramirez": 17000000,
    "Alex Bregman": 28500000,
    "Marcus Semien": 25000000,
    "Dansby Swanson": 25000000,
    "Corbin Burnes": 30000000,  # Estimate
    "Zack Wheeler": 24666667,
    
    # $15-20M
    "Willy Adames": 12400000,
    "Bo Bichette": 17100000,  # Arb
    "Carlos Rodon": 27000000,
    "Jacob deGrom": 37000000,
    "Yoshinobu Yamamoto": 32500000,
    "Kodai Senga": 15000000,
    "Luis Castillo": 24166667,
    "Tyler Glasnow": 22500000,
    "Sonny Gray": 25000000,
    "Pablo Lopez": 21750000,
    
    # $10-15M
    "Jose Altuve": 29000000,
    "Eugenio Suarez": 13900000,
    "Brandon Lowe": 10500000,
    "Teoscar Hernandez": 23500000,
    "Jorge Polanco": 10500000,
    "Marcell Ozuna": 16000000,
    "J.T. Realmuto": 23875000,
    "Salvador Perez": 22000000,
    "Willson Contreras": 18000000,
    "Adley Rutschman": 2500000,  # Pre-arb
    
    # $5-10M
    "Joe Ryan": 6000000,
    "Logan Webb": 13000000,
    "Hunter Brown": 800000,  # Pre-arb
    "Grayson Rodriguez": 800000,
    "Bryce Miller": 800000,
    "Bobby Miller": 800000,
    "Tanner Bibee": 800000,
    "Tarik Skubal": 2500000,
    "Cole Ragans": 800000,
    "Garrett Crochet": 3000000,
    
    # Pre-arb/Team Control Bargains
    "Bobby Witt Jr.": 7500000,
    "Gunnar Henderson": 5000000,
    "Elly De La Cruz": 800000,
    "Jackson Holliday": 800000,
    "Julio Rodriguez": 12000000,
    "Corbin Carroll": 2000000,
    "Jackson Chourio": 2000000,
    "Paul Skenes": 800000,
    "Jackson Merrill": 800000,
    "Wyatt Langford": 800000,
    "Colton Cowser": 800000,
    "Masyn Winn": 800000,
    "Anthony Volpe": 1500000,
    "CJ Abrams": 4000000,
    "Riley Greene": 2500000,
    "Spencer Torkelson": 1500000,
    "Michael Harris II": 4000000,
    "Spencer Strider": 8750000,
    
    # More established stars
    "Ronald Acuna Jr.": 17000000,
    "Fernando Tatis Jr.": 36000000,
    "Jazz Chisholm Jr.": 5250000,
    "Jarren Duran": 1500000,
    "Steven Kwan": 1800000,
    "Ketel Marte": 16000000,
    "Ha-Seong Kim": 8000000,
    "Nico Hoerner": 11750000,
    "Ozzie Albies": 7000000,
    "Andres Gimenez": 11000000,
    "Brandon Nimmo": 20600000,
    "Cody Bellinger": 27500000,
    "Kyle Schwarber": 20000000,
    "Yordan Alvarez": 12500000,
    "Kyle Tucker": 15000000,  # Old contract - will be replaced
    "Christian Yelich": 26000000,
    "Nolan Arenado": 27000000,
    "Paul Goldschmidt": 26000000,
    "Austin Riley": 15000000,
}

# Load existing and merge
try:
    with open('src/contract_data.json') as f:
        existing = json.load(f)
except:
    existing = {}

# Merge (new data takes precedence)
existing.update(contracts_2026)

with open('src/contract_data.json', 'w') as f:
    json.dump(existing, f, indent=2)

print(f"Added/updated {len(contracts_2026)} contracts")
print(f"Total contracts in database: {len(existing)}")
print("\nSample updates:")
for name in list(contracts_2026.keys())[:10]:
    print(f"  {name}: ${contracts_2026[name]:,}")
