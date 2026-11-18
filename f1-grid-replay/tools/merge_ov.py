"""Add on-track overtakes (from ovcollect.js) to stats.json: each gp/sprint event gets "ov": {code: [passes made, times passed]}.
usage: merge_ov.py <stats.json> <overtakes.json>   (run after build_stats.py)"""
import json, sys
st, ov = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])); n = 0
for e in st["events"]:
    k = f"{e['y']}|{e['kind']}|{e['name']}"
    if e["kind"] in ("gp", "sprint") and k in ov: e["ov"] = ov[k]["c"]; n += 1
json.dump(st, open(sys.argv[1], "w"), separators=(",", ":")); print(n, "events got overtakes")
