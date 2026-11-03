"""GRID font lab: modular sci-fi fonts generated from one 5x7 cell skeleton.
Static:  GRID Block, GRID Stencil
Dynamic (OpenType variable): GRID Pulse (wght axis), GRID Morph (CHMF + slnt axes)
"""
import math, io, os
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.varLib import instancer
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

# ---- 1. SKELETON: each glyph = rows of cells, top-down. Rows 0-6 sit above baseline, 7-8 are descenders.
UP = dict(
A=".###. #...# #...# ##### #...# #...# #...#", B="####. #...# #...# ####. #...# #...# ####.",
C=".###. #...# #.... #.... #.... #...# .###.", D="####. #...# #...# #...# #...# #...# ####.",
E="##### #.... #.... ####. #.... #.... #####", F="##### #.... #.... ####. #.... #.... #....",
G=".###. #...# #.... #.### #...# #...# .####", H="#...# #...# #...# ##### #...# #...# #...#",
I="##### ..#.. ..#.. ..#.. ..#.. ..#.. #####", J="..### ...#. ...#. ...#. ...#. #..#. .##..",
K="#...# #..#. #.#.. ##... #.#.. #..#. #...#", L="#.... #.... #.... #.... #.... #.... #####",
M="#...# ##.## #.#.# #.#.# #...# #...# #...#", N="#...# #...# ##..# #.#.# #..## #...# #...#",
O=".###. #...# #...# #...# #...# #...# .###.", P="####. #...# #...# ####. #.... #.... #....",
Q=".###. #...# #...# #...# #.#.# #..#. .##.#", R="####. #...# #...# ####. #.#.. #..#. #...#",
S=".#### #.... #.... .###. ....# ....# ####.", T="##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
U="#...# #...# #...# #...# #...# #...# .###.", V="#...# #...# #...# #...# #...# .#.#. ..#..",
W="#...# #...# #...# #.#.# #.#.# #.#.# .#.#.", X="#...# #...# .#.#. ..#.. .#.#. #...# #...#",
Y="#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..", Z="##### ....# ...#. ..#.. .#... #.... #####")
LO = dict(
a="..... ..... .###. ....# .#### #...# .####", b="#.... #.... ####. #...# #...# #...# ####.",
c="..... ..... .###. #.... #.... #...# .###.", d="....# ....# .#### #...# #...# #...# .####",
e="..... ..... .###. #...# ##### #.... .###.", f="..##. .#..# .#... ###.. .#... .#... .#...",
g="..... ..... .#### #...# #...# #...# .#### ....# .###.", h="#.... #.... #.##. ##..# #...# #...# #...#",
i="..#.. ..... .##.. ..#.. ..#.. ..#.. .###.", j="...#. ..... ..##. ...#. ...#. ...#. ...#. #..#. .##..",
k="#.... #.... #..#. #.#.. ##... #.#.. #..#.", l=".##.. ..#.. ..#.. ..#.. ..#.. ..#.. .###.",
m="..... ..... ##.#. #.#.# #.#.# #.#.# #.#.#", n="..... ..... #.##. ##..# #...# #...# #...#",
o="..... ..... .###. #...# #...# #...# .###.", p="..... ..... ####. #...# #...# #...# ####. #.... #....",
q="..... ..... .#### #...# #...# #...# .#### ....# ....#", r="..... ..... #.##. ##..# #.... #.... #....",
s="..... ..... .###. #.... .###. ....# ####.", t=".#... .#... ###.. .#... .#... .#..# ..##.",
u="..... ..... #...# #...# #...# #..## .##.#", v="..... ..... #...# #...# #...# .#.#. ..#..",
w="..... ..... #...# #...# #.#.# #.#.# .#.#.", x="..... ..... #...# .#.#. ..#.. .#.#. #...#",
y="..... ..... #...# #...# #...# #...# .#### ....# .###.", z="..... ..... ##### ...#. ..#.. .#... #####")

P, ADV, LSB = 100, 600, 50          # cell pitch, advance width, left side bearing (units per em = 1000)
GLYPHS = {}
for k, v in {**UP, **LO}.items():
    GLYPHS[k] = [(LSB + c * P + P / 2, (6 - r) * P + P / 2)
                 for r, row in enumerate(v.split()) for c, ch in enumerate(row) if ch == "#"]

# ---- 2. CELL RENDERER: every style is just (scale, chamfer, slant) applied to each cell.
# Always 8 points per cell, so all styles stay interpolation-compatible (needed for variable fonts).
def glyph(cells, scale, chm, slant):
    pen, h = TTGlyphPen(None), P * scale / 2
    c, t = chm * 2 * h, math.tan(math.radians(slant))
    for cx, cy in cells:
        x0, x1, y0, y1 = cx - h, cx + h, cy - h, cy + h
        pts = [(x0+c, y1), (x1-c, y1), (x1, y1-c), (x1, y0+c), (x1-c, y0), (x0+c, y0), (x0, y0+c), (x0, y1-c)]
        pts = [(round(x + (y - 350) * t), round(y)) for x, y in pts]
        pen.moveTo(pts[0]); [pen.lineTo(p) for p in pts[1:]]; pen.closePath()
    return pen.glyph()

