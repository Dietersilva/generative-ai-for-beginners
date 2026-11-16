"""Assemble the publishable folder: pub/index.json, pub/data/<sk>.txt (base64 race data), pub/radio/<sk>.mp3 (radio pack)."""
import base64, gzip, json, os, shutil, struct
idx = json.load(open("out/index.json"))
os.makedirs("pub/data", exist_ok=True); os.makedirs("pub/radio", exist_ok=True)
races = []
for r in idx["races"]:
    sk = r["session_key"]; raw = open(f"out/{r['file']}", "rb").read()
    open(f"pub/data/{sk}.txt", "w").write(base64.b64encode(raw).decode())
    b = gzip.decompress(raw); n = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + n])
    o = h["outline"]; thumb = []
    if len(o) > 20:
        o = o[::max(1, len(o) // 90)]; xs = [p[0] for p in o]; ys = [-p[1] for p in o]
        sc = 100 / max(max(xs) - min(xs), max(ys) - min(ys)); ox = (100 - (max(xs) - min(xs)) * sc) / 2; oy = (100 - (max(ys) - min(ys)) * sc) / 2
        thumb = [[round((x - min(xs)) * sc + ox, 1), round((y - min(ys)) * sc + oy, 1)] for x, y in zip(xs, ys)]
    w = next((d for d in h["drivers"] if d["result"]["position"] == 1), None)
    e = {k: r[k] for k in ("session_key", "round", "name", "circuit", "location", "country", "code", "date", "winner", "laps", "drivers")}
    e.update(file=f"data/{sk}.txt", thumb=thumb, winner_colour=w["colour"] if w else "#8590a8")
    if r.get("radio") and os.path.exists(f"out/radio/{sk}.bin"):
        shutil.copy(f"out/radio/{sk}.bin", f"pub/radio/{sk}.mp3"); e.update(radio=r["radio"], radio_file=f"radio/{sk}.mp3")
    races.append(e)
up = [dict(u, pending=False) for u in json.load(open("upcoming.json"))]
json.dump({"season": 2026, "races": races, "upcoming": up}, open("pub/index.json", "w"), separators=(",", ":"))
tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk("pub") for f in fs)
print(len(races), "races,", sum(1 for r in races if r.get("radio")), "with radio, total", round(tot / 1e6, 1), "MB")

# ---- sprints + qualifying
idx2 = json.load(open("pub/index.json"))
sprints = []
if os.path.exists("out_sprint/index.json"):
    for r in json.load(open("out_sprint/index.json"))["races"]:
        sk = r["session_key"]; raw = open(f"out_sprint/data/{sk}.bin", "rb").read()
        open(f"pub/data/{sk}.txt", "w").write(base64.b64encode(raw).decode())
        e = {k: r.get(k) for k in ("session_key", "round", "name", "circuit", "location", "country", "code", "date", "winner", "laps", "drivers")}
        e.update(kind="sprint", file=f"data/{sk}.txt")
        if r.get("radio") and os.path.exists(f"out_sprint/radio/{sk}.bin"):
            shutil.copy(f"out_sprint/radio/{sk}.bin", f"pub/radio/{sk}.mp3"); e.update(radio=r["radio"], radio_file=f"radio/{sk}.mp3")
        sprints.append(e)
quali = []
if os.path.exists("out_quali/index.json"):
    os.makedirs("pub/quali", exist_ok=True)
    for q in json.load(open("out_quali/index.json")):
        shutil.copy(f"out_quali/{q['session_key']}.json", f"pub/quali/{q['session_key']}.json"); quali.append(q)
idx2["sprints"] = sprints; idx2["quali"] = quali
json.dump(idx2, open("pub/index.json", "w"), separators=(",", ":"))
print(len(sprints), "sprints,", len(quali), "qualifying sessions")
if os.path.exists("out_quali/previews.json"):
    pv = json.load(open("out_quali/previews.json"))
    for p in pv: shutil.copy(f"out_quali/{os.path.basename(p['file'])}", f"pub/{p['file']}")
    idx2["previews"] = pv; json.dump(idx2, open("pub/index.json", "w"), separators=(",", ":")); print(len(pv), "previews")

# ---- season standings (cumulative points after each GP and sprint)
def season_from(idx2):
    events = sorted(idx2["races"] + idx2.get("sprints", []), key=lambda r: (r["date"], r.get("kind") != "sprint"))
    drivers, rounds = {}, []
    for k, r in enumerate(events):
        src = f"out/data/{r['session_key']}.bin" if r.get("kind") != "sprint" else f"out_sprint/data/{r['session_key']}.bin"
        b = gzip.decompress(open(src, "rb").read()); n = struct.unpack("<I", b[:4])[0]; h = json.loads(b[4:4 + n])
        rounds.append({"label": ("R%02d " % r["round"]) + r.get("code", ""), "name": r["name"], "kind": r.get("kind") or "gp", "winner": r.get("winner")})
        for d in h["drivers"]:
            e = drivers.setdefault(d["code"], {"code": d["code"], "name": f"{d['first']} {d['last']}", "team": d["team"], "colour": d["colour"], "pts": [0.0] * len(events)})
            e["team"], e["colour"] = d["team"], d["colour"]
            e["pts"][k] = float(d["result"].get("points") or 0)
    for e in drivers.values():
        c = 0
        for i, p in enumerate(e["pts"]): c += p; e["pts"][i] = c
    return {"rounds": rounds, "drivers": sorted(drivers.values(), key=lambda e: -e["pts"][-1])}
season = season_from(idx2)
json.dump(season, open("pub/season.json", "w"), separators=(",", ":"))
print("season:", len(season["rounds"]), "events; leader", season["drivers"][0]["code"], season["drivers"][0]["pts"][-1])
