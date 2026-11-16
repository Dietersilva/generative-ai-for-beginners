"""Build a single offline HTML file: page + index + race data embedded."""
import json, sys
src, idx_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
page = open(src).read()
idx = json.load(open(idx_path)); base = idx_path.rsplit('/', 1)[0]
emb = {"index.json": json.dumps(idx, separators=(',', ':'))}
for r in idx["races"] + idx.get("sprints", []):
    emb[r["file"]] = open(f"{base}/{r['file']}").read()
    if r.get("radio_file"):
        import base64
        emb[r["radio_file"]] = base64.b64encode(open(f"{base}/{r['radio_file']}", "rb").read()).decode()
import base64 as _b64
for q in idx.get("quali", []) + idx.get("previews", []):
    emb[q["file"]] = _b64.b64encode(open(f"{base}/{q['file']}", "rb").read()).decode()
import os as _os
if _os.path.exists(f"{base}/season.json"): emb["season.json"] = _b64.b64encode(open(f"{base}/season.json", "rb").read()).decode()
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
