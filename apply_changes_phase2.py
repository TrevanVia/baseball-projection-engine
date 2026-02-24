import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# 3. Update getCareerWAR to handle name matching
old_func = '''function getCareerWAR(playerId) {
  const d = WAR_DATA[String(playerId)] || WAR_DATA?.default?.[String(playerId)];
  return d ? d.careerWAR : null;
}'''

new_func = '''function getCareerWAR(playerId, playerName) {
  const d = WAR_DATA[String(playerId)];
  if (d) return d.careerWAR;
  if (playerName) {
    const normName = normalizeN(playerName);
    const entry = Object.values(WAR_DATA).find(v => normalizeN(v.name) === normName);
    if (entry) return entry.careerWAR;
  }
  return null;
}'''

content = content.replace(old_func, new_func)
print("✓ Updated getCareerWAR with name matching")

# 4. Update all getCareerWAR calls to pass playerName
# Find patterns like getCareerWAR(player.id) and add player.fullName
content = re.sub(
    r'getCareerWAR\(([^,)]+)\)',
    lambda m: f'getCareerWAR({m.group(1)}, player.fullName)' if 'player' in m.group(1) else m.group(0),
    content
)
print("✓ Updated getCareerWAR calls")

with open('src/App.jsx', 'w') as f:
    f.write(content)

print("Phase 2 complete.")
