#!/usr/bin/env python3
"""Prep a photo so it converts to clean ASCII: isolate subject, boost local
contrast, composite onto white so the background maps to blank (spaces).

Run locally once per photo (needs pillow, numpy, opencv-python, rembg):

    python scripts/prep_photo.py source-photo.jpg
    # -> writes source-prepped.png (grayscale, white background)
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

OUT = "source-prepped.png"


def main(src):
    # 1) isolate subject (RGBA with alpha cutout)
    cut = remove(Image.open(src).convert("RGBA"))

    rgba = np.array(cut)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0

    # 2) grayscale + CLAHE for real highlights/shadows on a flat face
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    g = clahe.apply(gray).astype(np.float32)

    # 2b) stretch contrast within the subject, then gamma-lift the midtones so
    #     highlights fall into the sparse end of the ramp (avoids a dark blob).
    m = alpha > 0.3
    if m.any():
        lo, hi = np.percentile(g[m], 3), np.percentile(g[m], 97)
        if hi > lo:
            g = np.clip((g - lo) / (hi - lo), 0, 1)
            g = (g ** 0.72) * 255.0  # gamma < 1 brightens midtones

    # 3) composite onto pure white using the alpha matte
    white = np.full_like(g, 255.0)
    out = g * alpha + white * (1.0 - alpha)

    Image.fromarray(out.clip(0, 255).astype(np.uint8), mode="L").save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/prep_photo.py <source-photo.jpg>")
    main(sys.argv[1])