# ---- 3. EXPORT: build a .ttf with metrics and a character map.
def build(family, scale, chm, slant, path):
    order = [".notdef", "space"] + list(GLYPHS)
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{ord(k): k for k in GLYPHS}})
    g = {".notdef": glyph([], 1, 0, 0), "space": glyph([], 1, 0, 0)}
    g.update({k: glyph(cs, scale, chm, slant) for k, cs in GLYPHS.items()})
    fb.setupGlyf(g)
    glyf = fb.font["glyf"]
    fb.setupHorizontalMetrics({n: (ADV, getattr(glyf[n], "xMin", 0)) for n in order})
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
        p = f"build/masters/{family.replace(' ', '')}_m{i}.ttf"; build(family, *params, p)
        s = SourceDescriptor(); s.path, s.location = p, loc; ds.addSource(s)
    varLib.build(ds)[0].save(out)

os.makedirs("build/masters", exist_ok=True); os.makedirs("out/fonts", exist_ok=True)
build("GRID Block",   1.04, 0.00, 0, "out/fonts/GRID-Block.ttf")      # static: solid terminal cells
build("GRID Stencil", 0.80, 0.22, 0, "out/fonts/GRID-Stencil.ttf")    # static: gapped, chamfered
varfont("GRID Pulse", [("wght", "Weight", 100, 100, 900)],            # dynamic: cells breathe
        [({"Weight": 100}, (0.30, 0.2, 0)), ({"Weight": 900}, (1.04, 0.2, 0))], "out/fonts/GRID-Pulse-VF.ttf")
varfont("GRID Morph", [("CHMF", "Chamfer", 0, 0, 50), ("slnt", "Slant", -14, 0, 0)],  # dynamic: square->diamond, upright->lean
        [({"Chamfer": 0, "Slant": 0}, (0.9, 0.02, 0)), ({"Chamfer": 50, "Slant": 0}, (0.9, 0.5, 0)),
         ({"Chamfer": 0, "Slant": -14}, (0.9, 0.02, 14))], "out/fonts/GRID-Morph-VF.ttf")

# ---- 4. PREVIEWS
BG, FG, DIM = (8, 12, 22), (94, 242, 255), (110, 130, 160)
def inst(path, loc):
    b = io.BytesIO(); instancer.instantiateVariableFont(TTFont(path), loc).save(b); b.seek(0); return b
def F(src, size): return ImageFont.truetype(src, size)

label = lambda s: F("out/fonts/GRID-Block.ttf", 22)
rows = [("GRID BLOCK  static", "out/fonts/GRID-Block.ttf"),
        ("GRID STENCIL  static", "out/fonts/GRID-Stencil.ttf"),
        ("GRID PULSE  variable  wght 500", inst("out/fonts/GRID-Pulse-VF.ttf", {"wght": 500})),
        ("GRID MORPH  variable  CHMF 30 slnt -10", inst("out/fonts/GRID-Morph-VF.ttf", {"CHMF": 30, "slnt": -10}))]
img = Image.new("RGB", (1500, 1560), BG); d = ImageDraw.Draw(img); y = 40
for name, src in rows:
    d.text((50, y), name, font=label(0), fill=DIM); y += 40
    for txt, sz in (("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 50), ("abcdefghijklmnopqrstuvwxyz", 50), ("Hyperdrive Online", 80)):
        if hasattr(src, "seek"): src.seek(0)
        d.text((50, y), txt, font=F(src, sz), fill=FG); y += int(sz * 1.25)
    y += 30
img.save("out/specimen.png")

def gif(path, frames_loc, text, out):
    frames = []
    for loc in frames_loc:
        im = Image.new("RGB", (900, 330), BG); dd = ImageDraw.Draw(im)
        dd.text((40, 20), "  ".join(f"{k} {v:.0f}" for k, v in loc.items()), font=label(0), fill=DIM)
        f = inst(path, loc)
        dd.text((40, 70), text[0], font=F(f, 90), fill=FG); f.seek(0)
        dd.text((40, 200), text[1], font=F(f, 64), fill=FG); frames.append(im)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=70, loop=0)

N = 36
gif("out/fonts/GRID-Pulse-VF.ttf", [{"wght": 500 - 400 * math.cos(2 * math.pi * i / N)} for i in range(N)],
    ("Reactor Core", "Pulse Online"), "out/pulse.gif")
gif("out/fonts/GRID-Morph-VF.ttf", [{"CHMF": 25 - 25 * math.cos(2 * math.pi * i / N),
                                     "slnt": -7 + 7 * math.cos(2 * math.pi * i / N + 1.2)} for i in range(N)],
    ("Warp Signal", "Morph Engaged"), "out/morph.gif")
print("done")
