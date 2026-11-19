"""Build an ESTIMATED replay of a 2018-2022 race from Jolpica data (lap times + positions per lap, pit stops, results).
No GPS exists for these years without an F1 login, so each car is moved along a reference lap taken from a modern
race at the same circuit: the reference gives the racing line and how speed varies around the lap; each estimated lap
is that reference stretched to the real lap time. The data is shaped like OpenF1's and packed by build_race.build,
so the page needs no special code; the header marks the whole race as estimated.
usage: build_estimated.py <jolpica dir> <year> <round> <ref race pack> <out dir>"""
import base64, datetime, gzip, json, os, struct, sys
import numpy as np
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
import build_race
J, Y, RND, REF, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
D = f"{J}/{Y}/{RND:02d}"; L = lambda n: json.load(open(f"{D}/{n}.json"))
sched = next(r for r in json.load(open(f"{J}/{Y}/schedule.json")) if int(r["round"]) == RND)
results, laps_j, pits_j = L("results"), L("laps"), L("pitstops")
COL = {  # team colours by constructor and year (approximate official liveries)
 "mercedes": "00D2BE", "red_bull": "1E41FF", "ferrari": "DC0000", "mclaren": "FF8700", "renault": "FFF500", "alpine": "0090FF",
 "force_india": "F596C8", "racing_point": "F596C8", "aston_martin": "006F62", "sauber": "9B0000", "alfa": "900000",
 "toro_rosso": "469BFF", "alphatauri": "2B4562", "williams": "FFFFFF", "haas": "B6BABD"}
if Y == 2022: COL.update(mercedes="6CD3BF", red_bull="3671C6", ferrari="F91536", mclaren="F58020", alpine="2293D1", aston_martin="358C75", alfa="C92D4B", alphatauri="5E8FAA", williams="37BEDD")
if Y == 2021: COL.update(williams="005AFF")
# ---- reference lap from a modern race pack: positions over the overall fastest lap
b = open(REF, "rb").read()
if REF.endswith(".txt"): b = base64.b64decode(b)
b = gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b
hl = struct.unpack("<I", b[:4])[0]; H = json.loads(b[4:4 + hl]); nd, N = len(H["drivers"]), H["n"]
q = np.frombuffer(b[4 + hl:], "<i2").astype(np.int64).reshape(nd, N, 2).cumsum(axis=1) * H["scale"]
te, num, dur, _ = H["best"][-1]; di = [d["num"] for d in H["drivers"]].index(num)
i0, i1 = int((te - dur) / H["dt"]), int(te / H["dt"]) + 1
ref = q[di, i0:i1 + 1].astype(float); rt = (np.arange(len(ref)) * H["dt"] - ((te - dur) - i0 * H["dt"])) / dur   # time fraction 0..1
seg = np.hypot(*np.diff(ref, axis=0).T); dist = np.concatenate([[0], np.cumsum(seg)]); lap_len = dist[-1]
def at(frac):   # position at a fraction of lap TIME (handles negatives/over 1 by wrapping)
    f = np.mod(frac, 1.0); return np.interp(f, rt, ref[:, 0]), np.interp(f, rt, ref[:, 1])
def at_dist(dfrac):  # position at a fraction of lap DISTANCE (for grid slots)
    f = np.mod(dfrac, 1.0); return np.interp(f * lap_len, dist, ref[:, 0]), np.interp(f * lap_len, dist, ref[:, 1])
# ---- timing from Jolpica
start = datetime.datetime.fromisoformat((sched["date"] + "T" + sched.get("time", "14:00:00Z")).replace("Z", "+00:00")).timestamp()
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
def secs(s):
    p = s.split(":"); return float(p[0]) * 60 + float(p[1]) if len(p) == 2 else float(p[0])
num_of = {r["Driver"]["driverId"]: int(r["number"]) for r in results}
drv_laps = {}
for Lp in laps_j:
    for t in Lp["Timings"]: drv_laps.setdefault(num_of[t["driverId"]], []).append((int(Lp["number"]), secs(t["time"]), int(t["position"])))
for v in drv_laps.values(): v.sort()
grid = {int(r["number"]): int(r["grid"]) or 20 for r in results}
lapstart = {n: {} for n in drv_laps}   # n -> lap -> (start, duration)
for n, v in drv_laps.items():
    t = start
    for lap, d, _ in v: lapstart[n][lap] = (t, d); t += d
ends = [s + d for n in lapstart for s, d in lapstart[n].values()]
T_end = max(ends) + 60
pit_by = {}
for p in pits_j: pit_by.setdefault(num_of[p["driverId"]], []).append((int(p["lap"]), secs(p["duration"]) if ":" not in p["duration"] else None))
def loc(n):
    out = []; g = grid.get(n, 20); gf = -(8.0 * g + 30) / lap_len   # grid slot: 8 m apart behind the line
    gx, gy = at_dist(gf)
    t = start - 25
    while t < start: out.append({"date": iso(t), "x": float(gx), "y": float(gy)}); t += 0.5
    laps = lapstart.get(n, {}); last = None
    for lap in sorted(laps):
        s, d = laps[lap]; tt = s
        while tt < s + d:
            u = (tt - s) / d
            if lap == 1: x, y = at_dist(gf + (1 - gf) * float(np.interp(u, rt, dist / lap_len)))   # first lap starts from the grid slot
            else: x, y = at(u)
            out.append({"date": iso(tt), "x": float(x), "y": float(y)}); tt += 0.5
        last = s + d
    if last is not None:   # after the flag (or retirement) the car stays where it stopped, then the data ends
        x, y = at(0.0) if n in fin else at(0.5)
        for k in range(8): out.append({"date": iso(last + k * 0.5), "x": float(x), "y": float(y)})
    return out
