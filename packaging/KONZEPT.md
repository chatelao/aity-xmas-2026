# Verpackungskonzept – AITY Weihnachtsbaum 2026 (10 cm)

Dieses Dokument beschreibt das technisch geprüfte, ganzheitliche Verpackungskonzept für den **10 cm AITY Weihnachtsbaum 2026**. Ziel ist es, die empfindliche SMD-Elektronik zuverlässig zu schützen, ein festliches und interaktives Unboxing-Erlebnis zu schaffen und gleichzeitig wirtschaftliche Fertigung sowie günstigen Postversand (CH / DE / AT) zu ermöglichen.

---

## 1. Technische Produktanalyse & Konstruktions-Audit (aus KiCad)

Alle Geometrie- und Bauteildaten wurden direkt gegen [`kicad/aity-xmas-tree-2026.kicad_pcb`](../kicad/aity-xmas-tree-2026.kicad_pcb) verifiziert. Dabei zeigen sich **vier entscheidende konstruktive Besonderheiten**, die jede funktionierende Verpackung berücksichtigen muss:

### 1.1 Exakte Platinen-Geometrie

- **Außenmaße (B × H):** `69,41 mm × 99,60 mm` (`X = 3,00..72,41 mm`, `Y = 3,00..102,60 mm`)
- **Platinendicke:** `1,6 mm` FR4
- **Besonderheit 1 – Konischer Wurzelstamm (nach unten breiter!):**
  - Stamm-Taille oben unter den Ästen (`Y = 89,2 mm`): **`14,02 mm`** schmal (`X = 30,69..44,71 mm`)
  - Stamm-Mitte (`Y = 96,8 mm`): **`15,8 mm`** breit
  - Stamm-Fuß unten (`Y = 101,0..102,6 mm`): **`18,17 mm`** breit (`X = 28,61..46,78 mm`)
  - *Konsequenz für Standfüße:* Ein einfaches Loch im Standfuß muss entweder `18,5 mm` breit sein (wobei der Stamm oben seitlich Spiel hätte) oder der Standfuß nutzt **zwei geschlitzte Steckwangen von unten** (`1,75 mm` Klemmschlitz auf das `1,6 mm` FR4), die den Stamm unabhängig von seiner Kegelform spielfrei klemmen!
- **Besonderheit 2 – Kein Aufhängeloch im Stern:**
  - Die Platine besitzt `0` Montagebohrungen im Stern (`Edge.Cuts` ist komplett geschlossen, nur 0,3/0,4 mm Durchkontaktierungen).
  - Der Stern hat jedoch zwei ausgeprägte Einschnürungen: unter den seitlichen Sternspitzen (`Y = 16,0 mm`, Breite **`9,87 mm`**) und am Sternhals (`Y = 23,7 mm`, Breite **`11,50 mm`**).
  - *Konsequenz für Christbaum-Aufhängung:* Eine einfache Schnur rutscht ohne Loch ab – beigelegt oder eingelasert wird daher ein winziger **Aufhänge-Clip / Schlaufen-Adapter** für den `9,9 mm` Sternhals!

### 1.2 Bauteil-Topografie & USB-C-Einbaurichtung

- **Vorderseite (`F.Cu`):**
  - 60 × `SK6812` Mini-RGB-LEDs (`1,5 × 1,5 mm`, Bauhöhe `~0,8 mm`)
  - 10 × `0603` Abblockkondensatoren
  - **9 × kapazitive Touch-/Testpunkt-Christbaumkugeln** (`TP101`–`TP109` als vergoldete `xmas:Kugel`-Pads direkt auf der Vorderseite!) sowie vergoldeter Stern & Gold-Umrandung.
