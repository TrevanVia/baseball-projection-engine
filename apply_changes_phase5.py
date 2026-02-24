import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Find the WAR calculation section in projectFromSeasons
# Need to add defense and baserunning before the final baseWAR calculation

defense_baserunning_code = '''
  const def = getDefense(playerName);
  const spd = getSprintSpeed(playerName);

  // Defensive runs: OAA * 1.75 (primary) blended with DRS direction (secondary)
  const defPeak = posCode === "6" || posCode === "8" ? 26 : 28;
  const defAge = Math.max(0, 1 - Math.max(0, age - defPeak) * 0.06);
  let defRuns = 0;
  if (def) {
    const oaaRuns = def.oaa * 1.75;
    const drsAdj = def.drs * 1.5;
    defRuns = (oaaRuns * 0.70 + drsAdj * 0.30) * defAge * (estPA / 600);
  }

  // Baserunning runs: sprint speed tiers
  let bsrRuns = 0;
  if (spd !== null) {
    const speedTier = spd >= 29.5 ? 6.0 : spd >= 28.5 ? 4.0 : spd >= 28.0 ? 3.0 : spd >= 27.0 ? 1.5 : spd >= 26.0 ? 0 : -2.0;
    bsrRuns = speedTier * (estPA / 600);
  }
'''

# Insert before the batRuns calculation
content = re.sub(
    r'(const estPA = highestLevel === "MLB"[^;]+;)\s*\n\s*(const batRuns)',
    r'\1\n' + defense_baserunning_code + '\n  \2',
    content,
    flags=re.DOTALL
)
print("✓ Added defense and baserunning calculations")

# Update WAR formula to include defRuns and bsrRuns
content = content.replace(
    'const baseWAR = (batRuns + posAdj + repl) / 9.5;',
    'const baseWAR = (batRuns + defRuns + bsrRuns + posAdj + repl) / 9.5;'
)
print("✓ Updated WAR formula to include defense and baserunning")

with open('src/App.jsx', 'w') as f:
    f.write(content)

print("Phase 5 complete.")
