#!/usr/bin/env python3
"""Generate a resolution/edition text overlay PNG (45 degree style).

Reproduces the look of the existing ``overlays/resolution-top-left-45deg``
assets without Photoshop: text runs at 45 degrees up the top-left corner,
with an optional white prefix (the resolution) followed by a
gradient-colored format tag (HDR, HLG, DV, ...). Geometry, glyph size and
the word gap were measured from the shipped overlays; the closest system
font to the original artwork is Noto Sans Black.

The ribbon background is a separate overlay
(``background_top_left_313_wide.yml``) — these files are text only, and the
``-Dovetail`` variants in the existing set are byte-identical copies, so the
script writes both names by default.

Examples:

    python3 scripts/generate_resolution_overlay.py \
        --gradient-text HLG --gradient '#12ab4f,#a8e214' --name HLG

    python3 scripts/generate_resolution_overlay.py --white 4K \
        --gradient-text HLG --gradient '#12ab4f,#a8e214' --name 4K-HLG

Requires: pillow, numpy (pip install pillow numpy).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CANVAS = (1000, 1500)
SS = 4  # supersampling factor
GLYPH_HEIGHT = 28  # cap height of the shipped overlays, in final pixels
WORD_GAP = 12
FONT_PATHS = [
    "/usr/share/fonts/noto/NotoSans-Black.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Black.ttf",
    "/usr/share/fonts/TTF/OpenSans-ExtraBold.ttf",
]
# Rotated-bbox center of the text block, measured per resolution prefix.
ANCHORS = {
    "4K": (139.5, 140.0),
    "1080P": (139.5, 137.0),
    "720P": (138.5, 137.0),
    "": (137.0, 136.0),
}
DEFAULT_ANCHOR = (138.5, 137.5)


def _load_font(px_height: int) -> ImageFont.FreeTypeFont:
    path = next((p for p in FONT_PATHS if Path(p).exists()), None)
    if path is None:
        raise SystemExit("no suitable font found; install noto-fonts")
    # scale font size until the cap height of 'H' matches px_height
    size = px_height
    for _ in range(8):
        font = ImageFont.truetype(path, size)
        bbox = font.getbbox("H")
        h = bbox[3] - bbox[1]
        if abs(h - px_height) <= 1:
            return font
        size = max(4, round(size * px_height / max(h, 1)))
    return ImageFont.truetype(path, size)


def _render_segment(text: str, font: ImageFont.FreeTypeFont) -> Image.Image:
    bbox = font.getbbox(text)
    img = Image.new("L", (bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 8), 0)
    ImageDraw.Draw(img).text((4 - bbox[0], 4 - bbox[1]), text, font=font, fill=255)
    arr = np.array(img)
    ys, xs = np.where(arr > 8)
    return img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def _parse_color(value: str) -> np.ndarray:
    value = value.lstrip("#")
    return np.array([int(value[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def build_text_block(white: str, grad_text: str,
                     grad_colors: tuple[np.ndarray, np.ndarray]) -> Image.Image:
    font = _load_font(GLYPH_HEIGHT * SS)
    segments = []
    if white:
        segments.append(("white", _render_segment(white, font)))
    if grad_text:
        segments.append(("grad", _render_segment(grad_text, font)))
    if not segments:
        raise SystemExit("nothing to render")

    gap = WORD_GAP * SS
    width = sum(s.width for _, s in segments) + gap * (len(segments) - 1)
    height = max(s.height for _, s in segments)
    block = np.zeros((height, width, 4), dtype=float)

    x = 0
    for kind, seg in segments:
        a = np.array(seg, dtype=float) / 255.0
        h, w = a.shape
        y0 = height - h  # baseline-align at the bottom
        rgb = np.zeros((h, w, 3), dtype=float)
        if kind == "white":
            rgb[...] = 255.0
        else:
            c1, c2 = grad_colors
            t = np.linspace(0.0, 1.0, w)[None, :, None]
            rgb[...] = c1[None, None, :] * (1 - t) + c2[None, None, :] * t
        block[y0:y0 + h, x:x + w, :3] = rgb
        block[y0:y0 + h, x:x + w, 3] = a * 255.0
        x += w + gap

    img = Image.fromarray(block.astype(np.uint8), "RGBA")
    return img.resize((max(1, img.width // SS), max(1, img.height // SS)),
                      Image.LANCZOS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--white", default="",
                        help="white prefix text (e.g. 4K, 1080P)")
    parser.add_argument("--gradient-text", default="",
                        help="gradient-colored text (e.g. HLG)")
    parser.add_argument("--gradient", default="#e71a5b,#fd9c11",
                        help="gradient as '#RRGGBB,#RRGGBB' (default: the HDR ramp)")
    parser.add_argument("--name", required=True,
                        help="output basename; writes <name>.png")
    parser.add_argument("--skip-dovetail", action="store_true",
                        help="do not also write <name>-Dovetail.png")
    parser.add_argument("--output-dir", type=Path,
                        default=Path("overlays/resolution-top-left-45deg"))
    args = parser.parse_args()

    c1, c2 = ((_parse_color(c)) for c in args.gradient.split(","))
    block = build_text_block(args.white, args.gradient_text, (c1, c2))
    rotated = block.rotate(45, expand=True, resample=Image.BICUBIC)

    arr = np.array(rotated)
    ys, xs = np.where(arr[..., 3] > 8)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    ax, ay = ANCHORS.get(args.white, DEFAULT_ANCHOR)

    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    canvas.alpha_composite(rotated, (round(ax - cx), round(ay - cy)))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / f"{args.name}.png"
    canvas.save(out, optimize=True)
    print(f"wrote {out}")
    if not args.skip_dovetail:
        dovetail = args.output_dir / f"{args.name}-Dovetail.png"
        canvas.save(dovetail, optimize=True)
        print(f"wrote {dovetail}")


if __name__ == "__main__":
    main()
