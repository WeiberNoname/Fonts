# GRID Fonts

An experiment in building game fonts with code: one 5×7 grid skeleton, many styles (sci-fi HUD, neon, F1 speed, monumental, cute dog-themed, glitch, rune, ink brush), exported as real `.ttf` files for Unreal Engine.

![Neon variants](previews/neon/neon-variants.png)

## How it works

1. **Skeleton** (`scripts/skeleton.py`): every letter A–Z / a–z is a few rows of `#` cells on a 5×7 grid (2 extra rows for descenders).
2. **Renderer**: each style decides how a cell becomes outlines.
   - v1 (`gridfont.py`): each cell becomes a square/chamfered dot (LED look).
   - v2 (`gridfont2.py`): neighbouring cells join into strokes, and lone diagonals become 45° cuts (futuristic look).
3. **Shared library** (`scripts/gridlib.py`, used from v6 on): skeleton structure, polygon clipping, curves, export and preview helpers, so each style script only contains its design ideas.
4. **Export**: fontTools builds the glyphs, metrics and character map into `.ttf`. Variable fonts are built from 2–3 masters with identical point structure.
5. **Neon** (`neon.py`): a preview renderer with a dead glass tube, wide bloom, tight halo, white-hot core and per-letter flicker.

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

## v4: Titan (monumental, "dinosaur" weight)

![Titan specimen](previews/v4-titan/specimen.png)

The brief was letters that feel **stable, heavy, super strong**, like a giant you could walk into. Four design moves:

1. **Ultra-heavy strokes:** the stroke is about 19% of the cap height (Speed is about 12%), so counters shrink and the letters become solid mass.
2. **Slab feet:** every stem that ends at the bottom gets a wide, thick slab, and stem tops get a smaller cap. The letters look planted on the ground.
3. **Pyramid flare:** each glyph is scaled horizontally by height, about 30% wider at the baseline than at the top. Monuments, pyramids and a dinosaur's legs widen at the base, and that's what reads as *stable*.
4. **Fossil cracks:** in **GRID Titan Fossil**, every letter gets 1–2 near-vertical crack gaps at seeded random positions, so each letter cracks differently and consistently, like a stone tablet.

**GRID Stomp VF** has one custom axis, `MASS` (0–100). At 0 it's a light, plain monoline; at 100 it's full Titan (heavy, flared, slab-footed).

![Stomp animation](previews/v4-titan/stomp.gif)

In the animation, letters drop one by one (gravity: accelerating fall), each landing triggers **screen shake and a dust puff**, then "walk into it" gains `MASS` from 0 to 100. Key frames:

![Stomp frames](previews/v4-titan/stomp-frames.png)

**Ideas for Unreal:** boss names and chapter titles (Titan), ruins and ancient-temple signage (Fossil), and a camera shake plus dust Niagara burst timed to each letter landing for a title card.

## v5: Pup (dog-themed match-3)

![Pup specimen](previews/v5-pup/specimen.png)

A match-3 game about dogs needs the opposite of Titan: **soft, round, chewable, happy**. The design moves:

1. **Puffy round strokes:** every cell is a real curve-built circle (quadratic Béziers), joined by bars, so all ends and joints are rounded like plush toys or candy tiles. Overlaps are merged into clean outlines.
2. **Paw-print dots:** the dots on `i` and `j` are replaced with a paw (one pad and four toes). Small detail, instant theme.
3. **Bone endings (GRID Bone):** every stroke that ends gets two round knobs perpendicular to the stroke, like the end of a dog bone. The script finds endings automatically: cells with exactly one straight neighbour and no diagonal.
4. **Match-3 presentation:** tile colours per letter, a thick dark cartoon outline and a soft drop shadow. In Unreal this is UMG Outline and Shadow settings, so no extra font is needed.

**GRID Wag VF** has one custom axis, `SQSH` (-100 to 100). Negative values stretch (tall and narrow), positive values squash (short and wide), around the baseline. It's the classic animation principle of **squash and stretch**.

![Bounce animation](previews/v5-pup/bounce.gif)

In the animation, letters hop in a wave like an excited puppy. Each letter **squashes on landing and stretches in the air**, and its ground shadow shrinks while it's airborne. Key frames:

![Bounce frames](previews/v5-pup/bounce-frames.png)

**Ideas for Unreal:** combo text ("Good Boy!", "Pawsome!") bouncing in with Wag instances; Bone for score and buttons; paw-dot `i` in the title logo; a Niagara burst of paw prints on match.

## v6: Glitch (corrupted signal, horror / hacking)

![Glitch specimen](previews/v6-glitch/specimen.png)

Letters that look like a damaged video signal:

1. **Band slicing:** every stroke polygon is cut into horizontal bands (52 units tall) with a thin slit between them, like scanlines.
2. **Seeded shifts:** about 45% of the bands slide sideways by a random amount. The random seed is the glyph's name, so each letter is always corrupted the same way and the font stays consistent.
3. **Dropouts:** some bands disappear entirely (5% in Glitch, 13% in Glitch Hard).

**GRID Glitch VF** has a `GLCH` axis (0–100). At 0 the bands line up (clean, with scanlines); at 100 they're fully displaced. Because the slicing is identical in both masters and only the shift changes, the outlines stay compatible.

