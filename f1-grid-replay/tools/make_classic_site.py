"""Turn the main page into the Pit Wall Redux CLASSIC edition page (seasons built under <site>/<year>/).
usage: make_classic_site.py <main page> <site dir> [out page]   (default out: <site>/index.html)"""
import glob, json, os, shutil, sys
src, site = sys.argv[1], sys.argv[2]; out = sys.argv[3] if len(sys.argv) > 3 else f"{site}/index.html"
years = sorted((int(os.path.basename(os.path.dirname(f))) for f in glob.glob(f"{site}/*/index.json")), reverse=True)
s = open(src).read()
cfg = {"seasons": [{"y": y, "p": f"{y}/"} for y in years], "sub": "estimated replay", "name": "classic"}
s = s.replace("<title>Pit Wall Redux</title>", "<title>Pit Wall Redux Classic</title>", 1)
s = s.replace('class="brand-name">PIT WALL <span class="rx">REDUX</span><', 'class="brand-name">PIT WALL <span class="rx">REDUX</span> <span class="ed">CLASSIC</span><', 1)
s = s.replace(".brand-name .rx{", ".brand-name .ed{font-size:.55em;letter-spacing:.18em;color:var(--muted);font-style:normal;vertical-align:middle;border:1px solid var(--line);border-radius:4px;padding:1px 5px;margin-left:4px}\n.brand-name .rx{", 1)
s = s.replace("· Pit Wall Redux ${st.year", "· Pit Wall Redux Classic ${st.year")
i = s.index("<script>\n(() => {"); s = s[:i] + f"<script>window.__EDITION = {json.dumps(cfg)};</script>\n" + s[i:]
open(out, "w").write(s)
if os.path.exists("pub/stats.json") and os.path.abspath(site) != os.path.abspath("pub"): shutil.copy("pub/stats.json", f"{site}/stats.json")
print(out, "seasons", years)
