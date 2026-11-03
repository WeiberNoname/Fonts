"""GRID Sumi: ink-brush fonts on the grid.
- Brush pressure: every stroke run starts thick and thins as the brush moves (left->right, top->bottom)
- Ink blobs where the brush lands, pointed tips where it lifts off
- Hand tremor: each glyph is rotated / shifted slightly (seeded, so it's consistent)
- Dry variant: thin dry-brush streaks running along the stroke direction
Fonts: GRID Sumi, GRID Sumi Dry (static), GRID Sumi VF (INKS axis 0-100: dry thin -> wet heavy)
Run from repo root: python scripts/inkfont.py  ->  out8/
"""
import math, os, random
import numpy as np
from gridlib import *
from PIL import Image, ImageDraw, ImageFilter

PX, LSB = 120, 80
lerp = lambda a, b, t: a + (b - a) * t

def runs(cells, axis):
    """Pressure factor per cell along horizontal (axis 0) or vertical (axis 1) runs."""
    f = {}
    for c, r in cells:
        step = (1, 0) if axis == 0 else (0, 1)
        if (c - step[0], r - step[1]) in cells: continue             # not a run start
        run = [(c, r)]
        while (run[-1][0] + step[0], run[-1][1] + step[1]) in cells: run.append((run[-1][0] + step[0], run[-1][1] + step[1]))
        if len(run) > 1:
            for i, cr in enumerate(run): f[cr] = lerp(1.42, .42, i / (len(run) - 1))
    return f

def make(w, dry=False):
    h = w / 2
    def fn(name, cells):
        rnd = random.Random("ink" + name)
        th, dy, cx = math.radians(rnd.uniform(-2.5, 2.5)), rnd.uniform(-12, 12), LSB + h + 2 * PX
        g = G(lambda x, y: (cx + (x - cx) * math.cos(th) - (y - 350) * math.sin(th),
                            350 + (x - cx) * math.sin(th) + (y - 350) * math.cos(th) + dy))
        hf, vf = runs(cells, 0), runs(cells, 1)
        P = lambda cr: pos(*cr, PX, LSB, h)
        dry_y = [rnd.uniform(-.5, .5) * h for _ in range(2)]; dry_x = [rnd.uniform(-.5, .5) * h for _ in range(2)]
        def put(pts, kind, x0, y0):
            pieces = [pts]
            if dry:
                for o in (dry_y if kind == "h" else dry_x if kind == "v" else []):
                    a, b, c = (0, 1, y0 + o) if kind == "h" else (1, 0, x0 + o)
                    pieces = [q for pc in pieces for q in split(pc, a, b, c, 5)]
            for pc in pieces: g.poly(pc)
        for c, r in cells:
            x, y = P((c, r)); k = max([d[(c, r)] for d in (hf, vf) if (c, r) in d] or [1.0])
            g.circle(x, y, h * k * 1.02)                                      # ink blob at every joint
            nb = neighbours(cells, c, r)
            diag = any((c+dc, r+dr) in cells for dc in (1, -1) for dr in (1, -1))
            if len(nb) == 1 and not diag and nb[0] in ((-1, 0), (0, -1)):    # brush lifts off -> pointed tip
                kk = (hf if nb[0] == (-1, 0) else vf).get((c, r), 1) * h
                if nb[0] == (-1, 0): g.poly([(x, y + kk), (x + h * 2.2, y - kk * .5), (x, y - kk)])
                else:                g.poly([(x - kk, y), (x + kk * .5, y - h * 2.3), (x + kk, y)])
        for kind, a, b in links(cells):
            (x, y), (x2, y2) = P(a), P(b)
            if kind == "h":
                k1, k2 = hf[a] * h, hf[b] * h
                put([(x, y + k1), (x2, y2 + k2), (x2, y2 - k2), (x, y - k1)], "h", x, y)
            elif kind == "v":
                k1, k2 = vf[a] * h, vf[b] * h
                put([(x - k1, y), (x + k1, y), (x2 + k2, y2), (x2 - k2, y2)], "v", x, y)
            else:
                L = math.hypot(x2-x, y2-y); nx, ny = -(y2-y)/L, (x2-x)/L
                put([(x + nx*h, y + ny*h), (x2 + nx*h*.7, y2 + ny*h*.7), (x2 - nx*h*.7, y2 - ny*h*.7), (x - nx*h, y - ny*h)], "d", x, y)
        return g.glyph()
    return fn

