"""Fill holes in a race's car-position data with estimates from lap + sector times, and refresh retirement times.
Real tracking is never overwritten; filled stretches are recorded in header['est'] so the page can label them."""
import gzip, json, struct, sys, os, datetime, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from build_race import get
bin_path, sk = sys.argv[1], int(sys.argv[2])
raw = gzip.decompress(open(bin_path, "rb").read()); n = struct.unpack("<I", raw[:4])[0]
h = json.loads(raw[4:4 + n]); N, DT, sc, T0 = h["n"], h["dt"], h["scale"], h["T0"]; D = len(h["drivers"])
P = np.frombuffer(raw[4 + n:], dtype="<i2").reshape(D, N, 2).astype(np.int64).cumsum(axis=1)
vis = np.ones((D, N), bool)
for i, d in enumerate(h["drivers"]):
    for a, b in d["missing"]: vis[i, a:min(b, N)] = False
ts = lambda s: datetime.datetime.fromisoformat(s).timestamp()
laps = get("laps", session_key=sk); by = {}
for l in laps:
    if l["date_start"]: by.setdefault(l["driver_number"], []).append(l)
for v in by.values(): v.sort(key=lambda l: l["lap_number"])
idx_of = {d["num"]: i for i, d in enumerate(h["drivers"])}
# --- retirement times from the current lap data
for i, d in enumerate(h["drivers"]):
    if not d["result"].get("dnf"): continue
    done = [l for l in by.get(d["num"], []) if l["lap_duration"]]
    if (d["result"].get("number_of_laps") or 0) > 0 and by.get(d["num"]):
        last = by[d["num"]][-1]; d["out"] = round(ts(last["date_start"]) + (last["lap_duration"] or 60) - T0, 1)
    else:   # retired without completing a lap: when the real tracking shows the car last moving
        mv = np.nonzero(vis[i, 1:] & vis[i, :-1] & (np.hypot(*np.diff(P[i], axis=0).T) * sc > 25))[0]
        d["out"] = round((mv.max() + 2) * DT if len(mv) else 120.0, 1)
# --- reference lap: fastest clean lap that was fully tracked
cands = [l for l in laps if l["date_start"] and l["lap_duration"] and l["lap_number"] >= 2 and not l["is_pit_out_lap"]
         and l["duration_sector_1"] and l["duration_sector_2"] and l["duration_sector_3"] and l["driver_number"] in idx_of]
cands.sort(key=lambda l: l["lap_duration"])
ref = None
for l in cands:
    a = int((ts(l["date_start"]) - T0) / DT) - 2; b = int((ts(l["date_start"]) + l["lap_duration"] - T0) / DT) + 2
    if any(e0 <= b*DT and a*DT <= e1 for e0, e1 in h.get("est", [])): continue   # only real tracking for the reference
    if a > 0 and b < N and vis[idx_of[l["driver_number"]], a:b].all(): ref = l; break
holes_exist = any((~vis[i]).any() for i in range(D))
if ref is None: sys.exit(f"{sk}: no fully tracked reference lap")
s0, dur = ts(ref["date_start"]), ref["lap_duration"]
loc = [p for p in get("location", session_key=sk, driver_number=ref["driver_number"]) if p["x"] or p["y"]]
t = np.array([ts(p["date"]) for p in loc]); x = np.array([p["x"] for p in loc], float); y = np.array([p["y"] for p in loc], float)
m = (t >= s0 - 0.5) & (t <= s0 + dur + 0.5); tr, xr, yr = t[m] - s0, x[m], y[m]
dr = np.r_[0, np.cumsum(np.hypot(np.diff(xr), np.diff(yr)))]; d0 = float(np.interp(0, tr, dr)); lapLen = float(np.interp(dur, tr, dr)) - d0
refT = np.linspace(0, dur, 2000); refD = np.interp(refT, tr, dr) - d0; pathD = dr - d0
secT = [0, ref["duration_sector_1"], ref["duration_sector_1"] + ref["duration_sector_2"], dur]
def xy(dist): dist %= lapLen; return np.interp(dist, pathD, xr), np.interp(dist, pathD, yr)
def dist_in_lap(e, lt, secs):
    if all(secs):
        k = sum(secs); s = [v * lt / k for v in secs]; b = [0, s[0], s[0] + s[1], lt]
        j = min(2, int(np.searchsorted(b, e, side="right") - 1)); f = (e - b[j]) / max(1e-6, b[j + 1] - b[j])
        rt = secT[j] + f * (secT[j + 1] - secT[j])
    else: rt = e / lt * dur
    return float(np.interp(rt, refT, refD))
