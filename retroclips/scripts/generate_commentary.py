#!/usr/bin/env python3
"""
Auto-generate the commentary blurb for one or all films in data/films.json.

This is the "auto generate commentary" half of the pipeline. It calls the
Claude API directly (stdlib only, no SDK dependency) with a prompt built
from the film's metadata and scene description, targeting a ~15-20
second read: roughly 45-65 words.

Requires an ANTHROPIC_API_KEY in the environment. Get one at
https://console.anthropic.com/ -- this script does not ship with one and
never should.

Usage:
    # Preview commentary for one film without touching films.json
    python3 scripts/generate_commentary.py --film-id nosferatu-1922

    # Regenerate every film's commentary and write the results back
    python3 scripts/generate_commentary.py --all --write

The existing hand-written commentary already in films.json is example
output for this prototype -- written in the same target style so the
site has real content while this script isn't wired to a live key. Once
you have a key, running this will produce comparable copy on demand for
new films you add.
"""

import argparse
import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILMS_JSON = ROOT / "data" / "films.json"

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-5"

PROMPT_TEMPLATE = """You are writing the commentary blurb for a single clip on RetroClips, \
a site that pairs 6-7 second clips from public-domain films with a short \
piece of commentary underneath.

Film: {title} ({year}), directed by {director}, {country} -- {genre}
Scene shown in the clip: {scene_label} -- {scene_description}

Write ONE paragraph of commentary, 45-65 words, that a viewer can read in \
15-20 seconds. It should teach something concrete and specific about this \
exact scene or shot (a production detail, a technique, its influence, a \
piece of trivia) -- not generic praise. Confident, plain-spoken, no \
marketing language, no exclamation points, no emoji. Output only the \
paragraph, nothing else."""


def call_claude(prompt: str, api_key: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read())
    return payload["content"][0]["text"].strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--film-id", help="generate for a single film id")
    parser.add_argument("--all", action="store_true", help="generate for every film in films.json")
    parser.add_argument("--write", action="store_true", help="write results back into films.json (default: print only)")
    args = parser.parse_args()

    if not args.film_id and not args.all:
        parser.error("pass --film-id <id> or --all")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set. Export it and re-run.")

    data = json.loads(FILMS_JSON.read_text())
    films = data["films"]
    targets = films if args.all else [f for f in films if f["id"] == args.film_id]
    if not targets:
        sys.exit(f"No film with id '{args.film_id}' in {FILMS_JSON}")

    for film in targets:
        prompt = PROMPT_TEMPLATE.format(
            title=film["title"], year=film["year"], director=film["director"],
            country=film["country"], genre=film["genre"],
            scene_label=film["scene_label"], scene_description=film["scene_description"],
        )
        commentary = call_claude(prompt, api_key)
        word_count = len(commentary.split())
        print(f"\n{film['title']} ({film['year']}) -- {word_count} words")
        print(commentary)
        if args.write:
            film["commentary"] = commentary

    if args.write:
        FILMS_JSON.write_text(json.dumps(data, indent=2) + "\n")
        print(f"\nWrote updated commentary to {FILMS_JSON}")


if __name__ == "__main__":
    main()
