"""Pack qualifying files (quali/<sk>.json) as gzip binary: u32 header_len | JSON (drivers without pts) | int32 deltas
of every driver's [t*100, x, y] points, in driver order. Served as quali/<sk>.mp3 (the host only serves media types;
the page sees the gzip header). Lossless for the stored precision. usage: qpack.py <site dir>"""
import glob, gzip, json, os, struct, sys
import numpy as np
root = sys.argv[1]; n = saved = 0
for ix in glob.glob(f"{root}/**/index.json", recursive=True) + [f"{root}/index.json"]:
    if not os.path.exists(ix): continue
    i = json.load(open(ix)); changed = False
    for q in i.get("quali", []) + i.get("previews", []):
        f = q.get("file", "")
        if not f.endswith(".json") or not os.path.exists(f"{root}/{f}"): continue
        raw = open(f"{root}/{f}", "rb").read(); d = json.loads(raw); body = []
        for dr in d["drivers"]:
            p = np.array(dr.pop("pts") or [[0, 0, 0]], dtype=float); dr["np"] = len(dr.get("np", p)) if False else len(p)
            a = np.round(np.c_[p[:, 0] * 100, p[:, 1], p[:, 2]]).astype(np.int64); body.append(np.diff(a, axis=0, prepend=0).astype("<i4").tobytes())
        hb = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
        out = gzip.compress(struct.pack("<I", len(hb)) + hb + b"".join(body), 9)
        nf = f[:-5] + ".mp3"; open(f"{root}/{nf}", "wb").write(out); os.remove(f"{root}/{f}")
        q["file"] = nf; changed = True; n += 1; saved += len(raw) - len(out)
    if changed: json.dump(i, open(ix, "w"), separators=(",", ":"), ensure_ascii=False)
print("packed", n, "qualifying files, saved", round(saved / 1e6, 1), "MB")
