"""GRID Glitch: corrupted-signal fonts. Strokes are sliced into horizontal bands; bands shift sideways
(seeded per glyph) and some drop out, like a damaged video signal.
Fonts: GRID Glitch, GRID Glitch Hard (static), GRID Glitch VF (GLCH axis 0-100: clean -> corrupted)
Run from repo root: python scripts/glitchfont.py  ->  out6/
"""
import math, os, random
import numpy as np
from gridlib import *
from PIL import Image, ImageDraw

BAND, SLIT = 52, 4          # band height, gap between bands (scanline slit)

def strokes(cells, w, px, lsb):
    h = w / 2; P = lambda cr: pos(*cr, px, lsb, h); out = []
    for c, r in cells:
        x, y = P((c, r)); out.append([(x-h, y+h), (x+h, y+h), (x+h, y-h), (x-h, y-h)])
    for kind, a, b in links(cells):
        (x, y), (x2, y2) = P(a), P(b)
        if kind == "h": out.append([(x, y+h), (x2, y+h), (x2, y-h), (x, y-h)])
        elif kind == "v": out.append([(x-h, y), (x+h, y), (x+h, y2), (x-h, y2)])
        else:
            L = math.hypot(x2-x, y2-y); nx, ny = -(y2-y)/L*h, (x2-x)/L*h
            out.append([(x+nx, y+ny), (x2+nx, y2+ny), (x2-nx, y2-ny), (x-nx, y-ny)])
    return out

def make(w, px, lsb, amt, drop):
    def fn(name, cells):
        g, rnd = G(), random.Random("glitch" + name)
        edges = list(range(-300, 800, BAND))
        offs = [rnd.uniform(-1, 1) * amt if rnd.random() < .45 else 0 for _ in edges]
        dead = {i for i in range(len(edges)) if rnd.random() < drop}
        for pts in strokes(cells, w, px, lsb):
            for i, b in enumerate(edges):
                if i in dead: continue
                pc = clip(clip(pts, lambda p: p[1] - (b + SLIT / 2)), lambda p: (b + BAND - SLIT / 2) - p[1])
                if len(pc) >= 3: g.poly([(x + offs[i], y) for x, y in pc])
        return g.glyph()
    return fn

W_, PX, LSB = 74, 125, 70
ADV = 2 * LSB + W_ + 4 * PX
os.makedirs("out6/fonts", exist_ok=True)
build("GRID Glitch",      "out6/fonts/GRID-Glitch.ttf",      make(W_, PX, LSB, 40, .05), ADV)
build("GRID Glitch Hard", "out6/fonts/GRID-Glitch-Hard.ttf", make(W_, PX, LSB, 100, .13), ADV)
varfont("GRID Glitch VF", "GLCH", "Glitch", (0, 0, 100),
        [(0, make(W_, PX, LSB, 0, 0), ADV), (100, make(W_, PX, LSB, 110, 0), ADV)],
        "out6/fonts/GRID-Glitch-VF.ttf", "build6")

BG, FG, DIM, ACC = (8, 8, 10), (235, 240, 240), (110, 115, 125), (255, 40, 90)
specimen("out6/specimen.png", BG, DIM,
         [("GRID GLITCH  -  static", "out6/fonts/GRID-Glitch.ttf", FG, "System Error"),
          ("GRID GLITCH HARD  -  static", "out6/fonts/GRID-Glitch-Hard.ttf", ACC, "Corrupted")],
         ("GRID GLITCH VF  -  variable, GLCH axis 0 / 50 / 100", "out6/fonts/GRID-Glitch-VF.ttf", "GLCH",
          (0, 50, 100), "No Signal", FG))

# ---- corrupt / repair GIF: GLCH spikes, RGB channel split, screen tears, scanlines
W, H, N = 1300, 360, 56
rng = random.Random(5)
def mask(v, text, size, x, y):
    m = Image.new("L", (W, H)); ImageDraw.Draw(m).text((x, y), text, font=F(inst("out6/fonts/GRID-Glitch-VF.ttf", {"GLCH": v}), size), fill=255)
    return np.asarray(m, np.float32)
def level(f):   # mostly calm, with sharp spikes and a full meltdown in the middle
    if 22 <= f < 34: return 100 * (1 - abs(f - 28) / 7)
    return 85 if rng.random() < .12 else rng.uniform(0, 12)
scan = np.ones((H, W, 1), np.float32); scan[::3] = .72
frames, levels = [], []
for f in range(N):
    v = int(round(level(f) / 10) * 10); levels.append(v)
    m = mask(v, "SYSTEM FAILURE", 112, 60, 50) + mask(v, "rebooting", 70, 64, 220)
    s = int(v * .14)                                          # RGB split grows with corruption
    rgb = np.stack([np.roll(m, -s, 1), m, np.roll(m, s, 1)], -1).clip(0, 255)
    tint = np.array([1.0, .92, .96]) if v < 50 else np.array([1.0, .55, .75])
    img = (np.array(BG, np.float32) + rgb * tint) * scan
    if v >= 40:                                               # screen tears: shift random horizontal strips
        for _ in range(3):
            y0 = rng.randrange(0, H - 30); hgt = rng.randrange(6, 30)
            img[y0:y0 + hgt] = np.roll(img[y0:y0 + hgt], rng.randrange(-60, 60), 1)
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    ImageDraw.Draw(im).text((W - 170, 15), f"GLCH {v}", font=LABEL, fill=DIM)
    frames.append(im)
pick = (next(i for i, v in enumerate(levels) if v == 0), next(i for i, v in enumerate(levels) if 30 <= v <= 60), levels.index(max(levels)))
save_gif(frames, "out6/glitch.gif", 60, pick, "out6/glitch-frames.png")
print("done")
