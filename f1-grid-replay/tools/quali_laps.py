import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_quali import session_laps
for f in sorted(glob.glob("out_quali/[0-9]*.json")):
    q = json.load(open(f)); q.update(session_laps(q["session_key"]))
    json.dump(q, open(f, "w"), separators=(",", ":"))
    print(q["name"], q["session"], len(q["all"]), "laps, phases", [p[0] for p in q["phases"]], flush=True)
