#!/usr/bin/env python3
"""Generate a network/streaming corner-ribbon overlay PNG.

Reproduces the look of the existing ``overlays/network-top-left`` assets
(originally built from ``templates/poster_overlay_network.psd``) without
needing Photoshop: a brand-colored triangle in the top-left corner with a
top-edge highlight, inner edge shading, a soft drop shadow along the
hypotenuse and the network logo composited on top.

The shading profiles below were sampled from the shipped overlays so new
files blend in with the existing set.

Example:

    python3 scripts/generate_network_overlay.py \
        --logo /tmp/dazn.png --color '#0b0b0b' --name DAZN

    python3 scripts/generate_network_overlay.py \
        --logo /tmp/skyshowtime.png --color '#0f0f23' \
        --name SkyShowtime --rotate

Requires: pillow, numpy (pip install pillow numpy).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

CANVAS = (1000, 1500)
EDGE = 233.5  # triangle legs: pixels with x + y <= EDGE are inside the ribbon

# Sampled from overlays/network-top-left/ESPN.png -----------------------------
# White glow mixed into the ribbon color, indexed by distance from the top edge.
TOP_HIGHLIGHT = [0.361, 0.349, 0.329, 0.302, 0.263, 0.224,
                 0.180, 0.137, 0.098, 0.067, 0.043, 0.024, 0.012, 0.004]
# Darkening factor indexed by distance from the left edge.
LEFT_SHADE = [0.883, 0.887, 0.895, 0.908, 0.921, 0.937, 0.954,
              0.966, 0.975, 0.983, 0.992, 0.996, 0.996, 1.0]
# Darkening factor indexed by (EDGE - x - y), i.e. approach to the hypotenuse.
HYP_SHADE_DIST = [2.5, 5.5, 8.5, 11.5, 14.5, 17.5, 20.5, 23.5]
HYP_SHADE_VAL = [0.883, 0.904, 0.933, 0.966, 0.983, 0.992, 0.996, 1.0]
SHADOW_SIGMA = 11.0
SHADOW_STRENGTH = 0.45

# Logo placement conventions measured across the existing set.
UPRIGHT_CENTER = (72, 70)
UPRIGHT_MAX = (130, 88)
ROTATED_CENTER = (84, 84)
ROTATED_MAX_DIAG = 200  # max logo width along the 45° diagonal


def _lut(dist: np.ndarray, values: list[float], fill: float) -> np.ndarray:
    """Linear interpolation over integer-spaced samples starting at 0."""
    return np.interp(dist, np.arange(len(values)), values, right=fill)


def build_ribbon(color: tuple[int, int, int]) -> Image.Image:
    w, h = CANVAS
    yy, xx = np.mgrid[0:h, 0:w].astype(float)

    coverage = np.clip(EDGE - (xx + yy) + 0.5, 0.0, 1.0)

    shade = np.minimum(
        _lut(xx, LEFT_SHADE, 1.0),
        np.interp(EDGE - (xx + yy), HYP_SHADE_DIST, HYP_SHADE_VAL,
                  left=HYP_SHADE_VAL[0], right=1.0),
    )
    highlight = _lut(yy, TOP_HIGHLIGHT, 0.0)

    rgb = np.zeros((h, w, 3))
    for i, ch in enumerate(color):
        shaded = ch * shade
        rgb[..., i] = shaded * (1.0 - highlight) + 255.0 * highlight

    # Soft drop shadow spilling past the hypotenuse.
    mask_img = Image.fromarray((coverage * 255).astype(np.uint8))
    blurred = np.asarray(
        mask_img.filter(ImageFilter.GaussianBlur(SHADOW_SIGMA)), dtype=float) / 255.0
    shadow = SHADOW_STRENGTH * blurred * (1.0 - coverage)

    alpha = np.clip(coverage + shadow, 0.0, 1.0)
    # Shadow pixels are pure black; ribbon pixels keep their color.
    out = np.zeros((h, w, 4), dtype=np.uint8)
    ribbon_weight = np.divide(coverage, alpha, out=np.zeros_like(alpha),
                              where=alpha > 0)
    for i in range(3):
        out[..., i] = np.clip(rgb[..., i] * ribbon_weight, 0, 255).astype(np.uint8)
    out[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def prepare_logo(path: Path, logo_color: str | None, trim: bool = True) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    arr = np.asarray(logo, dtype=float)
    alpha = arr[..., 3]
    if alpha.max() == 0:
        raise SystemExit(f"{path}: logo has no alpha channel content")

    if logo_color is not None:
        rgb = _parse_color(logo_color)
        arr[..., 0], arr[..., 1], arr[..., 2] = rgb
        logo = Image.fromarray(arr.astype(np.uint8), "RGBA")

    if trim:
        bbox = logo.getbbox()
        if bbox:
            logo = logo.crop(bbox)
    return logo


def place_logo(canvas: Image.Image, logo: Image.Image, rotate: bool,
               scale: float, center: tuple[int, int] | None) -> None:
    if rotate:
        max_w = ROTATED_MAX_DIAG * scale
        ratio = min(max_w / logo.width, (max_w * 0.45) / logo.height, 1.0)
        logo = logo.resize((max(1, round(logo.width * ratio)),
                            max(1, round(logo.height * ratio))),
                           Image.LANCZOS)
        logo = logo.rotate(45, expand=True, resample=Image.BICUBIC)
        cx, cy = center or ROTATED_CENTER
    else:
        max_w, max_h = UPRIGHT_MAX[0] * scale, UPRIGHT_MAX[1] * scale
        ratio = min(max_w / logo.width, max_h / logo.height)
        logo = logo.resize((max(1, round(logo.width * ratio)),
                            max(1, round(logo.height * ratio))),
                           Image.LANCZOS)
        cx, cy = center or UPRIGHT_CENTER
    canvas.alpha_composite(logo, (cx - logo.width // 2, cy - logo.height // 2))


def _parse_color(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise SystemExit(f"expected #RRGGBB color, got {value!r}")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--logo", required=True, type=Path,
                        help="logo image (transparent PNG works best)")
    parser.add_argument("--color", required=True,
                        help="ribbon color as #RRGGBB")
    parser.add_argument("--name", required=True,
                        help="network name; becomes <output-dir>/<name>.png")
    parser.add_argument("--logo-color", default="#ffffff",
                        help="recolor the logo silhouette (#RRGGBB); "
                             "pass 'keep' to preserve original colors")
    parser.add_argument("--rotate", action="store_true",
                        help="lay the logo along the 45 degree diagonal "
                             "(good for wide wordmarks)")
    parser.add_argument("--logo-scale", type=float, default=1.0,
                        help="scale factor on the standard logo size")
    parser.add_argument("--logo-center", default=None,
                        help="override logo center as X,Y")
    parser.add_argument("--output-dir", type=Path,
                        default=Path("overlays/network-top-left"))
    args = parser.parse_args()

    center = None
    if args.logo_center:
        x, y = args.logo_center.split(",")
        center = (int(x), int(y))

    logo_color = None if args.logo_color == "keep" else args.logo_color
    canvas = build_ribbon(_parse_color(args.color))
    logo = prepare_logo(args.logo, logo_color)
    place_logo(canvas, logo, args.rotate, args.logo_scale, center)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output_dir / f"{args.name}.png"
    canvas.save(out_path, optimize=True)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
