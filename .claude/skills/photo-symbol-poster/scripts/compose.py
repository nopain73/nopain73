#!/usr/bin/env python3
"""Compose the poster: photo on the top half, printed symbol on the bottom half.

  python3 compose.py --photo PHOTO --symbol symbol.svg --out poster.png

The canvas is 3:4 (default 2400x3200) and is split exactly in half. The photo is
never stretched: it is cover-cropped around a focus point, or (--fit extend) kept
whole with its own blurred edges continued outward. The symbol SVG is rendered
one [data-plate] group at a time and "printed" onto paper with multiply
overprint, a few pixels of mis-registration, ink grain and scanner noise.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255


def noise(rng, w, h, scale):
    """Value noise in 0..1; scale = feature size in px (1 = per-pixel)."""
    if scale <= 1:
        return rng.random((h, w), dtype=np.float32)
    small = rng.random((max(2, int(h / scale) + 2), max(2, int(w / scale) + 2)), dtype=np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im, dtype=np.float32) / 255


# ---------- top half: the photograph ----------

def fit_photo(im, w, h, fit, fx, fy):
    sw, sh = im.size
    cover = max(w / sw, h / sh)
    if fit == "cover":
        im2 = im.resize((round(sw * cover), round(sh * cover)), Image.LANCZOS)
        x = int(round((im2.width - w) * fx)); y = int(round((im2.height - h) * fy))
        return im2.crop((x, y, x + w, y + h))
    # extend: whole photo visible, canvas filled by a blurred continuation of itself
    contain = min(w / sw, h / sh)
    bg = im.resize((round(sw * cover), round(sh * cover)), Image.LANCZOS)
    bx = (bg.width - w) // 2; by = (bg.height - h) // 2
    bg = bg.crop((bx, by, bx + w, by + h)).filter(ImageFilter.GaussianBlur(w / 28))
    fg = im.resize((round(sw * contain), round(sh * contain)), Image.LANCZOS)
    ox = (w - fg.width) // 2; oy = (h - fg.height) // 2
    feather = max(8, int(min(w, h) * 0.05))
    mask = Image.new("L", fg.size, 255)
    m = np.asarray(mask, dtype=np.float32).copy()
    ramp = np.linspace(0, 1, feather, dtype=np.float32)
    if fg.width < w:
        m[:, :feather] *= ramp[None, :]; m[:, -feather:] *= ramp[None, ::-1]
    if fg.height < h:
        m[:feather, :] *= ramp[:, None]; m[-feather:, :] *= ramp[::-1, None]
    bg.paste(fg, (ox, oy), Image.fromarray(m.astype(np.uint8)))
    return bg


def grade(a, strength, rng):
    """Light editorial grade: soft S-curve, lifted blacks, a touch less saturation, fine grain."""
    if strength <= 0:
        return a
    s = strength
    curve = a * a * (3 - 2 * a)                      # smoothstep S-curve
    a = a * (1 - 0.35 * s) + curve * (0.35 * s)
    a = 0.022 * s + a * (1 - 0.034 * s)              # lifted blacks, held highlights
    lum = (a * np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)).sum(-1, keepdims=True)
    a = lum + (a - lum) * (1 - 0.07 * s)
    a = a * (1 + (np.array([0.012, 0.004, -0.014], dtype=np.float32) * s) * lum)   # warm highlights
    g = rng.normal(0, 0.016 * s, a.shape[:2]).astype(np.float32)[..., None]
    return np.clip(a + g * (0.4 + 0.6 * (1 - lum)), 0, 1)


# ---------- bottom half: paper + plates ----------

def make_paper(rng, w, h, color):
    p = np.ones((h, w, 3), dtype=np.float32) * color
    p *= (0.985 + 0.03 * noise(rng, w, h, 420))[..., None]          # uneven sheet
    p *= (0.988 + 0.024 * noise(rng, w, h, 3))[..., None]           # tooth
    p += rng.normal(0, 0.006, (h, w, 1)).astype(np.float32)
    fib = noise(rng, w, h, 2) * noise(rng, w, h, 9)                 # sparse fibres / dust
    p -= (np.clip(fib - 0.80, 0, 1) * 0.9)[..., None]
    return np.clip(p, 0, 1)


def print_plate(rng, base, rgba, misreg, grain, key):
    h, w = base.shape[:2]
    if not key and misreg > 0:
        ang = rng.uniform(-0.05, 0.05) * min(1.0, misreg / 3)
        dx, dy = rng.uniform(-1, 1, 2) * misreg
        if abs(dx) + abs(dy) < misreg * 0.6:                        # make the error visible, not zero
            dx, dy = np.sign(dx or 1) * misreg * 0.7, np.sign(dy or 1) * misreg * 0.5
        rgba = rgba.rotate(ang, resample=Image.BICUBIC, translate=(float(dx), float(dy)))
    arr = np.asarray(rgba, dtype=np.float32) / 255
    rgb, a = arr[..., :3], arr[..., 3]
    if grain > 0:
        fine = noise(rng, w, h, 1); mid = noise(rng, w, h, 2.5); low = noise(rng, w, h, 260)
        a = a * (1 - grain * 0.42 * fine * fine)                    # riso speckle in the solids
        a = a * (1 - grain * 0.55 * np.clip(mid - 0.72, 0, 1) / 0.28)   # small drop-outs
        a = a * (1 - grain * 0.16 * low)                            # uneven drum pressure
        ghost = np.asarray(rgba.getchannel("A").filter(ImageFilter.GaussianBlur(1.6)), dtype=np.float32) / 255
        a = np.maximum(a, ghost * 0.10 * grain * mid)               # faint xerox halo at edges
    return base * (1 - a[..., None] * (1 - rgb))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photo", required=True)
    ap.add_argument("--symbol", required=True, help="SVG, viewBox 0 0 2400 1600, with [data-plate] groups")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=2400, help="canvas width; height is width*4/3")
    ap.add_argument("--fit", choices=["cover", "extend"], default="cover")
    ap.add_argument("--focus", default="0.5,0.5", help="cover-crop anchor x,y in 0..1 (where the subject is)")
    ap.add_argument("--grade", type=float, default=1.0, help="photo grade strength, 0 = untouched")
    ap.add_argument("--paper", default=None, help="paper hex; default: the SVG's data-paper or #EFEBE1")
    ap.add_argument("--misreg", type=float, default=3.0, help="max plate offset in px at 2400 wide")
    ap.add_argument("--grain", type=float, default=1.0, help="ink grain strength")
    ap.add_argument("--scan", type=float, default=1.0, help="scanner noise strength on the printed half")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--keep-plates", help="directory to keep the rendered plate PNGs in")
    a = ap.parse_args()

    W = a.width - a.width % 6
    H = W * 4 // 3
    half = H // 2
    rng = np.random.default_rng(a.seed)
    k = W / 2400

    photo = ImageOps.exif_transpose(Image.open(a.photo)).convert("RGB")
    fx, fy = (float(v) for v in a.focus.split(","))
    top = np.asarray(fit_photo(photo, W, half, a.fit, fx, fy), dtype=np.float32) / 255
    top = grade(top, a.grade, rng)

    pdir = a.keep_plates or tempfile.mkdtemp(prefix="plates_")
    r = subprocess.run(["node", os.path.join(HERE, "render_plates.js"), a.symbol, pdir, str(W), str(half)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("plate rendering failed:\n" + r.stdout + r.stderr)
    meta = json.load(open(os.path.join(pdir, "plates.json")))
    paper_hex = a.paper or meta.get("paper") or "#EFEBE1"
    bottom = make_paper(rng, W, half, hex_rgb(paper_hex))
    for p in meta["plates"]:
        rgba = Image.open(os.path.join(pdir, p["file"])).convert("RGBA")
        bottom = print_plate(rng, bottom, rgba, a.misreg * k, a.grain, p["register"] == "key")

    if a.scan > 0:                                                   # scanner: noise + faint banding
        bottom = bottom + rng.normal(0, 0.009 * a.scan, bottom.shape[:2]).astype(np.float32)[..., None]
        band = (noise(rng, 1, half, 40) - 0.5) * 0.012 * a.scan
        bottom = bottom + band.reshape(half, 1, 1)
        bottom = np.clip(bottom, 0, 1)

    canvas = np.concatenate([top, bottom], axis=0)
    out = Image.fromarray((np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8))
    out.save(a.out)
    print(f"{a.out}  {out.size[0]}x{out.size[1]}  split at y={half}  plates={[p['name'] for p in meta['plates']]}  paper={paper_hex}")


if __name__ == "__main__":
    main()
