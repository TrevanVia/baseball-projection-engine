#!/usr/bin/env python3
"""
VIAcast Pitcher Data Pipeline
Fetches pitcher Statcast data from Baseball Savant, plus K%/BB%/IP and
FIP/xFIP from the MLB Stats API (FanGraphs' own API is Cloudflare-blocked).

  python3 build_pitcher_data.py            # refresh the last 3 seasons
  python3 build_pitcher_data.py 2026       # refresh one season

Merges into the existing files: seasons not being refreshed are kept as-is.
Outputs: src/pitcher_savant_data.json, src/fg_pitcher_data.json (seasons missing only)
"""

import csv
import io
import json
import ssl
import sys
import time
import urllib.request

import datetime
_cur = datetime.date.today().year if datetime.date.today().month >= 3 else datetime.date.today().year - 1
YEARS = [int(a) for a in sys.argv[1:]] or [_cur - 2, _cur - 1, _cur]

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

def fetch_csv(url, label=""):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        raw = urllib.request.urlopen(req, timeout=30).read()
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        print("  %s: %d rows" % (label, len(rows)))
        return rows
    except Exception as e:
        print("  %s: ERROR - %s" % (label, e))
        return []

def sf(v, d=None):
    try:
        return float(v) if v and v != "null" and v != "" else d
    except:
        return d

def clean_name(raw):
    if "," in raw:
        parts = raw.split(",", 1)
        return (parts[1].strip() + " " + parts[0].strip()).strip()
    return raw.strip()


# ──────────────────────────────────────────────────────────────
# STEP 1: Expected Stats (xwOBA against, xERA, xBA against)
# ──────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Pitcher Expected Statistics (3 years)")
print("=" * 60)

exp_by_year = {}
name_map = {}

for year in YEARS:
    url = "https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=pitcher&year=%d&position=&team=&min=1&csv=true" % year
    rows = fetch_csv(url, "%d expected" % year)
    exp_by_year[year] = {}
    for r in rows:
        pid = r.get("player_id", "").strip()
        raw_name = r.get("last_name, first_name", "").strip()
        if not pid:
            continue
        if raw_name and pid not in name_map:
            name_map[pid] = clean_name(raw_name)
        exp_by_year[year][pid] = {
            "bfp": sf(r.get("pa"), 0),
            "xwoba": sf(r.get("est_woba")),
            "woba": sf(r.get("woba")),
            "xba": sf(r.get("est_ba")),
            "xslg": sf(r.get("est_slg")),
            "era": sf(r.get("era")),
            "xera": sf(r.get("xera")),
        }
    time.sleep(1)


# ──────────────────────────────────────────────────────────────
# STEP 2: Batted Ball Quality Against (EV, barrels)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Pitcher EV / Barrels Against (3 years)")
print("=" * 60)

ev_by_year = {}
for year in YEARS:
    url = "https://baseballsavant.mlb.com/leaderboard/statcast?type=pitcher&year=%d&position=&team=&min=1&csv=true" % year
    rows = fetch_csv(url, "%d EV" % year)
    ev_by_year[year] = {}
    for r in rows:
        pid = r.get("player_id", "").strip()
        raw_name = r.get("last_name, first_name", "").strip()
        if not pid:
            continue
        if raw_name and pid not in name_map:
            name_map[pid] = clean_name(raw_name)
        ev_by_year[year][pid] = {
            "bbe": sf(r.get("attempts"), 0),
            "avg_ev": sf(r.get("avg_hit_speed")),
            "ev50": sf(r.get("ev50")),
            "barrel_pct": sf(r.get("brl_percent")),
            "hard_hit_pct": sf(r.get("ev95percent")),
        }
    time.sleep(1)


# ──────────────────────────────────────────────────────────────
# STEP 3: Pitch Velocity (fastball velo as a key metric)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Pitch Velocities (3 years)")
print("=" * 60)

velo_by_year = {}
for year in YEARS:
    url = "https://baseballsavant.mlb.com/leaderboard/pitch-arsenals?type=avg_speed&min=1&year=%d&csv=true" % year
    rows = fetch_csv(url, "%d velo" % year)
    velo_by_year[year] = {}
    for r in rows:
        pid = r.get("pitcher", "").strip()
        raw_name = r.get("last_name, first_name", "").strip()
        if not pid:
            continue
        if raw_name and pid not in name_map:
            name_map[pid] = clean_name(raw_name)
        ff = sf(r.get("ff_avg_speed"))
        si = sf(r.get("si_avg_speed"))
        fb_velo = ff or si  # Use 4-seam, fall back to sinker
        velo_by_year[year][pid] = {
            "fb_velo": fb_velo,
            "ff_velo": ff,
            "si_velo": si,
            "sl_velo": sf(r.get("sl_avg_speed")),
            "ch_velo": sf(r.get("ch_avg_speed")),
            "cu_velo": sf(r.get("cu_avg_speed")),
            "sv_velo": sf(r.get("sv_avg_speed")),
        }
    time.sleep(1)