grid = T0 + np.arange(N) * DT; filled = np.zeros(N, bool); count = 0
for i, d in enumerate(h["drivers"]):
    ls = by.get(d["num"], []); starts = [ts(l["date_start"]) for l in ls]
    out_i = int(d["out"] / DT) if d.get("out") is not None else N
    for k, l in enumerate(ls):
        a = starts[k]; b = starts[k + 1] if k + 1 < len(ls) else (a + l["lap_duration"] if l["lap_duration"] else None)
        if b is None and k == len(ls) - 1 and not d["result"].get("dnf"):   # finisher's last lap with no recorded time
            recent = [x["lap_duration"] for x in ls[-6:-1] if x["lap_duration"]]
            if recent: b = a + float(np.median(recent))
        if b is None or l["lap_number"] < 2: continue
        secs = [l["duration_sector_1"], l["duration_sector_2"], l["duration_sector_3"]]
        for j in range(max(0, int(np.ceil((a - T0) / DT))), min(N, int((b - T0) / DT) + 1, out_i)):
            if vis[i, j]: continue
            px, py = xy(dist_in_lap(grid[j] - a, b - a, secs)); P[i, j] = [round(px / sc), round(py / sc)]; vis[i, j] = True; filled[j] = True; count += 1
# finishers: roll on at cool-down pace after the flag instead of vanishing (only where tracking is missing)
for i, d in enumerate(h["drivers"]):
    ls = by.get(d["num"], [])
    if d["result"].get("dnf") or not ls: continue
    a = ts(ls[-1]["date_start"]); dl = ls[-1]["lap_duration"] or float(np.median([x["lap_duration"] for x in ls[-6:-1] if x["lap_duration"]] or [90]))
    end = a + dl; j0 = int((end - T0) / DT) + 1
    for j in range(max(0, j0), min(N, j0 + 160)):
        if vis[i, j]: continue
        px, py = xy((grid[j] - end) * 30 * 10); P[i, j] = [round(px / sc), round(py / sc)]; vis[i, j] = True; filled[j] = True
for i, d in enumerate(h["drivers"]):
    rng, j, v = [], 0, vis[i].tolist()
    while j < N:
        if not v[j]:
            k = j
            while k < N and not v[k]: k += 1
            rng.append([j, k]); j = k
        else: j += 1
    d["missing"] = rng
est, j = [], 0
while j < N:
    if filled[j]:
        k = j
        while k < N and (filled[k] or (k + 6 < N and filled[k:k + 6].any())): k += 1
        est.append([round(j * DT, 1), round(k * DT, 1)]); j = k
    else: j += 1
old = h.get("est", []) + ([[h["est_from"], h["n"] * DT]] if h.get("est_from") is not None else [])
merged = []
for e0, e1 in sorted(old + est):
    if merged and e0 <= merged[-1][1] + 3: merged[-1][1] = max(merged[-1][1], e1)
    else: merged.append([e0, e1])
h["est"] = merged; h.pop("est_from", None)
if len(h["outline"]) < 20: h["outline"] = [[int(a // sc), int(b // sc)] for a, b in zip(xr[::2], yr[::2])]
delta = np.clip(np.diff(P, axis=1, prepend=0), -32767, 32767).astype("<i2")
hb = json.dumps(h, separators=(",", ":")).encode()
open(bin_path, "wb").write(gzip.compress(struct.pack("<I", len(hb)) + hb + delta.tobytes(), 9))
tot = sum(b - a for a, b in est)
print(f"{sk}: ref lap {ref['lap_number']} #{ref['driver_number']} ({lapLen/10:.0f} m) | filled {count} samples | estimated stretches {len(est)}, {tot/60:.1f} min")