- **Rückseite (`B.Cu`):**
  - **Seeed Studio XIAO (`U101`)** bei `X = 36,87 mm, Y = 77,87 mm` (`rot = 180°` auf `B.Cu`):
    - **Wichtig (USB-C zeigt nach OBEN!):** Durch die 180°-Rotation auf `B.Cu` sitzt die **USB-C-Buchse auf der Oberseite des XIAO bei `Y ≈ 66,2 mm`** (also Richtung Baumspitze, *nicht* unten am Stamm!).
    - Ein eingesteckter USB-C-Stecker benötigt von `Y = 66,2 mm` nach oben bis `Y ≈ 42 mm` freien Raum für Gehäuse und Kabelbiegeradius. Ein USB-C-Kabel führt daher **von der Platinenmitte in einem sanften Bogen nach hinten/unten** weg – oder es wird ein **90°-Winkelstecker** verwendet.
    - *Aufbauhöhe:* `~4,5 mm` SMD-direktgelötet (Gesamtdicke Baum `~6,9 mm`) bzw. `~12–13 mm` gesockelt (Gesamtdicke `~15 mm`).
  - **Magnetischer SMD-Buzzer (`LS101`, `CMT-8504-100-SMT`)** bei `X = 47,02 mm, Y = 59,27 mm` (`8,5 × 8,5 × 4,0 mm`), schräg rechts oberhalb des XIAO.
  - **Persönlicher Gruß auf `B.SilkS`:** Auf der Rückseite steht im Siebdruck die Widmung zum *„Weihnachtsprojekt 2026 – Für die Kiddies in der Micro:bit Gruppe / Workshops 2026 – Bern“* sowie *„Merry Christmas“*. Die Rückseite ist also bewusst liebevoll gestaltet und darf beim Auspacken gerne sichtbar werden!

### 1.3 Kritische Schadensrisiken & Gegenmaßnahmen

| Risiko | Ursache | Konstruktive Lösung im Verpackungskonzept |
|---|---|---|
| **Abscheren von 1,5 mm SK6812-LEDs** | Verrutschen der Platine oder Kontakt mit rauer Pappe/Kabel | Echter **+1,0 mm Parallel-Offset** im Kontur-Inlay (statt verzerrter Skalierung!) oder formschlüssige Halteschlitze in den Ast-Tälern (`Y = 39 mm` & `Y = 88 mm`) + mind. `2 mm` Freiraum über `F.Cu` |
| **Wipp- & Biegebruch über dem XIAO** | Einseitige Punktbelastung auf XIAO (`Y = 78 mm`) und Buzzer (`Y = 59 mm`) | Rückseitige Aussparung (`24 × 32 mm` inkl. USB-C-Überstand + `13 × 13 mm` für Buzzer), sodass die Platine flächig auf dem FR4-Rand aufliegt |
| **ESD-Schäden (Elektrostatik)** | Reibung in Standard-Plastikfolie, Acryl oder Styropor an 60 CMOS-LEDs + MCU + offenen Touch-Kugeln (`TP101–109`) | **ESD-Abschirmbeutel**, leitfähiger **ESD-Schaumstoff** oder trockener, unbeschichteter **Natur-/Kraftkarton**; keine ungeschützten Standard-PE-Tüten |
| **Kratzer auf Gold-ENIG-Kugeln** | Lose beigelegtes USB-C-Kabel scheuert auf `F.Cu` | Strikte Trennung in zweiter Ebene (Bodenfach unter dem Inlay) oder separater Kabeltasche |

---

## 2. Marken-, Zielgruppen- & Unboxing-Konzept

Aus der Platinen-Widmung (*Bern, Micro:bit-Gruppe, Workshops 2026*) und der Hardware ergeben sich **zwei Haupt-Zielgruppen**, die dasselbe Grunddesign mit leicht angepasster Tonalität abholt:

1. **Kids, Jugendliche & Workshop-Teilnehmende:** Spielerisch, motivierend, sofortiges Erfolgserlebnis („Dein eigener programmierbarer Weihnachtsbaum – steck ihn an, verbinde dich per Handy oder programmiere deine eigene Lichtshow!“).
2. **Unterstützer, Partner, Kunden & Freundeskreis:** Wertschätzend, edel, überraschend („Handgemachte Schweizer Maker-Weihnachtskunst mit 60 funkelnden Lichtern & Musik“).

### 2.1 Visuelle Identität & „Diffusor-Clou“

