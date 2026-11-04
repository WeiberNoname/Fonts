"""GRID font lab v2: futuristic connected-stroke fonts from the same 5x7 skeleton (skeleton.py).
Cells become nodes; neighbours join into bars; lone diagonals become 45-degree cuts.
Static:  GRID Neon (thin line), GRID Velocity (heavy, extended, italic)
Dynamic: GRID Pulse VF (wght = stroke thickness), GRID Morph VF (wdth = extension, slnt = lean)
"""
import math, io, os
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.varLib import instancer
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from skeleton import UP, LO, SYM, CODE

PY, LSB = 100, 60   # row pitch, side bearing (units per em = 1000)
CELLS = {k: {(c, r) for r, row in enumerate(v.split()) for c, ch in enumerate(row) if ch == "#"}
         for k, v in {**UP, **LO, **SYM}.items()}

def quad(pen, pts):
    area = sum(pts[i][0] * pts[(i+1) % 4][1] - pts[(i+1) % 4][0] * pts[i][1] for i in range(4))
    if area > 0: pts = pts[::-1]                      # TrueType outer contours run clockwise
    pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()

def glyph(cells, w, px, slant):
    """w = stroke thickness, px = column pitch (wider = more extended), slant in degrees."""
    pen, t, h = TTGlyphPen(None), math.tan(math.radians(slant)), w / 2
    pos = lambda c, r: (LSB + h + c * px, (6 - r) * PY + 50)
    put = lambda pts: quad(pen, [(round(x + (y - 350) * t), round(y)) for x, y in pts])
    for c, r in sorted(cells):
        x, y = pos(c, r)
        put([(x-h, y+h), (x+h, y+h), (x+h, y-h), (x-h, y-h)])                 # node
        for dc, dr in ((1, 0), (0, 1)):                                        # straight bars
            if (c+dc, r+dr) in cells:
                x2, y2 = pos(c+dc, r+dr)
                put([(x-h, y+h), (x2+h, y+h), (x2+h, y2-h), (x-h, y2-h)])
        for dc in (1, -1):                                                     # 45-degree cuts
            if (c+dc, r+1) in cells and (c+dc, r) not in cells and (c, r+1) not in cells:
                x2, y2 = pos(c+dc, r+1); L = math.hypot(x2-x, y2-y)
                nx, ny = -(y2-y) / L * h, (x2-x) / L * h
                put([(x+nx, y+ny), (x2+nx, y2+ny), (x2-nx, y2-ny), (x-nx, y-ny)])
    return pen.glyph()

def build(family, w, px, slant, path):
    order = [".notdef", "space"] + list(CELLS)
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{CODE[k]: k for k in CELLS}})
    g = {".notdef": glyph(set(), w, px, 0), "space": glyph(set(), w, px, 0)}
    g.update({k: glyph(cs, w, px, slant) for k, cs in CELLS.items()})
    fb.setupGlyf(g)
    adv, glyf = int(2 * LSB + w + 4 * px), fb.font["glyf"]
    fb.setupHorizontalMetrics({n: (adv, getattr(glyf[n], "xMin", 0)) for n in order})
    fb.setupHorizontalHeader(ascent=850, descent=-250)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=850, sTypoDescender=-250, usWinAscent=850, usWinDescent=250)
    fb.setupPost(); fb.save(path)

def varfont(family, axes, masters, out):
    ds = DesignSpaceDocument()
    for tag, name, mn, df, mx in axes:
        a = AxisDescriptor(); a.tag, a.name, a.minimum, a.default, a.maximum = tag, name, mn, df, mx
        ds.addAxis(a)
    for i, (loc, params) in enumerate(masters):
        p = f"build2/masters/{family.replace(' ', '')}_m{i}.ttf"; build(family, *params, p)
        s = SourceDescriptor(); s.path, s.location = p, loc; ds.addSource(s)
    varLib.build(ds)[0].save(out)

os.makedirs("build2/masters", exist_ok=True); os.makedirs("out2/fonts", exist_ok=True)
build("GRID Neon",     20, 125, 0,  "out2/fonts/GRID-Neon.ttf")       # static: hairline HUD
build("GRID Velocity", 74, 150, 12, "out2/fonts/GRID-Velocity.ttf")   # static: heavy, extended, racing lean
varfont("GRID Pulse", [("wght", "Weight", 100, 100, 900)],
        [({"Weight": 100}, (12, 125, 0)), ({"Weight": 900}, (80, 125, 0))], "out2/fonts/GRID-Pulse-VF.ttf")
varfont("GRID Morph", [("wdth", "Width", 75, 75, 150), ("slnt", "Slant", -14, 0, 0)],
        [({"Width": 75, "Slant": 0}, (36, 95, 0)), ({"Width": 150, "Slant": 0}, (36, 165, 0)),
         ({"Width": 75, "Slant": -14}, (36, 95, 14))], "out2/fonts/GRID-Morph-VF.ttf")

# ---- previews
BG, FG, DIM = (6, 9, 18), (94, 242, 255), (110, 130, 160)
LABEL = ImageFont.load_default(size=20)
def inst(path, loc):
    b = io.BytesIO(); instancer.instantiateVariableFont(TTFont(path), loc).save(b); b.seek(0); return b
def F(src, size):
    if hasattr(src, "seek"): src.seek(0)
    return ImageFont.truetype(src, size)

rows = [("GRID NEON  -  static", "out2/fonts/GRID-Neon.ttf"),
        ("GRID VELOCITY  -  static", "out2/fonts/GRID-Velocity.ttf"),
        ("GRID PULSE  -  variable, wght 450", inst("out2/fonts/GRID-Pulse-VF.ttf", {"wght": 450})),
        ("GRID MORPH  -  variable, wdth 130, slnt -8", inst("out2/fonts/GRID-Morph-VF.ttf", {"wdth": 130, "slnt": -8}))]
img = Image.new("RGB", (1600, 1500), BG); d = ImageDraw.Draw(img); y = 40
for name, src in rows:
    d.text((50, y), name, font=LABEL, fill=DIM); y += 38
    for txt, sz in (("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 44), ("abcdefghijklmnopqrstuvwxyz", 44), ("Hyperdrive Online", 70)):
        d.text((50, y), txt, font=F(src, sz), fill=FG); y += int(sz * 1.3)
    y += 30
img.save("out2/specimen.png")

def gif(path, frames_loc, text, out):
    frames = []
    for loc in frames_loc:
        im = Image.new("RGB", (1150, 330), BG); dd = ImageDraw.Draw(im)
        dd.text((40, 20), "   ".join(f"{k} {v:.0f}" for k, v in loc.items()), font=LABEL, fill=DIM)
        f = inst(path, loc)
        dd.text((40, 70), text[0], font=F(f, 90), fill=FG)
        dd.text((40, 200), text[1], font=F(f, 64), fill=FG); frames.append(im)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=70, loop=0)

N = 36
gif("out2/fonts/GRID-Pulse-VF.ttf", [{"wght": 500 - 400 * math.cos(2 * math.pi * i / N)} for i in range(N)],
    ("Reactor Core", "Pulse Online"), "out2/pulse.gif")
gif("out2/fonts/GRID-Morph-VF.ttf", [{"wdth": 112 - 37 * math.cos(2 * math.pi * i / N),
                                      "slnt": -7 + 7 * math.cos(2 * math.pi * i / N + 1.2)} for i in range(N)],
    ("Warp Signal", "Morph Engaged"), "out2/morph.gif")
print("done")