fin = {int(r["number"]) for r in results if r["status"] == "Finished" or r["status"].startswith("+")}
# positions and gaps at every lap end (official running order per lap from Jolpica)
pos_ev, int_ev = [], []
for lap in sorted({l for v in drv_laps.values() for l, _, _ in v}):
    rows = sorted(((lapstart[n][lap][0] + lapstart[n][lap][1], n) for n in lapstart if lap in lapstart[n]))
    lead_t = rows[0][0]; prev = None
    for k, (te, n) in enumerate(rows):
        pos_ev.append({"date": iso(te), "driver_number": n, "position": k + 1})
        int_ev.append({"date": iso(te), "driver_number": n, "gap_to_leader": round(te - lead_t, 3) if k else 0, "interval": round(te - prev, 3) if prev else 0}); prev = te
for n in grid: pos_ev.append({"date": iso(start - 20), "driver_number": n, "position": grid[n] if grid[n] else 20})
def status(r): return r["status"]
session_result = [{"driver_number": int(r["number"]), "position": int(r["position"]) if (r["status"] == "Finished" or r["status"].startswith("+")) else None,
   "number_of_laps": int(r["laps"]), "points": float(r["points"]), "dnf": not (r["status"] == "Finished" or r["status"].startswith("+")) and r["status"] != "Disqualified",
   "dsq": r["status"] == "Disqualified", "dns": int(r["laps"]) == 0 and r["status"] in ("Did not start", "Withdrew"),
   "gap_to_leader": None, "duration": int(r["Time"]["millis"]) / 1000 if r.get("Time") else None} for r in results]
for s, r in zip(session_result, results):   # classified non-finishers (e.g. +1 Lap) still get their finishing position
    if s["position"] is None and r.get("positionText", "").isdigit() and not s["dnf"]: s["position"] = int(r["position"])
drivers = [{"driver_number": int(r["number"]), "name_acronym": r["Driver"].get("code") or r["Driver"]["familyName"][:3].upper(), "first_name": r["Driver"]["givenName"],
   "last_name": r["Driver"]["familyName"], "team_name": r["Constructor"]["name"], "team_colour": COL.get(r["Constructor"]["constructorId"], "888888")} for r in results]
laps_o = [{"driver_number": n, "lap_number": lap, "date_start": iso(s), "lap_duration": d, "is_pit_out_lap": any(pl + 1 == lap for pl, _ in pit_by.get(n, []))}
   for n in lapstart for lap, (s, d) in lapstart[n].items()]
stints, pits = [], []
for n in lapstart:
    pl = sorted(pit_by.get(n, [])); start_lap = 1
    for i, (lap, du) in enumerate(pl):
        stints.append({"driver_number": n, "lap_start": start_lap, "lap_end": lap, "compound": "UNKNOWN", "tyre_age_at_start": 0}); start_lap = lap + 1
        s, d = lapstart[n].get(lap, (None, None))
        if s: pits.append({"driver_number": n, "lap_number": lap, "date": iso(s + d + min(du or 22, 40) * 0.6), "stop_duration": None, "lane_duration": du})
    stints.append({"driver_number": n, "lap_start": start_lap, "lap_end": max(lapstart[n] or [1]), "compound": "UNKNOWN", "tyre_age_at_start": 0})
DATA = {"drivers": drivers, "laps": laps_o, "session_result": session_result, "position": pos_ev, "intervals": int_ev, "stints": stints, "pit": pits,
        "race_control": [], "weather": []}
def get(ep, **kw):
    if ep == "location": return loc(kw["driver_number"])
    return [dict(x) for x in DATA.get(ep, [])]
build_race.get = get
sk = Y * 100 + RND
meta = {"name": sched["raceName"], "circuit": sched["Circuit"]["circuitName"], "location": sched["Circuit"]["Location"]["locality"],
        "country": sched["Circuit"]["Location"]["country"], "date": sched["date"]}
os.makedirs(OUT, exist_ok=True)
info = build_race.build(sk, meta, RND, OUT)
# mark the whole race as estimated and add a note
p = f"{OUT}/{sk}.bin"; b = gzip.decompress(open(p, "rb").read()); hl = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + hl])
h["est"] = [[0, h["n"] * h["dt"]]]; h["estimated"] = {"source": "Jolpica lap times", "ref": H.get("session_key")}
hb = json.dumps(h, separators=(",", ":")).encode(); open(p, "wb").write(gzip.compress(struct.pack("<I", len(hb)) + hb + b[4 + hl:], 9))
print(json.dumps({"session_key": sk, "round": RND, **meta, **info}))