- **Farbwelt (analog `docs/styles.css` & PCB):**
  - **Tannengrün:** `#1B4332` / `#2EA043`
  - **Weihnachtsgold:** `#D4A853` / `#F3D28A` (passend zu den vergoldeten ENIG-Kugeln & dem Stern)
  - **Tech-Kontrast:** Tiefschwarz `#0D1117` oder warmer Kraftkarton (Naturbraun)
- **Ergänzende Idee – Transparentpapier als Schutz UND Lichtdiffusor:**
  - Ein Blatt **mattes Architekten-/Transparentpapier (`90–115 g/m²`, Pergamin)** liegt in der Box als edle Schutzschicht über den 60 SMD-LEDs (wie bei hochwertigen Pralinen- oder Elektronikboxen).
  - **Zweitnutzen:** Legt oder klemmt man dieses Pergaminblatt im Betrieb vor den Baum (oder nutzt Variante G „Laternen-Sleeve“), verwandeln sich die 60 grellen Punkt-LEDs in ein **butterweich leuchtendes Weihnachts-Stimmungslicht**!

### 2.2 Der „Power-On-in-Box“-Effekt (Leuchtende Geschenkübergabe!)

Da der XIAO sehr kompakt ist, lässt sich in den Box-Varianten (**B, C, D, H**) im unteren Kabelfach optional eine **flache Mini-Powerbank** (oder ein kleiner `5 V`-USB-Stick-Akku mit kurzem 90°-USB-C-Kabel) vorab anschließen:
- Beim Aufklappen des Deckels (oder über einen kleinen Reed-/Lichtsensor bzw. vorab eingeschaltet) **leuchtet und funkelt der Baum bereits beim Öffnen der Schachtel** durch das Pergaminpapier hindurch!

---

## 3. Lieferumfang, Zubehör & Beileger-Konzept

| Baustein | Basis / Mailing (A, E) | Geschenk / Standard (B, D, G) | VIP / Komplett-Set (C, H) |
|---|---|---|---|
| **10 cm PCB-Tannenbaum** | Fertig bestückt & geflasht | Fertig bestückt & geflasht | Fertig bestückt & geflasht |
| **Sternhals-Aufhängeclip** | Vorgestanzt in Karte | Im Standfuß-Bogen integriert | Aus Schwarz-/Goldkarton oder Holz |
| **Tisch-Standfuß (Klemmständer)** | Optional (faltbar) | **Ja (aus Inlay steckbar)** | **Ja (Holz/Acryl/Karton)** |
| **Pergamin-Diffusorblatt** | Optional | Ja (Schutzlage + Lichtdiffusor) | Ja (bedruckt mit Goldsternen) |
| **Quickstart- & QR-Karte (`A7`)** | Auf Klappkarte integriert | Ja (`300 g/m²`) | Ja (`350 g/m²` mit Goldakzent) |
| **USB-C-Kabel** | Nein (Empfänger nutzt eigenes) | Optional (`30–50 cm`, weich/90°) | **Ja** (Textilkabel / 90°-Winkelstecker) |

### Inhalt der Quickstart-Karte (`A7: 74 × 105 mm` – passt in jede Variante)

- **Vorderseite:** Weihnachtsgruß + kurzes Dankeschön / persönliche Widmungszeile.
- **Rückseite (3 Schritte in 15 Sekunden):**
  1. **Aufstellen oder Aufhängen:** Baum unten in den Steckfuß schieben (oder Clip an den Sternhals klemmen).
  2. **Einstecken (`5 V USB-C`):** USB-C-Kabel auf der Rückseite **von oben** in das XIAO-Modul stecken.
  3. **Steuern & Coden:**
     - *Mit ESP32-C6:* **WLAN-QR-Code** (`WIFI:S:AITY-XMAS;T:nopass;;`) scannen → Captive Portal öffnet sofort Licht- & Musiksteuerung.
     - *Web-Simulator & Python:* Zweiter QR-Code zum Browser-Flasher & Simulator (`circuitpython` / Web-UI).
     - *Geheimtipp:* Die 9 goldenen Kugeln auf der Vorderseite sind echte Touch-/Testpunkte (`TP101–TP109`) für eigene Experimente!
