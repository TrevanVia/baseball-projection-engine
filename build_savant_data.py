#!/usr/bin/env python3
"""
VIAcast Data Pipeline v2
Uses Savant as primary data source (names + stats), FanGraphs for plate discipline.
Output: src/savant_data.json
"""

import csv
import io
import json
import ssl
import sys
import time
import urllib.request

YEARS = [2023, 2024, 2025]

# Fix macOS SSL
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

def fetch_json(url, label=""):
    try:
        raw = urllib.request.urlopen(url, timeout=15).read()
        return json.loads(raw)
    except Exception as e:
        print("  %s: ERROR - %s" % (label, e))
        return None

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

def extract_fg_name(html):
    if ">" in html and "</" in html:
        return html[html.index(">")+1:html.index("</")]
    return html


print("=" * 60)
print("STEP 1: Savant Expected Statistics (3 years)")
print("=" * 60)

exp_by_year = {}
name_map = {}

for year in YEARS:
    url = "https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=batter&year=%d&position=&team=&min=1&csv=true" % year
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
            "pa": sf(r.get("pa"), 0),
            "xwoba": sf(r.get("est_woba")),
            "xba": sf(r.get("est_ba")),
            "xslg": sf(r.get("est_slg")),
            "woba": sf(r.get("woba")),
            "ba": sf(r.get("ba")),
            "slg": sf(r.get("slg")),
            "xwoba_diff": sf(r.get("est_woba_minus_woba_diff")),
        }
    time.sleep(1)


print("")
print("=" * 60)
print("STEP 2: Savant EV / Barrels (3 years)")
print("=" * 60)

ev_by_year = {}
for year in YEARS:
    url = "https://baseballsavant.mlb.com/leaderboard/statcast?type=batter&year=%d&position=&team=&min=1&csv=true" % year
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
            "max_ev": sf(r.get("max_hit_speed")),
            "ev50": sf(r.get("ev50")),
            "barrel_pct": sf(r.get("brl_percent")),
            "hard_hit_pct": sf(r.get("ev95percent")),
            "sweet_spot_pct": sf(r.get("anglesweetspotpercent")),
            "avg_la": sf(r.get("avg_hit_angle")),
        }
    time.sleep(1)


print("")
print("=" * 60)
print("STEP 3: Savant Sprint Speed (3 years, keep latest)")
print("=" * 60)

sprint_data = {}
for year in YEARS:
    url = "https://baseballsavant.mlb.com/leaderboard/sprint_speed?type=batter&year=%d&position=&team=&min=1&csv=true" % year
    rows = fetch_csv(url, "%d sprint" % year)
    for r in rows:
        pid = r.get("player_id", "").strip()
        raw_name = r.get("last_name, first_name", "").strip()
        if not pid:
            continue
        if raw_name and pid not in name_map:
            name_map[pid] = clean_name(raw_name)
        sprint_data[pid] = {
            "sprint_speed": sf(r.get("sprint_speed")),
            "hp_to_1b": sf(r.get("hp_to_1b")),
            "bolts": sf(r.get("bolts"), 0),
        }
    time.sleep(1)


print("")
print("=" * 60)
print("STEP 4: Savant OAA Defense (2024-2025)")
print("=" * 60)

oaa_by_year = {}
for year in [2024, 2025]:
    url = "https://baseballsavant.mlb.com/leaderboard/outs_above_average?type=Fielder&year=%d&position=&team=&min=1&csv=true" % year
    rows = fetch_csv(url, "%d OAA" % year)
    oaa_by_year[year] = {}
    for r in rows:
        pid = r.get("player_id", "").strip()
        raw_name = r.get("last_name, first_name", "").strip()
        if not pid:
            continue
        if raw_name and pid not in name_map:
            name_map[pid] = clean_name(raw_name)
        oaa_by_year[year][pid] = {
            "oaa": sf(r.get("outs_above_average"), 0),
            "frp": sf(r.get("fielding_runs_prevented"), 0),
            "pos": r.get("primary_pos_formatted", ""),
        }
    time.sleep(1)


print("")
print("=" * 60)
print("STEP 5: FanGraphs Plate Discipline (by position)")
print("=" * 60)

fg_by_year = {}
positions = ["all", "of", "ss", "2b", "3b", "1b", "c", "dh"]

