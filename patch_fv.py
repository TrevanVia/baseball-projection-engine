#!/usr/bin/env python3
"""Update FV data with 2026 FanGraphs grades. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

# New FV_BY_NAME data
NEW = {
  # 70
  "Konnor Griffin": 70,
  # 65
  "Jesus Made": 65, "Jes\u00fas Made": 65,
  "Nolan McLean": 65, "Samuel Basallo": 65, "Kevin McGonigle": 65,
  # 60
  "Leo De Vries": 60, "Max Clark": 60, "Thomas White": 60,
  "Trey Yesavage": 60, "Bubba Chandler": 60, "Colt Emerson": 60,
  "Roki Sasaki": 60, "Paul Skenes": 60,
  "JJ Wetherholt": 60, "Franklin Arias": 60,
  # 55
  "Eli Willits": 55, "Sebastian Walcott": 55,
  "Walker Jenkins": 55, "Aidan Miller": 55,
  "Carson Benge": 55, "Alfredo Duno": 55,
  "Bryce Eldridge": 55, "Josue De Paula": 55,
  "Ryan Sloan": 55, "Bryce Rainer": 55,
  "Luis Pe\u00f1a": 55, "Rainiel Rodriguez": 55,
  "Chase DeLauter": 55, "Andrew Painter": 55,
  "Carson Williams": 55, "Jarlin Susana": 55,
  "Carter Jensen": 55, "Caleb Bonemer": 55,
  "Sal Stewart": 55, "Ryan Waldschmidt": 55,
  "Noah Schultz": 55, "Brandon Sproat": 55,
  "Connelly Early": 55, "Edward Florentino": 55,
  "Kade Anderson": 55, "Jonah Tong": 55,
  "Robby Snelling": 55, "Gage Jump": 55,
  "George Lombard Jr.": 55, "Seth Hernandez": 55,
  "Josue Brice\u00f1o": 55, "Josuar Gonzalez": 55,
  "Payton Tolle": 55, "Luis Mey": 55,
  "Colson Montgomery": 55, "Roman Anthony": 55,
  "Marcelo Mayer": 55, "Jordan Lawlar": 55,
  "Dylan Crews": 55, "Chase Burns": 55,
  "Jared Jones": 55, "Quinn Mathews": 55,
  "Jacob Misiorowski": 55, "AJ Smith-Shawver": 55,
  "Tanner Bibee": 55, "Chase Petty": 55,
  "Noble Meyer": 55, "Caden Dana": 55,
  "Michael Arroyo": 55, "Liam Doyle": 55,
  "Cooper Pratt": 55,
  # 50
  "Hagen Smith": 50, "Jackson Ferris": 50,
  "Richard Fitts": 50, "Gunnar Hoglund": 50,
  "Logan Henderson": 50, "Jurrangelo Cijntje": 50,
  "Eury Perez": 50, "Chase Dollander": 50,
  "Rhett Lowder": 50, "Drew Thorpe": 50,
  "Travis Bazzana": 50, "Ethan Salas": 50,
  "Braden Montgomery": 50, "Ethan Holliday": 50,
  "Jett Williams": 50, "Arjun Nimmala": 50,
  "Alan Roden": 50, "Jac Caglianone": 50,
  "Jacob Reimer": 50, "Ralphy Velazquez": 50,
  "Joe Mack": 50, "Mike Sirota": 50,
  "Dylan Beavers": 50, "Nick Kurtz": 50,
  "Jacob Wilson": 50, "Kyle Teel": 50,
  "Drake Baldwin": 50, "Cam Smith": 50,
  "Zac Veen": 50, "Brooks Lee": 50,
  "Henry Davis": 50, "Dillon Dingler": 50,
  "Owen Caissie": 50, "Zyhir Hope": 50,
  "Jaison Chourio": 50, "Charlie Condon": 50,
  "Mikey Romero": 50, "George Klassen": 50,
  "Jamie Arnold": 50, "Grant Taylor": 50,
  # 45 (young graduated MLBers)
  "Matt Shaw": 45, "Jace Jung": 45,
  "Brady House": 45, "Robert Hassell III": 45,
  "Dalton Rushing": 45, "Tyler Soderstrom": 45,
  "Noelvi Marte": 45,
}

# Build JS object string
lines = ["const FV_BY_NAME = {"]
for name, fv in NEW.items():
    lines.append('  "%s": %d,' % (name, fv))
lines.append("};")
new_block = "\n".join(lines)

# Replace old block
s = src.find("const FV_BY_NAME = {")
e = src.find("};", s) + 2
src = src[:s] + new_block + src[e:]

# Upgrade McGonigle in FV_LOOKUP too
src = src.replace("805808: 60, // Kevin McGonigle", "805808: 65, // Kevin McGonigle")

open(APP, "w").write(src)
print("Updated FV data: %d players" % len(NEW))
