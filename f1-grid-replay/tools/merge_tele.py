"""Add qualifying telemetry (tele/<session_key>.json from fetch_qtele.py) to the packed qualifying files in a site dir.
Pack: gzip( u32 header_len | JSON header | int32 [t*100,x,y] point deltas per driver | int16 telemetry ) where the
telemetry is, per driver listed in header["tele_order"] with header["tele_n"] samples: six columns (t*10, speed km/h,
throttle %, brake, gear, drs), each delta-encoded, column after column. usage: merge_tele.py <site dir> <tele dir>"""
import glob, gzip, json, os, struct, sys
import numpy as np
root, td = sys.argv[1], sys.argv[2]; n = add = 0
for f in sorted(set(glob.glob(f"{root}/quali/*.mp3") + glob.glob(f"{root}/20*/quali/*.mp3"))):
    b = gzip.decompress(open(f, "rb").read()); hl = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + hl])
    npts = sum(d.get("np", 0) for d in h["drivers"]); pts = b[4 + hl: 4 + hl + npts * 12]
    tf = f"{td}/{h['session_key']}.json"
    h.pop("tele_order", None); h.pop("tele_n", None); body = b""
    if os.path.exists(tf):
        t = json.load(open(tf)); order = [d["num"] for d in h["drivers"] if str(d["num"]) in t]; parts = []
        for num in order:
            r = np.array(t[str(num)], dtype=np.int64)[:, :6]
            parts.append(np.diff(r.T, axis=1, prepend=0).astype("<i2").tobytes())
        h["tele_order"] = order; h["tele_n"] = [len(t[str(x)]) for x in order]; body = b"".join(parts); add += 1
    hb = json.dumps(h, separators=(",", ":"), ensure_ascii=False).encode()
    open(f, "wb").write(gzip.compress(struct.pack("<I", len(hb)) + hb + pts + body, 9)); n += 1
print("repacked", n, "qualifying files,", add, "with telemetry")
