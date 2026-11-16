"""Render a commentary script (from tools/commscript.js) to audio with Piper and pack it like a radio pack.
usage: build_comm.py script.json out.mp3 [bitrate=20k]
Pack: u32 header_len | JSON [{t,pri,who,e,text,radio?,off,len}] | concatenated MP3 clips.
Voices (rhasspy/piper-voices): lead = en_GB northern_english_male medium (CC BY-SA 4.0 data),
analyst = en_GB alba medium (CC BY 4.0 data)."""
import io, json, os, re, struct, subprocess, sys, wave
from piper import PiperVoice, SynthesisConfig
V = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "piper_voices")
src, dst = sys.argv[1], sys.argv[2]; br = sys.argv[3] if len(sys.argv) > 3 else "20k"
_cache = {}
def voice(w):
    if w not in _cache: _cache[w] = PiperVoice.load(f"{V}/en_GB-{'northern_english_male' if w == 'L' else 'alba'}-medium.onnx")
    return _cache[w]
SAY = {"Piastri": "Pee-astri", "Bortoleto": "Bortoletto"}   # Piper says the other names well as written
def speakable(t):
    t = re.sub(r"\bP(\d+)\b", r"P \1", t)
    for k, v in SAY.items(): t = re.sub(rf"\b{k}\b", v, t)
    return t
lines = json.load(open(src)); out, blob = [], bytearray()
for x in lines:
    cfg = SynthesisConfig(length_scale={2: 0.88, 1: 0.97, 0: 1.04}.get(x.get("e", 1), 1.0), noise_scale=0.75 if x.get("e") == 2 else 0.667)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w: voice(x["who"]).synthesize_wav(speakable(x["text"]), w, syn_config=cfg)
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "wav", "-i", "pipe:0", "-af", "volume=1.6" if x["who"] == "L" else "volume=1.4",
                        "-ac", "1", "-ar", "22050", "-b:a", br, "-f", "mp3", "pipe:1"], input=buf.getvalue(), capture_output=True)
    if p.returncode or len(p.stdout) < 200: print("skip", x["text"][:40]); continue
    out.append({**x, "off": len(blob), "len": len(p.stdout)}); blob += p.stdout
hb = json.dumps(out, separators=(",", ":"), ensure_ascii=False).encode()
open(dst, "wb").write(struct.pack("<I", len(hb)) + hb + bytes(blob))
print(os.path.basename(dst), len(out), "lines", (4 + len(hb) + len(blob)) // 1024, "KB")
