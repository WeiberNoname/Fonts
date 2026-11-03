"""Neon sign renderer for GRID fonts: dead glass tube + wide bloom + tight halo + white-hot core, with flicker.
Each variant = font + tube style + colour. Outputs out2/neon/<name>.gif, a still per variant, and a comparison sheet."""
import io, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from fontTools.varLib import instancer
from fontTools.ttLib import TTFont

def inst(path, loc):
    b = io.BytesIO(); instancer.instantiateVariableFont(TTFont(path), loc).save(b); b.seek(0); return b.getvalue()
PULSE, MORPH, VEL = "out2/fonts/GRID-Pulse-VF.ttf", "out2/fonts/GRID-Morph-VF.ttf", "out2/fonts/GRID-Velocity.ttf"

# name: (font bytes/path, outline-tube?, colour)
VARIANTS = {
    "neon-thin":      (inst(PULSE, {"wght": 200}), False, (255, 60, 180)),
    "neon-regular":   (inst(PULSE, {"wght": 330}), False, (50, 225, 255)),
    "neon-thick":     (inst(PULSE, {"wght": 650}), False, (255, 140, 40)),
    "neon-heavy-outline": (VEL, True, (60, 255, 140)),          # double-tube sign look
    "neon-wide":      (inst(MORPH, {"wdth": 150}), False, (170, 90, 255)),
}
W, H, N = 1250, 340, 56
BG, OFF = (7, 5, 14), (38, 26, 44)
LINES = [("NEON CITY", 112, 50, 2), ("open all night", 74, 205, 9)]   # text, size, y, broken letter

def power(f):
    if f < 10: return [0, .5, 0, 0, .9, .2, 1, .6, 1, 1][f]
    if 34 <= f < 41: return [.3, 1, 0, 0, .8, .4, 1][f - 34]
    return 1.0

def font(src, size): return ImageFont.truetype(io.BytesIO(src) if isinstance(src, bytes) else src, size)
def tint(mask, col): return ImageChops.multiply(Image.merge("RGB", [mask] * 3), Image.new("RGB", mask.size, col))

def frame(src, outline, col, f, rng):
    lit, dead = Image.new("L", (W, H)), Image.new("L", (W, H))
    dl, dd = ImageDraw.Draw(lit), ImageDraw.Draw(dead)
    for text, size, y, broken in LINES:
        fnt, x = font(src, size), 60
        for i, ch in enumerate(text):
            v = power(f) * (rng.choice([1, 1, 0, .15, 1, .5, 0, 1]) if i == broken else 1)
            dd.text((x, y), ch, font=fnt, fill=255); dl.text((x, y), ch, font=fnt, fill=int(255 * v))
            x += fnt.getlength(ch)
    if outline:   # hollow the strokes: mask minus eroded mask = two thin tubes per stroke
        lit = ImageChops.subtract(lit, lit.filter(ImageFilter.MinFilter(7)))
        dead = ImageChops.subtract(dead, dead.filter(ImageFilter.MinFilter(7)))
    hot = tuple(int(c + (255 - c) * .65) for c in col)
    img = ImageChops.add(Image.new("RGB", (W, H), BG), tint(dead, OFF))
    glow = tint(lit, col)
    for r in (28, 28, 7): img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(r)))
    return ImageChops.add(img, tint(lit, hot).filter(ImageFilter.GaussianBlur(1)))

os.makedirs("out2/neon", exist_ok=True)
stills = []
for name, (src, outline, col) in VARIANTS.items():
    rng = random.Random(7)
    frames = [frame(src, outline, col, f, rng) for f in range(N)]
    frames[0].save(f"out2/neon/{name}.gif", save_all=True, append_images=frames[1:], duration=65, loop=0)
    still = frame(src, outline, col, 20, random.Random(1)); still.save(f"out2/neon/{name}.png"); stills.append((name, still))

sheet = Image.new("RGB", (W, H * len(stills)), BG)
for i, (name, s) in enumerate(stills):
    sheet.paste(s, (0, i * H)); ImageDraw.Draw(sheet).text((W - 330, i * H + 20), name, font=ImageFont.load_default(size=22), fill=(120, 130, 160))
sheet.save("out2/neon/neon-variants.png")
print("done")
