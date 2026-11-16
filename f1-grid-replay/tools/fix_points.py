"""Recompute championship points from finishing positions where OpenF1's points field is wrong.
Rules for 2019-2024: race 25-18-15-12-10-8-6-4-2-1 plus 1 for the fastest lap if the driver finishes in the
top 10; sprint (2022+) 8-7-6-5-4-3-2-1. usage: fix_points.py <work dir>   (rewrites race/data/*.bin and publish/data/*.txt)"""
import base64, gzip, json, struct, sys
W = sys.argv[1]; idx = json.load(open(f"{W}/publish/index.json"))
RACE = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]; SPR = [8, 7, 6, 5, 4, 3, 2, 1]
changed = 0
for r in idx["races"] + idx.get("sprints", []):
    sk = r["session_key"]; f = f"{W}/race/data/{sk}.bin"; b = gzip.decompress(open(f, "rb").read())
    n = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + n]); rest = b[4 + n:]
    spr = r.get("kind") == "sprint"; table = SPR if spr else RACE
    fl = h["best"][-1][1] if h.get("best") and not spr else None
    diffs = []
    for d in h["drivers"]:
        res = d["result"]; p = res.get("position")
        pts = float(table[p - 1]) if isinstance(p, int) and p <= len(table) and not res.get("dsq") else 0.0
        if fl == d["num"] and isinstance(p, int) and p <= 10: pts += 1
        if (res.get("points") or 0) != pts: diffs.append(f"{d['code']} {res.get('points')}->{pts}"); res["points"] = pts
    if diffs:
        changed += 1; print(r["name"], "sprint" if spr else "race", ", ".join(diffs))
        hb = json.dumps(h, separators=(",", ":")).encode(); raw = gzip.compress(struct.pack("<I", len(hb)) + hb + rest, 9)
        open(f, "wb").write(raw); open(f"{W}/publish/data/{sk}.txt", "w").write(base64.b64encode(raw).decode())
print("events changed:", changed)
