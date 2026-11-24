# Verpackungsvarianten – AITY Weihnachtsbaum 2026 (10 cm)

Auf Basis des überprüften [Verpackungskonzepts](KONZEPT.md) stehen **acht praxisgeprüfte Verpackungsvarianten (A–H)** zur Auswahl. Neben klassischen Versand- und Geschenkboxen wurden gezielt **zwei neue funktionale Konzepte (G & H)** ergänzt, bei denen die Verpackung selbst Teil des Leucht- bzw. Geschenk-Erlebnisses wird.

---

## Vergleichsmatrix aller 8 Varianten

| Kriterium | **A: Flat-Mail Klappkarte** | **B: Pop-Up-Stand Faltschachtel** ⭐ | **C: Window-Showcase Box** | **D: Maker-Laser Schiebebox** | **E: Workshop ESD-Kit** | **F: Klarsicht-Ornament** | **G: Laternen-Sleeve (Diffusor)** 💡 | **H: Streichholz-Schubladenbox** 🎁 |
|---|---|---|---|---|---|---|---|---|
| **Außenmaße (mm)** | `148 × 105 × 12` | `125 × 95 × 20` *(oder 16)* | `140 × 105 × 28` | `130 × 98 × 24` | `110 × 165 × 12` | `110 × 80 × 25` / `Ø 120` | `125 × 90 × 18` | `130 × 95 × 24` |
| **CH B4 / DE Großbrief (`≤ 20 mm`)** | **Ja** (auch im Umschlag) | **Ja** (direkt `20 mm` / `16 mm` im Umschlag) | Nein (Midi-/Maxibrief) | Nein (Midi-/Maxibrief) | **Ja** | Nein | **Ja** (`18 mm`) | Nein (Midi-/Maxibrief) |
| **Mechanischer Schutz** | Mittel–Hoch (mit Distanzrahmen) | Hoch | Sehr hoch | Sehr hoch | Mittel (mit Rückkarte) | Mittel–Hoch | Hoch | Sehr hoch (doppelwandig) |
| **ESD-Schutz** | Naturkarton / ESD-Beutel | Naturkarton / ESD-Beutel | **ESD-Schaum (optimal)** | Holz/Pappe + Pergamin | **ESD-Beutel (optimal)** | Antistatik-rPET nötig | Naturkarton + Pergamin | Naturkarton / ESD-Schaum |
| **Unboxing / Wow-Faktor** | Gut (Weihnachtspost) | **Sehr gut (Standfuß!)** | **Exzellent (VIP)** | **Sehr gut (Laser-Unikat)** | Funktional (Maker/Kids) | Sehr gut (Schaufenster) | **Exzellent (leuchtet!)** | **Exzellent (Schubladen-Effekt)** |
| **Platz für USB-C-Kabel** | Nein (nur Karte) | Ja (SMD-XIAO, flaches Kabel) | Ja (eigenes Fach) | Ja (unter Baum / Fach) | Ja (im Beutel) | Begrenzt | Optional (kurzes Kabel) | **Ja (perfekt versteckt)** |
| **Zweitnutzen** | Grußkarte + Sternclip | **Klemm-Standfuß + Lagerbox** | Dauerhafte Edel-Box | **Holz-Standfuß + Lagerbox** | Aufbewahrungsbeutel | Direkt als Baumschmuck | **Tisch-Leuchtlaterne!** | Aufstell-Bühne + Schatzbox |
| **Stückkosten (~25 Stk.)** | ~1,80 € / CHF | ~3,50 € / CHF | ~7,50 € / CHF | ~4,20 € / CHF (Material) | ~0,90 € / CHF | ~2,80 € / CHF | ~3,20 € / CHF | ~3,80 € / CHF |
| **Stückkosten (~100 Stk.)** | ~1,10 € / CHF | ~2,10 € / CHF | ~4,80 € / CHF | ~3,40 € / CHF | ~0,55 € / CHF | ~1,90 € / CHF | ~1,95 € / CHF | ~2,40 € / CHF |
| **Vorlage im Repo** | [`flat_mail_card_a6.svg`](templates/flat_mail_card_a6.svg) | [`folding_box_125x95x20_dieline.svg`](templates/folding_box_125x95x20_dieline.svg) + [`stand_insert_1to1.svg`](templates/stand_insert_1to1.svg) | [`inlay_foam_1to1.svg`](templates/inlay_foam_1to1.svg) | [`laser_slide_box_3mm.svg`](templates/laser_slide_box_3mm.svg) + [`stand_insert_1to1.svg`](templates/stand_insert_1to1.svg) | Standard-Zukauf | Standard-Zukauf + [`stand_insert_1to1.svg`](templates/stand_insert_1to1.svg) | [`lantern_sleeve_125x90x18.svg`](templates/lantern_sleeve_125x90x18.svg) | Basis `125×95` + Inlay |

