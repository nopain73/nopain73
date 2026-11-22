#!/usr/bin/env python3
"""Extract a small palette from a photo so the symbol's inks come from the image, not from guesswork.

Usage: python3 palette.py PHOTO [-k 8] [--swatch out.png]
Prints one line per cluster: hex, share of pixels, saturation, lightness — sorted by share.
"""
import argparse, colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageOps


def kmeans(px, k, iters=25, seed=7):
    rng = np.random.default_rng(seed)
    c = px[rng.choice(len(px), k, replace=False)].astype(np.float32)
    for _ in range(iters):
        d = ((px[:, None, :] - c[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for i in range(k):
            m = lab == i
            if m.any():
                c[i] = px[m].mean(0)
    return c, lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("-k", type=int, default=8)
    ap.add_argument("--swatch", help="optional PNG of the swatches, to look at")
    a = ap.parse_args()
    im = ImageOps.exif_transpose(Image.open(a.photo)).convert("RGB")
    im.thumbnail((160, 160))
    px = np.asarray(im, dtype=np.float32).reshape(-1, 3)
    c, lab = kmeans(px, a.k)
    share = np.bincount(lab, minlength=a.k) / len(lab)
    rows = []
    for i in np.argsort(-share):
        r, g, b = (c[i] / 255).tolist()
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        hexv = "#%02X%02X%02X" % tuple(int(round(v)) for v in c[i])
        rows.append((hexv, share[i], h * 360, s, l))
        print(f"{hexv}  share={share[i]:.2f}  hue={h*360:5.0f}  sat={s:.2f}  light={l:.2f}")
    if a.swatch:
        sw = Image.new("RGB", (120 * len(rows), 120), "white")
        d = ImageDraw.Draw(sw)
        for i, r in enumerate(rows):
            d.rectangle([i * 120, 0, i * 120 + 119, 119], fill=r[0])
        sw.save(a.swatch)


if __name__ == "__main__":
    main()
