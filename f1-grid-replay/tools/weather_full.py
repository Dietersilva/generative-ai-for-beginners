"""Replace each race's weather rows with the full feed: [t, air, track, rain, humidity, wind m/s, wind dir]."""
import gzip, json, struct, sys, os, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_race import get
ts = lambda s: datetime.datetime.fromisoformat(s).timestamp()
for f in sys.argv[1:]:
    raw = gzip.decompress(open(f, "rb").read()); n = struct.unpack("<I", raw[:4])[0]; h = json.loads(raw[4:4 + n]); body = raw[4 + n:]
    w = get("weather", session_key=h["session_key"])
    rows = [[round(ts(x["date"]) - h["T0"], 1), x["air_temperature"], x["track_temperature"], x["rainfall"], x.get("humidity"), x.get("wind_speed"), x.get("wind_direction")] for x in w]
    h["weather"] = [r for r in sorted(rows) if -1800 < r[0] < h["n"] * h["dt"] + 600]
    hb = json.dumps(h, separators=(",", ":")).encode()
    open(f, "wb").write(gzip.compress(struct.pack("<I", len(hb)) + hb + body, 9))
    print(os.path.basename(f), len(h["weather"]), "rows", flush=True)