![Glitch animation](previews/v6-glitch/glitch.gif)

In the animation, `GLCH` sits calm with random spikes and a full meltdown in the middle. The renderer adds an **RGB channel split** that grows with corruption, **screen tears** (shifted horizontal strips) and CRT scanlines. Key frames (clean, mild, meltdown):

![Glitch frames](previews/v6-glitch/glitch-frames.png)

**Ideas for Unreal:** horror jump-scare text, hacking minigames, "signal lost" screens; drive a material's UV offset per band with noise for an in-engine version.

## v7: Rune (carved fantasy)

![Rune specimen](previews/v7-rune/specimen.png)

Letters that look cut into stone with a chisel:

1. **Chisel contrast:** vertical strokes are twice as thick as horizontal ones (92 vs 46 units), the way a flat chisel or broad pen makes thick downstrokes and thin cross-strokes.
2. **Wedge spikes:** every stroke ending sharpens into a point, giving an aggressive, ancient-weapon feel. Lone dots become diamond gems.
3. **V-groove carving (Rune Carved):** every stroke is split down its centre line with a thin gap, so each stroke reads as two bevelled faces, like a real inscription.

**GRID Rune VF** has an `EDGE` axis (0–100) that grows the spikes from blunt stubs to long blades.

![Awaken animation](previews/v7-rune/awaken.gif)

In the animation, carved stone letters **ignite one by one** with a magic glow (bloom, halo and a hot core, the same pipeline as the neon fonts) and embers rising from the lit runes. Key frames:

![Awaken frames](previews/v7-rune/awaken-frames.png)

**Ideas for Unreal:** dungeon doors and ancient tablets (decals with an emissive material that lights up on interaction), spell names, fantasy quest titles.

## v8: Sumi (ink brush)

![Sumi specimen](previews/v8-ink/specimen.png)

Bringing a brush feel to a rigid grid:

1. **Brush pressure:** every stroke run starts thick (142%) and thins toward the end (42%), left to right and top to bottom, the way a brush loses ink as it moves.
2. **Ink blobs and lift-off tips:** each joint is a round ink pool, and stroke endings taper to a sharp point where the brush leaves the paper.
3. **Hand tremor:** each glyph is rotated up to ±2.5° and shifted up or down slightly (seeded, so it's consistent), so words don't look machine-set.
4. **Dry brush (Sumi Dry):** thin streak gaps run along each stroke, like bristles running out of ink.

**GRID Sumi VF** has an `INKS` axis (0–100), from a thin, dry brush to a heavy, wet one.

![Brush animation](previews/v8-ink/brush.gif)

In the animation, each letter is **painted by a brush sweep** on textured rice paper, with soft ink bleed at the edges, then a red **hanko seal** stamps down to finish. Key frames:

![Brush frames](previews/v8-ink/brush-frames.png)

**Ideas for Unreal:** samurai and martial-arts titles, Japanese-themed menus, story scrolls; animate a material mask sweep for the brush-reveal effect.

## Fonts

| Folder | Font | Type |
|---|---|---|
| `fonts/v8-ink` | GRID Sumi | static, brush pressure, ink blobs, tremor |
| | GRID Sumi Dry | static, dry-brush streaks |
| | GRID Sumi VF | variable: `INKS` (dry thin to wet heavy) |
| `fonts/v7-rune` | GRID Rune | static, chisel contrast, wedge spikes |
| | GRID Rune Carved | static, V-groove carving |
| | GRID Rune VF | variable: `EDGE` (blunt to spiked) |
| `fonts/v6-glitch` | GRID Glitch | static, sliced and shifted bands |
| | GRID Glitch Hard | static, heavy corruption |
| | GRID Glitch VF | variable: `GLCH` (clean to corrupted) |
| `fonts/v5-pup` | GRID Puppy | static, puffy round strokes, paw-print dots |
| | GRID Bone | static, bone-knob stroke endings |
| | GRID Wag VF | variable: `SQSH` (stretch to squash) |
| `fonts/v4-titan` | GRID Titan | static, ultra heavy, slab feet, pyramid flare |
| | GRID Titan Fossil | static, Titan with cracked-stone splits |
| | GRID Stomp VF | variable: `MASS` (light to monumental) |
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
python scripts/titanfont.py    # v4 titan fonts + previews -> out4/
python scripts/dogfont.py      # v5 pup fonts + previews -> out5/
python scripts/glitchfont.py   # v6 glitch -> out6/
python scripts/runefont.py     # v7 rune -> out7/
python scripts/inkfont.py      # v8 ink brush -> out8/ (needs v7 built for the seal)
```

## Unreal notes

- Drag a `.ttf` into the Content Browser to get a Font Face, then use it in UMG or a Text Render component.
- Variable-font axes aren't animated by Unreal's text renderer. Export instances, or animate with a material.
- Neon in-world: use a Text Render with an emissive material (colour × intensity × ~20), let bloom do the glow, and drive intensity from `Time` + noise for flicker.

## Not done yet

Digits, punctuation, kerning, accented characters, and a finer grid for M/N/W.

Made with AI assistance (Claude).