---

## Variante A: „Flat-Mail“ Klappkarte mit Distanzrahmen *(Briefversand-Champion)*

Eine stabile Weihnachtsklappkarte im **DIN-A6-Format** (`105 × 148 mm` gefaltet, `210 × 148 mm` offen), die Grußkarte, Anleitung und Platinenhalterung in einem einzigen Bogen vereint.

- **Überprüfte Konstruktion (Geometrie-Fix):**
  - Der Baum wird auf der rechten Innenseite über **vier präzise Laschenschlitze in den natürlichen Ast-Tälern** gehalten: oben in der ersten Ast-Mulde (`Y_lokal = 39 mm`, Taillenbreite `25,0 mm`) und unten in der Stamm-Mulde (`Y_lokal = 88,5 mm`, Taillenbreite `14,0 mm`). Dadurch kann der Baum weder nach oben noch nach unten herausrutschen, und keine einzige LED wird verdeckt!
  - **Wichtige Ergänzung für XIAO & Buzzer:** Da XIAO + Buzzer auf der Rückseite `~4,5 mm` auftragen, erhält die rechte Kartenrückseite entweder eine eingeklebte `5 mm` Wellpapp-/Schaum-Distanzlage mit `24 × 32 mm` XIAO-Fenster – oder die Karte wird als **3-teilige Wickelkarte (Altarfalz)** ausgeführt, deren drittes Blatt sich schützend mit Abstandshaltern über die Vorderseite legt.
  - Direkt mit eingestanzt: ein kleiner **Aufhänge-Clip für den 9,9-mm-Sternhals** zum Herausdrücken.
- **Ideal für:** Große Weihnachtspost-Aktionen (> 50 Stk.), günstiges A-/B-Post-Briefporto (`≤ 20 mm` selbst im C6-Umschlag).
- **Vorlage:** [`templates/flat_mail_card_a6.svg`](templates/flat_mail_card_a6.svg)

---

## Variante B: „Pop-Up-Stand“ Faltschachtel (`125 × 95 × 20 mm`) ⭐ *(Empfohlener Allrounder)*

Eine einteilige **Klappdeckel-Faltschachtel**, deren Abwicklung (`245 × 165 mm`) komplett auf einen **einzigen DIN-A4-Bogen** passt – perfekt sowohl für den eigenen Schneideplotter/Lasercutter als auch für die Druckerei.

