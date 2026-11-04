"""GRID Titan: monumental, heavy, grounded fonts from the same 5x7 skeleton.
- Ultra heavy strokes (mass)
- Slab feet on every stem bottom, smaller caps on stem tops (planted on the ground)
- Pyramid flare: glyph widens toward the baseline (stability)
- Fossil variant: cracked-stone splits (polygon clipping)
Fonts: GRID Titan, GRID Titan Fossil (static), GRID Stomp VF (MASS axis 0-100)
Run from repo root: python scripts/titanfont.py  ->  out4/
"""
import math, io, os, sys, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skeleton import UP, LO, SYM, CODE
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.varLib import instancer
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import removeOverlaps
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PY = 100
CELLS = {k: {(c, r) for r, row in enumerate(v.split()) for c, ch in enumerate(row) if ch == "#"}
         for k, v in {**UP, **LO, **SYM}.items()}

def poly(pen, pts):
    pts = [p for i, p in enumerate(pts) if p != pts[i - 1]]
    if len(pts) < 3: return
    area = sum(pts[i][0] * pts[(i+1) % len(pts)][1] - pts[(i+1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if abs(area) < 1: return
    if area > 0: pts = pts[::-1]
    pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()

def clip(pts, f):
    out = []
    for i in range(len(pts)):
        P, Q = pts[i], pts[(i + 1) % len(pts)]
        fp, fq = f(P), f(Q)
        if fp >= 0: out.append(P)
        if (fp >= 0) != (fq >= 0):
            s = fp / (fp - fq); out.append((P[0] + s * (Q[0] - P[0]), P[1] + s * (Q[1] - P[1])))
    return out

def glyph(cells, w, px, flare, foot, lsb, cracks=None):
    pen, h = TTGlyphPen(None), w / 2
    pos = lambda c, r: (lsb + h + c * px, (6 - r) * PY + 50)
    cx = lsb + h + 2 * px
    def put(pts):
        pieces = [pts]
        for x0, y0, m, g in (cracks or []):          # each crack = thin near-vertical gap
            line = lambda p: x0 + m * (p[1] - y0)
            pieces = [q for pc in pieces for q in (clip(pc, lambda p: p[0] - line(p) - g / 2),
                                                    clip(pc, lambda p: line(p) - g / 2 - p[0])) if q]
        for pc in pieces:   # pyramid flare: scale x around centre, wider toward the bottom
            poly(pen, [(round(cx + (x - cx) * (1 + flare * (350 - y) / 700)), round(y)) for x, y in pc])
    fx, fy = foot * px, foot * 110                    # slab foot overhang and height
    for c, r in sorted(cells):
        x, y = pos(c, r)
        put([(x-h, y+h), (x+h, y+h), (x+h, y-h), (x-h, y-h)])
        for dc, dr in ((1, 0), (0, 1)):
            if (c+dc, r+dr) in cells:
                x2, y2 = pos(c+dc, r+dr); put([(x-h, y+h), (x2+h, y+h), (x2+h, y2-h), (x-h, y2-h)])
        for dc in (1, -1):
            if (c+dc, r+1) in cells and (c+dc, r) not in cells and (c, r+1) not in cells:
                x2, y2 = pos(c+dc, r+1); L = math.hypot(x2-x, y2-y); nx, ny = -(y2-y)/L*h, (x2-x)/L*h
                put([(x+nx, y+ny), (x2+nx, y2+ny), (x2-nx, y2-ny), (x-nx, y-ny)])
        if (c, r-1) in cells and (c, r+1) not in cells:          # bottom of a stem -> big slab foot
            put([(x-h-fx, y-h+fy), (x+h+fx, y-h+fy), (x+h+fx, y-h), (x-h-fx, y-h)])
        if (c, r+1) in cells and (c, r-1) not in cells:          # top of a stem -> smaller cap
            put([(x-h-fx*.5, y+h), (x+h+fx*.5, y+h), (x+h+fx*.5, y+h-fy*.6), (x-h-fx*.5, y+h-fy*.6)])
    return pen.glyph()

def build(family, path, w, px, flare, foot, lsb=50, fossil=False, merge=True):
    order = [".notdef", "space"] + list(CELLS)
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{CODE[k]: k for k in CELLS}})
    pad = (2 * px + w / 2) * flare * 0.65                       # room for the flared base / descenders
    L = lsb + pad
    def cracks(name):
        if not fossil: return None
        rnd = random.Random(name)
        return [(L + w / 2 + rnd.uniform(0.7, 3.3) * px, rnd.uniform(150, 550), rnd.uniform(-.35, .35), rnd.uniform(9, 15))
                for _ in range(rnd.choice((1, 2)))]
    g = {".notdef": glyph(set(), w, px, 0, 0, L), "space": glyph(set(), w, px, 0, 0, L)}
    g.update({k: glyph(cs, w, px, flare, foot, L, cracks(k)) for k, cs in CELLS.items()})
    fb.setupGlyf(g)
    adv, glyf = int(2 * L + w + 4 * px), fb.font["glyf"]
    fb.setupHorizontalMetrics({n: (adv, getattr(glyf[n], "xMin", 0)) for n in order})
    fb.setupHorizontalHeader(ascent=850, descent=-250)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=850, sTypoDescender=-250, usWinAscent=850, usWinDescent=250)
    fb.setupPost()
    if merge: removeOverlaps(fb.font)
    fb.save(path)

