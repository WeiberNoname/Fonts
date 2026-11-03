# GRID Fonts

An experiment in building game fonts with code: sci-fi/HUD typefaces generated from a single 5×7 grid skeleton, exported as real `.ttf` files for Unreal Engine.

![Neon variants](previews/neon/neon-variants.png)

## How it works

1. **Skeleton** (`scripts/skeleton.py`): every letter A–Z / a–z is a few rows of `#` cells on a 5×7 grid (2 extra rows for descenders).
2. **Renderer**: each style decides how a cell becomes outlines.
   - v1 (`gridfont.py`): each cell becomes a square/chamfered dot (LED look).
   - v2 (`gridfont2.py`): neighbouring cells join into strokes, and lone diagonals become 45° cuts (futuristic look).
3. **Export**: fontTools builds the glyphs, metrics and character map into `.ttf`. Variable fonts are built from 2–3 masters with identical point structure.
4. **Neon** (`neon.py`): a preview renderer with a dead glass tube, wide bloom, tight halo, white-hot core and per-letter flicker.

## v3: Speed (F1-style racing fonts)

![Speed specimen](previews/v3-speed/specimen.png)

The goal was letters that feel fast before they even move. Four design moves do it, all applied to the same skeleton:

1. **Extended width:** columns are about 1.7× wider than rows, so letters stretch horizontally like they're being pulled.
2. **Heavy strokes:** thick stems give weight and power.
3. **Hard italic (16–18°):** everything leans forward, which reads as forward motion.
4. **The speed cut:** a thin, slightly rising slash cuts through every letter. It is done geometrically: each stroke polygon is clipped against two slanted lines (Sutherland–Hodgman), leaving a gap, and the overlaps are then merged into clean outlines with `removeOverlaps`.

**GRID Apex Streak** adds tapered **motion streaks** trailing off the left edge of each letter (rows 1, 3, 5), like the speed lines in racing graphics.

**GRID Throttle VF** has one custom axis, `SPED` (0–100). At 0 it is upright, narrow and light; at 100 it is wide, heavy and race-italic. Animating it reads like a car accelerating.

![Speed animation](previews/v3-speed/speed.gif)

The animation preview shows the text flying in with horizontal motion blur, braking to `SPED 0` (upright), revving back to 100, and blasting out. Key frames:

![Speed frames](previews/v3-speed/speed-frames.png)

**Ideas for Unreal:** drive the `SPED` look in-game by swapping exported instances (0/25/50/75/100) on boost; use Apex Streak for lap times and position banners; put a UMG animation with a quick X-translation and a blur material on title cards.

## Fonts

| Folder | Font | Type |
|---|---|---|
| `fonts/v3-speed` | GRID Apex | static, heavy extended italic with speed cut |
| | GRID Apex Streak | static, Apex plus motion streaks |
| | GRID Throttle VF | variable: `SPED` (upright to race italic) |
| `fonts/v2-futuristic` | GRID Neon | static, hairline HUD |
| | GRID Velocity | static, heavy extended italic |
| | GRID Pulse VF | variable: `wght` (stroke thickness) |
| | GRID Morph VF | variable: `wdth` (extension), `slnt` (lean) |
| `fonts/v1-dots` | Block, Stencil, Pulse VF, Morph VF | first dot-matrix experiment |

## Rebuild

```bash
pip install fonttools pillow
python scripts/gridfont.py     # v1 -> out/
python scripts/gridfont2.py    # v2 -> out2/
python scripts/neon.py         # neon previews -> out2/neon/ (needs v2 built first)
pip install skia-pathops       # needed by v3 for overlap removal
python scripts/speedfont.py    # v3 speed fonts + previews -> out3/
```

## Unreal notes

- Drag a `.ttf` into the Content Browser to get a Font Face, then use it in UMG or a Text Render component.
- Variable-font axes aren't animated by Unreal's text renderer. Export instances, or animate with a material.
- Neon in-world: use a Text Render with an emissive material (colour × intensity × ~20), let bloom do the glow, and drive intensity from `Time` + noise for flicker.

## Not done yet

Digits, punctuation, kerning, accented characters, and a finer grid for M/N/W.

Made with AI assistance (Claude).