- **Pflicht- & Sicherheitshinweise (kompakt am unteren Rand):**
  - Nur an geprüfter `5 V` USB-Quelle betreiben (`max. 500 mA` im Standardmodus), vor Feuchtigkeit schützen, kein Kleinkind-Spielzeug (unter 3 J.), Elektronik am Lebensende fachgerecht entsorgen (WEEE/SENS/SWICO, nicht in den Hausmüll).

---

## 4. Versand- & Portotauglichkeit (Schweiz, Deutschland, Österreich)

Da das Projekt in **Bern** beheimatet ist, sind sowohl die **Schweizerische Post** als auch **Deutsche Post / Österreichische Post** berücksichtigt – erfreulicherweise gilt in allen drei Ländern exakt dieselbe magische Höhenschwelle von **20 mm**:

| Versandtarif | Max. Außenmaße (L × B × H) | Max. Gewicht | Kompatible Varianten |
|---|---|---|---|
| **CH: Brief B4 / Großbrief (A-/B-Post)** | `353 × 250 × 20 mm` | `500 g` / `1000 g` | **Variante A** (`~12 mm`), **Variante B** (`20 mm` im Karton-Umschlag, *ohne* Luftpolstertasche!), **Variante E**, **Variante G** (`18 mm`) |
| **DE: Großbrief** | `353 × 250 × 20 mm` | `500 g` | **Variante A, B** (als direkter Versandkarton `20 mm`), **E, G** |
| **AT: Brief M (PRIO/ECO)** | `353 × 250 × 20 mm` | `750 g` | **Variante A, B** (direkt `20 mm`), **E, G** |
| **CH Midibrief / DE Maxibrief / AT Paket S** | bis `50 mm` Höhe | `1000 g` | **Alle Varianten (A–H)**, inkl. Luftpolstertasche, gesockeltem XIAO & dickem USB-Kabel |

> [!IMPORTANT]
> **Praxis-Check zur 20-mm-Grenze (Prüfschlitz der Post):**
> Steckt man eine `20 mm` hohe Faltschachtel (Variante B) zusätzlich in einen Luftpolsterumschlag (`+4–6 mm`), wird die Sendung **25 mm dick** und rutscht in den teureren Midi-/Maxibrief-Tarif!
> **Lösung:**
> 1. Wenn **im Umschlag** verschickt wird → Schachtelhöhe auf **`16 mm`** reduzieren (bei SMD-XIAO mit `7 mm` Bauhöhe bleiben immer noch `9 mm` für Karton + Schutzspalt!) oder **Variante A / G** wählen.
> 2. Oder **Variante B (`20 mm`) aus stabiler `1,2 mm` E-Welle direkt als Versandkarton** adressieren und mit einem Papier-Siegelstreifen verschließen – dann nutzt sie die vollen `20,0 mm` optimal aus!

---

## 5. Konfektionierungs-Effizienz & Nachhaltigkeit

- **Schnelles Packen bei 30–100 Stück (Workshop-/Vereins-Realität):**
  - Keine komplizierten Klebestellen: Varianten **A, B, G und H** kommen komplett ohne Leim aus (reine Steck-/Faltkonstruktionen).
  - Richtwert Konfektionierung: `< 45 Sekunden` pro Baum (Baum einklicken → QR-Karte + Pergaminblatt auflegen → schließen → Siegelaufkleber).
- **Monomaterial & echter Zweitnutzen statt Abfall:**
  - **Standfuß + Aufhängeclip** werden aus demselben Materialbogen gestanzt/gelasert wie das Inlay (`stand_insert_1to1.svg`).
  - **Pergamin-Schutzblatt** dient weiter als optischer LED-Diffusor.
  - **Verpackung = Sommer-Tresor:** Nach dem 6. Januar wandert der Baum samt Standfuß wieder flach und staubgeschützt in dieselbe Schachtel für das nächste Jahr.
