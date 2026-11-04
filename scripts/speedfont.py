"""GRID Speed: F1-style racing fonts from the same 5x7 skeleton.
- Very wide + heavy + hard italic = forward momentum
- A slanted "speed cut" slices every glyph (clipped geometrically, Sutherland-Hodgman)
- Optional motion streaks trailing off the left edge
Fonts: GRID Apex (static), GRID Apex Streak (static), GRID Throttle VF (SPED axis 0-100)
Run from repo root: python scripts/speedfont.py  ->  out3/
"""
import math, io, os, sys
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
from PIL import Image, ImageDraw, ImageFont

PY = 100
CELLS = {k: {(c, r) for r, row in enumerate(v.split()) for c, ch in enumerate(row) if ch == "#"}
         for k, v in {**UP, **LO, **SYM}.items()}
CUT_Y, CUT_K, GAP = 300, 0.22, 24          # speed cut: centre height, rise per unit x, gap thickness

def poly(pen, pts):
    pts = [p for i, p in enumerate(pts) if p != pts[i - 1]]           # drop duplicate points
    if len(pts) < 3: return
    area = sum(pts[i][0] * pts[(i+1) % len(pts)][1] - pts[(i+1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if abs(area) < 1: return
    if area > 0: pts = pts[::-1]                                       # clockwise outer contours
    pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()

def clip(pts, f):   # keep the part of polygon where f(p) >= 0
    out = []
    for i in range(len(pts)):
        P, Q = pts[i], pts[(i + 1) % len(pts)]
        fp, fq = f(P), f(Q)
        if fp >= 0: out.append(P)
        if (fp >= 0) != (fq >= 0):
            s = fp / (fp - fq); out.append((P[0] + s * (Q[0] - P[0]), P[1] + s * (Q[1] - P[1])))
    return out

def glyph(cells, w, px, slant, lsb, cut=False, streak=False):
    pen, t, h = TTGlyphPen(None), math.tan(math.radians(slant)), w / 2
    pos = lambda c, r: (lsb + h + c * px, (6 - r) * PY + 50)
    mid = lsb + h + 2 * px
    line = lambda x: CUT_Y + CUT_K * (x - mid)
    def put(pts):
        pieces = [clip(pts, lambda p: p[1] - (line(p[0]) + GAP / 2)),
                  clip(pts, lambda p: (line(p[0]) - GAP / 2) - p[1])] if cut else [pts]
        for pc in pieces:
            if pc: poly(pen, [(round(x + (y - 350) * t), round(y)) for x, y in pc])
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
    if streak:      # tapered motion streaks off the leftmost cell of rows 1, 3, 5
        for r in (1, 3, 5):
            row = [c for c, rr in cells if rr == r]
            if not row: continue
            x, y = pos(min(row), r); xe, s1 = x - h - px * 0.9, h * 0.38
            put([(x - h + 1, y + s1), (x - h + 1, y - s1), (xe, y - 3), (xe, y + 3)])
    return pen.glyph()

def build(family, path, w, px, slant, lsb=40, cut=False, streak=False, merge=True):
    order = [".notdef", "space"] + list(CELLS)
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{CODE[k]: k for k in CELLS}})
    g = {".notdef": glyph(set(), w, px, 0, lsb), "space": glyph(set(), w, px, 0, lsb)}
    g.update({k: glyph(cs, w, px, slant, lsb, cut, streak) for k, cs in CELLS.items()})
    fb.setupGlyf(g)
    adv, glyf = int(2 * lsb + w + 4 * px), fb.font["glyf"]
    fb.setupHorizontalMetrics({n: (adv, getattr(glyf[n], "xMin", 0)) for n in order})
    fb.setupHorizontalHeader(ascent=850, descent=-250)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=850, sTypoDescender=-250, usWinAscent=850, usWinDescent=250)
    fb.setupPost()
    if merge: removeOverlaps(fb.font)          # clean single outlines (marketplace quality)
    fb.save(path)

