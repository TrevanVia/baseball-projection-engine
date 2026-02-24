import re

with open('src/App.jsx', 'r') as f:
    content = f.read()

# Find VpDPanel function and add the grading function
# First, find where VpDPanel starts
vpd_panel_match = re.search(r'function VpDPanel\(\) \{[^}]*useState\(\{ key: "vpd", dir: -1 \}\);', content)

if vpd_panel_match:
    # Insert grading function after the useState
    grade_function = '''

  function getVpdGrade(warPerM) {
    if (warPerM >= 1.00) return { grade: "A+", color: "#10b981", label: "Elite" };
    if (warPerM >= 0.50) return { grade: "A", color: "#22c55e", label: "Excellent" };
    if (warPerM >= 0.30) return { grade: "A-", color: "#84cc16", label: "Great" };
    if (warPerM >= 0.20) return { grade: "B+", color: "#eab308", label: "Very Good" };
    if (warPerM >= 0.15) return { grade: "B", color: "#f59e0b", label: "Good" };
    if (warPerM >= 0.125) return { grade: "C+", color: "#fb923c", label: "Above Avg" };
    if (warPerM >= 0.10) return { grade: "C", color: "#94a3b8", label: "Fair" };
    if (warPerM >= 0.075) return { grade: "D", color: "#ef4444", label: "Below Avg" };
    return { grade: "F", color: "#dc2626", label: "Overpaid" };
  }
'''
    
    insert_pos = vpd_panel_match.end()
    content = content[:insert_pos] + grade_function + content[insert_pos:]
    print("✓ Added getVpdGrade function")
    
    # Change default sort key from "vpd" to "warPerM"
    content = content.replace(
        'useState({ key: "vpd", dir: -1 });',
        'useState({ key: "warPerM", dir: -1 });'
    )
    print("✓ Updated default sort to warPerM")
    
    # Update the return object to use warPerM instead of vpd
    content = re.sub(
        r'vpd: Math\.min\(99\.9, Math\.max\(0\.1, Math\.round\(\(base\.baseWAR / \(salary / 1000000\)\) \* 100\) / 10\)\),',
        r'warPerM: base.baseWAR / (salary / 1000000),',
        content
    )
    print("✓ Changed vpd calculation to warPerM")
    
else:
    print("! Could not find VpDPanel - may need manual update")

with open('src/App.jsx', 'w') as f:
    f.write(content)

print("Phase 6 complete.")