for year in YEARS:
    fg_by_year[year] = {}
    for pos in positions:
        for qual in [50, 0]:
            url = "https://www.fangraphs.com/api/leaders/major-league/data?pos=%s&stats=bat&lg=all&qual=%d&type=10&season=%d&page=1_30" % (pos, qual, year)
            data = fetch_json(url, "%d FG %s q%d" % (year, pos, qual))
            if not data or "data" not in data:
                continue
            for p in data["data"]:
                mid = str(p.get("xMLBAMID", ""))
                if not mid or mid == "0" or mid in fg_by_year[year]:
                    continue
                fg_by_year[year][mid] = {
                    "name": extract_fg_name(p.get("Name", "")),
                    "team": extract_fg_name(p.get("Team", "")),
                    "age": p.get("Age"),
                    "pa": p.get("PA", 0),
                    "bb_pct": p.get("BB%"),
                    "k_pct": p.get("K%"),
                    "o_swing_pct": p.get("O-Swing%"),
                    "z_swing_pct": p.get("Z-Swing%"),
                    "swing_pct": p.get("Swing%"),
                    "o_contact_pct": p.get("O-Contact%"),
                    "z_contact_pct": p.get("Z-Contact%"),
                    "contact_pct": p.get("Contact%"),
                    "zone_pct": p.get("Zone%"),
                    "f_strike_pct": p.get("F-Strike%"),
                    "swstr_pct": p.get("SwStr%"),
                    "cstr_pct": p.get("CStr%"),
                    "wrc_plus": p.get("wRC+"),
                    "war": p.get("WAR"),
                    "iso": p.get("ISO"),
                    "babip": p.get("BABIP"),
                    "bat_speed": p.get("AvgBatSpeed"),
                    "squared_up_pct": p.get("SquaredUpContact%"),
                    "gb_pct": p.get("GB%"),
                    "fb_pct": p.get("FB%"),
                    "ld_pct": p.get("LD%"),
                    "pull_pct": p.get("Pull%"),
                    "hr": p.get("HR"),
                    "sb": p.get("SB"),
                    "xwoba": p.get("xwOBA"),
                }
            time.sleep(0.3)

    for mid, fg in fg_by_year[year].items():
        if fg.get("name") and mid not in name_map:
            name_map[mid] = fg["name"]

    print("  %d FG unique: %d players" % (year, len(fg_by_year[year])))


print("")
print("=" * 60)
print("STEP 6: Merging all data")
print("=" * 60)

all_pids = set()
for year in YEARS:
    all_pids.update(exp_by_year.get(year, {}).keys())
    all_pids.update(ev_by_year.get(year, {}).keys())
    all_pids.update(fg_by_year.get(year, {}).keys())
all_pids.update(sprint_data.keys())
for year in [2024, 2025]:
    all_pids.update(oaa_by_year.get(year, {}).keys())

print("  Unique player IDs: %d" % len(all_pids))
print("  Players with names: %d" % len(name_map))