- **Aufbau & Verbesserungen:**
  - **Außenbox:** `125 × 95 × 20 mm` (als direkter Versandkarton mit Siegelstreifen = exakt Großbrief/B4-Limit; alternativ mit `16 mm` Höhe für Versand im Umschlag).
  - **Schwebende Platinen-Aufnahme:** Das obere Karton-Inlay nutzt die bereinigte 1:1 Außenkontur (`+1,0 mm` echter Parallel-Offset), hält den Baum formschlüssig fest und lässt über den 60 SK6812-LEDs `~3 mm` Sicherheitsluft (abgedeckt durch ein Blatt **Pergamin-Transparentpapier**).
  - **Zweitnutzen – Verbesserter Klemm-Standfuß & Sternclip:**
    - Da der Stamm nach unten breiter wird (`14,0 → 18,2 mm`), nutzt der beiliegende Standfuß ([`stand_insert_1to1.svg`](templates/stand_insert_1to1.svg)) **zwei seitliche Klemmwangen mit `1,75 mm` Präzisionsschlitz** für die `1,6 mm` dicke FR4-Platine.
    - Weil die USB-C-Buchse am XIAO auf `B.Cu` **nach oben (`Y ≈ 66 mm`)** zeigt, bleibt der Raum zwischen den beiden Stützwangen hinten komplett frei für die elegante Kabelführung!
    - Zusätzlich enthält derselbe Stanzbogen einen **herausdrückbaren Sternhals-Aufhängeclip** (`Ø 4 mm` Öse), falls der Beschenkte den Baum lieber an den echten Weihnachtsbaum hängt.
- **Ideal für:** Das beste Gesamtpaket für Workshops, Team-, Partner- und Kundengeschenke (10 bis 500+ Stück).
- **Vorlagen:** [`templates/folding_box_125x95x20_dieline.svg`](templates/folding_box_125x95x20_dieline.svg) und [`templates/stand_insert_1to1.svg`](templates/stand_insert_1to1.svg)

---

## Variante C: „Window-Showcase“ Geschenkschachtel mit ESD-Schaumstoff *(VIP / Sponsoren)*

Eine edle **Stülpdeckel- oder Magnetklappbox** (`140 × 105 × 28 mm`) aus kaschierter Graupappe mit Goldprägung und schwarzem, leitfähigem **2-Lagen-ESD-Schaumstoff**.

- **Aufbau & geprüfte Maße:**
  - **Lage 1 (oben, `8 mm` ESD-Schaum):** Exakte 1:1 Baumkontur mit `+1,0 mm` umlaufendem Parallel-Offset + zwei seitliche `Ø 17 mm` Finger-Greifmulden auf halber Höhe (`X = ±34 mm`), wo die Äste schmaler sind.
  - **Lage 2 (unten, `10–12 mm` ESD-Schaum):** Durchgehende Auflageplatte mit überprüfter Aussparung für **XIAO inkl. oberem USB-C-Überstand (`24 × 32 mm`)** und **Buzzer (`13 × 13 mm`)**. So liegt die FR4-Platine rundum satt auf, ohne auf den rückseitigen Bauteilen zu wippen.
  - **Power-On-Option:** Unter Lage 2 oder im seitlichen Fach lässt sich eine Mini-Powerbank mit 90°-USB-C-Stecker verstecken, sodass der Baum durch ein mattes Sichtfenster bereits beim Überreichen leuchtet.
- **Ideal für:** Sponsoren („Danke für die breite Unterstützung“), Ehrengäste, Geschäftsleitung, dauerhafte Sammlerbox.
- **Vorlage:** [`templates/inlay_foam_1to1.svg`](templates/inlay_foam_1to1.svg)

---

## Variante D: „Maker-Laser“ 3-mm-Sperrholz-Schiebebox *(FabLab / Kleinserie)*

Direkt passend zur bestehenden Laser-Infrastruktur im Projekt (`cutout_patterns/laser_stencils/`): Eine komplett lasergeschnittene **Schiebedeckel-Schatulle aus `3,0 mm` Pappelsperrholz oder Birkensperrholz** (alternativ `3 mm` Kraftplex / Finnpappe).

- **Konstruktion (neu als fertige 1:1 Laserdatei ergänzt!):**
  - **Außenmaße:** `130 × 98 × 24 mm` (Innenraum `124 × 92 × 18 mm`).
  - **Steck-Korpus mit Fingerzinken:** Boden, 2 Längswände, 1 Rückwand und 1 abgesenkte Vorderwand (damit sich der Deckel bündig einschieben lässt) greifen über passgenaue `3,0 mm` Fingerzinken ineinander. Zwei schmale innere Führungsschienen halten den `3 mm` Schiebedeckel.
  - **Personalisierbarer Schiebedeckel:** Mit eingravierter 1:1 Baum-Silhouette, Daumenmulde und freiem Textfeld für die **individuelle Laser-Gravur des Namens** (z. B. jedes einzelnen Workshop-Kindes!).
  - Im selben 3-mm-Holzjob lässt sich der passende Holz-Standfuß mitschneiden (Steckschlitze auf `3,0 mm` skaliert).
