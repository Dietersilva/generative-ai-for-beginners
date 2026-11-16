"""Re-encode a radio pack's clips as 24 kbps mono MP3 (speech quality) to roughly halve its size.
usage: python3 tools/shrink_radio.py in.mp3|bin out.mp3   (pack = u32 header_len | JSON [{t,num,off,len,text}] | mp3 clips)"""
import json, struct, subprocess, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read(); n = struct.unpack("<I", b[:4])[0]; items = json.loads(b[4:4 + n]); body = b[4 + n:]
out, blob = [], bytearray()
for c in items:
    clip = body[c["off"]:c["off"] + c["len"]]
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "mp3", "-i", "pipe:0", "-ac", "1", "-ar", "22050", "-b:a", "24k", "-f", "mp3", "pipe:1"], input=clip, capture_output=True)
    new = p.stdout if p.returncode == 0 and len(p.stdout) > 500 and len(p.stdout) < len(clip) else clip
    out.append({**c, "off": len(blob), "len": len(new)}); blob += new
hb = json.dumps(out, separators=(",", ":"), ensure_ascii=False).encode()
open(dst, "wb").write(struct.pack("<I", len(hb)) + hb + bytes(blob))
print(src, len(b) // 1024, "->", (4 + len(hb) + len(blob)) // 1024, "KB")