merged = {}
for pid in all_pids:
    name = name_map.get(pid)
    if not name:
        continue

    team = None
    age = None
    for year in reversed(YEARS):
        fg = fg_by_year.get(year, {}).get(pid, {})
        if fg.get("team"):
            team = fg["team"]
            age = fg.get("age")
            break

    player = {"name": name, "mlbam_id": int(pid) if pid.isdigit() else pid}
    if team:
        player["team"] = team
    if age:
        player["age"] = age
    player["seasons"] = {}

    for year in YEARS:
        season = {}

        exp = exp_by_year.get(year, {}).get(pid, {})
        if exp:
            season["pa"] = exp.get("pa", 0)
            season["xwoba"] = exp.get("xwoba")
            season["xba"] = exp.get("xba")
            season["xslg"] = exp.get("xslg")
            season["woba"] = exp.get("woba")
            season["ba"] = exp.get("ba")
            season["slg"] = exp.get("slg")
            season["xwoba_diff"] = exp.get("xwoba_diff")

        ev = ev_by_year.get(year, {}).get(pid, {})
        if ev:
            season["avg_ev"] = ev.get("avg_ev")
            season["max_ev"] = ev.get("max_ev")
            season["ev50"] = ev.get("ev50")
            season["barrel_pct"] = ev.get("barrel_pct")
            season["hard_hit_pct"] = ev.get("hard_hit_pct")
            season["sweet_spot_pct"] = ev.get("sweet_spot_pct")
            season["avg_la"] = ev.get("avg_la")
            season["bbe"] = ev.get("bbe", 0)

        fg = fg_by_year.get(year, {}).get(pid, {})
        if fg:
            season["o_swing_pct"] = fg.get("o_swing_pct")
            season["z_swing_pct"] = fg.get("z_swing_pct")
            season["o_contact_pct"] = fg.get("o_contact_pct")
            season["z_contact_pct"] = fg.get("z_contact_pct")
            season["contact_pct"] = fg.get("contact_pct")
            season["swstr_pct"] = fg.get("swstr_pct")
            season["zone_pct"] = fg.get("zone_pct")
            season["f_strike_pct"] = fg.get("f_strike_pct")
            season["cstr_pct"] = fg.get("cstr_pct")
            season["bb_pct"] = fg.get("bb_pct")
            season["k_pct"] = fg.get("k_pct")
            season["wrc_plus"] = fg.get("wrc_plus")
            season["war"] = fg.get("war")
            season["iso"] = fg.get("iso")
            season["babip"] = fg.get("babip")
            season["bat_speed"] = fg.get("bat_speed")
            season["squared_up_pct"] = fg.get("squared_up_pct")
            season["gb_pct"] = fg.get("gb_pct")
            season["fb_pct"] = fg.get("fb_pct")
            season["ld_pct"] = fg.get("ld_pct")
            season["pull_pct"] = fg.get("pull_pct")
            if not season.get("pa"):
                season["pa"] = fg.get("pa", 0)

        if season.get("pa", 0) > 0 or season.get("xwoba") is not None:
            player["seasons"][str(year)] = season

    sp = sprint_data.get(pid, {})
    if sp.get("sprint_speed"):
        player["sprint_speed"] = sp["sprint_speed"]
        if sp.get("hp_to_1b"):
            player["hp_to_1b"] = sp["hp_to_1b"]
        player["bolts"] = sp.get("bolts", 0)

    oaa25 = oaa_by_year.get(2025, {}).get(pid, {})
    oaa24 = oaa_by_year.get(2024, {}).get(pid, {})
    if oaa25 or oaa24:
        c = oaa25.get("oaa", 0) if oaa25 else 0
        p2 = oaa24.get("oaa", 0) if oaa24 else 0
        if oaa25 and oaa24:
            player["oaa"] = round(c * 0.65 + p2 * 0.35, 1)
        elif oaa25:
            player["oaa"] = c
        else:
            player["oaa"] = p2
        player["fielding_runs"] = oaa25.get("frp") or oaa24.get("frp")
        player["def_position"] = oaa25.get("pos") or oaa24.get("pos")

    if player["seasons"]:
        merged[pid] = player

print("  Merged players: %d" % len(merged))

has3 = sum(1 for p in merged.values() if len(p["seasons"]) == 3)
has2 = sum(1 for p in merged.values() if len(p["seasons"]) >= 2)
hasSp = sum(1 for p in merged.values() if p.get("sprint_speed"))
hasOaa = sum(1 for p in merged.values() if p.get("oaa") is not None)
hasDisc = sum(1 for p in merged.values()
    if any(s.get("o_swing_pct") is not None for s in p["seasons"].values()))

print("  3-year profiles: %d" % has3)
print("  2+ year profiles: %d" % has2)
print("  With sprint speed: %d" % hasSp)
print("  With OAA defense: %d" % hasOaa)
print("  With plate discipline: %d" % hasDisc)


print("")
print("=" * 60)
print("STEP 7: Writing src/savant_data.json")
print("=" * 60)

out = "src/savant_data.json"
with open(out, "w") as f:
    json.dump(merged, f, separators=(",", ":"))

size = len(open(out).read())
print("  File: %s" % out)
print("  Size: %d bytes (%d KB)" % (size, size // 1024))
print("  Players: %d" % len(merged))

soto = merged.get("665742")
if soto:
    s = soto["seasons"].get("2025", {})
    print("")
    print("  Sample: %s" % soto["name"])
    print("    xwOBA: %s" % s.get("xwoba"))
    print("    avg EV: %s" % s.get("avg_ev"))
    print("    barrel%%: %s" % s.get("barrel_pct"))
    print("    O-Swing%%: %s" % s.get("o_swing_pct"))
    print("    Z-Contact%%: %s" % s.get("z_contact_pct"))
    print("    K%%: %s" % s.get("k_pct"))
    print("    BB%%: %s" % s.get("bb_pct"))
    print("    wRC+: %s" % s.get("wrc_plus"))
    print("    Sprint: %s ft/s" % soto.get("sprint_speed"))
    print("    OAA: %s" % soto.get("oaa"))

print("")
print("Done! Now run: npm run build")
