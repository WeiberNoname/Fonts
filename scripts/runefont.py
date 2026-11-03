"""GRID Rune: carved fantasy fonts.
- Chisel contrast: vertical strokes thick, horizontal strokes thin (like cuts made with a flat chisel)
- Wedge terminals: every stroke ending sharpens into a spike
- Carved variant: a V-groove split down the centre of every stroke, read as two bevelled faces
Fonts: GRID Rune, GRID Rune Carved (static), GRID Rune VF (EDGE axis 0-100: blunt -> spiked)
Run from repo root: python scripts/runefont.py  ->  out7/
"""
import math, os, random
import numpy as np
from gridlib import *
from PIL import Image, ImageDraw, ImageFilter, ImageChops

def make(wv, wh, px, lsb, tip, carve=0):
    hx, hy = wv / 2, wh / 2
    def fn(name, cells):
        g = G(); P = lambda cr: pos(*cr, px, lsb, hx); shapes = []   # (polygon, groove lines)
        for c, r in cells:
            x, y = P((c, r)); nb = neighbours(cells, c, r)
            diag = any((c+dc, r+dr) in cells for dc in (1, -1) for dr in (1, -1))
            if not nb and not diag:                                    # lone cell -> diamond gem
                d = wv * .75; shapes.append(([(x, y+d), (x+d*.8, y), (x, y-d), (x-d*.8, y)], [(1, 0, x)])); continue
            shapes.append(([(x-hx, y+hy), (x+hx, y+hy), (x+hx, y-hy), (x-hx, y-hy)], [(1, 0, x), (0, 1, y)]))
            if len(nb) == 1 and not diag:                              # stroke ending -> wedge spike
                ox, oy = -nb[0][0], nb[0][1]
                if ox: shapes.append(([(x, y+hy), (x + ox * (hx + tip), y), (x, y-hy)], [(0, 1, y)]))
                else:  shapes.append(([(x-hx, y), (x, y + oy * (hy + tip + hx)), (x+hx, y)], [(1, 0, x)]))
        for kind, a, b in links(cells):
            (x, y), (x2, y2) = P(a), P(b)
            if kind == "h": shapes.append(([(x, y+hy), (x2, y+hy), (x2, y-hy), (x, y-hy)], [(0, 1, y)]))
            elif kind == "v": shapes.append(([(x-hx, y), (x+hx, y), (x+hx, y2), (x-hx, y2)], [(1, 0, x)]))
            else:
                hd = (wv + wh) / 4; L = math.hypot(x2-x, y2-y); nx, ny = -(y2-y)/L, (x2-x)/L
                shapes.append(([(x+nx*hd, y+ny*hd), (x2+nx*hd, y2+ny*hd), (x2-nx*hd, y2-ny*hd), (x-nx*hd, y-ny*hd)],
                               [(nx, ny, nx * x + ny * y)]))
        for pts, grooves in shapes:
            pieces = [pts]
            if carve:
                for a, b, c in grooves: pieces = [q for pc in pieces for q in split(pc, a, b, c, carve)]
            for pc in pieces: g.poly(pc)
        return g.glyph()
    return fn

WV, WH, PX, LSB = 92, 46, 122, 90
ADV = 2 * LSB + WV + 4 * PX
os.makedirs("out7/fonts", exist_ok=True)
build("GRID Rune",        "out7/fonts/GRID-Rune.ttf",        make(WV, WH, PX, LSB, 70), ADV)
build("GRID Rune Carved", "out7/fonts/GRID-Rune-Carved.ttf", make(WV, WH, PX, LSB, 70, carve=12), ADV)
varfont("GRID Rune VF", "EDGE", "Edge", (0, 0, 100),
        [(0, make(WV, WH, PX, LSB, 2), ADV), (100, make(WV, WH, PX, LSB, 130), ADV)],
        "out7/fonts/GRID-Rune-VF.ttf", "build7")

BG, STONE, DIM, MAGIC = (16, 18, 22), (178, 172, 160), (110, 112, 120), (90, 235, 210)
specimen("out7/specimen.png", BG, DIM,
         [("GRID RUNE  -  static", "out7/fonts/GRID-Rune.ttf", STONE, "Old Kingdom"),
          ("GRID RUNE CARVED  -  static, V-groove", "out7/fonts/GRID-Rune-Carved.ttf", MAGIC, "Dragon Gate")],
         ("GRID RUNE VF  -  variable, EDGE axis 0 / 50 / 100", "out7/fonts/GRID-Rune-VF.ttf", "EDGE",
          (0, 50, 100), "Sharpen", STONE))

# ---- awaken GIF: stone runes ignite letter by letter with magic glow and rising embers
W, H, N = 1300, 430, 60
TITLE, SUB = "AWAKEN", "the old runes"
tf, sf = F("out7/fonts/GRID-Rune-Carved.ttf", 175), F("out7/fonts/GRID-Rune-Carved.ttf", 66)
xs, x = [], 80
for ch in TITLE: xs.append(x); x += tf.getlength(ch)
stone = Image.new("L", (W, H)); ds = ImageDraw.Draw(stone)
for i, ch in enumerate(TITLE): ds.text((xs[i], 40), ch, font=tf, fill=255)
ds.text((90, 270), SUB, font=sf, fill=255)
rng = random.Random(11)
embers = [(rng.uniform(80, 1150), rng.uniform(0, N), rng.uniform(2, 4), rng.uniform(1.5, 3.5)) for _ in range(70)]
frames = []
for f in range(N):
    lit = Image.new("L", (W, H)); dl = ImageDraw.Draw(lit)
    for i, ch in enumerate(TITLE):
        t0 = 6 + 6 * i
        if f >= t0:
            v = min(1, (f - t0) / 5) * (0.85 + 0.15 * rng.random())       # ignite, then a living shimmer
            dl.text((xs[i], 40), ch, font=tf, fill=int(255 * v))
    if f >= 44: dl.text((90, 270), SUB, font=sf, fill=int(255 * min(1, (f - 44) / 6)))
    base = Image.new("RGB", (W, H), BG)
    base.paste(Image.new("RGB", (W, H), (70, 72, 78)), (0, 0), stone)          # unlit carved stone
    glow = Image.merge("RGB", [lit.point(lambda p, k=k: int(p * k / 255)) for k in MAGIC])
    img = base
    for r in (24, 24, 6): img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(r)))
    core = Image.merge("RGB", [lit.point(lambda p, k=k: int(p * (k + (255 - k) * .55) / 255)) for k in MAGIC])
    img = ImageChops.add(img, core)
    d = ImageDraw.Draw(img)
    lit_w = xs[min(len(TITLE) - 1, max(0, (f - 6) // 6))] + 120 if f >= 6 else 0
    for ex, t0, sp, sz in embers:                                               # embers rise from lit runes
        age = (f - t0) % N
        if ex < lit_w and age < 18:
            ey = 230 - age * sp; a = 1 - age / 30
            d.ellipse((ex - sz, ey - sz, ex + sz, ey + sz), fill=tuple(int(c * a) for c in (255, 200, 120)))
    frames.append(img)
save_gif(frames, "out7/awaken.gif", 60, (10, 30, 59), "out7/awaken-frames.png")
print("done")
