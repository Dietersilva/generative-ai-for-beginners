"""Build the 2025 Miami GP (10033) replay with GPS-reconstructed lap starts for laps 1-25.
Pit records are complete in OpenF1, but its stints for this race are off by a few laps, so stint
boundaries are rebuilt from the pit laps."""
import json, os, sys
TOOLS = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, TOOLS)
import build_race
D = "raw2025/mia"; real_get = build_race.get
laps = json.load(open(f"{D}/laps_fixed.json")); pits = json.load(open(f"{D}/pit.json"))
def fix_stints(st):
    out = []
    for n in {s["driver_number"] for s in st}:
        mine = sorted((s for s in st if s["driver_number"] == n), key=lambda s: s["stint_number"])
        pl = sorted(p["lap_number"] for p in pits if p["driver_number"] == n)
        if len(pl) == len(mine) - 1:
            for i, s in enumerate(mine):
                if i: s["lap_start"] = pl[i - 1] + 1
                if i < len(pl): s["lap_end"] = pl[i]
        out += mine
    return out
def get(ep, **kw):
    if kw.get("session_key") == 10033 and ep == "laps" and "driver_number" not in kw: return [dict(l) for l in laps]
    r = real_get(ep, **kw)
    return fix_stints(r) if kw.get("session_key") == 10033 and ep == "stints" else r
build_race.get = get
meta = {"name": "Miami Grand Prix", "circuit": "Miami", "location": "Miami Gardens", "country": "United States", "code": "USA", "date": "2025-05-04", "gmt_offset": "-04:00:00"}
os.makedirs("work_mia/race/data", exist_ok=True)
info = build_race.build(10033, meta, 6, "work_mia/race/data")
print(info)
json.dump([{"session_key": 10033, "round": 6, "kind": None, **meta, **info}], open("work_mia/race/partial.json", "w"))
