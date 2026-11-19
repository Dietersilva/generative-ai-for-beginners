"""Download Formula 1 history 1950-2022 from Jolpica for the all-time stats: every race result, qualifying (where it
exists), sprint results, final driver and constructor standings, plus the 2023-2026 schedules (to match circuit names).
Resumable, paced under Jolpica's limit (~480 requests/hour). usage: fetch_alltime.py <out dir>"""
import json, os, subprocess, sys, time
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
def get(path):
    for a in range(10):
        p = subprocess.run(["curl", "-sS", "-m", "90", "-w", "\n%{http_code}", f"https://api.jolpi.ca/ergast/f1/{path}"], capture_output=True, text=True)
        body, _, code = p.stdout.rpartition("\n"); time.sleep(7.5)
        if code == "200": return json.loads(body)["MRData"]
        time.sleep(60 if code == "429" else 10)
    raise RuntimeError(f"{path} -> {code}")
def races_paged(path, key):   # rows come race by race; merge the pieces of a race split across pages
    races, off = {}, 0
    while True:
        m = get(f"{path}?limit=100&offset={off}")
        for r in m["RaceTable"]["Races"]:
            k = int(r["round"]); races.setdefault(k, {kk: v for kk, v in r.items() if kk != key}).setdefault(key, []).extend(r.get(key, []))
        off += 100
        if off >= int(m["total"]): return [races[k] for k in sorted(races)]
def save(name, fn):
    f = f"{out}/{name}.json"
    if os.path.exists(f): return
    try: json.dump(fn(), open(f, "w")); print(name, "ok", flush=True)
    except Exception as e: print(name, "FAILED", e, flush=True)
for y in (2023, 2024, 2025, 2026): save(f"schedule_{y}", lambda y=y: get(f"{y}.json")["RaceTable"]["Races"])
for y in range(1950, 2023):
    save(f"{y}_results", lambda y=y: races_paged(f"{y}/results.json", "Results"))
    if y >= 1994: save(f"{y}_qualifying", lambda y=y: races_paged(f"{y}/qualifying.json", "QualifyingResults"))
    if y >= 2021: save(f"{y}_sprint", lambda y=y: races_paged(f"{y}/sprint.json", "SprintResults"))
    save(f"{y}_drivers", lambda y=y: get(f"{y}/driverStandings.json")["StandingsTable"]["StandingsLists"])
    if y >= 1958: save(f"{y}_constructors", lambda y=y: get(f"{y}/constructorStandings.json")["StandingsTable"]["StandingsLists"])
print("ALLTIME DONE", flush=True)
