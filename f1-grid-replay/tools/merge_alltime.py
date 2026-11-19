"""Add Formula 1 history 1950-2022 (from fetch_alltime.py) to stats.json, plus world champions 1950-today.
Run after build_stats.py and merge_ov.py. usage: merge_alltime.py <stats.json> <alltime dir>
- Drivers who also race in 2023+ keep their 3-letter key (so careers join up); others are keyed by archive id
  with a "code" for display. Points are as awarded at the time. Rows of drivers who failed to qualify,
  withdrew or did not start are left out, so "GPs" counts starts."""
import glob, json, os, sys, unicodedata
SP, A = sys.argv[1], sys.argv[2]; st = json.load(open(SP))
st["events"] = [e for e in st["events"] if e["y"] >= 2023]; st["champs"] = []
norm = lambda s: unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower().replace("-", " ")
modern = {k: v for k, v in st["drivers"].items()}
TEAM = {"red_bull": "Red Bull Racing", "haas": "Haas F1 Team", "alpine": "Alpine", "aston_martin": "Aston Martin", "alphatauri": "AlphaTauri", "alfa": "Alfa Romeo"}
def team(c):   # early constructors are listed as chassis-engine ("Lotus-Climax"): use the chassis maker
    i = c["constructorId"]
    if i in TEAM: return TEAM[i]
    n = c["name"].split("-")[0].strip() if "-" in i else c["name"]
    return {"Lotus": "Team Lotus"}.get(n, n)
keys = {}
def key(d):
    i = d["driverId"]
    if i in keys: return keys[i]
    c = d.get("code"); k = i
    if c and c in modern and norm(modern[c]["name"]).endswith(norm(d["familyName"])): k = c
    keys[i] = k
    if k not in st["drivers"]: st["drivers"][k] = {"name": f"{d['givenName']} {d['familyName']}", "code": c or norm(d["familyName"]).replace(" ", "")[:3].upper(), "colour": "#8590a8"}
    return k
def secs(t):
    if not t: return None
    p = t.split(":"); return round(float(p[0]) * 60 + float(p[1]), 3) if len(p) == 2 else round(float(p[0]), 3)
# circuit names: map archive circuit ids to the names used for 2023+ races (matched by date), else the town
cmap = {}
for f in glob.glob(f"{A}/schedule_*.json"):
    for r in json.load(open(f)):
        e = next((e for e in st["events"] if e["kind"] == "gp" and e["date"] == r["date"]), None)
        if e: cmap[r["Circuit"]["circuitId"]] = e["circuit"]
cname = lambda r: cmap.get(r["Circuit"]["circuitId"], r["Circuit"]["Location"]["locality"])
SKIP = ("Did not qualify", "Did not prequalify", "Withdrew", "Did not start", "Excluded")
hist = []
for y in range(1950, 2023):
    f = f"{A}/{y}_results.json"
    if not os.path.exists(f): continue
    for kind, src in (("gp", f), ("sprint", f"{A}/{y}_sprint.json")):
        if not os.path.exists(src): continue
        for r in json.load(open(src)):
            rows, fl = [], None
            for x in r.get("Results") or r.get("SprintResults") or []:
                if x["status"] in SKIP or x.get("positionText") in ("F", "W"): continue
                k = key(x["Driver"]); pt = x.get("positionText", "")
                rows.append([k, team(x["Constructor"]), int(x["grid"]) or None, int(pt) if pt.isdigit() else None, float(x["points"]),
                             1 if pt == "R" or pt == "N" else 0, 1 if pt == "D" else 0, int(x["laps"])])
                if x.get("FastestLap", {}).get("rank") == "1": fl = [k, secs(x["FastestLap"].get("Time", {}).get("time"))]
            best = {}   # shared drives (1950s): one row per driver, best finish, points added up
            for x in rows:
                o = best.get(x[0])
                if not o: best[x[0]] = x; continue
                pts = o[4] + x[4]; keep = x if (x[3] or 999) < (o[3] or 999) else o; keep = keep[:]; keep[4] = pts; keep[2] = min([g for g in (o[2], x[2]) if g] or [None]); best[x[0]] = keep
            rows = list(best.values())
            hist.append({"y": y, "rd": int(r["round"]), "kind": kind, "name": r["raceName"], "circuit": cname(r), "date": r["date"], "res": rows, "fl": fl, "pits": []})
    qf = f"{A}/{y}_qualifying.json"
    if os.path.exists(qf):
        for r in json.load(open(qf)):
            rows = [[key(x["Driver"]), team(x["Constructor"]), int(x["position"]), min([t for t in (secs(x.get(q)) for q in ("Q3", "Q2", "Q1")) if t] or [None], key=lambda v: v or 1e9)] for x in r["QualifyingResults"]]
            hist.append({"y": y, "rd": int(r["round"]), "kind": "quali", "name": r["raceName"], "circuit": cname(r), "date": r["date"], "res": rows})
    df, cf = f"{A}/{y}_drivers.json", f"{A}/{y}_constructors.json"
    if os.path.exists(df):
        ds = json.load(open(df))[0]["DriverStandings"][0]; cs = json.load(open(cf))[0]["ConstructorStandings"][0] if os.path.exists(cf) else None
        st["champs"].append({"y": y, "d": key(ds["Driver"]), "pts": float(ds["points"]), "wins": int(ds["wins"]), "team": team(cs["Constructor"]) if cs else None, "tpts": float(cs["points"]) if cs else None, "final": True})
# 2023 onward: from this app's own (OpenF1) results, which match the official tables
for y in sorted({e["y"] for e in st["events"]}):
    ev = [e for e in st["events"] if e["y"] == y and e["kind"] in ("gp", "sprint")]; P, W, T = {}, {}, {}
    for e in ev:
        for r in e["res"]:
            P[r[0]] = P.get(r[0], 0) + r[4]; T[r[1]] = T.get(r[1], 0) + r[4]
            if e["kind"] == "gp" and r[3] == 1: W[r[0]] = W.get(r[0], 0) + 1
    d = max(P, key=P.get); t = max(T, key=T.get)
    final = y < 2026 or any(e["kind"] == "gp" and "Abu Dhabi" in e["name"] for e in ev)
    st["champs"].append({"y": y, "d": d, "pts": P[d], "wins": W.get(d, 0), "team": t, "tpts": T[t], "final": final})
st["events"] = hist + st["events"]
json.dump(st, open(SP, "w"), separators=(",", ":"))
print(len(hist), "historic events,", len(st["drivers"]), "drivers,", len(st["champs"]), "seasons of champions,", os.path.getsize(SP) // 1024, "KB")
