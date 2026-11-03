"""GRID Pup: cute, bouncy fonts for a dog-themed match-3 game, from the same 5x7 skeleton.
- Round, puffy strokes: circles at every node + rounded bars (real quadratic curves)
- Paw-print dots on i / j
- Bone variant: stroke endings become dog-bone knobs
- Wag VF: SQSH axis (-100 stretch ... 0 ... 100 squash) for squash-and-stretch bouncing
Run from repo root: python scripts/dogfont.py  ->  out5/
"""
import math, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skeleton import UP, LO
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
         for k, v in {**UP, **LO}.items()}
DOTS = {"i": (2, 0), "j": (3, 0)}           # cells that become paw prints

def glyph(name, cells, w, px, lsb, bone=False, paw=True, sx=1.0, sy=1.0):
    pen, h = TTGlyphPen(None), w / 2
    pos = lambda c, r: (lsb + h + c * px, (6 - r) * PY + 50)
    cx = lsb + h + 2 * px
    T = lambda x, y: (round(cx + (x - cx) * sx), round(y * sy))     # squash & stretch about baseline
    def polyg(pts):
        pts = [T(*p) for p in pts]
        area = sum(pts[i][0] * pts[(i+1) % 4][1] - pts[(i+1) % 4][0] * pts[i][1] for i in range(4))
        if area > 0: pts = pts[::-1]
        pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()
    def circle(x, y, r, rx=1.0):   # clockwise quadratic circle/ellipse, 8 segments
        k = 1 / math.cos(math.pi / 8)
        on = lambda a: T(x + r * rx * math.cos(a), y + r * math.sin(a))
        off = lambda a: T(x + r * rx * k * math.cos(a), y + r * k * math.sin(a))
        pen.moveTo(on(0))
        for i in range(8):
            a0 = -i * math.pi / 4
            pen.qCurveTo(off(a0 - math.pi / 8), on(a0 - math.pi / 4))
        pen.closePath()
    def paw(x, y):
        circle(x, y - 20, h * 0.95, 1.12)                              # main pad
        for ang, d, s in ((155, 1.45, .42), (110, 1.62, .44), (70, 1.62, .44), (25, 1.45, .42)):
            a = math.radians(ang)
            circle(x + math.cos(a) * h * d * 1.1, y - 20 + math.sin(a) * h * d, h * s)   # toes
    paw_cell = DOTS.get(name) if paw else None
    for c, r in sorted(cells):
        x, y = pos(c, r)
        if (c, r) == paw_cell: paw(x, y - 5); continue
        circle(x, y, h)
        for dc, dr in ((1, 0), (0, 1)):
            if (c+dc, r+dr) in cells:
                x2, y2 = pos(c+dc, r+dr)
                polyg([(x, y+h), (x2, y+h), (x2, y2-h), (x, y2-h)] if dr == 0 else [(x-h, y), (x+h, y), (x+h, y2), (x-h, y2)])
        for dc in (1, -1):
            if (c+dc, r+1) in cells and (c+dc, r) not in cells and (c, r+1) not in cells:
                x2, y2 = pos(c+dc, r+1); L = math.hypot(x2-x, y2-y); nx, ny = -(y2-y)/L*h, (x2-x)/L*h
                polyg([(x+nx, y+ny), (x2+nx, y2+ny), (x2-nx, y2-ny), (x-nx, y-ny)])
        if bone:   # stroke ending (exactly one straight neighbour, no diagonal) -> two bone knobs
            nb = [(dc, dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (c+dc, r+dr) in cells]
            diag = any((c+dc, r+dr) in cells for dc in (1, -1) for dr in (1, -1))
            if len(nb) == 1 and not diag:
                ox, oy = -nb[0][0], nb[0][1]                           # outward direction in font space (y up)
                px_, py_ = -oy, ox                                     # perpendicular
                for s in (1, -1):
                    circle(x + ox * h * .55 + px_ * s * h * .78, y + oy * h * .55 + py_ * s * h * .78, h * .78)
    return pen.glyph()

def build(family, path, w, px, lsb=55, bone=False, paw=True, sx=1.0, sy=1.0, merge=True):
    order = [".notdef", "space"] + list(CELLS)
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{ord(k): k for k in CELLS}})
    g = {n: TTGlyphPen(None).glyph() for n in (".notdef", "space")}
    g.update({k: glyph(k, cs, w, px, lsb, bone, paw, sx, sy) for k, cs in CELLS.items()})
    fb.setupGlyf(g)
    adv, glyf = int(2 * lsb + w + 4 * px), fb.font["glyf"]
    fb.setupHorizontalMetrics({n: (adv, getattr(glyf[n], "xMin", 0)) for n in order})
    fb.setupHorizontalHeader(ascent=900, descent=-260)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=900, sTypoDescender=-260, usWinAscent=900, usWinDescent=260)
    fb.setupPost()
    if merge: removeOverlaps(fb.font)
    fb.save(path)

