# Cutout Patterns, MDF Cutting & 13 mm WS2812 LED Mounting Tutorial

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC--BY--NC--4.0-lightgrey.svg)](../LICENSE)

This guide walks you step by step through building the 1:1 cutout pattern, cutting the tree out of MDF, drilling the 60 LED holes, optionally spray-painting the ornaments, and mounting a **13 mm WS2812 RGB LED strip / pixel strand** (`60 LEDs`, indices `0–59`).

---

## Available Sizes & Files

Each tree size (`40 cm`, `85 cm`, `105 cm`) is available as a complete manufacturing ZIP on the [GitHub Releases](https://github.com/chatelao/aity-xmas-2026/releases) page (`aity-xmas-tree-2026_{40cm,85cm,105cm}.zip`) and in this folder:

| Tree Height | Tree Width | A4 Cutout PDF | 1:1 Tree + LEDs SVG | Laser Stencil SVGs (`5 cm` border) |
|---|---|---|---|---|
| **40 cm** | `27.9 cm` | [`tree_cutout_a4_40cm.pdf`](tree_cutout_a4_40cm.pdf) | [`tree_40cm_1to1.svg`](laser_stencils/40cm/tree_40cm_1to1.svg) | [`laser_stencils/40cm/`](laser_stencils/40cm) (7 steps) |
| **85 cm** | `59.2 cm` | [`tree_cutout_a4_85cm.pdf`](tree_cutout_a4_85cm.pdf) | [`tree_85cm_1to1.svg`](laser_stencils/85cm/tree_85cm_1to1.svg) | [`laser_stencils/85cm/`](laser_stencils/85cm) (7 steps) |
| **105 cm** | `73.2 cm` | [`tree_cutout_a4_105cm.pdf`](tree_cutout_a4_105cm.pdf) | [`tree_105cm_1to1.svg`](laser_stencils/105cm/tree_105cm_1to1.svg) | [`laser_stencils/105cm/`](laser_stencils/105cm) (7 steps) |

> [!TIP]
> If you have access to a laser cutter or CNC router large enough for your tree size, you can cut the tree outline and all 60 LED holes directly from `tree_{40,85,105}cm_1to1.svg` and skip Steps 1–3 below.

---

## Tools & Materials

- **Wood:** MDF board (`6–12 mm` thick for `40 cm`; `10–16 mm` thick for `85 cm` / `105 cm`)
  - *Note on thickness:* Standard 12–13 mm WS2812 bullet pixels have a ~10–12 mm mounting collar. If you use MDF thicker than `12 mm`, counterbore the back of each hole slightly or secure the pixels with hot glue / silicone.
- **LEDs:** 60 × **13 mm WS2812 RGB LED** strand / pixel strip (`5 V`, `DIN`, `GND`)
- **Pattern Assembly:** Printer (A4 paper), scissors or hobby knife, metal ruler, glue stick or clear tape
- **Woodworking:** Jigsaw (fine wood blade) or scroll saw, sandpaper (`120` & `240` grit), clamps, sacrificial scrap wood backing board
- **Drilling:** Center punch / awl, `3 mm` pilot drill bit, **`13 mm` brad-point wood bit or Forstner bit** (plus a `12.5 mm` bit if you want to test for a tighter press-fit)
- **Finishing (optional):** Wood primer, base paint, spray paint + ornament stencils, painter's tape / masking paper

---

## Step 1: Print & Assemble the 1:1 Cutout Pattern

1. Open `tree_cutout_a4_{40,85,105}cm.pdf`.
2. **Print at 100% ("Actual Size" / Scale 1.0)** — make sure **"Fit to Page" is disabled** in your PDF viewer/printer dialog.
3. On **Page 1 (Assembly Overview)**, measure the **100 mm calibration bar** with a ruler. It must measure **exactly 100.0 mm**.
4. Lay out the numbered tile pages (`R1C1`, `R1C2`, ...) according to the overview grid on Page 1.
5. For each seam:
   - Cut along the dashed red **`CUT ON THIS LINE`** edge on the overlapping tile.
   - Apply glue stick or double-sided tape to the light-orange **`GLUE AREA (15mm)`** strip of the neighboring tile.
   - Align the cut edge flush on the dashed line and match the **`(+)` registration crosshairs** at the corners and along the seam.
6. Once all tiles are joined and dry, roughly trim the excess white paper around the tree (leave ~2–3 cm margin so it is easy to tape down).

---

## Step 2: Transfer & Cut the Wood (MDF)

1. Place your MDF board on a flat workbench.
2. Attach the assembled 1:1 paper template flat onto the **front** face of the MDF using:
   - light spray adhesive, **or**
   - a glue stick / painter's tape along the edges (make sure the paper lies completely flat with no bubbles).
3. Clamp the MDF securely to your workbench with overhang for the saw blade.
4. **Cut the outer tree outline** using a jigsaw (fine-tooth wood/laminate blade) or scroll saw:
   - Cut ~0.5–1 mm outside the black outline if you want to sand right up to the line for a crisp edge.
   - Take tight inner corners slowly or make relief cuts into waste material first.
5. **Sand the cut edges** with `120` grit, then `240` grit sandpaper until smooth. *(Keep the paper template on the front face for Step 3!)*

---

## Step 3: Center-Punch & Drill the 60 LED Holes (13 mm)

1. **Mark all 60 LED centers (`0–59`):**
   - With the paper template still attached, use an awl or center punch to make a clear dimple at the exact center of every blue **`(+)` crosshair** (`0` through `59`).
   - Double-check that all 60 positions are punched before removing the paper.
   - Peel off the paper template (keep it nearby so you can read the `0–59` LED order later!).
2. **Test-fit on scrap MDF first:**
   - Drill a test hole in a scrap piece of the same MDF using your **`13 mm` brad-point / Forstner bit**.
   - Push one 13 mm WS2812 pixel into the hole. Some "13 mm" pixels measure `12.3–12.8 mm` at the collar — if `13 mm` is slightly loose, test a `12.5 mm` bit or plan to add a dab of hot glue from the back.
3. **Drill the 60 holes:**
   - Place a **sacrificial scrap wood board** tightly underneath the MDF to prevent tear-out on the back side.
   - *(Recommended)* Drill a `3 mm` pilot hole at each center-punched dimple first — this keeps the `13 mm` bit from wandering.
   - Drill straight down (perpendicular to the board; use a drill press or portable drill guide if available) with the `13 mm` bit at moderate speed.
   - Lightly deburr the front and back edges of each hole with `240` grit sandpaper.

---

## Step 4: Paint & Spray the Ornaments (Optional)

1. Apply wood primer and your base tree color (e.g. dark green or matte black/white) to the MDF and let it dry completely.
2. Cut out the ornament stencils from the last pages of `tree_cutout_a4_*.pdf`, **or** laser-cut the ready-made 1:1 SVGs in [`laser_stencils/`](laser_stencils/) (in paper, cardboard, or acrylic).
   - The laser-cut SVGs include a **5 cm (50 mm) border** around every ornament so you can tape protective painter's paper / masking paper around the stencil to prevent overspray.
3. For multi-layer ornaments (**Bauble / Kugel** = 3 steps, **Snowflake Large / Schnee-Gross** = 2 steps):
   - Cut/use the `2 mm` corner **`ALIGN`** holes in Layer 1 and mark or pin them on the tree so Layers 2 & 3 snap into exact registration.
4. Spray in light, thin passes from ~20–25 cm away and let each layer dry before placing the next stencil.

---

## Step 5: Mount & Wire the 13 mm WS2812 RGB LED Strip

1. **Check the data direction (`DIN → DOUT`):**
   - Locate the **input end (`DIN`)** of your 60-LED WS2812 strand (marked with an arrow or `DI`/`DIN` on the PCB/wire).
2. **Insert LEDs `0` to `59` from the BACK of the MDF:**
   - Match the LED numbers `0–59` shown on your paper pattern (or `tree_*_1to1.svg`):
     - **`0–17`**: Lower bough (`SEG_BOUGH_LOW`)
     - **`18–31`**: Middle bough (`SEG_BOUGH_MID`)
     - **`32–44`**: Upper bough (`SEG_BOUGH_HIGH`)
     - **`45–49`**: Stem / connecting arc (`SEG_STEM`)
     - **`50–59`**: Star (`SEG_STAR`)
   - Push each pixel firmly through its `13 mm` hole until the front collar sits flush.
   - If any pixel sits loosely, secure it from the back with a small dab of hot glue.
3. **Connect to your XIAO controller (`RP2040` or `ESP32-C6`):**
   - `DIN` → **`D10`** (recommended: via a `330 Ω` inline resistor near the first LED)
   - `5V` → **`5V`** (for high brightness with 60 LEDs, use an external `5V` PSU capable of `2–3 A` and place a `470–1000 µF` capacitor across `5V` and `GND`)
   - `GND` → **`GND`** (common ground between PSU, controller, and LED strand)
4. Flash CircuitPython or Arduino firmware using [HOWTO_RP2040.md](../HOWTO_RP2040.md) or [HOWTO_ESP32-C6.md](../HOWTO_ESP32-C6.md) and test all 60 LEDs!

---

## License

Licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)**. See [`LICENSE`](../LICENSE) or <https://creativecommons.org/licenses/by-nc/4.0/>.
