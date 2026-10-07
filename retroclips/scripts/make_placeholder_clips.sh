#!/usr/bin/env bash
# Generates stand-in clip files for every film in data/films.json.
#
# These are NOT real movie footage. This sandbox's network policy blocks
# outbound access to archive.org (and every other general web host), so
# there is no way to fetch real public-domain source video from here.
# Each placeholder is a synthesized old-film-style loop (grain, vignette,
# flicker, title card) that is exactly the target 6-7s length, so the
# site's layout, playback, and pacing can be judged honestly before real
# clips are dropped in via fetch_clip.py.
#
# Run from the retroclips/ directory: bash scripts/make_placeholder_clips.sh

set -euo pipefail
cd "$(dirname "$0")/.."

OUT_DIR="assets/clips"
mkdir -p "$OUT_DIR"

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SMALL="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

jq -c '.films[]' data/films.json | while read -r film; do
  id=$(echo "$film" | jq -r '.id')
  title=$(echo "$film" | jq -r '.title')
  year=$(echo "$film" | jq -r '.year')
  duration=$(echo "$film" | jq -r '.clip.duration_sec')
  out="$OUT_DIR/${id}.mp4"

  echo "Generating placeholder for: $title ($year) -> $out"

  # Escape single quotes for drawtext
  safe_title=$(printf '%s' "$title" | sed "s/'/\\\\'/g")

  ffmpeg -nostdin -y -loglevel error \
    -f lavfi -i "color=c=black:s=854x480:r=24:d=${duration}" \
    -f lavfi -i "anoisesrc=d=${duration}:c=pink:r=44100:a=0.03" \
    -vf "noise=alls=25:allf=t+u,eq=brightness=0.03:contrast=1.1,vignette=PI/3.2,drawtext=fontfile=${FONT}:text='${safe_title}':fontcolor=white@0.92:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2-30,drawtext=fontfile=${FONT}:text='${year}':fontcolor=white@0.75:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2+30,drawtext=fontfile=${FONT_SMALL}:text='CLIP PLACEHOLDER -- see fetch_clip.py':fontcolor=#999999:fontsize=14:x=(w-text_w)/2:y=h-40,format=gray" \
    -c:v libx264 -pix_fmt yuv420p -crf 28 -preset veryfast \
    -c:a aac -b:a 64k -shortest \
    "$out"

  ffmpeg -nostdin -y -loglevel error -ss 1.5 -i "$out" -frames:v 1 -q:v 3 "$OUT_DIR/${id}.jpg"
done

echo "Done. Placeholder clips written to $OUT_DIR/"
