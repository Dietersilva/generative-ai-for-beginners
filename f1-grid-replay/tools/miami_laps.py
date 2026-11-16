"""Reconstruct the missing lap starts (laps 2-25) of the 2025 Miami GP (session 10033) from GPS.

OpenF1 has full GPS for the race but no lap records for laps 2-25. Each car's crossings of the
timing line are found in its GPS track; the crossing that matches the first recorded lap start
anchors the numbering, and earlier crossings are counted back from it. Laps OpenF1 does have are
used to measure the error of the method before anything is filled in."""
import json, sys, numpy as np
D = sys.argv[1] if len(sys.argv) > 1 else "raw2025/mia"
def ts(s): return np.array([x[:26].replace("+00:00", "") for x in s], dtype="datetime64[us]").astype("int64") / 1e6
def iso(t): return str(np.datetime64(int(t * 1e6), "us")) + "+00:00"
laps = json.load(open(f"{D}/laps.json")); res = json.load(open(f"{D}/../res10033.json"))
nums = [r["driver_number"] for r in res]
trk = {}
for n in nums:
    L = [p for p in json.load(open(f"{D}/loc{n}.json")) if p["x"] or p["y"]]
    if len(L) < 50: continue
    t = ts([p["date"] for p in L]); o = np.argsort(t)
    trk[n] = (t[o], np.array([p["x"] for p in L], float)[o], np.array([p["y"] for p in L], float)[o])
known = [l for l in laps if l["date_start"] and l["driver_number"] in trk]
# timing line point & direction: median position at known lap starts, direction from 0.3 s later
P, V = [], []
for l in known:
    t, x, y = trk[l["driver_number"]]; a = ts([l["date_start"]])[0]
    p0 = np.array([np.interp(a, t, x), np.interp(a, t, y)]); p1 = np.array([np.interp(a + .3, t, x), np.interp(a + .3, t, y)])
    P.append(p0); V.append(p1 - p0)
P = np.median(P, axis=0); dv = np.median(V, axis=0); dv /= np.linalg.norm(dv); nv = np.array([-dv[1], dv[0]])
def crossings(n):
    t, x, y = trk[n]; rel = np.stack([x - P[0], y - P[1]], 1); s = rel @ dv; lat = np.abs(rel @ nv)
    i = np.where((s[:-1] < 0) & (s[1:] >= 0) & (lat[:-1] < 900) & (t[1:] - t[:-1] < 3))[0]   # within 90 m sideways (covers the pit lane)
    return t[i] + (t[i + 1] - t[i]) * (-s[i]) / (s[i + 1] - s[i])
out, errs = [], []
for n in trk:
    c = crossings(n); mine = {l["lap_number"]: l for l in laps if l["driver_number"] == n}
    kn = sorted((k, ts([l["date_start"]])[0]) for k, l in mine.items() if l["date_start"])
    if not kn: continue
    k0, a0 = kn[0]; j0 = int(np.argmin(np.abs(c - a0)))
    if abs(c[j0] - a0) > 2: print("anchor miss", n, c[j0] - a0); continue
    for k, a in kn:                                   # validation on laps OpenF1 has
        j = j0 + (k - k0)
        if j < len(c): errs.append(c[j] - a)
    for k in range(2, k0):
        j = j0 - (k0 - k)
        if j < 0: break
        l = mine.get(k) or {"driver_number": n, "lap_number": k, "session_key": 10033, "meeting_key": 1259, "is_pit_out_lap": False,
                            "duration_sector_1": None, "duration_sector_2": None, "duration_sector_3": None, "i1_speed": None, "i2_speed": None, "st_speed": None, "segments_sector_1": None, "segments_sector_2": None, "segments_sector_3": None}
        l["date_start"] = iso(c[j]); l["lap_duration"] = round(float(c[j + 1] - c[j]), 3); l["gps_est"] = True
        mine[k] = l
    if 1 in mine and 2 in mine:   # lap 1 starts at lights out: 20:03:42.617 UTC, the moment the grid moves in the GPS (several cars agree)
        lo = ts(["2025-05-04T20:03:42.617"])[0]
        mine[1]["date_start"] = iso(lo); mine[1]["lap_duration"] = round(float(ts([mine[2]["date_start"]])[0] - lo), 3); mine[1]["gps_est"] = True
    out += mine.values()
out += [l for l in laps if l["driver_number"] not in trk]
e = np.abs(np.array(errs))
print(f"validation on {len(e)} recorded laps: median {np.median(e):.3f}s, 95% {np.percentile(e, 95):.3f}s, max {e.max():.3f}s")
print("laps", len(laps), "->", len(out), "| filled", sum(1 for l in out if l.get("gps_est")))
json.dump(out, open(f"{D}/laps_fixed.json", "w"))
