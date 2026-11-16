"""Build Grid-Replay.html, the small launcher page for the split offline version (no data inside).
usage: launcher.py <page> <out>   - put grid-replay-YYYY.js files (standalone.py with SPLIT_JS=1) next to it."""
import sys
page = open(sys.argv[1]).read()
i = page.index("<script>\n(() => {")
page = page[:i] + "<script>window.__SPLIT = 1; window.__EMBED = window.__EMBED || {};</script>\n" + page[i:]
head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style>')
cut = page.index("<div class=\"app\"")
open(sys.argv[2], "w").write(head + page[:cut] + "</head><body>" + page[cut:] + "</body></html>")
print(sys.argv[2])