- **Ideal für:** Die Berner Micro:bit-/Workshop-Gruppe (jedes Kind bekommt seine Box mit eingraviertem Vornamen!), Kleinserien von 5–50 Stück ohne Druckerei-Mindestmengen.
- **Vorlage:** [`templates/laser_slide_box_3mm.svg`](templates/laser_slide_box_3mm.svg) + [`templates/inlay_foam_1to1.svg`](templates/inlay_foam_1to1.svg)

---

## Variante E: „Workshop-Kit“ ESD-Abschirmbeutel + Reiterkarte *(Bausatz / Schule)*

Die schnellste, normgerechte Elektronik-Verpackung für Löt- oder Programmier-Workshops.

- **Aufbau:**
  - Halbtransparenter metallisierter **ESD-Abschirmbeutel (`100 × 150 mm`)** + eingelegte `350 g/m²` Rückenkarte (schützt vor Biegen, trägt auf der Rückseite das Pinout aus [`README.md`](../README.md) & den QR-Code) + dünne Lage rosa Antistatik-Schaumfolie (`2 mm`) vor den LEDs.
  - Oben verschlossen mit einer gefalteten, farbig gedruckten **Header-Card (`105 × 40 mm`)** („AITY Weihnachtsbaum 2026 – Workshop Edition“).
- **Ergänzungs-Tipp für Workshops:** Auf der Rückenkarte ein weißes Beschriftungsfeld **„Gebaut & programmiert von: __________“** vorsehen, damit im Workshop keine Bäume verwechselt werden!
- **Ideal für:** Schulklassen, Micro:bit-/CircuitPython-Kurse, Bausätze mit noch nicht aufgelötetem XIAO.

---

## Variante F: „Ornament-Showcase“ Klarsicht-Box / Christbaumkugel *(Deko-Präsentation)*

Verwandelt die Platine bereits ungeöffnet in ein funkelndes Weihnachts-Ornament.

- **Aufbau & wichtiger Praxis-Check:**
  - **F1 – rPET-Klarsichtschachtel (`110 × 80 × 25 mm`):** Kristallklare Hülle (antistatisch ausgerüstetes rPET wählen!) mit tannengrün-goldener Einlegekarte, die den Baum fixiert und das USB-Kabel dahinter unsichtbar macht.
  - **F2 – Zweiteilige Acryl-Christbaumkugel (`Ø 120 mm`):**
    - *Geometrie-Check:* Bei `69,4 × 99,6 mm` beträgt die Eckdiagonale unten/oben ca. `104 mm` – eine `100 mm` Kugel ist zu klein, benötigt wird zwingend **`Ø 120 mm`**!
    - Befestigt wird der Baum in der Kugel über den neuen **Sternhals-Clip** (aus [`stand_insert_1to1.svg`](templates/stand_insert_1to1.svg)) an einer Goldkordel. Vor dem Einsetzen die Kugelhälften innen kurz mit Antistatik-Tuch/Spray abwischen.
- **Ideal für:** Direktübergabe am Weihnachtsbaum, Ausstellungen, Verkaufsstände.

---

## NEU – Variante G: „Laternen-Sleeve“ Schuber mit Diffusor-Fenster 💡 *(Verpackung = Tischleuchte!)*

Eine besonders clevere Ergänzung: Eine flache **Schiebeschachtel (Bauchbinde/Schuber + Innenschale, `125 × 90 × 18 mm`)**, die nach dem Auspacken **selbst als stimmungsvolle Weihnachts-Tischlaterne** genutzt werden kann!