adv = lambda w: 2 * LSB + w + 4 * PX
os.makedirs("out8/fonts", exist_ok=True)
build("GRID Sumi",     "out8/fonts/GRID-Sumi.ttf",     make(84), adv(84))
build("GRID Sumi Dry", "out8/fonts/GRID-Sumi-Dry.ttf", make(84, dry=True), adv(84))
varfont("GRID Sumi VF", "INKS", "Ink", (0, 0, 100),
        [(0, make(44), adv(44)), (100, make(112), adv(112))], "out8/fonts/GRID-Sumi-VF.ttf", "build8")

PAPER, INK, DIM, SEAL = (238, 230, 212), (28, 24, 30), (150, 135, 115), (196, 40, 36)
specimen("out8/specimen.png", PAPER, DIM,
         [("GRID SUMI  -  static, brush pressure + ink blobs", "out8/fonts/GRID-Sumi.ttf", INK, "Way of Ink"),
          ("GRID SUMI DRY  -  static, dry-brush streaks", "out8/fonts/GRID-Sumi-Dry.ttf", (70, 60, 66), "Mountain")],
         ("GRID SUMI VF  -  variable, INKS axis 0 / 50 / 100", "out8/fonts/GRID-Sumi-VF.ttf", "INKS",
          (0, 50, 100), "Brush Spirit", INK))

# ---- brush GIF: letters painted left to right with ink bleed, then a red seal stamps down
W, H, N = 1300, 430, 64
rng = np.random.default_rng(4)
paper = (np.array(PAPER, np.float32) + rng.normal(0, 5, (H, W, 1)) +
         np.repeat(rng.normal(0, 4, (1, W, 1)), H, 0)).clip(0, 255)        # fibre texture
TEXT, tf = "Way of Ink", F("out8/fonts/GRID-Sumi.ttf", 160)
X = np.arange(W)[None, :]
letters, x = [], 90
for ch in TEXT:
    wch = tf.getlength(ch)
    if ch != " ":
        m = Image.new("L", (W, H)); ImageDraw.Draw(m).text((x, 30), ch, font=tf, fill=255)
        letters.append((np.asarray(m.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255, x, wch))
    x += wch
sub = Image.new("L", (W, H)); ImageDraw.Draw(sub).text((96, 290), "brush spirit", font=F("out8/fonts/GRID-Sumi-Dry.ttf", 64), fill=255)
sub = np.asarray(sub, np.float32) / 255
frames = []
for f in range(N):
    ink = np.zeros((H, W), np.float32)
    for i, (m, x0, wch) in enumerate(letters):
        p = (f - 4 - 5 * i) / 5
        if p <= 0: continue
        reveal = np.clip((x0 + min(p, 1) * (wch + 60) - X) / 25, 0, 1)     # brush sweeps across the letter
        ink = np.maximum(ink, m * reveal)
    if f >= 44: ink = np.maximum(ink, sub * min(1, (f - 44) / 6) * .8)
    img = paper * (1 - ink[..., None]) + np.array(INK, np.float32) * ink[..., None]
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8))
    if f >= 52:                                                              # hanko seal stamps down
        s = max(1.0, 1.6 - (f - 52) * .25); size = int(130 * s); cxs, cys = 1110, 300
        seal = Image.new("L", (size, size)); dd = ImageDraw.Draw(seal)
        dd.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 9, fill=255)
        dd.rounded_rectangle((size * .08, size * .08, size * .92, size * .92), radius=size // 12, outline=0, width=max(2, size // 30))
        sf = F("out7/fonts/GRID-Rune.ttf", int(size * .3))
        dd.text((size * .2, size * .16), "GR", font=sf, fill=0); dd.text((size * .2, size * .52), "ID", font=sf, fill=0)
        a = min(1, (f - 51) / 3)
        im.paste(Image.new("RGB", (size, size), SEAL), (cxs - size // 2, cys - size // 2), seal.point(lambda v: int(v * a * .92)))
    frames.append(im)
save_gif(frames, "out8/brush.gif", 60, (14, 30, 63), "out8/brush-frames.png")
print("done")