os.makedirs("build5", exist_ok=True); os.makedirs("out5/fonts", exist_ok=True)
build("GRID Puppy", "out5/fonts/GRID-Puppy.ttf", 96, 112)
build("GRID Bone",  "out5/fonts/GRID-Bone.ttf",  66, 122, lsb=85, bone=True)
ds = DesignSpaceDocument()
a = AxisDescriptor(); a.tag, a.name, a.minimum, a.default, a.maximum = "SQSH", "Squash", -100, 0, 100; ds.addAxis(a)
for i, (v, sx, sy) in enumerate(((-100, .90, 1.14), (0, 1.0, 1.0), (100, 1.16, .76))):
    p = f"build5/wag_m{i}.ttf"; build("GRID Wag", p, 90, 112, lsb=75, sx=sx, sy=sy, merge=False)
    s = SourceDescriptor(); s.path, s.location = p, {"Squash": v}; ds.addSource(s)
varLib.build(ds)[0].save("out5/fonts/GRID-Wag-VF.ttf")

# ---- previews: warm cream board, match-3 tile colours, cartoon outline + shadow
BG, INK, DIM = (255, 243, 222), (74, 46, 30), (160, 130, 100)
TILES = [(240, 70, 80), (255, 150, 40), (250, 205, 50), (90, 190, 90), (60, 160, 235), (160, 100, 220)]
LABEL = ImageFont.load_default(size=22)
_cache = {}
def wag(v):
    v = int(round(v / 10) * 10)
    if v not in _cache:
        b = io.BytesIO(); instancer.instantiateVariableFont(TTFont("out5/fonts/GRID-Wag-VF.ttf"), {"SQSH": v}).save(b)
        _cache[v] = b.getvalue()
    return _cache[v]
def F(src, size): return ImageFont.truetype(io.BytesIO(src) if isinstance(src, bytes) else src, size)
def toon(d, xy, ch, fnt, col, sw):
    d.text((xy[0] + sw * .6, xy[1] + sw * 1.2), ch, font=fnt, fill=(220, 190, 150), stroke_width=sw, stroke_fill=(220, 190, 150))
    d.text(xy, ch, font=fnt, fill=col, stroke_width=sw, stroke_fill=INK)
def word(d, x, y, text, fnt, sw, colorful=True):
    for i, ch in enumerate(text):
        if ch != " ": toon(d, (x, y), ch, fnt, TILES[i % len(TILES)] if colorful else (255, 255, 255), sw)
        x += fnt.getlength(ch)

img = Image.new("RGB", (1700, 1640), BG); d = ImageDraw.Draw(img); y = 40
for name, src, col in (("GRID PUPPY  -  static, round + paw-print dots", "out5/fonts/GRID-Puppy.ttf", INK),
                       ("GRID BONE  -  static, bone-knob stroke endings", "out5/fonts/GRID-Bone.ttf", (200, 110, 40))):
    d.text((50, y), name, font=LABEL, fill=DIM); y += 40
    for txt, sz in (("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 46), ("abcdefghijklmnopqrstuvwxyz", 46)):
        d.text((50, y), txt, font=F(src, sz), fill=col); y += int(sz * 1.35)
    word(d, 50, y, "Good Boy" if "PUPPY" in name else "Fetch it", F(src, 120), 7); y += 190
d.text((50, y), "GRID WAG  -  variable, SQSH axis -100 / 0 / 100", font=LABEL, fill=DIM); y += 40
for v in (-100, 0, 100):
    word(d, 50, y, "Wiggle", F(wag(v), 96), 6, colorful=(v == 0))
    d.text((1450, y + 40), f"SQSH {v}", font=LABEL, fill=DIM); y += 150
img.save("out5/specimen.png")

# ---- bounce GIF: each letter hops with a phase offset; squash on landing, stretch in the air
W, H, N = 1300, 420, 40
TEXT, size = "GOOD DOG", 150
base = F(wag(0), size); xs, x = [], 80
for ch in TEXT: xs.append(x); x += base.getlength(ch)
frames = []
for f in range(N):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    for i, ch in enumerate(TEXT):
        if ch == " ": continue
        t = (f / N * 2 + i * 0.12) % 1.0                       # two hops per loop, wave across the word
        hop = math.sin(math.pi * t)                            # 0 on ground, 1 at top
        sq = 100 * max(0, 1 - hop / .18) if hop < .18 else -60 * hop   # squash on contact, stretch in air
        fnt = F(wag(sq), size)
        y0 = 200 - 150 * hop - fnt.getbbox(ch)[3] + base.getbbox("O")[3] * 0
        sh = 1 - .5 * hop                                      # ground shadow shrinks while airborne
        cxs = xs[i] + base.getlength(ch) / 2
        d.ellipse((cxs - 50 * sh, 352 - 9 * sh, cxs + 50 * sh, 352 + 9 * sh), fill=(235, 215, 185))
        toon(d, (xs[i] + (base.getlength(ch) - fnt.getlength(ch)) / 2, y0 + 150), ch, fnt, TILES[i % 6], 8)
    frames.append(im)
frames[0].save("out5/bounce.gif", save_all=True, append_images=frames[1:], duration=50, loop=0)
strip = Image.new("RGB", (W, H * 3))
for k, i in enumerate((0, 7, 14)): strip.paste(frames[i], (0, H * k))
strip.save("out5/bounce-frames.png")
print("done")