- **So funktioniert das Prinzip:**
  - **Innenschale (Tray):** Hält den 10 cm Tannenbaum aufrecht zentriert; unten an der Rückwand befindet sich eine kleine **vorperforierte Ausbrech-Öffnung (`14 × 8 mm`) für das USB-C-Kabel** sowie zwei ausklappbare Standfüßchen an der Unterkante.
  - **Außenschuber (Sleeve):** Hat auf der Vorderseite ein **ausgestanztes Tannenbaum-Fenster**, das von innen mit **mattem Pergamin-/Transparentpapier (`115 g/m²`)** hinterklebt ist (schützt beim Versand die LEDs vor Staub und Berührung). Auf der Rückseite sitzen dezente Schalllöcher über dem Buzzer (`LS101`).
  - **Der Clou im Betrieb:**
    - *Modus 1 (Kristallklar):* Baum aus der Box nehmen und in den Steckfuß stellen – man sieht die vergoldete Platine und die 60 einzelnen Pixel.
    - *Modus 2 (Weihnachts-Laterne):* Baum **in der Schachtel lassen**, USB-Kabel hinten durch die Perforation einstecken und die Box senkrecht aufstellen → Das Pergamin-Fenster streut die 60 NeoPixel zu einer **warm leuchtenden, blendfreien Design-Tischleuchte**!
- **Vorteile:** Großbrieftauglich (`18 mm` flach!), 100 % Papier/Pergamin, einzigartiger funktionaler Mehrwert ohne Mehrkosten.
- **Vorlage:** [`templates/lantern_sleeve_125x90x18.svg`](templates/lantern_sleeve_125x90x18.svg)

---

## NEU – Variante H: „Matchbox-Stage“ Schubladen-Geschenkbox 🎁 *(Aufstell-Bühne)*

Inspiriert von edlen Riesen-Streichholzschachteln und modernen Smartphone-Unboxings: Eine doppelwandige **Schubladenbox (`130 × 95 × 24 mm`)** mit Seidenband-Zuglasche an der kurzen Seite.

- **Aufbau & Bühnen-Effekt:**
  - Zieht man an der kleinen goldenen Bandschlaufe, gleitet die stabile Innenschublade sanft aus dem tannengrünen Schuber.
  - Das oberste Inlay ist in der Mitte quer genutet: Zieht man die Schublade zur Hälfte heraus und klappt sie leicht an, **stellt sich der Tannenbaum wie auf einer kleinen Pop-Up-Bühne schräg auf**!
  - Unter dem Bühnen-Inlay liegt unsichtbar ein großzügiges Fach für jedes beliebige USB-C-Kabel (auch dickere Standardkabel), den Standfuß und Süßigkeiten (z. B. ein flaches Schweizer Schöggeli / Napolitain neben dem Stamm!).
- **Vorteile:** Extrem druckstabil durch doppelte Seitenwände, kinderleicht wiederverschließbar, haptisch eines der schönsten Auspack-Erlebnisse überhaupt.

---

## Empfohlene Kombination nach Einsatzzweck (Zusammenfassung)

| Zielgruppe im Projekt | Beste Wahl | Warum? |
|---|---|---|
| **Kids & Micro:bit-Workshop-Abschluss** | **Variante D** *(mit Namensgravur)* oder **Variante B** | Persönliche Wertschätzung + robuster Schutz im Schulrucksack auf dem Heimweg! |
| **Unterstützer & Dankeschön-Post (CH/DE)** | **Variante G (Laternen-Sleeve)** oder **Variante B (`16/20 mm`)** | Spart Paketporto (`≤ 20 mm` Brief), bietet sofortigen Tisch-Aufsteller bzw. Laternen-Effekt. |
| **Großes Weihnachtskarten-Mailing** | **Variante A (Flat-Mail A6)** | Unschlagbar günstig im Druck & Versand, persönlicher handschriftlicher Gruß direkt neben dem Baum. |
| **Hauptsponsoren & Ehrengäste** | **Variante C** oder **Variante H** *(inkl. Schöggeli & 90°-Kabel)* | Höchste Geschenk-Wertigkeit, dauerhafte Aufbewahrungsschatulle. |
