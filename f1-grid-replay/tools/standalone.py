"""Build a single offline HTML file: page + index + race data embedded."""
import json, sys
src, idx_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
page = open(src).read()
idx = json.load(open(idx_path)); base = idx_path.rsplit('/', 1)[0]
# optional 4th arg: season prefix such as "2025/" (index paths already carry it; files live under the site root)
pre = sys.argv[4] if len(sys.argv) > 4 else ""
sbase = base
if pre: base = base[: -len(pre.rstrip("/"))].rstrip("/") or "."
emb = {pre + "index.json": json.dumps(idx, separators=(',', ':'))}
for r in idx["races"] + idx.get("sprints", []):
    fb = open(f"{base}/{r['file']}", "rb").read()
    emb[r["file"]] = fb.decode() if r["file"].endswith(".txt") else __import__("base64").b64encode(fb).decode()
    if r.get("radio_file"):
        import base64
        emb[r["radio_file"]] = base64.b64encode(open(f"{base}/{r['radio_file']}", "rb").read()).decode()
import base64 as _b64, os as _os2
# optional: COMM_DIR=comm/<year> embeds pre-rendered commentary packs (<sk>.mp3) for every race that has one
cd = _os2.environ.get("COMM_DIR")
if cd:
    for r in idx["races"] + idx.get("sprints", []):
        f = f"{cd}/{r['session_key']}.mp3"
        if _os2.path.exists(f):
            r["comm_file"] = f"{pre}comm/{r['session_key']}.mp3"; emb[r["comm_file"]] = _b64.b64encode(open(f, "rb").read()).decode()
    for q in idx.get("quali", []) + idx.get("previews", []):   # qualifying commentary packs live in <COMM_DIR>q/
        f = f"{cd}q/{q['session_key']}.mp3"
        if _os2.path.exists(f):
            q["comm_file"] = f"{pre}comm/{q['session_key']}.mp3"; emb[q["comm_file"]] = _b64.b64encode(open(f, "rb").read()).decode()
    emb[pre + "index.json"] = json.dumps(idx, separators=(',', ':'))
for q in idx.get("quali", []) + idx.get("previews", []):
    emb[q["file"]] = _b64.b64encode(open(f"{base}/{q['file']}", "rb").read()).decode()
import os as _os
if _os.path.exists(f"{sbase}/season.json"): emb[pre + "season.json"] = _b64.b64encode(open(f"{sbase}/season.json", "rb").read()).decode()
if _os.environ.get("SPLIT_JS"):   # split offline mode: write only this season's data, as a script the launcher page loads
    open(out, "w").write("window.__EMBED = Object.assign(window.__EMBED || {}, " + json.dumps(emb) + ");\n")
    print(out, _os.path.getsize(out) // 1024, "KB"); sys.exit(0)
embed = "<script>window.__EMBED = " + json.dumps(emb) + ";</script>\n"
i = page.index("<script>\n(() => {")
page = page[:i] + embed + page[i:]
head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
        'body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style>')
# move <title>/<meta>/<link>/<style> block into head
cut = page.index("<div class=\"app\"")
open(out, "w").write(head + page[:cut] + "</head><body>" + page[cut:] + "</body></html>")
print(out, len(open(out).read()) // 1024, "KB")
