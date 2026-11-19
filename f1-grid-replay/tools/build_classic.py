"""Build one season of the Pit Wall Redux CLASSIC edition (2018-2022): ESTIMATED replays from Jolpica data.
No GPS exists for these years without an F1 login. Each car moves along a reference lap: a real lap from a 2023+ race at
the same circuit (racing line + how speed varies round the lap), or, for circuits not raced since, the open
f1-circuits outline (MIT, (c) Tomislav Bacinger) with a speed profile worked out from its corners. Every lap is that
reference stretched to the real lap time. Also: pit-lane visits, safety-car/red-flag periods detected from lap times,
standings after every round, qualifying times and retirement reasons (per-season extra file).
usage: build_classic.py <jolpica dir> <year> <site dir> [round ...]"""
import datetime, glob, gzip, json, math, os, struct, sys
import numpy as np
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
import build_race
J, Y, SITE = sys.argv[1], int(sys.argv[2]), sys.argv[3]; ONLY = {int(a) for a in sys.argv[4:]}
PRE = f"{Y}/"; OUT = f"{SITE}/{Y}/data"; os.makedirs(OUT, exist_ok=True)
U = 10.0   # position units per metre (as in OpenF1)
sched = json.load(open(f"{J}/{Y}/schedule.json"))
COL = {"mercedes": "00D2BE", "red_bull": "1E41FF", "ferrari": "DC0000", "mclaren": "FF8700", "renault": "FFF500", "alpine": "0090FF",
       "force_india": "F596C8", "racing_point": "F596C8", "aston_martin": "006F62", "sauber": "9B0000", "alfa": "900000",
       "toro_rosso": "469BFF", "alphatauri": "2B4562", "williams": "FFFFFF", "haas": "B6BABD"}
if Y == 2022: COL.update(mercedes="6CD3BF", red_bull="3671C6", ferrari="F91536", mclaren="F58020", alpine="2293D1", aston_martin="358C75", alfa="C92D4B", alphatauri="5E8FAA", williams="37BEDD")
if Y == 2021: COL.update(williams="005AFF", mclaren="FF9800")
if Y <= 2019: COL.update(mclaren="FF8700", williams="FFFFFF")
CODE3 = {"BRN": "bahrain", "KSA": "jeddah"}
CC = {"Australia": "AUS", "Bahrain": "BRN", "China": "CHN", "Azerbaijan": "AZE", "Spain": "ESP", "Monaco": "MON", "Canada": "CAN", "France": "FRA",
      "Austria": "AUT", "UK": "GBR", "Germany": "GER", "Hungary": "HUN", "Belgium": "BEL", "Italy": "ITA", "Singapore": "SGP", "Russia": "RUS",
      "Japan": "JPN", "USA": "USA", "United States": "USA", "Mexico": "MEX", "Brazil": "BRA", "UAE": "UAE", "Portugal": "POR", "Turkey": "TUR",
      "Netherlands": "NED", "Qatar": "QAT", "Saudi Arabia": "KSA"}
# ---------------- reference laps ----------------
def ref_from_pack(path):
    b = open(path, "rb").read(); b = gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b
    hl = struct.unpack("<I", b[:4])[0]; H = json.loads(b[4:4 + hl]); nd, N = len(H["drivers"]), H["n"]
    q = np.frombuffer(b[4 + hl:], "<i2").astype(np.int64).reshape(nd, N, 2).cumsum(axis=1) * H["scale"]
    for te, num, dur, _ in reversed(H["best"]):   # fastest lap first; skip laps with GPS holes
        nums = [d["num"] for d in H["drivers"]]
        if num not in nums: continue
        di = nums.index(num); i0, i1 = int((te - dur) / H["dt"]), int(te / H["dt"]) + 1
        ref = q[di, i0:i1 + 1].astype(float); seg = np.hypot(*np.diff(ref, axis=0).T)
        if len(ref) > 40 and seg.max() < 60 * U: return ref, (np.arange(len(ref)) * H["dt"] - ((te - dur) - i0 * H["dt"])) / dur
    raise RuntimeError("no clean reference lap in " + path)
