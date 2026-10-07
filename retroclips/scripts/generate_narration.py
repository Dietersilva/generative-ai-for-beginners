#!/usr/bin/env python3
"""
Generate narration audio for each film's commentary using ElevenLabs TTS.

Requires ELEVENLABS_API_KEY in the environment -- get one at
https://elevenlabs.io/app/settings/api-keys. This script does not ship
with one and never should; it's read from the environment only, never
written to disk or committed.

Usage:
    # Generate narration for every film, using the voice in films.json
    python3 scripts/generate_narration.py

    # Regenerate just one film (e.g. after editing its commentary)
    python3 scripts/generate_narration.py --film-id nosferatu-1922

    # One-off test with a different voice, without touching films.json
    python3 scripts/generate_narration.py --voice-id <other_voice_id>

Writes one MP3 per film to assets/narration/<film-id>.mp3, matching the
ids in data/films.json. script.js plays these directly and only falls
back to the browser's built-in speech synthesis if a file is missing.

To change narrators permanently: edit `site.narration_voice_id` in
data/films.json and re-run with no --voice-id flag. That field is the
single source of truth for which voice this script defaults to.
"""

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILMS_JSON = ROOT / "data" / "films.json"
NARRATION_DIR = ROOT / "assets" / "narration"

API_URL_TEMPLATE = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def generate_one(film: dict, voice_id: str, api_key: str) -> pathlib.Path:
    body = json.dumps({
        "text": film["commentary"],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.35,
            "use_speaker_boost": True,
            "speed": 0.85,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL_TEMPLATE.format(voice_id=voice_id),
        data=body,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "content-type": "application/json",
            "accept": "audio/mpeg",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        audio = resp.read()

    NARRATION_DIR.mkdir(parents=True, exist_ok=True)
    out = NARRATION_DIR / f"{film['id']}.mp3"
    out.write_bytes(audio)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--voice-id",
        help="ElevenLabs voice ID to narrate with (default: site.narration_voice_id in films.json)",
    )
    parser.add_argument("--film-id", help="generate for a single film id (default: every film)")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY is not set. Export it and re-run.")

    data = json.loads(FILMS_JSON.read_text())

    voice_id = args.voice_id or data.get("site", {}).get("narration_voice_id")
    if not voice_id:
        sys.exit("No --voice-id given, and site.narration_voice_id isn't set in films.json.")

    films = data["films"]
    targets = films if not args.film_id else [f for f in films if f["id"] == args.film_id]
    if not targets:
        sys.exit(f"No film with id '{args.film_id}' in {FILMS_JSON}")

    print(f"Using voice: {voice_id}\n")
    for film in targets:
        print(f"Generating narration for {film['title']} ({film['year']})...")
        try:
            out = generate_one(film, voice_id, api_key)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            sys.exit(f"ElevenLabs API error {e.code} for '{film['id']}': {body}")
        print(f"  -> {out} ({out.stat().st_size} bytes)")

    print(f"\nDone. {len(targets)} narration file(s) written to {NARRATION_DIR}/")


if __name__ == "__main__":
    main()
