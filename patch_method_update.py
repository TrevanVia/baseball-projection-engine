#!/usr/bin/env python3
"""Update Methodology page to reflect current engine. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

replacements = [
    # 1. Layer 4: BsR
    ('Sprint speed (ft/s) with age-adjusted decay (-0.15 ft/s per year after 28). For MiLB players without sprint speed, baserunning is derived from SB/CS/G with efficiency multipliers.',
     'Statcast Baserunning Run Value (BsR) for 252 MLB players, measuring actual runs created via stolen bases, extra bases taken, and baserunner decisions. BsR maps directly to WAR (divide by 9.5). Players without BsR data fall back to sprint speed tiers. For MiLB players, baserunning is derived from SB/CS rates.',
     "Layer 4: BsR integration"),
    # 2. Layer 5: Defense
    ('OAA from Statcast, regressed 40% toward zero. Approximately 1.5 runs per OAA with position-specific aging curves (SS/CF peak at 26, corners at 28).',
     'Outs Above Average (OAA) from Statcast, converted at 0.5 runs per OAA with position-specific aging curves. Defensive peaks: SS/CF at 26, corners at 28. Defense decays at 6% per year past peak.',
     "Layer 5: 0.5 per OAA"),
    # 3. Layer 6: Peak ages
    ('Position-specific peaks: SS 26, CF 27, 2B/3B 27, 1B/DH/OF 28.',
     'Offensive peaks based on research (Fair 2025, Bradbury, FanGraphs): SS/2B/3B 28, CF 27, C 27, LF/RF 28, 1B 29, DH 30.',
     "Layer 6: corrected peak ages"),
    # 4. Pitcher starter detection
    ('Starter detection requires 100+ IP or 450+ BFP. Reliever IP capped at 75.',
     'Starter detection checks entire career history (not just most recent season), so injury-return pitchers are correctly classified. Returning starters project minimum 140 IP using 70% of career-max as floor. Reliever IP capped at 75.',
     "Pitcher: career-based starter detection"),
    # 5. FV integration
    ('The blend weights scale by sample size: small samples trust FV heavily, larger samples trust stats more. This ensures elite prospects like top FV 65+ players are not penalized by brief MLB callups.',
     'Higher FV grades get more FV weight (70 FV +20%, 65 +12%, 60 +6%). WAR floor is 50% of FV benchmark (70 FV = 4.0 WAR min). Slash line scales proportionally with FV-boosted OPS so wRC+ and OPS are always consistent. HR scales with the SLG boost.',
     "FV: WAR floor, slash sync"),
    # 6. Marcel HR translation
    ('Stats translated using level-specific conversion factors (AAA 0.82x, AA 0.68x, A+ 0.58x, A 0.50x).',
     'Stats translated using level-specific conversion factors (AAA 0.82x, AA 0.68x, A+ 0.58x, A 0.50x). HR are also translated by level factor and projected using games-based rate (HR/G x projected games). Players with fewer than 400 MLB PA use prospect PA estimation (projected games x 4.0 PA/G).',
     "Marcel: HR translation, games-based PA"),
    # 7. Data pipeline - add BsR
    ('Baseball Savant: xwOBA, xERA, xBA, barrel%, exit velocity, whiff%, sprint speed, OAA, bat speed (2023-2025, 900+ hitters, 1200+ pitchers).',
     'Baseball Savant: xwOBA, xERA, xBA, barrel%, exit velocity, whiff%, sprint speed, OAA, bat speed, Baserunning Run Value (2023-2025, 900+ hitters, 1200+ pitchers, 252 BsR players).',
     "Data pipeline: added BsR"),
]

for old, new, label in replacements:
    if old in src:
        src = src.replace(old, new)
        changes += 1
        print(f"  {changes}. {label}")

open(APP, "w").write(src)
print(f"\nApplied {changes} changes to Methodology page")