os.makedirs("build3", exist_ok=True); os.makedirs("out3/fonts", exist_ok=True)
build("GRID Apex",        "out3/fonts/GRID-Apex.ttf",        84, 170, 16, cut=True)
build("GRID Apex Streak", "out3/fonts/GRID-Apex-Streak.ttf", 84, 170, 16, lsb=70, cut=True, streak=True)
ds = DesignSpaceDocument()
a = AxisDescriptor(); a.tag, a.name, a.minimum, a.default, a.maximum = "SPED", "Speed", 0, 0, 100; ds.addAxis(a)
for i, (v, prm) in enumerate(((0, (56, 110, 0)), (100, (88, 190, 18)))):
    p = f"build3/throttle_m{i}.ttf"; build("GRID Throttle", p, *prm, merge=False)
    s = SourceDescriptor(); s.path, s.location = p, {"Speed": v}; ds.addSource(s)
varLib.build(ds)[0].save("out3/fonts/GRID-Throttle-VF.ttf")

# ---- previews
BG, WHITE, RED, DIM = (14, 14, 17), (245, 245, 245), (230, 20, 20), (120, 120, 135)
LABEL = ImageFont.load_default(size=22)
def throttle(v):
    b = io.BytesIO(); instancer.instantiateVariableFont(TTFont("out3/fonts/GRID-Throttle-VF.ttf"), {"SPED": v}).save(b)
    return b.getvalue()
def F(src, size): return ImageFont.truetype(io.BytesIO(src) if isinstance(src, bytes) else src, size)

img = Image.new("RGB", (1700, 1480), BG); d = ImageDraw.Draw(img); y = 40
for name, src, col in (("GRID APEX  -  static", "out3/fonts/GRID-Apex.ttf", WHITE),
                       ("GRID APEX STREAK  -  static", "out3/fonts/GRID-Apex-Streak.ttf", RED)):
    d.text((50, y), name, font=LABEL, fill=DIM); y += 40
    for txt, sz in (("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 46), ("abcdefghijklmnopqrstuvwxyz", 46), ("Lights Out", 120)):
        d.text((50, y), txt, font=F(src, sz), fill=col); y += int(sz * 1.3)
    y += 25
d.text((50, y), "GRID THROTTLE  -  variable, SPED axis 0 / 50 / 100", font=LABEL, fill=DIM); y += 40
for v in (0, 50, 100):
    d.text((50, y), "Full Throttle", font=F(throttle(v), 80), fill=WHITE if v < 100 else RED)
    d.text((1450, y + 30), f"SPED {v}", font=LABEL, fill=DIM); y += 105
img.save("out3/specimen.png")

# speed GIF: fly in with motion blur, rev down/up on the SPED axis, blast out
W, H, N = 1300, 340, 48
def ease_out(p): return 1 - (1 - p) ** 3
def ease_in(p): return p ** 3
def layer(src, x, size, y, text):
    m = Image.new("L", (W, H)); ImageDraw.Draw(m).text((x, y), text, font=F(src, size), fill=255); return np.asarray(m, np.float32)
def smear(a, length):   # horizontal motion blur trailing to the right (text moving left)
    n = max(1, int(length / 6)); acc = np.zeros_like(a)
    for i in range(n):
        s = int(i * length / n); acc[:, s:] += a[:, :a.shape[1] - s]   # shift right, no wrap-around
    return acc / n
frames, prev = [], None
for f in range(N):
    if f < 14: x, sp = 1350 - 1290 * ease_out(f / 13), 100
    elif f < 22: x, sp = 60, 100 - 100 * ease_out((f - 13) / 8)      # brake: race italic -> upright
    elif f < 26: x, sp = 60, 0
    elif f < 36: x, sp = 60, 100 * ease_in((f - 25) / 10)           # rev up: upright -> race italic
    else: x, sp = 60 - 1500 * ease_in((f - 35) / 12), 100
    sp = max(0, min(100, sp)); v = 0 if prev is None else abs(x - prev); prev = x
    src = throttle(sp)
    a, b = smear(layer(src, x, 120, 40, "LIGHTS OUT"), v * 1.4), smear(layer(src, x + 8, 76, 200, "Full Throttle"), v * 1.4)
    rgb = np.full((H, W, 3), BG, np.float32)
    for m, col in ((a, WHITE), (b, RED)):
        m = (m / 255)[..., None]; rgb = rgb * (1 - m) + np.array(col, np.float32) * m
    im = Image.fromarray(rgb.clip(0, 255).astype(np.uint8))
    ImageDraw.Draw(im).text((W - 170, 15), f"SPED {sp:.0f}", font=LABEL, fill=DIM)
    frames.append(im)
frames[0].save("out3/speed.gif", save_all=True, append_images=frames[1:], duration=55, loop=0)
print("done")
