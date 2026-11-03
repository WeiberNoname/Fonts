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

## Fonts

| Folder | Font | Type |
|---|---|---|
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
```

## Unreal notes

- Drag a `.ttf` into the Content Browser to get a Font Face, then use it in UMG or a Text Render component.
- Variable-font axes aren't animated by Unreal's text renderer. Export instances, or animate with a material.
- Neon in-world: use a Text Render with an emissive material (colour × intensity × ~20), let bloom do the glow, and drive intensity from `Time` + noise for flicker.

## Not done yet

Digits, punctuation, kerning, accented characters, and a finer grid for M/N/W.

Made with AI assistance (Claude).
