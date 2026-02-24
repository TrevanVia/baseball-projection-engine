import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Find where to insert - after getStatcast function
marker = 'function getStatcast(playerName) {\n  return STATCAST_DATA[playerName] || null;\n}'

# Add MLB stars to STATCAST_DATA first
statcast_additions = '''  "Fernando Tatis Jr.":  { avgEV: 91.8, maxEV: 115.5, barrelPct: 10.9 },
  "Aaron Judge":         { avgEV: 94.2, maxEV: 119.8, barrelPct: 16.5 },
  "Juan Soto":           { avgEV: 92.1, maxEV: 116.2, barrelPct: 12.8 },
  "Shohei Ohtani":       { avgEV: 92.8, maxEV: 119.0, barrelPct: 14.2 },
  "Bobby Witt Jr.":      { avgEV: 91.5, maxEV: 115.8, barrelPct: 11.2 },
  "Mookie Betts":        { avgEV: 90.8, maxEV: 114.2, barrelPct: 10.5 },
  "Ronald Acuna Jr.":    { avgEV: 91.2, maxEV: 116.5, barrelPct: 12.1 },
  "Yordan Alvarez":      { avgEV: 93.5, maxEV: 118.1, barrelPct: 15.8 },
  "Kyle Tucker":         { avgEV: 91.0, maxEV: 114.8, barrelPct: 11.5 },
  "Julio Rodriguez":     { avgEV: 90.5, maxEV: 114.0, barrelPct: 9.8 },
  "Gunnar Henderson":    { avgEV: 90.2, maxEV: 113.5, barrelPct: 10.2 },
  "Elly De La Cruz":     { avgEV: 89.5, maxEV: 113.2, barrelPct: 8.5 },
'''

# Insert before the closing brace of STATCAST_DATA
content = re.sub(
    r'(const STATCAST_DATA = \{[^}]+?)(\};)',
    r'\1  ' + statcast_additions + r'\2',
    content,
    flags=re.DOTALL
)
print("✓ Added MLB stars to STATCAST_DATA")

# Now add defense and sprint speed lookups after getStatcast
new_lookups = '''

function getXwoba(playerName) {
  return XWOBA_DATA[playerName] || null;
}

// ── DEFENSIVE LOOKUP (OAA 2023-2025 avg, DRS directional) ──────────────────
const DEFENSIVE_DATA = {
  "Bobby Witt Jr.":      { oaa: 8,  drs: 1 },
  "Gunnar Henderson":    { oaa: 6,  drs: 1 },
  "Francisco Lindor":    { oaa: 10, drs: 1 },
  "Fernando Tatis Jr.":  { oaa: 1,  drs: 0 },
  "Mookie Betts":        { oaa: 5,  drs: 1 },
  "Ronald Acuna Jr.":    { oaa: 3,  drs: 1 },
  "Elly De La Cruz":     { oaa: 2,  drs: 0 },
  "Masyn Winn":          { oaa: 7,  drs: 1 },
  "CJ Abrams":           { oaa: 3,  drs: 1 },
};

// ── SPRINT SPEED LOOKUP (ft/sec, Baseball Savant 2024) ──────────────────────
const SPRINT_SPEED = {
  "Elly De La Cruz":     30.2,
  "Bobby Witt Jr.":      29.8,
  "Trea Turner":         30.4,
  "Fernando Tatis Jr.":  28.3,
  "Ronald Acuna Jr.":    29.6,
  "Julio Rodriguez":     28.9,
  "Gunnar Henderson":    27.5,
  "CJ Abrams":           29.7,
  "Masyn Winn":          29.2,
};

function getDefense(playerName) { return DEFENSIVE_DATA[playerName] || null; }
function getSprintSpeed(playerName) { return SPRINT_SPEED[playerName] || null; }
'''

content = content.replace(marker, marker + new_lookups)
print("✓ Added defense and sprint speed lookups")

with open('src/App.jsx', 'w') as f:
    f.write(content)

print("Phase 3 complete.")
