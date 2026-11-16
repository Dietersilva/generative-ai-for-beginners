"""Fastest lap of every driver in each 2026 qualifying session, with its on-track path."""
import json, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_race import get
os.makedirs("out_quali", exist_ok=True)
def tyre_for(stints, num, lap):
    for st in stints:
        if st["driver_number"] == num and st["lap_start"] <= lap <= (st["lap_end"] or 999):
            return {"compound": st["compound"], "tyre_age": (st["tyre_age_at_start"] or 0) + lap - st["lap_start"]}
    return {}
ts = lambda s: datetime.datetime.fromisoformat(s).timestamp()
iso = lambda e: datetime.datetime.fromtimestamp(e, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
if __name__ == "__main__":
    meetings = {m["meeting_key"]: m for m in get("meetings", year=2026)}
    gp = {r["name"]: r["round"] for r in json.load(open("out/index.json"))["races"]}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(); index = []
    sessions = [s for s in get("sessions", year=2026) if s["session_name"] in ("Qualifying", "Sprint Qualifying") and not s.get("is_cancelled") and s["date_end"] < now]
    for s in sorted(sessions, key=lambda s: s["date_start"]):
        sk = s["session_key"]; m = meetings[s["meeting_key"]]; path = f"out_quali/{sk}.json"
        kind = "squali" if s["session_name"] == "Sprint Qualifying" else "quali"
        entry = {"session_key": sk, "kind": kind, "round": gp.get(m["meeting_name"], 0), "name": m["meeting_name"], "circuit": m["circuit_short_name"],
                 "code": m["country_code"], "date": s["date_start"][:10], "file": f"quali/{sk}.json"}
        if os.path.exists(path):
            q = json.load(open(path)); entry["pole"] = q["drivers"][0]["code"]; index.append(entry); continue
        print(s["session_name"], m["meeting_name"], sk, flush=True)
        drivers = {d["driver_number"]: d for d in get("drivers", session_key=sk)}
        res = {r["driver_number"]: r for r in get("session_result", session_key=sk)}
        laps = get("laps", session_key=sk); best = {}
        stints = get("stints", session_key=sk)
        for l in laps:
            if l["lap_duration"] and l["date_start"] and not l["is_pit_out_lap"] and (l["driver_number"] not in best or l["lap_duration"] < best[l["driver_number"]]["lap_duration"]):
                best[l["driver_number"]] = l
        out = []
        for num, l in best.items():
            d = drivers.get(num); r = res.get(num, {})
            if not d: continue
            a = ts(l["date_start"]); b = a + l["lap_duration"]
            loc = [p for p in get("location", **{"session_key": sk, "driver_number": num, "date>": iso(a - 2), "date<": iso(b + 2)}) if p["x"] or p["y"]]
            pts = [[round(ts(p["date"]) - a, 2), p["x"], p["y"]] for p in sorted(loc, key=lambda p: p["date"])]
            dur = r.get("duration"); phase = sum(1 for x in dur if x) if isinstance(dur, list) else 0
            out.append({"num": num, "code": d["name_acronym"], "first": d["first_name"], "last": d["last_name"], "team": d["team_name"],
                        "colour": "#" + (d["team_colour"] or "888888"), "pos": r.get("position") if isinstance(r.get("position"), int) else None, "phase": phase,
                        "time": l["lap_duration"], "lap": l["lap_number"], "sectors": [l["duration_sector_1"], l["duration_sector_2"], l["duration_sector_3"]],
                        "pts": pts, **tyre_for(stints, num, l["lap_number"])})
        out.sort(key=lambda d: (d["pos"] if isinstance(d["pos"], int) else 99, d["time"]))
        if not out: continue
        json.dump({"session_key": sk, "kind": kind, "name": m["meeting_name"], "session": s["session_name"], "drivers": out}, open(path, "w"), separators=(",", ":"))
        entry["pole"] = out[0]["code"]; index.append(entry)
        print("  drivers", len(out), "pts", sum(len(d["pts"]) for d in out), flush=True)
    json.dump(index, open("out_quali/index.json", "w"), indent=1)
    print("QUALI DONE", flush=True)



def session_laps(sk, get_fn=None):
    """Every timed lap of a qualifying session + when Q1/Q2/Q3 started (seconds from session start)."""
    import datetime as _dt
    g = get_fn or get
    tsx = lambda s: _dt.datetime.fromisoformat(s).timestamp()
    sess = g("sessions", session_key=sk)[0]; t0 = tsx(sess["date_start"])
    stints = g("stints", session_key=sk); laps = g("laps", session_key=sk)
    allv = []
    for l in laps:
        if not (l["lap_duration"] and l["date_start"]): continue
        tyre = tyre_for(stints, l["driver_number"], l["lap_number"])
        allv.append([l["driver_number"], l["lap_number"], round(tsx(l["date_start"]) + l["lap_duration"] - t0, 1), l["lap_duration"],
                     tyre.get("compound"), 1 if l["is_pit_out_lap"] else 0])
    phases = {}
    for r in g("race_control", session_key=sk):
        k = r.get("qualifying_phase")
        if k and k not in phases: phases[k] = round(tsx(r["date"]) - t0, 1)
    return {"all": sorted(allv, key=lambda v: v[2]), "phases": sorted([[k, v] for k, v in phases.items()])}
