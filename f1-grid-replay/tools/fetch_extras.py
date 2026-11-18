"""Download per-race extras from OpenF1 for every race/sprint in a site dir: official overtakes, championship
standings after the session (drivers and teams), and per-lap sector times, speed traps and mini-sector colours.
usage: fetch_extras.py <site dir> <out dir>   (resumable). Output <out>/<session_key>.json:
{"ov": [[t, overtaker, overtaken, pos], ...]   t = seconds from the race pack's T0
 "cd": [[num, pos_start, pos_now, pts_start, pts_now], ...], "ct": [[team, pos_start, pos_now, pts_start, pts_now], ...]
 "lp": {num: [[lap, s1, s2, s3, i1, i2, st, "minisectors"], ...]}   minisectors: y yellow, g personal best, p overall best,
       b pit lane, - none, | between sectors}"""
import base64, datetime, gzip, json, os, struct, subprocess, sys, time
root, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
def get(ep, q):
    for a in range(6):
        p = subprocess.run(["curl", "-sS", "-m", "180", "-w", "\n%{http_code}", f"https://api.openf1.org/v1/{ep}?{q}"], capture_output=True, text=True)
        body, _, code = p.stdout.rpartition("\n")
        if code == "200": time.sleep(0.35); return json.loads(body)
        if code == "404": return []
        time.sleep(3 * (a + 1))
    raise RuntimeError(f"{ep} {q} -> {code}")
def header(path):
    b = open(f"{root}/{path}", "rb").read()
    if path.endswith(".txt"): b = base64.b64decode(b)
    if b[:2] == b"\x1f\x8b": b = gzip.decompress(b)
    n = struct.unpack("<I", b[:4])[0]; return json.loads(b[4:4 + n])
ts = lambda s: datetime.datetime.fromisoformat(s).timestamp()
SEG = {2048: "y", 2049: "g", 2051: "p", 2064: "b"}
for pre in ("", "2025/", "2024/", "2023/"):
    ix = f"{root}/{pre}index.json"
    if not os.path.exists(ix): continue
    for r in (lambda i: i["races"] + i.get("sprints", []))(json.load(open(ix))):
        sk = r["session_key"]; dst = f"{out}/{sk}.json"
        if os.path.exists(dst): continue
        try:
            T0 = header(r["file"])["T0"]
            ov = [[round(ts(o["date"]) - T0, 1), o["overtaking_driver_number"], o["overtaken_driver_number"], o.get("position")] for o in get("overtakes", f"session_key={sk}") if o.get("date")]
            cd = [[c["driver_number"], c.get("position_start"), c.get("position_current"), c.get("points_start"), c.get("points_current")] for c in get("championship_drivers", f"session_key={sk}")]
            ct = [[c["team_name"], c.get("position_start"), c.get("position_current"), c.get("points_start"), c.get("points_current")] for c in get("championship_teams", f"session_key={sk}")]
            lp = {}
            for l in sorted(get("laps", f"session_key={sk}"), key=lambda l: (l["driver_number"], l["lap_number"])):
                ms = "|".join("".join(SEG.get(x, "-") for x in (l.get(k) or [])) for k in ("segments_sector_1", "segments_sector_2", "segments_sector_3"))
                lp.setdefault(l["driver_number"], []).append([l["lap_number"], l.get("duration_sector_1"), l.get("duration_sector_2"), l.get("duration_sector_3"), l.get("i1_speed"), l.get("i2_speed"), l.get("st_speed"), ms])
            json.dump({"ov": sorted(ov), "cd": cd, "ct": ct, "lp": lp}, open(dst, "w"), separators=(",", ":"))
            print(sk, r["name"], len(ov), "overtakes", len(cd), "standings", sum(len(v) for v in lp.values()), "laps", flush=True)
        except Exception as e: print(sk, "FAILED", e, flush=True)
print("EXTRAS DONE", flush=True)
