"""Package a past season's build (work<year>/publish) into pub/<year>/ with '<year>/'-prefixed paths.
usage: python3 tools/package2025.py [year]   (default 2025)"""
import gzip, json, os, shutil, struct, sys
Y = sys.argv[1] if len(sys.argv) > 1 else "2025"
SRC, DST, P = f"work{Y}/publish", f"pub/{Y}", f"{Y}/"
idx = json.load(open(f"{SRC}/index.json"))
SPRINT_KEYS = {9993, 10028} if Y == "2025" else set()   # 2025 China & Miami sprints mislabelled by the resume record
moved = [r for r in idx["races"] if r["session_key"] in SPRINT_KEYS]
idx["races"] = [r for r in idx["races"] if r["session_key"] not in SPRINT_KEYS]
for r in moved: r["kind"] = "sprint"
idx["sprints"] = sorted(idx.get("sprints", []) + moved, key=lambda r: r["date"])
idx.setdefault("upcoming", []); idx.setdefault("previews", [])
if os.path.exists(DST): shutil.rmtree(DST)
for sub in ("data", "radio", "quali"): shutil.copytree(f"{SRC}/{sub}", f"{DST}/{sub}")
for r in idx["races"] + idx["sprints"] + idx["quali"]:
    for k in ("file", "radio_file"):
        if r.get(k):
            assert os.path.exists(f"{SRC}/{r[k]}"), r[k]
            r[k] = P + r[k]

def season_from(idx):
    events = sorted(idx["races"] + idx["sprints"], key=lambda r: (r["date"], r.get("kind") != "sprint"))
    drivers, rounds = {}, []
    for k, r in enumerate(events):
        if r.get("_res"):
            rows = [(drv[x["driver_number"]]["name_acronym"], f"{drv[x['driver_number']]['first_name']} {drv[x['driver_number']]['last_name']}",
                     drv[x["driver_number"]]["team_name"], "#" + (drv[x["driver_number"]]["team_colour"] or "888888"), x.get("points") or 0) for x in res]
        else:
            b = gzip.decompress(open(f"work{Y}/race/data/{r['session_key']}.bin", "rb").read()); n = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + n])
            rows = [(d["code"], f"{d['first']} {d['last']}", d["team"], d["colour"], d["result"].get("points") or 0) for d in h["drivers"]]
        rounds.append({"label": ("R%02d " % r["round"]) + r.get("code", ""), "name": r["name"], "kind": r.get("kind") or "gp", "winner": r.get("winner")})
        for code, name, team, col, pts in rows:
            e = drivers.setdefault(code, {"code": code, "name": name, "team": team, "colour": col, "pts": [0.0] * len(events)})
            e["team"], e["colour"] = team, col
            e["pts"][k] = float(pts)
    for e in drivers.values():
        c = 0
        for i, p in enumerate(e["pts"]): c += p; e["pts"][i] = c
    return {"rounds": rounds, "drivers": sorted(drivers.values(), key=lambda e: -e["pts"][-1])}

season = season_from(idx)
json.dump(season, open(f"{DST}/season.json", "w"), separators=(",", ":"))
json.dump(idx, open(f"{DST}/index.json", "w"), separators=(",", ":"), ensure_ascii=False)
print("races", len(idx["races"]), "sprints", len(idx["sprints"]), "quali", len(idx["quali"]))
print("standings:", [(d["code"], d["pts"][-1]) for d in season["drivers"][:5]])

import subprocess; subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "binpack.py"), "pub"])   # data as binary
