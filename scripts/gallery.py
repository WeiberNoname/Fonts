"""Overview gallery for the README: one panel per style, each in its own colours.
Run from repo root after fonts exist in fonts/: python scripts/gallery.py -> previews/gallery.png"""
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from gridlib import F, LABEL, inst

W, PH = 1600, 190
PANELS = [  # (label, font, sample, bg, fg, extra)
    ("v1  DOTS",       "fonts/v1-dots/GRID-Block.ttf",          "Pixel Signal",   (8, 12, 22),    (94, 242, 255), None),
    ("v2  FUTURISTIC", "fonts/v2-futuristic/GRID-Velocity.ttf", "Hyperdrive",     (6, 9, 18),     (94, 242, 255), None),
    ("NEON",           inst("fonts/v2-futuristic/GRID-Pulse-VF.ttf", {"wght": 380}), "Neon City",      (7, 5, 14),     (255, 60, 180), "glow"),
    ("v3  SPEED",      "fonts/v3-speed/GRID-Apex-Streak.ttf",   "Lights Out",     (14, 14, 17),   (230, 20, 20),  None),
    ("v4  TITAN",      "fonts/v4-titan/GRID-Titan.ttf",         "Titanic",  (20, 16, 12),   (236, 224, 198), None),
    ("v5  PUP",        "fonts/v5-pup/GRID-Puppy.ttf",           "Good Boy",       (255, 243, 222), None,           "toon"),
    ("v6  GLITCH",     "fonts/v6-glitch/GRID-Glitch-Hard.ttf",  "Corrupted",      (8, 8, 10),     (255, 40, 90),  None),
    ("v7  RUNE",       "fonts/v7-rune/GRID-Rune-Carved.ttf",    "Dragon Gate",    (16, 18, 22),   (90, 235, 210), "glow"),
    ("v8  SUMI",       "fonts/v8-ink/GRID-Sumi.ttf",            "Way of Ink",     (238, 230, 212), (28, 24, 30),  None),
]
TILES = [(240, 70, 80), (255, 150, 40), (250, 205, 50), (90, 190, 90), (60, 160, 235), (160, 100, 220)]
out = Image.new("RGB", (W, PH * len(PANELS)))
for i, (label, path, sample, bg, fg, extra) in enumerate(PANELS):
    p = Image.new("RGB", (W, PH), bg); d = ImageDraw.Draw(p); fnt = F(path, 110)
    if extra == "toon":
        x = 330
        for k, ch in enumerate(sample):
            if ch != " ":
                d.text((x + 4, 38 + 8), ch, font=fnt, fill=(220, 190, 150), stroke_width=7, stroke_fill=(220, 190, 150))
                d.text((x, 38), ch, font=fnt, fill=TILES[k % 6], stroke_width=7, stroke_fill=(74, 46, 30))
            x += fnt.getlength(ch)
    elif extra == "glow":
        m = Image.new("L", (W, PH)); ImageDraw.Draw(m).text((330, 30), sample, font=fnt, fill=255)
        col = Image.merge("RGB", [m.point(lambda v, c=c: v * c // 255) for c in fg])
        for r in (18, 18, 5): p = ImageChops.add(p, col.filter(ImageFilter.GaussianBlur(r)))
        p = ImageChops.add(p, Image.merge("RGB", [m.point(lambda v, c=c: v * (c + (255 - c) * 6 // 10) // 255) for c in fg]))
        d = ImageDraw.Draw(p)
    else:
        d.text((330, 30), sample, font=fnt, fill=fg)
    dark = sum(bg) < 300
    d.text((40, PH // 2 - 12), label, font=LABEL, fill=(150, 150, 165) if dark else (130, 110, 90))
    d.line((300, 30, 300, PH - 30), fill=(60, 60, 70) if dark else (210, 195, 170), width=2)
    out.paste(p, (0, PH * i))
out.save("previews/gallery.png")
print("done")
