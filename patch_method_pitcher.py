#!/usr/bin/env python3
"""Update Methodology page for new pitching engine. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

replacements = [
    # 1. Pitcher engine intro - SIERA, not xERA
    ('5-layer pitcher projection system using Baseball Savant data. WAR is calculated from projected xERA against replacement level, which is more reliable than FIP when K%/BB% data is incomplete.',
     '5-layer pitcher projection system using Baseball Savant and FanGraphs data. WAR is calculated using a layered ERA anchor based on Peter Appel\'s predictive ranking: SIERA (primary) → xFIP → xERA → FIP → K-BB → ERA. FanGraphs data provides SIERA, xFIP, K%, BB%, and GB% for 815 pitchers across 2023-2025.',
     "Pitcher intro: SIERA-based engine"),

    # 2. Layer 1 - SIERA anchor, not xERA
    ('xERA is the projection anchor, weighted across 3 seasons (55/30/15%). Barrel rate allowed and hard-hit rate provide quality-of-contact validation.',
     'SIERA (Skill-Interactive ERA) is the primary projection anchor from FanGraphs, weighted across 3 seasons (55/30/15%) with IP-based reliability scaling. SIERA accounts for K%, BB%, and ground ball rate interactions, making it the most predictive single ERA estimator. Falls back to xFIP, then xERA from Statcast for pitchers without FG data.',
     "Layer 1: SIERA anchor"),

    # 3. Layer 2 - K% from FG, not whiff * 0.80
    ('K% estimated from whiff rate (whiff% × 0.80) when FanGraphs data is unavailable. BB% and swinging-strike rate round out the command profile.',
     'K% and BB% sourced directly from FanGraphs for 815 pitchers (2023-2025). When FG data is unavailable, K% is estimated from Statcast whiff rate (whiff% × 1.05). FIP is computed using these rates with HR allowed estimated from IP and barrel rate (league avg 1.2 HR/9, scaled by pitcher barrel% allowed).',
     "Layer 2: FG K%/BB%, fixed whiff conversion"),

    # 4. Pitcher Aging & WAR - update IP projection method, SIERA anchor
    ('Pitcher WAR uses xERA vs. replacement level (5.34 for starters, 4.49 for relievers). Starter detection checks entire career history (not just most recent season), so injury-return pitchers are correctly classified. Returning starters project minimum 140 IP using 70% of career-max as floor. Reliever IP capped at 75.',
     'Pitcher WAR uses the SIERA-based layered anchor vs. replacement level (5.34 for starters, 4.49 for relievers). Starter detection checks entire career history for injury returns. IP projection uses the best full season (100+ IP) from FanGraphs data with an age-based workload adjustment: ≤27 × 1.03 (trending up), 28-30 × 1.00 (peak workload), 31-33 × 0.97, 34+ × 0.93. Capped at 210 IP. Reliever IP capped at 75.',
     "Pitcher WAR: SIERA anchor, FG-based IP"),

    # 5. Data pipeline - add FG pitcher data
    ('FanGraphs: plate discipline, FV grades, career fWAR.',
     'FanGraphs: SIERA, xFIP, FIP, K%, BB%, GB%, IP for 815 pitchers (2023-2025), plus plate discipline, FV grades, career fWAR.',
     "Data pipeline: FG pitcher stats"),
]

for old, new, label in replacements:
    if old in src:
        src = src.replace(old, new)
        changes += 1
        print(f"  {changes}. {label}")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes to Methodology page")
