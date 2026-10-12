"""A self-contained 3x5 pixel font, so text stays crisp and no font file
(or font licence) is needed."""

from __future__ import annotations

from PIL import Image, ImageDraw

from .model import RGB

GLYPH_W, GLYPH_H = 3, 5
ADVANCE = GLYPH_W + 1

_GLYPHS = {
    "A": (".#.", "#.#", "###", "#.#", "#.#"),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "C": (".##", "#..", "#..", "#..", ".##"),
    "D": ("##.", "#.#", "#.#", "#.#", "##."),
    "E": ("###", "#..", "##.", "#..", "###"),
    "F": ("###", "#..", "##.", "#..", "#.."),
    "G": (".##", "#..", "#.#", "#.#", ".##"),
    "H": ("#.#", "#.#", "###", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "J": ("..#", "..#", "..#", "#.#", ".#."),
    "K": ("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": ("#..", "#..", "#..", "#..", "###"),
    "M": ("#.#", "###", "###", "#.#", "#.#"),
    "N": ("##.", "#.#", "#.#", "#.#", "#.#"),
    "O": (".#.", "#.#", "#.#", "#.#", ".#."),
    "P": ("##.", "#.#", "##.", "#..", "#.."),
    "Q": (".#.", "#.#", "#.#", "##.", ".##"),
    "R": ("##.", "#.#", "##.", "#.#", "#.#"),
    "S": (".##", "#..", ".#.", "..#", "##."),
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "U": ("#.#", "#.#", "#.#", "#.#", "###"),
    "V": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": ("#.#", "#.#", "###", "###", "#.#"),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": ("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": ("###", "..#", ".#.", "#..", "###"),
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("##.", "..#", ".#.", "#..", "###"),
    "3": ("##.", "..#", ".#.", "..#", "##."),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "##.", "..#", "##."),
    "6": (".##", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "##."),
    " ": ("...", "...", "...", "...", "..."),
    "+": ("...", ".#.", "###", ".#.", "..."),
    "-": ("...", "...", "###", "...", "..."),
    ".": ("...", "...", "...", "...", ".#."),
    "/": ("..#", "..#", ".#.", "#..", "#.."),
    ":": ("...", ".#.", "...", ".#.", "..."),
    "?": ("##.", "..#", ".#.", "...", ".#."),
}


def _mask(rows: tuple[str, ...]) -> Image.Image:
    img = Image.new("1", (GLYPH_W, GLYPH_H), 0)
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            if cell == "#":
                img.putpixel((x, y), 1)
    return img


_MASKS = {ch: _mask(rows) for ch, rows in _GLYPHS.items()}


def text_width(text: str) -> int:
    return max(len(text) * ADVANCE - 1, 0)


def draw_text(img: Image.Image, xy: tuple[int, int], text: str, color: RGB) -> None:
    """Draw upper-cased ``text`` with its top-left corner at ``xy``.
    Characters the font lacks are drawn as '?'."""
    x, y = xy
    for ch in text.upper():
        mask = _MASKS.get(ch, _MASKS["?"])
        img.paste(color, (x, y, x + GLYPH_W, y + GLYPH_H), mask)
        x += ADVANCE


def draw_text_right(img: Image.Image, right: int, y: int, text: str, color: RGB) -> None:
    draw_text(img, (right - text_width(text), y), text, color)


def fill(img: Image.Image, box: tuple[int, int, int, int], color: RGB) -> None:
    """Fill an inclusive pixel box."""
    ImageDraw.Draw(img).rectangle(box, fill=color)
