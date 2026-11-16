"""Add any newly finished 2026 sessions to a Grid Replay index.

usage: python3 -I tools/update_new.py <current index.json> <work dir>
Builds every finished Race / Sprint / Qualifying / Sprint Qualifying session that is not in the index yet,
writes <work>/publish/ (new data files + merged index.json) and prints the files to publish."""
import base64, datetime, gzip, json, os, shutil, struct, subprocess, sys
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
from build_race import build, get
from build_quali import tyre_for
idx_path, work = sys.argv[1], sys.argv[2]
idx = json.load(open(idx_path)); pubd = f"{work}/publish"
for d in ("data", "radio", "quali"): os.makedirs(f"{pubd}/{d}", exist_ok=True)
os.makedirs(f"{work}/race/data", exist_ok=True)
ts = lambda s: datetime.datetime.fromisoformat(s).timestamp()
iso = lambda e: datetime.datetime.fromtimestamp(e, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
now = datetime.datetime.now(datetime.timezone.utc)
have = {r["session_key"] for k in ("races", "sprints", "quali") for r in idx.get(k, [])}
meetings = {m["meeting_key"]: m for m in get("meetings", year=2026)}
sessions = [s for s in get("sessions", year=2026) if not s.get("is_cancelled")]
race_order = [s["meeting_key"] for s in sorted((s for s in sessions if s["session_name"] == "Race"), key=lambda s: s["date_start"])]
rnd_of = lambda mk: race_order.index(mk) + 1 if mk in race_order else 0
todo = [s for s in sessions if s["session_name"] in ("Race", "Sprint", "Qualifying", "Sprint Qualifying") and s["session_key"] not in have
        and datetime.datetime.fromisoformat(s["date_end"]) + datetime.timedelta(hours=1) < now]
new_files, added, skipped = ["index.json"], [], []
races_new = []
for s in sorted(todo, key=lambda s: s["date_start"]):
    sk = s["session_key"]; m = meetings[s["meeting_key"]]; rnd = rnd_of(s["meeting_key"])
    meta = {"name": m["meeting_name"], "circuit": m["circuit_short_name"], "location": s["location"], "country": s["country_name"],
            "code": m["country_code"], "date": s["date_start"][:10], "gmt_offset": s.get("gmt_offset")}
    if s["session_name"] in ("Race", "Sprint"):
        info = build(sk, meta, rnd, f"{work}/race/data")
        if not info: skipped.append(f"{m['meeting_name']} {s['session_name']} (no lap data yet)"); continue
        subprocess.run([sys.executable, "-I", f"{TOOLS}/fill_holes.py", f"{work}/race/data/{sk}.bin", str(sk)])
        races_new.append({"session_key": sk, "round": rnd, "kind": "sprint" if s["session_name"] == "Sprint" else None, **meta, **info})
    else:
        drivers = {d["driver_number"]: d for d in get("drivers", session_key=sk)}
        res = {r["driver_number"]: r for r in get("session_result", session_key=sk)}
        laps = get("laps", session_key=sk); stints = get("stints", session_key=sk); best = {}
        for l in laps:
            if l["lap_duration"] and l["date_start"] and not l["is_pit_out_lap"] and (l["driver_number"] not in best or l["lap_duration"] < best[l["driver_number"]]["lap_duration"]):
                best[l["driver_number"]] = l
        out = []
        for num, l in best.items():
            d = drivers.get(num); r = res.get(num, {})
            if not d: continue
            a = ts(l["date_start"]); b = a + l["lap_duration"]
            loc = [p for p in get("location", **{"session_key": sk, "driver_number": num, "date>": iso(a - 2), "date<": iso(b + 2)}) if p["x"] or p["y"]]
            pos = r.get("position")
            out.append({"num": num, "code": d["name_acronym"], "first": d["first_name"], "last": d["last_name"], "team": d["team_name"],
                        "colour": "#" + (d["team_colour"] or "888888"), "pos": pos if isinstance(pos, int) else None, "phase": 0,
                        "time": l["lap_duration"], "lap": l["lap_number"], "sectors": [l["duration_sector_1"], l["duration_sector_2"], l["duration_sector_3"]],
                        "pts": [[round(ts(p["date"]) - a, 2), p["x"], p["y"]] for p in sorted(loc, key=lambda p: p["date"])], **tyre_for(stints, num, l["lap_number"])})
        out = [d for d in out if len(d["pts"]) >= 20]
        if len(out) < 5: skipped.append(f"{m['meeting_name']} {s['session_name']} (no lap data yet)"); continue
        out.sort(key=lambda d: (d["pos"] if isinstance(d["pos"], int) else 99, d["time"]))
        kind = "squali" if s["session_name"] == "Sprint Qualifying" else "quali"
        json.dump({"session_key": sk, "kind": kind, "name": m["meeting_name"], "session": s["session_name"], "drivers": out}, open(f"{pubd}/quali/{sk}.json", "w"), separators=(",", ":"))
        idx.setdefault("quali", []).append({"session_key": sk, "kind": kind, "round": rnd, "name": m["meeting_name"], "circuit": m["circuit_short_name"],
                                            "code": m["country_code"], "date": s["date_start"][:10], "file": f"quali/{sk}.json", "pole": out[0]["code"]})
        new_files.append(f"quali/{sk}.json"); added.append(f"{m['meeting_name']} {s['session_name']}")
if races_new:
    json.dump({"season": 2026, "races": races_new}, open(f"{work}/race/index.json", "w"))
    subprocess.run([sys.executable, "-I", f"{TOOLS}/build_radio.py", f"{work}/race"])
    races_new = json.load(open(f"{work}/race/index.json"))["races"]
    # optional: transcribe the new radio (needs `pip install faster-whisper` and Hugging Face access for the model)
    try:
        import faster_whisper  # noqa: F401
        subprocess.run([sys.executable, f"{TOOLS}/transcribe.py", f"{work}/race/radio"], env={**os.environ, "HF_HUB_DISABLE_XET": "1"})
    except ImportError:
        print("faster-whisper not installed: radio added without transcripts")
for r in races_new:
    sk = r["session_key"]; raw = open(f"{work}/race/data/{sk}.bin", "rb").read()
    open(f"{pubd}/data/{sk}.txt", "w").write(base64.b64encode(raw).decode()); new_files.append(f"data/{sk}.txt")
    b = gzip.decompress(raw); n = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + n])
    o = h["outline"][::max(1, len(h["outline"]) // 90)]; thumb = []
    if len(o) > 10:
        xs = [p[0] for p in o]; ys = [-p[1] for p in o]; sc = 100 / max(max(xs) - min(xs), max(ys) - min(ys))
        thumb = [[round((x - min(xs)) * sc, 1), round((y - min(ys)) * sc, 1)] for x, y in zip(xs, ys)]
    w = next((d for d in h["drivers"] if d["result"]["position"] == 1), None)
    e = {k: r.get(k) for k in ("session_key", "round", "name", "circuit", "location", "country", "code", "date", "winner", "laps", "drivers")}
    e.update(file=f"data/{sk}.txt", thumb=thumb, winner_colour=w["colour"] if w else "#8590a8")
    if r.get("radio") and os.path.exists(f"{work}/race/radio/{sk}.bin"):
        shutil.copy(f"{work}/race/radio/{sk}.bin", f"{pubd}/radio/{sk}.mp3"); e.update(radio=r["radio"], radio_file=f"radio/{sk}.mp3"); new_files.append(f"radio/{sk}.mp3")
    if r.get("kind") == "sprint": e["kind"] = "sprint"; idx.setdefault("sprints", []).append(e)
    else: idx["races"].append(e)
    added.append(f"{r['name']} {'Sprint' if r.get('kind') == 'sprint' else 'Race'}")
for k in ("races", "sprints", "quali"): idx.get(k, []).sort(key=lambda r: (r["date"], r["session_key"]))
json.dump(idx, open(f"{pubd}/index.json", "w"), separators=(",", ":"))
print("ADDED:", added or "nothing"); print("NOT READY:", skipped or "none"); print("FILES:", json.dumps(new_files if added else []))
