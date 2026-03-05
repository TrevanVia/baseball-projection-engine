#!/usr/bin/env python3
"""Move mobile CSS from Spinner to main App style block. Run from project root."""
import re

APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Extract the mobile CSS from the Spinner's style tag
# Find the full media query blocks
match = re.search(
    r'(@media\(max-width:768px\)\{.*?\})\s*(@media\(max-width:480px\)\{.*?\})\s*`\}\</style>',
    src, re.DOTALL
)

if not match:
    print("ERROR: Could not find mobile CSS in Spinner")
    # Try alternate approach
    print("Trying alternate extraction...")
    
# Let me use a more robust approach - find the Spinner style tag content
spinner_style_start = src.find("<style>{`@keyframes spin{to{transform:rotate(360deg)}}")
if spinner_style_start == -1:
    print("ERROR: Cannot find Spinner style tag")
    exit(1)

spinner_style_end = src.find("`}</style>", spinner_style_start)
if spinner_style_end == -1:
    print("ERROR: Cannot find Spinner style tag end")
    exit(1)

spinner_style_content = src[spinner_style_start:spinner_style_end + len("`}</style>")]

# Extract just the media queries from the Spinner style
media_768_start = spinner_style_content.find("@media(max-width:768px){")
media_480_end = spinner_style_content.find("}", spinner_style_content.find("@media(max-width:480px){"))
if media_768_start == -1:
    print("ERROR: No media query in Spinner style")
    exit(1)

mobile_css = spinner_style_content[media_768_start:media_480_end+1]
print(f"Extracted {len(mobile_css)} chars of mobile CSS")

# 2. Remove the mobile CSS from the Spinner style tag
# Keep just the keyframes
new_spinner_style = '<style>{`@keyframes spin{to{transform:rotate(360deg)}} @keyframes fvGlow{from{box-shadow:0 0 8px rgba(192,132,252,.3),0 0 16px rgba(96,165,250,.15)}to{box-shadow:0 0 16px rgba(251,146,60,.4),0 0 28px rgba(192,132,252,.25)}}`}</style>'

src = src.replace(spinner_style_content, new_spinner_style)
changes += 1
print("1. Cleaned Spinner style tag (kept only keyframes)")

# 3. Add the mobile CSS to the main App style tag (at line ~3143)
# Find the main style tag that has the animation keyframes
main_style_marker = "        @media (max-width: 768px) {\n          .via-content { padding: 12px 14px 32px !important; }\n          .via-header-inner { gap: 10px !important; }\n          .via-stat-row { gap: 4px !important; }\n        }"

# Replace the existing minimal mobile rules with our full mobile CSS
new_main_mobile = """        @media (max-width: 768px) {
          .via-content { padding: 8px 12px 20px !important; }
          .via-header { padding: 12px 16px 0 !important; }
          .via-header-inner { flex-direction: row !important; align-items: center !important; gap: 8px !important; flex-wrap: nowrap !important; }
          .via-tabs { display: none !important; }
          .via-title { font-size: 28px !important; }
          .via-subtitle { font-size: 8px !important; letter-spacing: .14em !important; }
          .via-tagline { font-size: 7px !important; }
          .via-stat-row { gap: 4px !important; flex-wrap: wrap !important; justify-content: center !important; }
          .via-stat-box { min-width: 58px !important; padding: 6px 8px !important; }
          .via-stat-box .via-stat-val { font-size: 14px !important; }
          .via-stat-box .via-stat-label { font-size: 6px !important; }
          .via-panel { padding: 10px 12px !important; margin-bottom: 8px !important; }
          .via-footer { padding: 8px 12px !important; flex-direction: column !important; gap: 4px !important; text-align: center !important; }
          .via-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 0 -12px; padding: 0 12px; }
          .via-table-wrap table { min-width: 500px; }
          .via-table-wrap th, .via-table-wrap td { padding: 4px 6px !important; font-size: 10px !important; }
          .via-player-name { font-size: 20px !important; }
          .via-player-info { font-size: 10px !important; }
          .via-pos-filters { gap: 2px !important; }
          .via-pos-filters button { padding: 4px 8px !important; font-size: 9px !important; }
          .via-mode-toggle { gap: 2px !important; }
          .via-mode-toggle button { padding: 5px 12px !important; font-size: 10px !important; }
          .via-leaderboard-filters { flex-direction: column !important; gap: 8px !important; align-items: stretch !important; }
          .via-leaderboard-filters input { width: 100% !important; box-sizing: border-box !important; }
          /* Landing page grids → single column */
          .via-landing-2col { grid-template-columns: 1fr !important; }
          .via-compare-slots { grid-template-columns: 1fr !important; }
          .via-roster-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)) !important; }
          .via-quick-pick { padding: 6px 10px !important; font-size: 10px !important; }
          .via-engine-stats { gap: 12px !important; padding: 10px 14px !important; }
          .via-engine-stats > div { min-width: 60px !important; }
        }
        @media (max-width: 480px) {
          .via-title { font-size: 24px !important; }
          .via-stat-box { min-width: 50px !important; padding: 5px 6px !important; }
          .via-stat-box .via-stat-val { font-size: 12px !important; }
          .via-table-wrap th, .via-table-wrap td { padding: 3px 4px !important; font-size: 9px !important; }
          .via-player-name { font-size: 18px !important; }
          .via-engine-stats { gap: 8px !important; flex-wrap: wrap !important; }
          .via-quick-pick { padding: 5px 8px !important; font-size: 9px !important; }
        }"""

if main_style_marker in src:
    src = src.replace(main_style_marker, new_main_mobile)
    changes += 1
    print("2. Moved full mobile CSS to main App style tag (always rendered)")
else:
    print("WARNING: Could not find main style marker, trying fallback...")
    # Fallback: add before the closing `}</style> of the main block
    # Find the second style tag's closing
    second_style = src.find("      `}</style>\n      <link href")
    if second_style > 0:
        src = src[:second_style] + "\n" + new_main_mobile + "\n      " + src[second_style:]
        changes += 1
        print("2. Added mobile CSS before main style tag close (fallback)")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes")
print()
print("Mobile CSS is now in the main App style tag which ALWAYS renders,")
print("not inside the Spinner component which only renders during loading.")
