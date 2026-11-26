#!/bin/bash
# Full backup in parts of at most ~24 MB: online files + tools (make_backup_parts.sh), then guide/dev tools,
# original-quality radio and the raw Miami 2025 data. Output: backup/parts/Grid-Replay-backup-NN-*.zip
set -e
cd "$(dirname "$0")/.."
./tools/make_backup_parts.sh >/dev/null
[ -f backup/parts/Grid-Replay-backup-1-tools-scripts-readme.zip ] && mv backup/parts/Grid-Replay-backup-1-tools-scripts-readme.zip backup/parts/Grid-Replay-backup-01-tools-scripts-readme.zip
python3 - <<'PY'
import glob, os, re, shutil, zipfile
parts = "backup/parts"; LIM = 24e6
n = max(int(re.search(r"backup-(\d+)-", f).group(1)) for f in glob.glob(f"{parts}/*.zip")) + 1
def nm(name): global n; f = f"{parts}/Grid-Replay-backup-{n:02d}-{name}.zip"; n += 1; return f
x = "backup/x6"; shutil.rmtree(x, ignore_errors=True); os.makedirs(f"{x}/dev-tools"); shutil.copy("PROJECT-GUIDE.md", x)
for f in glob.glob("tools/*"):
    if os.path.isfile(f): shutil.copy(f, f"{x}/dev-tools/")
if os.path.exists("pt_hook.html"): shutil.copy("pt_hook.html", f"{x}/dev-tools/page-with-test-hook.html")
shutil.copytree("/home/user/generative-ai-for-beginners/f1-grid-replay", f"{x}/code-from-git")
with zipfile.ZipFile(nm("guide-and-dev-tools"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as Z:
    for d, _, fs in os.walk(x):
        for f in fs: p = os.path.join(d, f); Z.write(p, os.path.relpath(p, x))
for y in ("2026", "2025", "2024", "2023"):
    fs = sorted(glob.glob(f"radio_orig/{y}/*")); cur, s, k = [], 0, 1
    def emit(cur, k):
        with zipfile.ZipFile(nm(f"original-radio-{y}-{k}"), "w", zipfile.ZIP_STORED) as Z:
            for f in cur: Z.write(f, f.replace("radio_orig", "original-radio"))
    for f in fs:
        z = os.path.getsize(f)
        if cur and s + z > LIM: emit(cur, k); k += 1; cur, s = [], 0
        cur.append(f); s += z
    if cur: emit(cur, k)
with zipfile.ZipFile(nm("raw-miami-2025"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as Z:
    for d, _, fs in os.walk("raw2025"):
        for f in fs: p = os.path.join(d, f); Z.write(p, p.replace("raw2025", "raw-openf1-miami-2025"))
# Classic edition (2018-2022): the online site, in parts of at most ~24 MB
fs = sorted(os.path.join(d, f) for d, _, ff in os.walk("classic") for f in ff if not f.startswith("_")); cur, s, k = [], 0, 1
def emit_c(cur, k):
    with zipfile.ZipFile(nm(f"classic-online-{k}"), "w", zipfile.ZIP_STORED) as Z:
        for f in cur: Z.write(f, f.replace("classic", "classic-online", 1))
for f in fs:
    z = os.path.getsize(f)
    if cur and s + z > LIM: emit_c(cur, k); k += 1; cur, s = [], 0
    cur.append(f); s += z
if cur: emit_c(cur, k)
# raw source data: Jolpica 2018-2022 laps, 1950-2022 history, circuit outlines (MIT), OpenF1 extras
with zipfile.ZipFile(nm("raw-data-jolpica-history-extras"), "w", zipfile.ZIP_DEFLATED, compresslevel=9) as Z:
    for root in ("old/jolpica", "old/alltime", "old/circuits", "extras"):
        for d, _, ff in os.walk(root):
            for f in ff: p = os.path.join(d, f); Z.write(p, "raw-data/" + p)
PY
cd backup/parts && for f in *.zip; do unzip -tq "$f" >/dev/null || echo "BAD $f"; done
ls -la *.zip | awk '{s+=$5; if($5>m)m=$5; n++} END {printf "%d parts, %.0f MB total, largest %.1f MB\n", n, s/1e6, m/1e6}'
