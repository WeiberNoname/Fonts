"""Shared machinery for GRID font styles: skeleton cells, glyph drawing, clipping, export, previews."""
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

def pos(c, r, px, lsb, h):
    return (lsb + h + c * px, (6 - r) * PY + 50)

def links(cells):
    """Yield the skeleton's structure: ('h'|'v'|'d', a, b) segments between cells."""
    for c, r in sorted(cells):
        if (c + 1, r) in cells: yield "h", (c, r), (c + 1, r)
        if (c, r + 1) in cells: yield "v", (c, r), (c, r + 1)
        for dc in (1, -1):
            if (c + dc, r + 1) in cells and (c + dc, r) not in cells and (c, r + 1) not in cells:
                yield "d", (c, r), (c + dc, r + 1)

def neighbours(cells, c, r):
    return [(dc, dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (c + dc, r + dr) in cells]

def clip(pts, f):
    """Sutherland-Hodgman: keep the part of polygon pts where f(p) >= 0."""
    out = []
    for i in range(len(pts)):
        P, Q = pts[i], pts[(i + 1) % len(pts)]
        fp, fq = f(P), f(Q)
        if fp >= 0: out.append(P)
        if (fp >= 0) != (fq >= 0):
            s = fp / (fp - fq); out.append((P[0] + s * (Q[0] - P[0]), P[1] + s * (Q[1] - P[1])))
    return out

def split(pts, a, b, c, gap):
    """Cut polygon by line a*x + b*y = c, leaving a gap; returns the two sides."""
    n = math.hypot(a, b); a, b, c = a / n, b / n, c / n
    return [q for q in (clip(pts, lambda p: a * p[0] + b * p[1] - c - gap / 2),
                        clip(pts, lambda p: c - gap / 2 - a * p[0] - b * p[1])) if len(q) >= 3]

class G:
    """Glyph builder: polygons and circles, through an optional transform xf(x, y) -> (x, y)."""
    def __init__(self, xf=None):
        self.pen, self.xf = TTGlyphPen(None), xf or (lambda x, y: (x, y))
    def _pt(self, x, y):
        x, y = self.xf(x, y); return (round(x), round(y))
    def poly(self, pts):
        pts = [self._pt(*p) for p in pts]
        pts = [p for i, p in enumerate(pts) if p != pts[i - 1]]
        if len(pts) < 3: return
        area = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
        if abs(area) < 1: return
        if area > 0: pts = pts[::-1]                     # TrueType outer contours run clockwise
        self.pen.moveTo(pts[0]); [self.pen.lineTo(p) for p in pts[1:]]; self.pen.closePath()
    def circle(self, x, y, r, rx=1.0):
        k = 1 / math.cos(math.pi / 8)
        on = lambda a: self._pt(x + r * rx * math.cos(a), y + r * math.sin(a))
        off = lambda a: self._pt(x + r * rx * k * math.cos(a), y + r * k * math.sin(a))
        self.pen.moveTo(on(0))
        for i in range(8):
            a0 = -i * math.pi / 4; self.pen.qCurveTo(off(a0 - math.pi / 8), on(a0 - math.pi / 4))
        self.pen.closePath()
    def glyph(self): return self.pen.glyph()

def build(family, path, fn, adv, merge=True):
    """fn(name, cells) -> TTGlyph. Writes a .ttf with A-Z, a-z and space."""
    order = [".notdef", "space"] + list(CELLS)
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({32: "space", **{ord(k): k for k in CELLS}})
    g = {n: TTGlyphPen(None).glyph() for n in (".notdef", "space")}
    g.update({k: fn(k, cs) for k, cs in CELLS.items()})
    fb.setupGlyf(g)
    glyf = fb.font["glyf"]
    fb.setupHorizontalMetrics({n: (int(adv), getattr(glyf[n], "xMin", 0)) for n in order})
    fb.setupHorizontalHeader(ascent=900, descent=-280)
    fb.setupNameTable({"familyName": family, "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=900, sTypoDescender=-280, usWinAscent=900, usWinDescent=280)
    fb.setupPost()
    if merge: removeOverlaps(fb.font)
    fb.save(path)

def varfont(family, tag, name, rng, masters, out, tmp):
    """masters: [(axis_value, fn, adv)]; rng = (min, default, max)."""
    ds = DesignSpaceDocument()
    a = AxisDescriptor(); a.tag, a.name = tag, name; a.minimum, a.default, a.maximum = rng; ds.addAxis(a)
    os.makedirs(tmp, exist_ok=True)
    for i, (v, fn, adv) in enumerate(masters):
        p = f"{tmp}/{family.replace(' ', '')}_m{i}.ttf"; build(family, p, fn, adv, merge=False)
        s = SourceDescriptor(); s.path, s.location = p, {name: v}; ds.addSource(s)
    varLib.build(ds)[0].save(out)

_cache = {}
def inst(path, loc):
    key = (path, tuple(sorted(loc.items())))
    if key not in _cache:
        b = io.BytesIO(); instancer.instantiateVariableFont(TTFont(path), loc).save(b); _cache[key] = b.getvalue()
    return _cache[key]
def F(src, size): return ImageFont.truetype(io.BytesIO(src) if isinstance(src, bytes) else src, size)
LABEL = ImageFont.load_default(size=22)

def specimen(out, bg, dim, statics, vf):
    """statics: [(label, font_path, colour, sample)]; vf: (label, path, tag, values, sample, colour)."""
    img = Image.new("RGB", (1700, 1600), bg); d = ImageDraw.Draw(img); y = 40
    for label, src, col, sample in statics:
        d.text((50, y), label, font=LABEL, fill=dim); y += 40
        for txt, sz in (("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 46), ("abcdefghijklmnopqrstuvwxyz", 46), (sample, 120)):
            d.text((50, y), txt, font=F(src, sz), fill=col); y += int(sz * 1.35)
        y += 20
    label, path, tag, values, sample, col = vf
    d.text((50, y), label, font=LABEL, fill=dim); y += 40
    for v in values:
        d.text((50, y), sample, font=F(inst(path, {tag: v}), 84), fill=col)
        d.text((1450, y + 30), f"{tag} {v}", font=LABEL, fill=dim); y += 120
    img.crop((0, 0, 1700, y + 20)).save(out)

def save_gif(frames, out, duration, strip_frames=None, strip_out=None):
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=duration, loop=0)
    if strip_frames:
        W, H = frames[0].size; s = Image.new("RGB", (W, H * len(strip_frames)))
        for k, i in enumerate(strip_frames): s.paste(frames[i], (0, H * k))
        s.save(strip_out)
