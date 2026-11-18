"""Build Grid-Replay.html, the small launcher page for the split offline version (no data inside).
usage: launcher.py <page> <out>   - put grid-replay-YYYY.js files (standalone.py with SPLIT_JS=1) next to it."""
import sys
page = open(sys.argv[1]).read()
i = page.index("<script>\n(() => {")
import base64, os
st_f = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "stats.json")   # the stats hub's data, small enough to live in the page
emb = ('window.__EMBED["stats.json"] = "' + base64.b64encode(open(st_f, "rb").read()).decode() + '";') if os.path.exists(st_f) else ""
page = page[:i] + "<script>window.__SPLIT = 1; window.__EMBED = window.__EMBED || {};" + emb + "</script>\n" + page[i:]
head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style>')
cut = page.index("<div class=\"app\"")
out = head + page[:cut] + "</head><body>" + page[cut:] + "</body></html>"
if len(sys.argv) > 3:   # optional brand name for the offline page, e.g. "F1 Unleashed" (zips then named F1_Unleashed-YYYY.zip)
    b = sys.argv[3]; z = b.replace(" ", "_").upper()
    out = (out.replace("<title>Grid Replay 2026</title>", f"<title>{b}</title>").replace('class="brand-name">GRID REPLAY<', f'class="brand-name">{b.upper()}<')
              .replace("Grid Replay ${", f"{b} ${{").replace("GRID-REPLAY-${S.y} ZIP", f"{z}-${{S.y}} ZIP"))
open(sys.argv[2], "w").write(out)
print(sys.argv[2])
