"""Build stats.json for the STATS hub from a site dir (every season's index, race packs and qualifying files).
usage: build_stats.py <site dir> [out]   (default <site dir>/stats.json)"""
import base64, gzip, json, os, struct, sys
root = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else f"{root}/stats.json"
SEASONS = [(2026, ""), (2025, "2025/"), (2024, "2024/"), (2023, "2023/")]
def raw(path):
    b = open(f"{root}/{path}", "rb").read()
    if path.endswith(".txt"): b = base64.b64decode(b)
    if b[:2] == b"\x1f\x8b": b = gzip.decompress(b)
    return b
def header(path):
    b = raw(path)
    if b[:1] == b"{": return json.loads(b)
    n = struct.unpack("<I", b[:4])[0]; return json.loads(b[4:4 + n])
events, drivers, teams = [], {}, {}
for y, pre in SEASONS:
    ix = f"{root}/{pre}index.json"
    if not os.path.exists(ix): continue
    idx = json.load(open(ix))
    for r in idx["races"] + idx.get("sprints", []):
        h = header(r["file"]); kind = "sprint" if r.get("kind") == "sprint" else "gp"
        lo = min((v[0][1] for v in h["laps"].values() if v and v[0][0] == 1), default=25)
        grid = {}
        for t, num, pos in h["positions"]:
            if t <= lo - 1: grid[num] = pos
        res = []
        for d in h["drivers"]:
            x = d["result"]; drivers[d["code"]] = {"name": f"{d['first']} {d['last'].title() if d['last'].isupper() else d['last']}", "colour": d["colour"], "team": d["team"], "y": y}
            teams.setdefault(d["team"], d["colour"])
            res.append([d["code"], d["team"], grid.get(d["num"]), x.get("position") if isinstance(x.get("position"), int) else None,
                        x.get("points") or 0, 1 if x.get("dnf") else 0, 1 if x.get("dsq") else 0, x.get("number_of_laps") or 0])
        bynum = {d["num"]: d for d in h["drivers"]}
        fl = h["best"][-1] if h.get("best") else None
        pits = [[bynum[p[1]]["code"], bynum[p[1]]["team"], round(p[3], 2), p[2]] for p in h["pits"] if p[1] in bynum and isinstance(p[3], (int, float)) and 1.5 < p[3] < 15]
        events.append({"y": y, "rd": r["round"], "kind": kind, "name": r["name"], "circuit": r.get("circuit"), "date": r["date"], "laps": h.get("total_laps"),
                       "res": res, "fl": [bynum[fl[1]]["code"], round(fl[2], 3)] if fl and fl[1] in bynum else None, "pits": pits})
    for q in idx.get("quali", []):
        h = header(q["file"]); kind = "squali" if q.get("kind") == "squali" else "quali"
        res = [[d["code"], d["team"], d.get("pos") if isinstance(d.get("pos"), int) else None, round(d["time"], 3) if d.get("time") else None] for d in h["drivers"]]
        events.append({"y": y, "rd": q["round"], "kind": kind, "name": q["name"], "circuit": q.get("circuit"), "date": q["date"], "res": res})
events.sort(key=lambda e: (e["date"], {"squali": 0, "sprint": 1, "quali": 2, "gp": 3}[e["kind"]]))
latest = {}
for c, v in drivers.items(): latest[c] = v
json.dump({"built": "2023-2026", "drivers": latest, "teams": teams, "events": events}, open(out, "w"), separators=(",", ":"), ensure_ascii=False)
print(out, len(events), "events,", len(latest), "drivers,", os.path.getsize(out) // 1024, "KB")