os.makedirs("build4", exist_ok=True); os.makedirs("out4/fonts", exist_ok=True)
build("GRID Titan",        "out4/fonts/GRID-Titan.ttf",        132, 142, 0.30, 0.26)
build("GRID Titan Fossil", "out4/fonts/GRID-Titan-Fossil.ttf", 132, 142, 0.30, 0.26, fossil=True)
ds = DesignSpaceDocument()
a = AxisDescriptor(); a.tag, a.name, a.minimum, a.default, a.maximum = "MASS", "Mass", 0, 0, 100; ds.addAxis(a)
for i, (v, prm) in enumerate(((0, (48, 108, 0.0, 0.06)), (100, (132, 142, 0.30, 0.26)))):
    p = f"build4/stomp_m{i}.ttf"; build("GRID Stomp", p, *prm, merge=False)
    s = SourceDescriptor(); s.path, s.location = p, {"Mass": v}; ds.addSource(s)
varLib.build(ds)[0].save("out4/fonts/GRID-Stomp-VF.ttf")

# ---- previews: earth & bone palette
BG, BONE, AMBER, DIM = (20, 16, 12), (236, 224, 198), (232, 148, 40), (130, 115, 95)
LABEL = ImageFont.load_default(size=22)
def stomp(v):
    b = io.BytesIO(); instancer.instantiateVariableFont(TTFont("out4/fonts/GRID-Stomp-VF.ttf"), {"MASS": v}).save(b)
    return b.getvalue()
def F(src, size): return ImageFont.truetype(io.BytesIO(src) if isinstance(src, bytes) else src, size)

img = Image.new("RGB", (1700, 1560), BG); d = ImageDraw.Draw(img); y = 40
for name, src, col in (("GRID TITAN  -  static", "out4/fonts/GRID-Titan.ttf", BONE),
                       ("GRID TITAN FOSSIL  -  static", "out4/fonts/GRID-Titan-Fossil.ttf", AMBER)):
    d.text((50, y), name, font=LABEL, fill=DIM); y += 40
    for txt, sz in (("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 46), ("abcdefghijklmnopqrstuvwxyz", 46), ("Ancient Giant", 120)):
        d.text((50, y), txt, font=F(src, sz), fill=col); y += int(sz * 1.3)
    y += 25
d.text((50, y), "GRID STOMP  -  variable, MASS axis 0 / 50 / 100", font=LABEL, fill=DIM); y += 40
for v in (0, 50, 100):
    d.text((50, y), "Walk Into It", font=F(stomp(v), 84), fill=BONE if v < 100 else AMBER)
    d.text((1450, y + 30), f"MASS {v}", font=LABEL, fill=DIM); y += 115
img.save("out4/specimen.png")

# ---- stomp GIF: letters drop one by one, impact shake + dust, then subtitle gains MASS
W, H, N = 1300, 420, 70
TITLE, tf = "TITAN", F("out4/fonts/GRID-Titan.ttf", 190)
xs, x = [], 90
for ch in TITLE: xs.append(x); x += tf.getlength(ch)
BASE_Y, LAND = 40, [8 + 8 * i for i in range(len(TITLE))]       # landing frame per letter
rng = random.Random(3)
frames = []
for f in range(N):
    canvas = Image.new("RGB", (W + 60, H + 60), BG); d = ImageDraw.Draw(canvas)
    dust = Image.new("L", canvas.size); dd = ImageDraw.Draw(dust)
    shake = 0
    for i, ch in enumerate(TITLE):
        t0 = LAND[i] - 6
        if f < t0: continue
        p = min(1, (f - t0) / 6)
        yy = BASE_Y - 420 * (1 - p ** 2)                               # accelerating fall
        d.text((xs[i] + 30, yy + 30), ch, font=tf, fill=BONE)
        since = f - LAND[i]
        if 0 <= since < 8:                                             # impact: shake + dust puff
            shake = max(shake, 18 * (1 - since / 8))
            cx, gy, spread = xs[i] + 30 + tf.getlength(ch) / 2, BASE_Y + 30 + 168, 40 + since * 22
            a = int(170 * (1 - since / 8))
            for s in (-1, 1):
                dd.ellipse((cx + s * spread - 70, gy - 22, cx + s * spread + 70, gy + 18), fill=a)
    if f >= 48:                                                        # subtitle grows heavier
        m = min(100, (f - 48) / 14 * 100)
        d.text((120, 300 + 30), "walk into it", font=F(stomp(m), 78), fill=AMBER)
    canvas.paste(Image.new("RGB", canvas.size, (120, 100, 80)), (0, 0), dust.filter(ImageFilter.GaussianBlur(14)))
    ox, oy = (rng.uniform(-shake, shake), rng.uniform(-shake, shake)) if shake else (0, 0)
    frames.append(canvas.crop((int(30 + ox), int(30 + oy), int(30 + ox) + W, int(30 + oy) + H)))
frames[0].save("out4/stomp.gif", save_all=True, append_images=frames[1:], duration=55, loop=0)
strip = Image.new("RGB", (W, H * 3))
for k, i in enumerate((17, 41, 69)): strip.paste(frames[i], (0, H * k))
strip.save("out4/stomp-frames.png")
print("done")
