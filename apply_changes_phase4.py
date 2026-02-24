import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# 5. Update FV_BENCHMARKS to include 70 FV
old_benchmarks = '''const FV_BENCHMARKS = {
  65: { ops: .870, war: 5.0, wrc: 135, floor_ops: .780, ceil_ops: .950 },'''

new_benchmarks = '''const FV_BENCHMARKS = {
  70: { ops: .940, war: 7.0, wrc: 150, floor_ops: .850, ceil_ops: 1.050 },
  65: { ops: .870, war: 5.0, wrc: 135, floor_ops: .780, ceil_ops: .960 },'''

content = content.replace(old_benchmarks, new_benchmarks)
print("✓ Added 70 FV to benchmarks")

# 6. Update Statcast boost multipliers (find and replace in projectFromSeasons)
content = content.replace(
    'statcastBoost = 1 + (evScore * 0.05 + maxScore * 0.03 + barrelScore * 0.06);',
    'statcastBoost = 1 + (evScore * 0.08 + maxScore * 0.05 + barrelScore * 0.12);'
)
print("✓ Increased Statcast multipliers")

# 7. Add xwOBA boost - find the adjustedOPS calculation and add xwOBA logic after it
# This needs to be inserted carefully in projectFromSeasons
xwoba_code = '''  const xw = getXwoba(playerName);
  let xwobaBoost = 1.0;
  if (xw && xw.xwoba > 0) {
    const impliedWoba = rawOPS * 0.43;
    const xwobaDiff = xw.xwoba - impliedWoba;
    if (xwobaDiff > 0.01) {
      xwobaBoost = 1 + Math.min(0.15, xwobaDiff * 1.5);
    }
  }
  const finalAdjustedOPS = adjustedOPS * xwobaBoost;
'''

# Find where adjustedOPS is defined and insert xwOBA logic after
content = re.sub(
    r'(const adjustedOPS = rawOPS \* ageBoost \* performanceBoost \* statcastBoost;)',
    r'\1\n' + xwoba_code,
    content
)
print("✓ Added xwOBA boost logic")

# Replace adjustedOPS with finalAdjustedOPS in regression calculations
content = re.sub(
    r'adjustedOPS \* paRel \+ lgOPS',
    r'finalAdjustedOPS * paRel + lgOPS',
    content
)
print("✓ Updated OPS regression to use xwOBA-adjusted values")

with open('src/App.jsx', 'w') as f:
    f.write(content)

print("Phase 4 complete.")