# ──────────────────────────────────────────────────────────────
# STEP 4: Pitch Arsenal Stats (whiff%, K%, put-away%)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Pitch Arsenal Effectiveness (3 years)")
print("=" * 60)

arsenal_by_year = {}
for year in YEARS:
    url = "https://baseballsavant.mlb.com/leaderboard/pitch-arsenal-stats?type=pitcher&pitchType=&year=%d&position=&team=&min=1&csv=true" % year
    rows = fetch_csv(url, "%d arsenal" % year)
    arsenal_by_year[year] = {}
    for r in rows:
        pid = r.get("player_id", "").strip()
        if not pid:
            continue
        pitch = r.get("pitch_type", "")
        if pid not in arsenal_by_year[year]:
            arsenal_by_year[year][pid] = {"pitches": {}, "total_whiff": 0, "total_pitches": 0}
        whiff = sf(r.get("whiff_percent"), 0)
        k_pct = sf(r.get("k_percent"), 0)
        usage = sf(r.get("pitch_usage"), 0)
        pitches = sf(r.get("pitches"), 0)
        hard_hit = sf(r.get("hard_hit_percent"))
        xwoba = sf(r.get("est_woba"))
        arsenal_by_year[year][pid]["pitches"][pitch] = {
            "whiff": whiff, "k_pct": k_pct, "usage": usage,
            "hard_hit": hard_hit, "xwoba": xwoba,
        }
        arsenal_by_year[year][pid]["total_whiff"] += whiff * (usage / 100) if usage else 0
        arsenal_by_year[year][pid]["total_pitches"] += pitches
    time.sleep(1)


# ──────────────────────────────────────────────────────────────
# STEP 5: FanGraphs Plate Discipline (pitcher side)
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: FanGraphs Pitcher Discipline (3 years)")
print("=" * 60)

fg_by_year = {}
mlb_sab = {}
def _ip(v):
    try:
        x = float(v); w = int(x); return w + round((x - w) * 10) / 3
    except Exception:
        return None
for year in YEARS:
    # MLB Stats API: season totals + FanGraphs-sourced sabermetrics (FIP, xFIP, WAR)
    base = "https://statsapi.mlb.com/api/v1/stats?group=pitching&season=%d&sportId=1&gameType=R&playerPool=ALL&limit=5000&stats=" % year
    fg_by_year[year] = {}
    mlb_sab[year] = {}
    try:
        season = json.loads(urllib.request.urlopen(urllib.request.Request(base + "season", headers={"User-Agent": UA}), timeout=60).read())
        saber = json.loads(urllib.request.urlopen(urllib.request.Request(base + "sabermetrics", headers={"User-Agent": UA}), timeout=60).read())
        sab = {str(r["player"]["id"]): r["stat"] for r in saber["stats"][0]["splits"]}
        for r in season["stats"][0]["splits"]:
            pid = str(r["player"]["id"]); st = r["stat"]
            bf = st.get("battersFaced") or 0
            if not bf:
                continue
            k = 100.0 * (st.get("strikeOuts") or 0) / bf
            bb = 100.0 * (st.get("baseOnBalls") or 0) / bf
            fg_by_year[year][pid] = {"k_pct": round(k, 1), "bb_pct": round(bb, 1), "k_bb": round(k - bb, 1), "ip": _ip(st.get("inningsPitched"))}
            sb = sab.get(pid, {})
            mlb_sab[year][pid] = {"name": r["player"]["fullName"], "xfip": sf(str(sb.get("xfip", ""))), "fip": sf(str(sb.get("fip", ""))),
                                  "era": sf(st.get("era")), "k_pct": round(k, 1), "bb_pct": round(bb, 1), "kbb_pct": round(k - bb, 1),
                                  "ip": _ip(st.get("inningsPitched")), "whip": sf(st.get("whip"))}
        print("  %d MLB API pitching: %d pitchers" % (year, len(fg_by_year[year])))
    except Exception as e:
        print("  %d MLB API pitching: ERROR - %s" % (year, e))
    time.sleep(1)


# ──────────────────────────────────────────────────────────────
# STEP 6: Merge everything into pitcher profiles
# ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: Merging pitcher data")
print("=" * 60)