GEO = json.load(open("old/circuits/f1-circuits.geojson"))["features"]
def ref_from_geo(fid, clockwise):
    f = next(f for f in GEO if f["properties"]["id"] == fid); co = np.array(f["geometry"]["coordinates"], float)
    lat0 = math.radians(co[:, 1].mean()); x = (co[:, 0] - co[0, 0]) * 111320 * math.cos(lat0); y = (co[:, 1] - co[0, 1]) * 110540
    p = np.c_[x, y]
    if np.hypot(*(p[-1] - p[0])) > 1: p = np.vstack([p, p[:1]])
    area = 0.5 * np.sum(p[:-1, 0] * p[1:, 1] - p[1:, 0] * p[:-1, 1])
    if (area < 0) != clockwise: p = p[::-1]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; s = np.arange(0, d[-1], 5.0)
    r = np.c_[np.interp(s, d, p[:, 0]), np.interp(s, d, p[:, 1])]; n = len(r)
    k = np.zeros(n)
    for i in range(n):   # curvature from the circle through points 4 steps (20 m) either side
        a, b, c = r[(i - 4) % n], r[i], r[(i + 4) % n]
        ab, bc, ca = np.hypot(*(b - a)), np.hypot(*(c - b)), np.hypot(*(a - c)); cr = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        k[i] = 2 * cr / max(ab * bc * ca, 1e-6)
    k = np.convolve(np.r_[k[-3:], k, k[:3]], np.ones(7) / 7, "valid")
    v = np.minimum(92.0, np.sqrt(38.0 / np.maximum(k, 1e-6)))
    for _ in range(2):   # acceleration and braking limits, around the loop twice
        for i in range(n): v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * (2 + 12 * (1 - v[i - 1] / 95)) * 5.0))
        for i in range(n - 1, -1, -1): v[i] = min(v[i], math.sqrt(v[(i + 1) % n] ** 2 + 2 * 38.0 * 5.0))
    t = np.r_[0, np.cumsum(5.0 / v[:-1])]; tot = t[-1] + 5.0 / v[-1]
    r = np.vstack([r, r[:1]]); tf = np.r_[t, tot] / tot
    return r * U, tf
GEO_MAP = {"ricard": ("fr-1969", True), "sochi": ("ru-2014", True), "hockenheimring": ("de-1932", True), "istanbul": ("tr-2005", False),
           "portimao": ("pt-2008", True), "mugello": ("it-1914", True), "nurburgring": ("de-1927", True)}
def modern_packs():
    m = {}
    for yy in (2023, 2026, 2024, 2025):   # later entries win: prefer 2025, then 2024
        ix = json.load(open(f"pub/{'' if yy == 2026 else str(yy) + '/'}index.json")); byd = {r["date"]: r for r in ix["races"]}
        for r in json.load(open(f"old/alltime/schedule_{yy}.json")):
            dt = datetime.date.fromisoformat(r["date"]); e = None
            for dd in (0, -1, 1):
                e = byd.get(str(dt + datetime.timedelta(days=dd)))
                if e: break
            if e: m[r["Circuit"]["circuitId"]] = (f"pub/{e['file']}", e["circuit"])
    return m
PACKS = modern_packs()
NOTES = {"yas_marina": "track layout changed in 2021; the current layout is shown", "marina_bay": "track layout changed in 2023; the current layout is shown",
         "catalunya": "the final chicane was removed in 2023; the current layout is shown", "albert_park": "track layout changed in 2022; the current layout is shown"}
def reference(cid, rname):
    if cid == "bahrain" and "Sakhir" in rname: return ref_from_pack(PACKS["bahrain"][0]), "Bahrain", "the outer loop used this weekend isn't available, so cars are shown on the Grand Prix layout and look faster than they were"
    if cid in PACKS: return ref_from_pack(PACKS[cid][0]), PACKS[cid][1], NOTES.get(cid) if (cid != "albert_park" or Y < 2022) and (cid != "yas_marina" or Y < 2021) else None
    if cid in GEO_MAP: return ref_from_geo(*GEO_MAP[cid]), None, None
    raise RuntimeError("no reference for " + cid)
