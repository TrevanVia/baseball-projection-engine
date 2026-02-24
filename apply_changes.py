import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

print("Original file: {} lines".format(content.count('\n')))

# Backup
with open('src/App.jsx.backup', 'w') as f:
    f.write(content)

# 1. Add xwOBA import after war_data import
import_line = 'import warDataJson from "./war_data.json"; WAR_DATA = warDataJson;'
new_imports = '''import warDataJson from "./war_data.json";
import xwobaDataJson from "./xwoba_data.json";
const XWOBA_DATA = xwobaDataJson.default || xwobaDataJson;
WAR_DATA = warDataJson;'''

content = content.replace(import_line, new_imports)
print("✓ Added xwOBA import")

# 2. Add normalization function after imports
normalize_func = '''
function normalizeN(name) {
  return name.toLowerCase()
    .normalize("NFD").replace(/[\\u0300-\\u036f]/g, "")
    .replace(/[^a-z0-9 ]/g, "")
    .replace(/\\s+/g, " ").trim();
}
'''

# Insert after WAR_DATA line
content = content.replace(
    'WAR_DATA = warDataJson;',
    'WAR_DATA = warDataJson;' + normalize_func
)
print("✓ Added normalizeN function")

# Save
with open('src/App.jsx', 'w') as f:
    f.write(content)

print("\nPhase 1 complete. Test build? (y/n)")
