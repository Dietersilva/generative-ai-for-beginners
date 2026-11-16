"""Convert published race data from base64 text (data/*.txt) to raw binary served as data/*.mp3.
Artifacts only serve web media types, so the gzip pack travels under an audio extension, as the radio
packs already do; fetchBytes() reads it as bytes and spots the gzip header. Saves the 33% base64 overhead.
usage: binpack.py <site dir>   (every index.json under it is updated; old .txt files are deleted)"""
import base64, glob, json, os, sys
root = sys.argv[1]; moved = []
for ix in glob.glob(f"{root}/**/index.json", recursive=True):
    base = os.path.dirname(ix); i = json.load(open(ix)); pre = os.path.relpath(base, root); pre = "" if pre == "." else pre + "/"
    for r in i.get("races", []) + i.get("sprints", []):
        f = r.get("file", "")
        if not f.endswith(".txt"): continue
        src = f"{root}/{f}"; dst = src[:-4] + ".mp3"
        open(dst, "wb").write(base64.b64decode(open(src).read())); os.remove(src)
        r["file"] = f[:-4] + ".mp3"; moved.append(f)
    json.dump(i, open(ix, "w"), separators=(",", ":"), ensure_ascii=False)
print("converted", len(moved))
