"""Last year's qualifying at the circuits still to race: track layout + ghost laps for the preview."""
import json, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_race import get
from build_quali import tyre_for
ts = lambda s: datetime.datetime.fromisoformat(s).timestamp()
iso = lambda e: datetime.datetime.fromtimestamp(e, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
up = {u["round"]: u for u in json.load(open("upcoming.json"))}
targets = [(21, 9854, 11420, 11416), (22, 9846, 11428, 11424), (23, 9835, 11436, 11432)]   # round, 2025 quali, 2026 race, 2026 quali
sess26 = {s["session_key"]: s for s in json.load(open("sess_all.json"))}
out_idx = []
for rnd, sk, race26, q26 in targets:
    drivers = {d["driver_number"]: d for d in get("drivers", session_key=sk)}
    res = {r["driver_number"]: r for r in get("session_result", session_key=sk)}
    laps = get("laps", session_key=sk); stints = get("stints", session_key=sk); best = {}
    for l in laps:
        if l["lap_duration"] and l["date_start"] and not l["is_pit_out_lap"] and (l["driver_number"] not in best or l["lap_duration"] < best[l["driver_number"]]["lap_duration"]):
            best[l["driver_number"]] = l
    top = sorted(best.values(), key=lambda l: l["lap_duration"])[:10]
    out = []
    for l in top:
        num = l["driver_number"]; d = drivers[num]; a = ts(l["date_start"]); b = a + l["lap_duration"]
        loc = [p for p in get("location", **{"session_key": sk, "driver_number": num, "date>": iso(a - 2), "date<": iso(b + 2)}) if p["x"] or p["y"]]
        pos = res.get(num, {}).get("position")
        out.append({"num": num, "code": d["name_acronym"], "first": d["first_name"], "last": d["last_name"], "team": d["team_name"],
                    "colour": "#" + (d["team_colour"] or "888888"), "pos": pos if isinstance(pos, int) else None, "phase": 3,
                    "time": l["lap_duration"], "lap": l["lap_number"], "sectors": [l["duration_sector_1"], l["duration_sector_2"], l["duration_sector_3"]],
                    "pts": [[round(ts(p["date"]) - a, 2), p["x"], p["y"]] for p in sorted(loc, key=lambda p: p["date"])], **tyre_for(stints, num, l["lap_number"])})
    out.sort(key=lambda d: d["time"])
    u = up[rnd]; r26 = sess26[race26]; q = sess26[q26]
    json.dump({"session_key": sk, "kind": "preview", "name": u["name"], "session": "2025 Qualifying", "drivers": out}, open(f"out_quali/prev_{rnd}.json", "w"), separators=(",", ":"))
    out_idx.append({"session_key": race26, "kind": "preview", "round": rnd, "name": u["name"], "circuit": u["circuit"], "code": u["code"], "date": u["date"],
                    "file": f"quali/prev_{rnd}.json", "race_start": r26["date_start"], "quali_start": q["date_start"], "gmt_offset": r26["gmt_offset"],
                    "last_pole": out[0]["code"] + " " + str(out[0]["time"])})
    print(u["name"], "2025 laps", len(out), "pole", out_idx[-1]["last_pole"], flush=True)
json.dump(out_idx, open("out_quali/previews.json", "w"), indent=1)
