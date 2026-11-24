# Verpackungskonzept – AITY Weihnachtsbaum 2026 (10 cm PCB)

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC--BY--NC--4.0-lightgrey.svg)](../LICENSE)

Dieses Verzeichnis enthält das gegen die KiCad-Platinendaten geprüfte Verpackungskonzept, **acht ausgearbeitete Verpackungsvarianten (A–H)** sowie direkt nutzbare **1:1 Stanz- und Lasercutter-Vorlagen (SVG)** für die kleinen **10 cm PCB-Tannenbäume** (`aity-xmas-tree-2026`).

---

## Dokumente & 1:1 Vorlagen im Überblick

| Datei | Inhalt |
|---|---|
| [`KONZEPT.md`](KONZEPT.md) | Geprüftes Verpackungskonzept: KiCad-Hardware-Audit (USB-C zeigt nach oben, konischer Stamm, Stern ohne Bohrloch, 9 Touch-Kugeln), ESD-Schutz, Pergamin-Diffusor & „Power-On-in-Box“-Idee, CH/DE/AT-Briefversand (`≤ 20 mm`) |
| [`VARIANTEN.md`](VARIANTEN.md) | Detailvergleich von **8 Verpackungsvarianten (A–H)** inkl. der neuen Konzepte **G („Laternen-Sleeve“ Tischleuchte)** und **H („Matchbox-Stage“ Schubladenbox)**, Stückkosten & Zielgruppen-Empfehlung |
| [`generate_packaging_templates.py`](generate_packaging_templates.py) | Python-Generator: extrahiert die bereinigte Einzel-Außenkontur (ohne Doppelschleife), berechnet echten `+1,0 mm` Parallel-Offset und erzeugt alle 6 SVG-Vorlagen ohne verschachtelte Transforms |
| [`templates/flat_mail_card_a6.svg`](templates/flat_mail_card_a6.svg) | **Variante A:** 1:1 DIN-A6 Klappkarte mit 4 formschlüssigen Asttal-Laschen (verdeckt 0 LEDs) |
| [`templates/folding_box_125x95x20_dieline.svg`](templates/folding_box_125x95x20_dieline.svg) | **Variante B:** 1:1 Faltschachtel-Dieline (`125 × 95 × 20 mm`), passt komplett auf **DIN A4** |
| [`templates/stand_insert_1to1.svg`](templates/stand_insert_1to1.svg) | **Variante B, D & F:** 1:1 **Klemm-Standfuß** (`1,75 mm` FR4-Klemmschlitze für den konischen Stamm) + **Sternhals-Aufhängeclip** |
| [`templates/inlay_foam_1to1.svg`](templates/inlay_foam_1to1.svg) | **Variante C & D:** 1:1 2-Lagen-Inlay mit `+1,0 mm` Parallel-Offset, Greifmulden sowie nach oben erweitertem XIAO/USB-C- & Buzzer-Fenster |
| [`templates/lantern_sleeve_125x90x18.svg`](templates/lantern_sleeve_125x90x18.svg) | **Variante G (NEU):** 1:1 Diffusor-Schuber (`125 × 90 × 18 mm`, DIN A4) mit Pergamin-Baumfenster, Buzzer-Schalllöchern & USB-C-Perforation |
| [`templates/laser_slide_box_3mm.svg`](templates/laser_slide_box_3mm.svg) | **Variante D (NEU):** 1:1 Lasercutter-Teilesatz für eine `3,0 mm` Sperrholz-Schiebebox (`130 × 98 × 24 mm`) mit Fingerzinken & Namensgravur-Feld |

---

## Technisches Kurzprofil (verifiziert gegen `aity-xmas-tree-2026.kicad_pcb`)

| Eigenschaft | Geprüfter Wert | Relevanz für die Verpackung |
|---|---|---|
| **Platinenmaße (B × H × D)** | **69,41 × 99,60 × 1,6 mm** | Passt in DIN A6 (`105 × 148 mm`), Eckdiagonale für Kugeln: `~104 mm` (`→ Ø 120 mm` Kugel) |
| **Konischer Wurzelstamm** | Oben **14,0 mm** → unten **18,17 mm** | Standfuß klemmt das `1,6 mm` FR4 über zwei `1,75 mm` Schlitze spielfrei |
| **Sternspitze (Aufhängung)** | **Kein Bohrloch**, Halsbreite **9,87 mm** | Eigener **Sternhals-Aufhängeclip** (`Ø 4,2 mm` Öse) auf dem Stanzbogen integriert |
| **Vorderseite (`F.Cu`)** | 60 × SK6812 (`1,5 × 1,5 mm`) + **9 × goldene Touch-Kugeln (`TP101–109`)** | Mind. `2–3 mm` Luftspalt + weiches Pergaminblatt (dient zugleich als **Lichtdiffusor**!) |
| **Rückseite (`B.Cu`)** | Seeed XIAO (`rot=180°`, **USB-C zeigt nach OBEN** bei `Y ≈ 66 mm`!) + Buzzer (`Y = 59 mm`) + Workshop-Widmung | Rückseitige Aussparung muss nach **oben** (`24 × 31 mm`) reichen; Standfuß lässt Mitte hinten offen fürs Kabel |
| **Gesamtdicke bestückt** | **~6,9 mm** (SMD-XIAO) / **~15 mm** (gesockelt) | SMD-Variante bleibt in `16–20 mm` Box innerhalb des **CH B4 / DE Großbrief-Limits (`≤ 20 mm`)** |

---

## Schnell-Empfehlung nach Zielgruppe

| Szenario | Empfohlene Variante | Warum? |
|---|---|---|
| **Allrounder (Geschenk & Post)** | **Variante B: „Pop-Up-Stand“ Faltschachtel** | Passt auf 1× DIN A4, Monomaterial Karton, inkl. Klemm-Standfuß & Sternclip |
| **Kreativ-Highlight (2-in-1 Leuchte)** | **Variante G: „Laternen-Sleeve“ (`18 mm`)** | Großbrieftauglich + Schachtel wird dank Pergamin-Fenster selbst zur **Tisch-Leuchtlaterne** |
| **Kids & Micro:bit-Workshops (Bern)** | **Variante D: „Maker-Laser“ 3-mm-Holzbox** | Individueller Vorname jedes Kindes auf dem Schiebedeckel gravierbar, super stabil im Rucksack |
| **Großes Weihnachtspost-Mailing** | **Variante A: „Flat-Mail“ A6-Klappkarte** | Günstigstes Briefporto (`≤ 20 mm` auch im Umschlag), Grußkarte + Anleitung + Halterung in einem |
| **VIPs, Sponsoren & Unterstützer** | **Variante C (ESD-Schaum)** oder **H (Schubladen-Bühne)** | Höchste Wertigkeit, Platz für 90°-USB-Kabel, Mini-Powerbank („Power-On-in-Box“) & Schöggeli |
| **Löt-/Coding-Bausatz** | **Variante E: ESD-Beutel + Header-Card** | Unter `0,90 CHF/€`, 100 % ESD-normgerecht, mit Namensfeld auf der Pinout-Rückenkarte |

---

## Vorlagen neu generieren

```bash
python3 packaging/generate_packaging_templates.py
```

---

## Lizenz

Lizenziert unter **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)**. Siehe [`LICENSE`](../LICENSE).