all_pids = set()
for year in YEARS:
    all_pids |= set(exp_by_year.get(year, {}).keys())
    all_pids |= set(ev_by_year.get(year, {}).keys())
    all_pids |= set(velo_by_year.get(year, {}).keys())

print("  Total unique pitcher IDs: %d" % len(all_pids))

pitchers = {}
full_profiles = 0

for pid in all_pids:
    name = name_map.get(pid, "Unknown")
    seasons = {}
    for year in YEARS:
        exp = exp_by_year.get(year, {}).get(pid, {})
        ev = ev_by_year.get(year, {}).get(pid, {})
        vel = velo_by_year.get(year, {}).get(pid, {})
        ars = arsenal_by_year.get(year, {}).get(pid, {})
        fg = fg_by_year.get(year, {}).get(pid, {})

        bfp = exp.get("bfp", 0) or 0
        if bfp < 10:
            continue

        s = {
            "bfp": int(bfp),
            "xwoba": exp.get("xwoba"),
            "woba": exp.get("woba"),
            "xba": exp.get("xba"),
            "xslg": exp.get("xslg"),
            "era": exp.get("era"),
            "xera": exp.get("xera"),
            "avg_ev": ev.get("avg_ev"),
            "ev50": ev.get("ev50"),
            "barrel_pct": ev.get("barrel_pct"),
            "hard_hit_pct": ev.get("hard_hit_pct"),
            "fb_velo": vel.get("fb_velo"),
            "ff_velo": vel.get("ff_velo"),
            "whiff_pct": ars.get("total_whiff"),
            "k_pct": fg.get("k_pct"),
            "bb_pct": fg.get("bb_pct"),
            "k_bb": fg.get("k_bb"),
            "o_swing": fg.get("o_swing"),
            "z_contact": fg.get("z_contact"),
            "swstr": fg.get("swstr"),
            "csw": fg.get("csw"),
            "ip": fg.get("ip"),
        }
        # Remove None values to save space
        s = {k: v for k, v in s.items() if v is not None}
        if s:
            seasons[str(year)] = s

    if seasons:
        entry = {"name": name, "seasons": seasons}
        # Get latest velo for top-level reference
        for year in reversed(YEARS):
            vel = velo_by_year.get(year, {}).get(pid, {})
            if vel.get("fb_velo"):
                entry["fb_velo"] = vel["fb_velo"]
                break
        pitchers[pid] = entry
        if len(seasons) >= 3:
            full_profiles += 1

print("  Pitchers with data: %d" % len(pitchers))
print("  Full 3-year profiles: %d" % full_profiles)


# ──────────────────────────────────────────────────────────────
# STEP 7: Write output
# ──────────────────────────────────────────────────────────────
out_path = "src/pitcher_savant_data.json"
# Merge: keep every season we did NOT refresh, replace the ones we did.
try:
    existing = json.load(open(out_path))
except Exception:
    existing = {}
refreshed = {str(y) for y in YEARS}
for pid, old in existing.items():
    new = pitchers.get(pid)
    if new is None:
        old["seasons"] = {y: v for y, v in old.get("seasons", {}).items() if y not in refreshed}
        if old["seasons"]:
            pitchers[pid] = old
        continue
    keep = {y: v for y, v in old.get("seasons", {}).items() if y not in refreshed}
    new["seasons"] = {**keep, **new["seasons"]}
    for k, v in old.items():
        if k not in new:
            new[k] = v
with open(out_path, "w") as f:
    json.dump(pitchers, f, separators=(",", ":"))

# FanGraphs-style estimator table used for the engine's ERA anchor. Genuine
# FanGraphs seasons (with SIERA) are never overwritten; missing seasons are
# filled from the MLB API (FIP/xFIP, no SIERA). Keyed by player name.
fg_path = "src/fg_pitcher_data.json"
try:
    fgd = json.load(open(fg_path))
except Exception:
    fgd = {}
added = 0
for year in YEARS:
    for pid, row in mlb_sab.get(year, {}).items():
        if not row.get("ip"):
            continue
        name = row.pop("name")
        ent = fgd.setdefault(name, {"id": pid, "seasons": {}})
        if str(year) in ent["seasons"] and ent["seasons"][str(year)].get("siera") is not None:
            continue
        ent["seasons"][str(year)] = {k: v for k, v in row.items() if v is not None}
        added += 1
with open(fg_path, "w") as f:
    json.dump(fgd, f, separators=(",", ":"))
print("fg_pitcher_data.json: %d pitcher-seasons filled from MLB API" % added)

import os
size_kb = os.path.getsize(out_path) / 1024
print("\nOutput: %s (%.0f KB, %d pitchers)" % (out_path, size_kb, len(pitchers)))
print("Done!")
