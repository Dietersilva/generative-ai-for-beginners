"""Pack each race's team radio clips into out/radio/<session_key>.bin
Format: u32 header_len | header JSON [{t,num,off,len}] | concatenated mp3 bytes (not gzipped)."""
import gzip, json, os, re, struct, subprocess, sys, tempfile, urllib.parse, datetime
sys.path.insert(0, os.path.dirname(__file__))
from build_race import get, t1
out = sys.argv[1]
os.makedirs(f"{out}/radio", exist_ok=True)
idx = json.load(open(f"{out}/index.json"))
tmp = tempfile.mkdtemp()
for r in idx["races"]:
    sk = r["session_key"]; path = f"{out}/radio/{sk}.bin"
    if os.path.exists(path) or r.get("radio") == 0:
        continue
    b = gzip.decompress(open(f"{out}/{r['file']}", "rb").read())
    n = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + n]); T0 = h["T0"]
    hh, mm, ss = (int(x) for x in (r.get("gmt_offset") or "00:00:00").lstrip("-").split(":"))
    off = (hh * 3600 + mm * 60 + ss) * (-1 if (r.get("gmt_offset") or "").startswith("-") else 1)
    clips = get("team_radio", session_key=sk)
    items, blobs, pos = [], [], 0
    for c in clips:
        url = c["recording_url"]
        m = re.search(r"_(\d{8})_(\d{6})\.mp3$", url)
        if m:
            local = datetime.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").replace(tzinfo=datetime.timezone.utc)
            t = local.timestamp() - off - T0
        else:
            t = t1(c["date"]) - T0
        if t < -120 or t > h["chequer"] + 300:
            continue
        src = f"{tmp}/a.mp3"; dst = f"{tmp}/b.mp3"
        q = urllib.parse.quote(url, safe=":/")
        if subprocess.run(["curl", "-sS", "-f", "-m", "60", "-o", src, q]).returncode:
            continue
        if subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "32000", "-b:a", "48k", dst]).returncode:
            continue
        data = open(dst, "rb").read()
        items.append({"t": round(t, 2), "num": c["driver_number"], "off": pos, "len": len(data)})
        blobs.append(data); pos += len(data)
    items.sort(key=lambda i: i["t"])
    if not items:
        r["radio"] = 0
    else:
        hb = json.dumps(items, separators=(",", ":")).encode()
        open(path, "wb").write(struct.pack("<I", len(hb)) + hb + b"".join(blobs))
        r["radio"] = len(items); r["radio_file"] = f"radio/{sk}.bin"
    print(r["name"], "clips", r["radio"], "bytes", pos, flush=True)
    json.dump(idx, open(f"{out}/index.json", "w"), indent=1)
print("RADIO DONE")