# ---------------- helpers ----------------
iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
def secs(s):
    if not s: return None
    p = s.split(":")
    try: return float(p[0]) * 60 + float(p[1]) if len(p) == 2 else (float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2]) if len(p) == 3 else float(p[0]))
    except ValueError: return None
FIN = lambda r: r["status"] == "Finished" or r["status"].startswith("+") or r["status"] == "Lapped"
standings = {}; cstand = {}; seen_team = {}; extras = {}; idx_races = []; season_rounds = []; drv_info = {}
def stand_rows(tbl):   # official order: points, then countback on wins, seconds, ...
    return sorted(tbl.items(), key=lambda kv: (-kv[1]["pts"], [-kv[1]["fin"].get(p, 0) for p in range(1, 30)]))
for R in sched:
    rnd = int(R["round"]); D = f"{J}/{Y}/{rnd:02d}"
    if not os.path.exists(f"{D}/laps.json"): print("round", rnd, "not downloaded yet"); continue
    L = lambda n: json.load(open(f"{D}/{n}.json")) if os.path.exists(f"{D}/{n}.json") else []
    results, laps_j, pits_j, quali, sprint = L("results"), L("laps"), L("pitstops"), L("qualifying"), L("sprint")
    num_of = {r["Driver"]["driverId"]: int(r["number"]) for r in results}
    # ---- standings before / after (sprint points count before the race, like the official tables)
    before = {k: dict(v) for k, v in standings.items()}; cbefore = {k: dict(v) for k, v in cstand.items()}
    for src in (sprint, results):
        for r in src:
            did = r["Driver"]["driverId"]; s = standings.setdefault(did, {"pts": 0.0, "fin": {}, "num": int(r["number"]), "code": r["Driver"].get("code")}); s["pts"] += float(r["points"]); s["num"] = int(r["number"])
            c = cstand.setdefault(r["Constructor"]["name"], {"pts": 0.0, "fin": {}}); c["pts"] += float(r["points"])
            if src is results and r["positionText"].isdigit(): s["fin"][int(r["position"])] = s["fin"].get(int(r["position"]), 0) + 1; c["fin"][int(r["position"])] = c["fin"].get(int(r["position"]), 0) + 1
    if sprint:   # 'before' for the race view = after the sprint
        pass
    pos_b = {k: i + 1 for i, (k, _) in enumerate(stand_rows(before))}; pos_a = {k: i + 1 for i, (k, _) in enumerate(stand_rows(standings))}
    cpos_b = {k: i + 1 for i, (k, _) in enumerate(stand_rows(cbefore))}; cpos_a = {k: i + 1 for i, (k, _) in enumerate(stand_rows(cstand))}
    cd = [[v["num"], pos_b.get(k), pos_a[k], before.get(k, {}).get("pts", 0.0), v["pts"]] for k, v in standings.items()]
    ct = [[k, cpos_b.get(k), cpos_a[k], cbefore.get(k, {}).get("pts", 0.0), v["pts"]] for k, v in cstand.items()]
    if ONLY and rnd not in ONLY: continue
    # ---- reference lap
    (ref, rt), circ_name, note = reference(R["Circuit"]["circuitId"], R["raceName"])
    dist = np.r_[0, np.cumsum(np.hypot(*np.diff(ref, axis=0).T))]; lap_len = dist[-1]; df = dist / lap_len
    at_t = lambda f: (np.interp(f % 1.0, rt, ref[:, 0]), np.interp(f % 1.0, rt, ref[:, 1]))
    at_d = lambda f: (np.interp((f % 1.0) * lap_len, dist, ref[:, 0]), np.interp((f % 1.0) * lap_len, dist, ref[:, 1]))
    t_of_d = lambda f: float(np.interp(f, df, rt))
    def normal_at(f):
        a, b = np.array(at_d(f - 0.002)), np.array(at_d(f + 0.002)); d = b - a; l = np.hypot(*d) or 1; return np.array([-d[1], d[0]]) / l
    # ---- timing
    start = datetime.datetime.fromisoformat((R["date"] + "T" + R.get("time", "13:00:00Z")).replace("Z", "+00:00")).timestamp()
    drv_laps = {}
    for Lp in laps_j:
        for t in Lp["Timings"]:
            if t["driverId"] in num_of: drv_laps.setdefault(num_of[t["driverId"]], []).append((int(Lp["number"]), secs(t["time"]), int(t["position"])))
    lapst = {}
    for n, v in drv_laps.items():
        v.sort(); t = start; lapst[n] = {}
        for lap, d, _ in v:
            if d is None: d = 120.0
            lapst[n][lap] = (t, d); t += d
    grid = {int(r["number"]): int(r["grid"]) for r in results}
    pit_by = {}
    for p in pits_j:
        if p["driverId"] in num_of:
            du = secs(p["duration"]); pit_by.setdefault(num_of[p["driverId"]], {})[int(p["lap"])] = du if du and du < 60 else None
    # ---- neutralised periods from lap times (no race-control data exists for these years)
    clean = [d for n in lapst for lap, (s, d) in lapst[n].items() if lap > 1 and lap not in pit_by.get(n, {}) and lap - 1 not in pit_by.get(n, {})]
    M = float(np.median(clean)) if clean else 90.0; rc = []
    leader = min(lapst, key=lambda n: (-len(lapst[n]), sum(d for _, d in lapst[n].values())))
    lap_med = {}
    for lap in sorted({l for n in lapst for l in lapst[n]}):
        v = [lapst[n][lap][1] for n in lapst if lap in lapst[n]]   # all cars: pit laps are a minority except under a safety car, when every lap is slow anyway
        if len(v) >= max(3, len(lapst) * 0.5): lap_med[lap] = float(np.median(v))
    neutral = sorted(l for l, m in lap_med.items() if l > 1 and m > 1.12 * M)
    groups = []
    for l in neutral:   # slow laps one apart belong to the same period
        if groups and l <= groups[-1][-1] + 2: groups[-1] += list(range(groups[-1][-1] + 1, l + 1))
        else: groups.append([l])
    groups = [g for g in groups if len(g) >= 2 or max(lap_med.get(l, 0) for l in g) > 1.25 * M]   # one mildly slow lap is not enough
    def spread(lap):   # time between the leader and 5th place crossing the line at the end of this lap
        e = sorted(lapst[n][lap][0] + lapst[n][lap][1] for n in lapst if lap in lapst[n]); return e[4] - e[0] if len(e) > 4 else None
    def is_neutral(g):   # a safety car bunches the field up; rain or a slow track only slows everyone down
        if any(lap_med.get(l, 0) > 3.0 * M for l in g): return True
        a, b = spread(max(1, g[0] - 1)), spread(g[-1])
        return a is not None and b is not None and (b < 0.6 * a or b < 6.0)
    groups = [g for g in groups if is_neutral(g)]
    for g in groups:
        if g[0] not in lapst[leader]: continue
        red = any(lap_med[l] > 3.0 * M for l in g)
        s0 = lapst[leader][g[0]][0] + 5; s1 = lapst[leader][g[-1]][0] + (lapst[leader][g[-1]][1] if g[-1] in lapst[leader] else 60) * 0.5
        if red:
            rc += [{"date": iso(s0), "category": "Flag", "flag": "RED", "scope": "Track", "message": "RED FLAG (estimated from lap times)", "lap_number": g[0], "driver_number": None},
                   {"date": iso(s1), "category": "Flag", "flag": "GREEN", "scope": "Track", "message": "TRACK CLEAR", "lap_number": g[-1], "driver_number": None}]
        else:
            rc += [{"date": iso(s0), "category": "SafetyCar", "flag": None, "scope": None, "message": "SAFETY CAR DEPLOYED (estimated from lap times)", "lap_number": g[0], "driver_number": None},
                   {"date": iso(s1), "category": "SafetyCar", "flag": None, "scope": None, "message": "SAFETY CAR IN THIS LAP", "lap_number": g[-1], "driver_number": None}]
    fin = {int(r["number"]) for r in results if FIN(r)}
    # ---- synthetic car positions
    PL = 0.035; SIDE = 1.0
    def loc(n):
        out = []; laps = lapst.get(n, {}); g = grid.get(n) or 22
        gf = -(80.0 * (g - 1) + 150.0) / lap_len
        x, y = at_d(gf); t = start - 25
        while t < start: out.append({"date": iso(t), "x": float(x), "y": float(y)}); t += 0.5
        pits = pit_by.get(n, {}); last = None
        for lap in sorted(laps):
            s, d = laps[lap]; e = s + d; inl = lap in pits and lap > 1; outl = (lap - 1) in pits and lap > 2
            du_in = (pits.get(lap) or 22.0) if inl else 0.0; du_out = (pits.get(lap - 1) or 22.0) if outl else 0.0
            a0 = s + du_out / 2; a1 = e - du_in / 2
            f0 = t_of_d(PL) if outl else 0.0; f1 = t_of_d(1 - PL) if inl else 1.0
            tt = s
            while tt < e:
                if tt < a0 or tt >= a1:   # in the pit lane: either the second half (out-lap start) or first half (in-lap end) of the visit
                    if tt < a0: u = 0.5 + 0.5 * (tt - s) / max(du_out / 2, 0.1)
                    else: u = 0.5 * (tt - a1) / max(du_in / 2, 0.1)
                    gu = 0.5 * u / 0.4 if u < 0.4 else (0.5 if u < 0.6 else 0.5 + 0.5 * (u - 0.6) / 0.4)
                    fpos = -PL + 2 * PL * gu; side = min(1.0, min(u, 1 - u) / 0.12)
                    px, py = at_d(fpos); nv = normal_at(fpos) * 70 * SIDE * side
                    out.append({"date": iso(tt), "x": float(px + nv[0]), "y": float(py + nv[1])})
                else:
                    u = (tt - a0) / max(a1 - a0, 0.1)
                    if lap == 1: px, py = at_d(gf + (1 - gf) * float(np.interp(u, rt, df)))
                    else: px, py = at_t(f0 + (f1 - f0) * u)
                    out.append({"date": iso(tt), "x": float(px), "y": float(py)})
                tt += 0.5
            last = e
        if last is not None:
            px, py = at_t(0.0) if n in fin else at_t(0.5)
            for k in range(8): out.append({"date": iso(last + k * 0.5), "x": float(px), "y": float(py)})
        return out
    # ---- positions and gaps at every lap end (official running order)
    pos_ev, int_ev = [], []
    for n in grid: pos_ev.append({"date": iso(start - 20), "driver_number": n, "position": grid[n] or 22})
    for lap in sorted({l for n in lapst for l in lapst[n]}):
        rows = sorted((lapst[n][lap][0] + lapst[n][lap][1], n) for n in lapst if lap in lapst[n]); lead = rows[0][0]; prev = None
        for k, (te, n) in enumerate(rows):
            pos_ev.append({"date": iso(te), "driver_number": n, "position": k + 1})
            int_ev.append({"date": iso(te), "driver_number": n, "gap_to_leader": round(te - lead, 3) if k else 0, "interval": round(te - prev, 3) if prev else 0}); prev = te
    session_result = []
    for r in results:
        cl = r["positionText"].isdigit()
        session_result.append({"driver_number": int(r["number"]), "position": int(r["position"]) if cl else None, "number_of_laps": int(r["laps"]), "points": float(r["points"]),
            "dnf": not FIN(r) and r["positionText"] not in ("D",), "dsq": r["positionText"] == "D", "dns": int(r["laps"]) == 0 and not lapst.get(int(r["number"])),
            "gap_to_leader": None, "duration": int(r["Time"]["millis"]) / 1000 if r.get("Time") else None})
    drivers = [{"driver_number": int(r["number"]), "name_acronym": r["Driver"].get("code") or r["Driver"]["familyName"][:3].upper(), "first_name": r["Driver"]["givenName"],
                "last_name": r["Driver"]["familyName"], "team_name": r["Constructor"]["name"], "team_colour": COL.get(r["Constructor"]["constructorId"], "888888")} for r in results]
    laps_o = [{"driver_number": n, "lap_number": lap, "date_start": iso(s), "lap_duration": d, "is_pit_out_lap": (lap - 1) in pit_by.get(n, {})} for n in lapst for lap, (s, d) in lapst[n].items()]
    stints, pits = [], []
    for n in lapst:
        sl = 1
        for lap in sorted(pit_by.get(n, {})):
            stints.append({"driver_number": n, "lap_start": sl, "lap_end": lap, "compound": "UNKNOWN", "tyre_age_at_start": 0}); sl = lap + 1
            if lap in lapst[n] and lap + 1 in lapst[n]:
                du = pit_by[n][lap] or 22.0; pits.append({"driver_number": n, "lap_number": lap, "date": iso(lapst[n][lap + 1][0] + du / 2), "stop_duration": None, "lane_duration": du})
        stints.append({"driver_number": n, "lap_start": sl, "lap_end": max(lapst[n] or [1]), "compound": "UNKNOWN", "tyre_age_at_start": 0})
    DATA = {"drivers": drivers, "laps": laps_o, "session_result": session_result, "position": pos_ev, "intervals": int_ev, "stints": stints, "pit": pits, "race_control": rc, "weather": []}
    build_race.get = lambda ep, **kw: loc(kw["driver_number"]) if ep == "location" else [dict(x) for x in DATA.get(ep, [])]
    sk = Y * 100 + rnd; cname = circ_name or R["Circuit"]["Location"]["locality"]
    meta = {"name": R["raceName"], "circuit": cname, "location": R["Circuit"]["Location"]["locality"], "country": R["Circuit"]["Location"]["country"], "date": R["date"]}
    sys.stdout = open(os.devnull, "w")
    try: info = build_race.build(sk, meta, rnd, OUT)
    finally: sys.stdout = sys.__stdout__
    p = f"{OUT}/{sk}.bin"; b = gzip.decompress(open(p, "rb").read()); hl = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + hl])
    h["est"] = [[0, h["n"] * h["dt"]]]
    h["lap_note"] = "Estimated replay: positions come from official lap times (no car GPS exists for this season)" + (f"; {note}" if note else "") + ". Safety cars and red flags are worked out from lap times (virtual safety cars may be missed); tyre compounds aren't recorded."
    h["lap_note_until"] = 0
    hb = json.dumps(h, separators=(",", ":")).encode(); raw = gzip.compress(struct.pack("<I", len(hb)) + hb + b[4 + hl:], 9)
    os.remove(p); open(f"{OUT}/{sk}.mp3", "wb").write(raw)
    # ---- extras: standings, qualifying, retirement reasons, official fastest lap
    q = []
    for x in quali:
        q.append([int(x["number"]), int(x["position"]), x.get("Q1"), x.get("Q2"), x.get("Q3"), x["Driver"].get("code") or x["Driver"]["familyName"][:3].upper()])
    stt = {int(r["number"]): r["status"] for r in results if not FIN(r)}
    flo = next(([int(r["number"]), int(r["FastestLap"]["lap"]), r["FastestLap"]["Time"]["time"], r["FastestLap"].get("AverageSpeed", {}).get("speed")] for r in results if r.get("FastestLap", {}).get("rank") == "1"), None)
    extras[str(sk)] = {"cd": cd, "ct": ct, "q": q, "st": stt, "flo": flo}
    o = h["outline"][::max(1, len(h["outline"]) // 90)]; xs = [a[0] for a in o]; ys = [-a[1] for a in o]; sc = 100 / max(max(xs) - min(xs), max(ys) - min(ys))
    w = next((d for d in h["drivers"] if d["result"]["position"] == 1), None)
    idx_races.append({"session_key": sk, "round": rnd, **meta, "code": CC.get(R["Circuit"]["Location"]["country"], R["Circuit"]["Location"]["country"][:3].upper()),
        "winner": w["code"] if w else "", "laps": h["total_laps"], "drivers": len(h["drivers"]), "file": f"{PRE}data/{sk}.mp3",
        "thumb": [[round((a - min(xs)) * sc, 1), round((c - min(ys)) * sc, 1)] for a, c in zip(xs, ys)], "winner_colour": w["colour"] if w else "#8590a8",
        "extra_file": f"{PRE}extra.mp3", "estimated": True})
    print(Y, rnd, R["raceName"], "→", info["winner"], f"{len(raw) // 1024} KB", f"{len(groups)} neutralised period(s)", "(outline: f1-circuits)" if not circ_name else "", flush=True)
# ---- season files
ix_path = f"{SITE}/{Y}/index.json"
old = json.load(open(ix_path)) if os.path.exists(ix_path) and ONLY else {"races": []}
keep = {r["session_key"]: r for r in old["races"]}; keep.update({r["session_key"]: r for r in idx_races})
races = sorted(keep.values(), key=lambda r: r["round"])
json.dump({"season": Y, "races": races, "sprints": [], "quali": [], "upcoming": [], "previews": []}, open(ix_path, "w"), separators=(",", ":"), ensure_ascii=False)
xp = f"{SITE}/{Y}/extra.mp3"; allx = json.loads(gzip.decompress(open(xp, "rb").read())) if os.path.exists(xp) and ONLY else {}; allx.update(extras)
open(xp, "wb").write(gzip.compress(json.dumps(allx, separators=(",", ":")).encode(), 9, mtime=0))
# season.json: cumulative points per driver after every round (sprint points included in their round)
drv, rounds, tot = {}, [], {}
for R in sched:
    rnd = int(R["round"]); D = f"{J}/{Y}/{rnd:02d}"
    if not os.path.exists(f"{D}/results.json"): continue
    res = json.load(open(f"{D}/results.json")); spr = json.load(open(f"{D}/sprint.json")) if os.path.exists(f"{D}/sprint.json") else []
    w = next((r for r in res if r["position"] == "1"), None)
    rounds.append({"label": "R%02d %s" % (rnd, CC.get(R["Circuit"]["Location"]["country"], "")), "name": R["raceName"], "kind": "gp", "winner": w["Driver"].get("code") if w else ""})
    for r in spr + res:
        c = r["Driver"].get("code") or r["Driver"]["familyName"][:3].upper()
        e = drv.setdefault(c, {"code": c, "name": f"{r['Driver']['givenName']} {r['Driver']['familyName']}", "team": r["Constructor"]["name"], "colour": "#" + COL.get(r["Constructor"]["constructorId"], "888888"), "pts": {}})
        e["team"] = r["Constructor"]["name"]; e["colour"] = "#" + COL.get(r["Constructor"]["constructorId"], "888888"); e["pts"][len(rounds) - 1] = e["pts"].get(len(rounds) - 1, 0) + float(r["points"])
for e in drv.values():
    c = 0; arr = []
    for i in range(len(rounds)): c += e["pts"].get(i, 0); arr.append(c)
    e["pts"] = arr
json.dump({"rounds": rounds, "drivers": sorted(drv.values(), key=lambda e: -e["pts"][-1])}, open(f"{SITE}/{Y}/season.json", "w"), separators=(",", ":"))
print("season", Y, len(races), "races;", "standings:", [(d["code"], d["pts"][-1]) for d in sorted(drv.values(), key=lambda e: -e["pts"][-1])[:3]])
