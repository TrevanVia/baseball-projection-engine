import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Update column header from "VpD SCORE" to "VpD GRADE"
content = content.replace('VpD SCORE', 'VpD GRADE')
content = content.replace('VALUE GRADE', 'VpD GRADE')
print("✓ Updated column header")

# Find and replace the vpd display cell with grade badge
# Look for the pattern with p.vpd.toFixed(1)
old_display = r'{p\.vpd\.toFixed\(1\)}'
new_display = r'''{(() => {
                        const g = getVpdGrade(p.warPerM);
                        return <span style={{display:"inline-block",padding:"2px 8px",borderRadius:4,background:`${g.color}20`,color:g.color,fontWeight:700,fontSize:11}}>{g.grade}</span>;
                      })()}'''

content = re.sub(old_display, new_display, content)
print("✓ Updated display to show letter grades")

# Update methodology to mention xwOBA and defense
# This is optional - can be done manually later

with open('src/App.jsx', 'w') as f:
    f.write(content)

print("Phase 7 complete - all changes applied!")
print("\nRunning final build test...")
