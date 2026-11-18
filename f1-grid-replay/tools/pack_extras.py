"""Pack extras/<sk>.json (from fetch_extras.py) into ONE gzip file per season, <prefix>extra.mp3 = {"<sk>": {...}, ...},
and set "extra_file" (that path) on each race/sprint in the season index. One file per season keeps the online artifact
under its 511-file limit. usage: pack_extras.py <site dir> <extras dir>"""
import gzip, json, os, sys
root, src = sys.argv[1], sys.argv[2]; tot = n = 0
for pre in ("", "2025/", "2024/", "2023/"):
    ix = f"{root}/{pre}index.json"
    if not os.path.exists(ix): continue
    idx = json.load(open(ix)); bundle = {}; rel = f"{pre}extra.mp3"
    for r in idx["races"] + idx.get("sprints", []):
        f = f"{src}/{r['session_key']}.json"
        if os.path.exists(f): bundle[str(r["session_key"])] = json.load(open(f)); r["extra_file"] = rel
        else: r.pop("extra_file", None)
    b = gzip.compress(json.dumps(bundle, separators=(",", ":")).encode(), 9, mtime=0)
    open(f"{root}/{rel}", "wb").write(b); tot += len(b); n += len(bundle)
    json.dump(idx, open(ix, "w"), separators=(",", ":"))
    print(rel, len(bundle), "sessions", round(len(b) / 1e6, 2), "MB")
print(n, "extras packed,", round(tot / 1e6, 2), "MB")
