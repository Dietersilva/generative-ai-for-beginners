"""Transcribe every packed team-radio clip with Whisper; writes text into each radio pack's header."""
import json, struct, sys, os, tempfile, glob, subprocess
import numpy as np
from faster_whisper import WhisperModel
model = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)
dirs = sys.argv[1:] or ["out/radio", "out_sprint/radio"]
tmp = tempfile.mkdtemp()
for path in sorted(p for d in dirs for p in glob.glob(f"{d}/*.bin")):
    raw = open(path, "rb").read(); n = struct.unpack("<I", raw[:4])[0]; items = json.loads(raw[4:4 + n]); body = raw[4 + n:]
    if all("text" in c for c in items): continue
    for c in items:
        if "text" in c: continue
        f = f"{tmp}/c.mp3"; open(f, "wb").write(body[c["off"]:c["off"] + c["len"]])
        pcm = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout, np.float32)
        segs, _ = model.transcribe(pcm, language="en", beam_size=5, vad_filter=True,
                                   initial_prompt="Formula 1 team radio. Box box, push, tyres, safety car, DRS, gap, copy, mate, Lewis, Max, Lando, Charles, George, Kimi.")
        c["text"] = " ".join(s.text.strip() for s in segs).strip()
    hb = json.dumps(items, separators=(",", ":")).encode()
    open(path, "wb").write(struct.pack("<I", len(hb)) + hb + body)
    print(os.path.basename(path), len(items), "clips | e.g.", repr(items[0]["text"][:80]), flush=True)
print("TRANSCRIBE DONE", flush=True)
