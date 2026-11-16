"""Download one race from the OpenF1 API and pack it into a compact replay file.

Output: <out>/<session_key>.bin  (gzip of: u32 header_len | header JSON | int16 deltas)
Positions are resampled to a fixed 0.5 s grid per driver, delta-encoded along time.
"""
import gzip, json, struct, subprocess, sys, time
import numpy as np

API = "https://api.openf1.org/v1"
DT = 0.5


def get(ep, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{API}/{ep}?{q}"
    for attempt in range(6):
        p = subprocess.run(["curl", "-sS", "-m", "300", "-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
        body, _, code = p.stdout.rpartition("\n")
        if code == "200":
            time.sleep(0.35)
            return json.loads(body)
        if code == "404":
            return []
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"failed {url}: {code} {body[:200]}")


def ts(s):
    """ISO date list -> epoch seconds (float64)."""
    a = np.array([x[:26].replace("+00:00", "").rstrip("+") for x in s], dtype="datetime64[us]")
    return a.astype("int64") / 1e6


def t1(s):
    return float(ts([s])[0]) if s else None


def build(session_key, meeting, rnd, out_dir):
    drivers = get("drivers", session_key=session_key)
    laps = get("laps", session_key=session_key)
    result = get("session_result", session_key=session_key)
    if not laps or not result:
        print("  no laps/result, skip")
        return None

    # --- time window -------------------------------------------------------
    lap1 = [t1(l["date_start"]) for l in laps if l["lap_number"] == 1 and l["date_start"]]
    if not lap1:   # lap 1 start missing: estimate it from lap 2 starts and lap 1 durations
        lap2 = [t1(l["date_start"]) for l in laps if l["lap_number"] == 2 and l["date_start"]]
        d1 = sorted(l["lap_duration"] for l in laps if l["lap_number"] == 1 and l["lap_duration"]) or [100.0]
        if not lap2: print("  no lap timing, skip"); return None
        lap1 = [min(lap2) - d1[0]]
    T0 = min(lap1) - 25.0
    ends = []
    for l in laps:
        if l["date_start"] and l["lap_duration"]:
            ends.append(t1(l["date_start"]) + l["lap_duration"])
    chequer = max(ends)
    T1 = chequer + 50.0
    N = int((T1 - T0) / DT) + 1
    grid = T0 + np.arange(N) * DT

    res_by = {r["driver_number"]: r for r in result}
    total_laps = max((r["number_of_laps"] or 0) for r in result)
    drv = []
    seen = set()
    for d in drivers:
        n = d["driver_number"]
        if n in seen:
            continue
        seen.add(n)
        r = res_by.get(n)
        if r is None or r.get("dns"):
            continue
        drv.append(d)
    drv.sort(key=lambda d: d["driver_number"])

    # --- positions -----------------------------------------------------------
    pos = np.zeros((len(drv), N, 2), dtype=np.int32)
    missing = []          # per driver: [[i0, i1], ...] sample ranges with no data
    track_src = {}
    for di, d in enumerate(drv):
        n = d["driver_number"]
        loc = get("location", session_key=session_key, driver_number=n)
        loc = [p for p in loc if not (p["x"] == 0 and p["y"] == 0)]
        if len(loc) < 10:
            missing.append([[0, N]])
            continue
        t = ts([p["date"] for p in loc])
        x = np.array([p["x"] for p in loc], float)
        y = np.array([p["y"] for p in loc], float)
        o = np.argsort(t, kind="stable"); t, x, y = t[o], x[o], y[o]
        track_src[n] = (t, x, y)
        gx = np.interp(grid, t, x); gy = np.interp(grid, t, y)
        # nearest raw sample distance -> mask long holes
        idx = np.clip(np.searchsorted(t, grid), 1, len(t) - 1)
        near = np.minimum(np.abs(t[idx] - grid), np.abs(t[idx - 1] - grid))
        bad = (near > 4.0) | (grid < t[0] - 1) | (grid > t[-1] + 1)
        pos[di, :, 0] = np.round(gx); pos[di, :, 1] = np.round(gy)
        rng = []
        i = 0
        b = bad.tolist()
        while i < N:
            if b[i]:
                j = i
                while j < N and b[j]:
                    j += 1
                rng.append([i, j]); i = j
            else:
                i += 1
        missing.append(rng)
        print(f"  loc {d['name_acronym']}: {len(loc)} pts")

    span = int(np.abs(pos).max()) if pos.size else 1
    scale = max(1, int(np.ceil(span / 30000)))
    q = (pos // scale).astype(np.int32)
    delta = np.diff(q, axis=1, prepend=0)
    delta = np.clip(delta, -32767, 32767).astype("<i2")

    # --- track outline: winner's quickest clean lap --------------------------
    winner = next((r["driver_number"] for r in result if r["position"] == 1), drv[0]["driver_number"])
    cands = []
    for l in laps:
        if l["lap_duration"] and l["date_start"] and l["lap_number"] > 1 and not l["is_pit_out_lap"]:
            cands.append(l)
    cands.sort(key=lambda l: (l["driver_number"] != winner, l["lap_duration"]))
    outline = []
    for l in cands[:12]:
        src = track_src.get(l["driver_number"])
        if not src:
            continue
        t, x, y = src
        s = t1(l["date_start"]); e = s + l["lap_duration"]
        m = (t >= s - 0.3) & (t <= e + 0.3)
        if m.sum() > 60:
            outline = [[int(a) // scale, int(b) // scale] for a, b in zip(x[m], y[m])]
            break

    def rel(s):
        return round(t1(s) - T0, 2)

    # --- laps per driver ------------------------------------------------------
    lap_starts = {}
    best = []
    for l in sorted(laps, key=lambda l: (l["date_start"] or "")):
        if not l["date_start"]:
            continue
        lap_starts.setdefault(l["driver_number"], []).append([l["lap_number"], rel(l["date_start"])])
    fl = None
    timed = [l for l in laps if l["lap_duration"] and l["date_start"]]
    timed.sort(key=lambda l: t1(l["date_start"]) + l["lap_duration"])
    for l in timed:
        if fl is None or l["lap_duration"] < fl:
            fl = l["lap_duration"]
            best.append([round(t1(l["date_start"]) + l["lap_duration"] - T0, 2), l["driver_number"], l["lap_duration"], l["lap_number"]])

    # --- timing ---------------------------------------------------------------
    position = get("position", session_key=session_key)
    position.sort(key=lambda p: p["date"])
    pos_ev = [[rel(p["date"]), p["driver_number"], p["position"]] for p in position]

    ints = get("intervals", session_key=session_key)
    gaps = {}
    for it in ints:
        n = it["driver_number"]
        def enc(v):
            if v is None: return None
            if isinstance(v, str):
                try: return -int(v.strip("+").split()[0])
                except Exception: return None
            return round(float(v), 3)
        gaps.setdefault(n, []).append([rel(it["date"]), enc(it["gap_to_leader"]), enc(it["interval"])])
    for v in gaps.values():
        v.sort(key=lambda r: r[0])

    stints = [[s["driver_number"], s["lap_start"], s["lap_end"], s["compound"], s["tyre_age_at_start"]]
              for s in get("stints", session_key=session_key)]
    pits = [[rel(p["date"]), p["driver_number"], p["lap_number"], p.get("stop_duration"), p.get("lane_duration") or p.get("pit_duration")]
            for p in get("pit", session_key=session_key) if p["date"]]

    rc_raw = get("race_control", session_key=session_key)
    from stewards import stewards as _stew
    stew = _stew(rc_raw, T0)
    rc = []
    for r in rc_raw:
        msg = r["message"] or ""; cat = r["category"]; flag = r["flag"]
        kind = None
        if cat == "SafetyCar":
            if "VIRTUAL" in msg:
                kind = "VSC_END" if "ENDING" in msg else "VSC"
            else:
                kind = "SC_END" if ("IN THIS LAP" in msg or "ENDING" in msg) else "SC"
        elif cat == "Flag" and flag == "RED":
            kind = "RED"
        elif cat == "Flag" and flag == "CHEQUERED":
            kind = "CHQ"
        elif cat == "Flag" and flag == "GREEN" and r["scope"] == "Track":
            kind = "GREEN"
        elif cat == "Flag" and flag == "CLEAR" and r["scope"] == "Track":
            kind = "CLEAR"
        elif "PENALTY" in msg and "NO FURTHER" not in msg:
            kind = "PEN"
        elif "INCIDENT INVOLVING" in msg and "NOTED" in msg:
            kind = "INC"
        elif "RETIRED" in msg or "STOPPED" in msg or "CRASH" in msg or "COLLISION" in msg:
            kind = "INFO"
        if kind:
            rc.append([rel(r["date"]), kind, msg])
    rc.sort(key=lambda r: r[0])

    weather = [[rel(w["date"]), w["air_temperature"], w["track_temperature"], w["rainfall"], w.get("humidity"), w.get("wind_speed"), w.get("wind_direction")]
               for w in get("weather", session_key=session_key)]
    weather = [w for w in weather if -1800 < w[0] < T1 - T0 + 600]

    # retirement time: end of last completed lap (+ small margin)
    out_t = {}
    for d in drv:
        n = d["driver_number"]; r = res_by[n]
        if r.get("dnf") or r.get("dsq"):
            ls = [l for l in laps if l["driver_number"] == n and l["date_start"]]
            if ls:
                last = max(ls, key=lambda l: l["lap_number"])
                out_t[n] = round(t1(last["date_start"]) + (last["lap_duration"] or 60) - T0, 1)
            else:
                out_t[n] = 30.0

    header = {
        "v": 1, "session_key": session_key, "round": rnd,
        "meeting": meeting, "T0": T0, "dt": DT, "n": N, "scale": scale,
        "total_laps": total_laps, "chequer": round(chequer - T0, 2),
        "drivers": [{
            "num": d["driver_number"], "code": d["name_acronym"],
            "first": d["first_name"], "last": d["last_name"],
            "team": d["team_name"], "colour": "#" + (d["team_colour"] or "888888"),
            "missing": missing[i], "out": out_t.get(d["driver_number"]),
            "result": {k: res_by[d["driver_number"]].get(k) for k in ("position", "number_of_laps", "points", "dnf", "dsq", "gap_to_leader", "duration")},
        } for i, d in enumerate(drv)],
        "outline": outline, "laps": lap_starts, "best": best,
        "positions": pos_ev, "gaps": gaps, "stints": stints, "pits": pits,
        "rc": rc, "weather": weather, "stew": stew,
    }
    hb = json.dumps(header, separators=(",", ":")).encode()
    blob = struct.pack("<I", len(hb)) + hb + delta.tobytes()
    path = f"{out_dir}/{session_key}.bin"
    with open(path, "wb") as f:
        f.write(gzip.compress(blob, 9))
    winner_code = next((d["name_acronym"] for d in drv if d["driver_number"] == winner), "")
    return {"file": f"data/{session_key}.bin", "winner": winner_code, "laps": total_laps,
            "drivers": len(drv), "bytes": len(gzip.compress(blob, 9))}


if __name__ == "__main__":
    sk = int(sys.argv[1]); out = sys.argv[2]
    print(build(sk, {"name": "test"}, 0, out))
