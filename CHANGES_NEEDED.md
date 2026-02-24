# Changes to Re-apply from Today's Session

## 1. Import xwOBA Data (line ~11)
```javascript
import xwobaDataJson from "./xwoba_data.json";
const XWOBA_DATA = xwobaDataJson.default || xwobaDataJson;
```

## 2. Add Name Normalization Helper (after imports)
```javascript
function normalizeN(name) {
  return name.toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9 ]/g, "")
    .replace(/\s+/g, " ").trim();
}
```

## 3. Update getCareerWAR to Handle Name Matching
Replace existing function with name fallback for players with accents/hyphens.

## 4. Add Defense & Sprint Speed Lookup Tables (after STATCAST_DATA)
- DEFENSIVE_DATA: OAA and DRS for ~60 MLB players
- SPRINT_SPEED: ft/sec for ~40 MLB players
- Add getDefense() and getSprintSpeed() functions

## 5. Add MLB Stars to STATCAST_DATA
Tatis, Judge, Soto, Ohtani, Witt Jr, etc with avgEV, maxEV, barrelPct

## 6. Update FV_BENCHMARKS
Add 70 FV tier with elite benchmarks

## 7. Enhance projectFromSeasons() Function
- Add xwOBA boost logic
- Increase Statcast multipliers
- Add defensive runs calculation
- Add baserunning runs (sprint speed tiers)

## 8. Add VpD Letter Grade System
- Create getVpdGrade() function with strict A+ to F scale
- Modify VpDPanel to use warPerM instead of vpd score
- Update display to show letter grades with color badges

## 9. Update Methodology Panel
Add sections for xwOBA, batted ball quality, defense/baserunning

Want me to proceed with careful implementation?
