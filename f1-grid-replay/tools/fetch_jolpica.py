"""Download 2018-2022 race data from Jolpica (Ergast successor): schedule, results, qualifying, sprint results,
every lap's time and position, and pit stops. Resumable; paced to stay under Jolpica's rate limits (~450 requests/hour).
usage: fetch_jolpica.py <out dir> [years...]   -> <out>/<year>/<round>/{results,qualifying,sprint,laps,pitstops}.json"""
import json, os, subprocess, sys, time
out = sys.argv[1]; years = [int(y) for y in sys.argv[2:]] or [2022, 2021, 2020, 2019, 2018]
def get(path):
    for a in range(8):
        p = subprocess.run(["curl", "-sS", "-m", "90", "-w", "\n%{http_code}", f"https://api.jolpi.ca/ergast/f1/{path}"], capture_output=True, text=True)
        body, _, code = p.stdout.rpartition("\n"); time.sleep(8)
        if code == "200": return json.loads(body)["MRData"]
        time.sleep(30 * (a + 1) if code == "429" else 10)
    raise RuntimeError(f"{path} -> {code}")
def paged(path, key):
    rows, off = [], 0
    while True:
        m = get(f"{path}?limit=100&offset={off}"); races = m["RaceTable"]["Races"]
        if races: rows.extend(races[0].get(key, []))
        off += 100
        if off >= int(m["total"]): return rows
for y in years:
    os.makedirs(f"{out}/{y}", exist_ok=True); sf = f"{out}/{y}/schedule.json"
    if not os.path.exists(sf): json.dump(get(f"{y}.json")["RaceTable"]["Races"], open(sf, "w"))
    for r in json.load(open(sf)):
        d = f"{out}/{y}/{int(r['round']):02d}"; os.makedirs(d, exist_ok=True)
        for name, path, key in (("results", "results", "Results"), ("qualifying", "qualifying", "QualifyingResults"), ("sprint", "sprint", "SprintResults"), ("pitstops", "pitstops", "PitStops"), ("laps", "laps", "Laps")):
            f = f"{d}/{name}.json"
            if os.path.exists(f): continue
            try:
                rows = paged(f"{y}/{r['round']}/{path}.json", key)
                if name == "laps":   # laps come split across pages by lap: merge timings of the same lap
                    m = {}
                    for L in rows: m.setdefault(int(L["number"]), []).extend(L["Timings"])
                    rows = [{"number": k, "Timings": v} for k, v in sorted(m.items())]
                json.dump(rows, open(f, "w"))
            except Exception as e: print(y, r["round"], name, "FAILED", e, flush=True)
        print(y, r["round"], r["raceName"], "ok", flush=True)
print("JOLPICA DONE", flush=True)
