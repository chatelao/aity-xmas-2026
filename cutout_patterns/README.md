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
- **Drilling:** Center punch / awl, **`1.5–2 mm` (`1/16"`) pilot drill bit**, **`0.4 inch` (`10 mm` / `13/32"`) brad-point wood bit** (front LED-only hole), and a **`13 mm` (or `14 mm`) Forstner bit with a depth-stop collar** (back counterbore pocket for the `12–13 mm` pixel body)
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

## Step 3: Center-Punch & Drill the 60 Stepped LED Holes (`0.4"` Front + `12–13 mm` Back)

Drilling a **`0.4 inch` (`10 mm`)** hole from the front for the LED dome and a **`12–13 mm`** counterbore pocket from the back for the larger pixel body gives the cleanest result: the pixel cannot push out through the front face, no collar shows on the front, and it works even on thicker MDF (`10–18 mm`).

To keep the front and back holes **100% concentric**, drill in this exact order:

1. **Center-punch all 60 LED centers (`0–59`):**
   - With the paper template still attached to the **front**, use an awl or center punch to dimple the exact center of every blue **`(+)` crosshair** (`0` through `59`).
   - Double-check that all 60 positions are punched, then peel off the paper template (keep it nearby so you can read the `0–59` LED order later!).
2. **Drill `1.5–2 mm` (`1/16"`) pilot holes all the way through:**
   - Place a **sacrificial scrap wood board** underneath the MDF.
   - Drill a small `1.5–2 mm` pilot hole straight through at every center-punched dimple. This transfers all 60 exact centers to the **back** of the MDF while staying small enough to guide a Forstner bit's center spur.
3. **Test-fit on scrap MDF first:**
   - On a scrap piece of the same MDF, drill a `13 mm` (or `13.5–14 mm`, depending on your exact pixel body) Forstner counterbore from the back and a `0.4 inch` (`10 mm`) hole from the front.
   - Verify that the LED dome/lens pokes cleanly through the `0.4"` front hole while the `12–13 mm` pixel body seats snugly in the back counterbore.
4. **Drill the `12–13 mm` counterbore pockets from the BACK (16 mm MDF guide):**
   - Flip the MDF over to the **back** face and clamp it **flat against a solid workbench** (an unsupported board can flex and cause uneven depth).
   - **Target depth for 16 mm MDF:** Measure your actual MDF thickness (often `15.8–16.2 mm`). Drill **`11–12 mm` deep**, leaving **`4–5 mm` of solid MDF** at the front face. *(This is thick enough that the front won't bulge or break out, while still letting the LED dome sit flush in the `0.4"` front hole.)*
   - **Measure from the outer cutting rim, NOT the center spur:** A Forstner bit's center spur sticks out `1.5–2 mm` ahead of the flat rim. Always measure your `11–12 mm` depth from the **flat outer cutting rim** of the bit.
   - **Use a physical depth stop (choose one):**
     - *Best — Drill press:* Lower the bit until the **outer rim** touches a `16 mm` scrap piece, set the quill depth stop to **`11–12 mm`**, and test on scrap first.
     - *Best for hand drill — Spacer sleeve + stop collar:* Slip a short piece of PVC pipe or drilled wood block over the Forstner shank and lock a metal depth-stop collar behind it so **exactly `11–12 mm`** of the bit (from the outer rim) protrudes. When the sleeve touches the MDF, the drill physically cannot go deeper.
     - *Quick method — Painter's tape flag:* Wrap a crisp flag of painter's tape around the bit **`11–12 mm` up from the outer rim** and stop the instant the bottom edge touches the surface.
   - **Peck-drill with light pressure (`800–1200 RPM`):** Drill `4–5 mm`, lift the bit to clear packed MDF dust, then finish down to the stop. Packed dust makes you push harder, which is the #1 cause of sudden plunge-through.
   - **Verify on scrap first:** Check the test pocket with calipers or a depth gauge to confirm `4–5 mm` of MDF remains before drilling all 60 holes.
5. **Drill the `0.4 inch` (`10 mm`) LED-only holes from the FRONT:**
   - Flip the MDF back to the **front** face.
   - Using the **`0.4 inch` (`10 mm` / `13/32"`) brad-point bit**, center the tip on each `1.5–2 mm` pilot hole and drill through the remaining `4–5 mm` of MDF into the back pocket.
   - Lightly deburr the front edges with `240` grit sandpaper.

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
   - Push each pixel firmly into its **`12–13 mm` back counterbore** until the LED dome seats cleanly in the **`0.4"` (`10 mm`) front hole**.
   - Secure each pixel from the back with a small dab of hot glue or silicone if the counterbore is not a tight press-fit.
3. **Connect to your XIAO controller (`RP2040` or `ESP32-C6`):**
   - `DIN` → **`D10`** (recommended: via a `330 Ω` inline resistor near the first LED)
   - `5V` → **`5V`** (for high brightness with 60 LEDs, use an external `5V` PSU capable of `2–3 A` and place a `470–1000 µF` capacitor across `5V` and `GND`)
   - `GND` → **`GND`** (common ground between PSU, controller, and LED strand)
4. Flash CircuitPython or Arduino firmware using [HOWTO_RP2040.md](../HOWTO_RP2040.md) or [HOWTO_ESP32-C6.md](../HOWTO_ESP32-C6.md) and test all 60 LEDs!

---

## License

Licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)**. See [`LICENSE`](../LICENSE) or <https://creativecommons.org/licenses/by-nc/4.0/>.
