"""Download car telemetry (OpenF1 car_data: speed, throttle, brake, gear, rpm, drs) for every driver's
fastest qualifying lap. usage: fetch_qtele.py <site dir> <out dir>   (resumable: skips sessions already saved)
Output: <out>/<session_key>.json = {num: [[t*10, speed, throttle, brake, gear, drs, rpm/100], ...]} with t from lap start."""
import datetime, glob, gzip, json, os, struct, subprocess, sys, time
root, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
def get(ep, q):
    for a in range(6):
        p = subprocess.run(["curl", "-sS", "-m", "120", "-w", "\n%{http_code}", f"https://api.openf1.org/v1/{ep}?{q}"], capture_output=True, text=True)
        body, _, code = p.stdout.rpartition("\n")
        if code == "200": time.sleep(0.3); return json.loads(body)
        if code == "404": return []
        time.sleep(3 * (a + 1))
    raise RuntimeError(f"{ep} {q} -> {code}")
def load(f):
    b = open(f, "rb").read()
    if b[:2] == b"\x1f\x8b": b = gzip.decompress(b)
    if b[:1] == b"{": return json.loads(b)
    n = struct.unpack("<I", b[:4])[0]; return json.loads(b[4:4 + n])
files = sorted(set(glob.glob(f"{root}/quali/*") + glob.glob(f"{root}/20*/quali/*")), reverse=bool(os.environ.get("REV")))
files = [f for f in files if not os.path.basename(f).startswith("prev_")]   # previews reuse the full session's telemetry
done = 0
for f in files:
    q = load(f); sk = q["session_key"]; dst = f"{out}/{sk}.json"
    if os.path.exists(dst): continue
    try:
        laps = {(l["driver_number"], l["lap_number"]): l for l in get("laps", f"session_key={sk}")}
        res = {}
        for d in q["drivers"]:
            l = laps.get((d["num"], d["lap"]))
            if not l or not l.get("date_start"): continue
            a = datetime.datetime.fromisoformat(l["date_start"]); b = a + datetime.timedelta(seconds=d["time"] + 0.5)
            cd = get("car_data", f"session_key={sk}&driver_number={d['num']}&date>={a.isoformat()}&date<={b.isoformat()}")
            rows = []
            for c in sorted(cd, key=lambda c: c["date"]):
                t = (datetime.datetime.fromisoformat(c["date"]) - a).total_seconds()
                rows.append([round(t * 10), c.get("speed") or 0, c.get("throttle") or 0, c.get("brake") or 0, c.get("n_gear") or 0, c.get("drs") or 0, round((c.get("rpm") or 0) / 100)])
            if len(rows) > 20: res[d["num"]] = rows
        json.dump(res, open(dst, "w"), separators=(",", ":")); done += 1
        print(sk, q.get("name"), len(res), "drivers", flush=True)
    except Exception as e: print(sk, "FAILED", e, flush=True)
print("TELE DONE", done, flush=True)
