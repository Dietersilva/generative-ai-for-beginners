"""Merge the embedded data of several standalone builds into one file: combine.py out.html first.html other.html ..."""
import json, sys
out, first, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
M = "window.__EMBED = "
def split(s):
    i = s.index(M) + len(M); j = s.index(";</script>", i); return s[:i], json.loads(s[i:j]), s[j:]
a, emb, b = split(open(first).read())
for f in rest:
    _, e, _ = split(open(f).read())
    clash = set(e) & set(emb); assert not clash, clash
    emb.update(e)
open(out, "w").write(a + json.dumps(emb) + b)
print(out, len(emb), "entries")
