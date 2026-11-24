// AITY Xmas Tree 2026 — 10+2 Baum-Show 3D Simulation (port of circuitpython/code.8-show.py)
(function () {
  const NUM_LEDS = 60;
  const SHOW_TOTAL_MS = 1_260_000; // 21 minutes (10 acts)
  const SHOW_TOTAL_LABEL = "21:00";

  // (act_id, name, start_ms, dur_ms, bpm, bars)
  const ACTS = [
    [1, "Akt 1: Erwachen & Puls", 0, 120_000, 72, 36],
    [2, "Akt 2: Geometrie & Linien", 120_000, 150_000, 112, 70],
    [3, "Akt 3: Wellen & Dialog", 270_000, 180_000, 96, 72],
    [4, "Akt 4: Polarlicht & Stille", 450_000, 150_000, 64, 40],
    [5, "Akt 5: Uhrwerk & Crescendo", 600_000, 180_000, 128, 96],
    [6, "Akt 6: Finale & Winterfrieden", 780_000, 120_000, 120, 60],
    [7, "Akt 7: Zuckerstangen & Lametta", 900_000, 90_000, 120, 45],
    [8, "Akt 8: Baumschmuck & Lichterkette", 990_000, 90_000, 92, 35],
    [9, "Akt 9: Stern von Bethlehem", 1_080_000, 90_000, 68, 26],
    [10, "Akt 10: Adventskerzen & Schlitten", 1_170_000, 90_000, 116, 44],
  ];

  // Relevant animation milestones shown as preview thumbnails above the timeline
  const SHOW_STEP_PREVIEWS = [
    {
      id: "act1a",
      actId: 1,
      shortAct: "1a",
      label: "Glühwürmchen",
      fullTitle: "Akt 1a: Glühwürmchen (T01–T10 erwachen)",
      startMs: 0,
      endMs: 90_000,
      jumpMs: 0,
      previewMs: 15_350,
    },
    {
      id: "act1b",
      actId: 1,
      shortAct: "1b",
      label: "Hero-Puls",
      fullTitle: "Akt 1b: Hero-Puls (T11/T12 Basis erwacht)",
      startMs: 90_000,
      endMs: 120_000,
      jumpMs: 90_000,
      previewMs: 95_000,
    },
    {
      id: "act2",
      actId: 2,
      shortAct: "2",
      label: "3D-Ebene",
      fullTitle: "Akt 2: Volumetrische 3D-Schnittebene & Doppelhelix",
      startMs: 120_000,
      endMs: 270_000,
      jumpMs: 120_000,
      previewMs: 154_000,
    },
    {
      id: "act3",
      actId: 3,
      shortAct: "3",
      label: "Dialog",
      fullTitle: "Akt 3: S-Welle & Call-and-Response (T12 Gold ↔ T11 Blau)",
      startMs: 270_000,
      endMs: 450_000,
      jumpMs: 270_000,
      previewMs: 315_000,
    },
    {
      id: "act4",
      actId: 4,
      shortAct: "4",
      label: "Polarlicht",
      fullTitle: "Akt 4: Polarlicht & fallende Schneeflocken",
      startMs: 450_000,
      endMs: 600_000,
      jumpMs: 450_000,
      previewMs: 537_000,
    },
    {
      id: "act5",
      actId: 5,
      shortAct: "5",
      label: "Schallwelle",
      fullTitle: "Akt 5: Sphärische 3D-Schallwellen aus T12-Spitze",
      startMs: 600_000,
      endMs: 780_000,
      jumpMs: 600_000,
      previewMs: 660_197,
    },
    {
      id: "act6a",
      actId: 6,
      shortAct: "6a",
      label: "Supernova",
      fullTitle: "Akt 6a: Finale Supernova-Wirbel",
      startMs: 780_000,
      endMs: 860_000,
      jumpMs: 780_000,
      previewMs: 810_000,
    },
    {
      id: "act6b",
      actId: 6,
      shortAct: "6b",
      label: "Kerzenlicht",
      fullTitle: "Akt 6b: Winterfrieden & Kerzenflackern (60 BPM)",
      startMs: 860_000,
      endMs: 900_000,
      jumpMs: 860_000,
      previewMs: 875_000,
    },
    {
      id: "act7",
      actId: 7,
      shortAct: "7",
      label: "Zuckerstange",
      fullTitle: "Akt 7: Zuckerstangen & Silber-Lametta",
      startMs: 900_000,
      endMs: 990_000,
      jumpMs: 900_000,
      previewMs: 912_000,
    },
    {
      id: "act8",
      actId: 8,
      shortAct: "8",
      label: "Baumschmuck",
      fullTitle: "Akt 8: Christbaumkugeln & warme Lichterkette",
      startMs: 990_000,
      endMs: 1_080_000,
      jumpMs: 990_000,
      previewMs: 1_005_000,
    },
    {
      id: "act9",
      actId: 9,
      shortAct: "9",
      label: "Bethlehem",
      fullTitle: "Akt 9: Stern von Bethlehem & Sternschnuppe",
      startMs: 1_080_000,
      endMs: 1_170_000,
      jumpMs: 1_080_000,
      previewMs: 1_090_800,
    },
    {
      id: "act10",
      actId: 10,
      shortAct: "10",
      label: "Schlitten",
      fullTitle: "Akt 10: Adventskerzen & Rudolphs Rentierschlitten",
      startMs: 1_170_000,
      endMs: 1_260_000,
      jumpMs: 1_170_000,
      previewMs: 1_181_500,
    },
  ];

  function formatTimeMs(ms) {
    const clamped = ((ms % SHOW_TOTAL_MS) + SHOW_TOTAL_MS) % SHOW_TOTAL_MS;
    const m = Math.floor(clamped / 60_000);
    const sec = Math.floor((clamped % 60_000) / 1000);
    return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  }

  // (Lead-MIDI, Bass-MIDI) per 8th-note step
  const PATTERNS = {
    1: [
      [62, null, 65, null, 69, null, 67, null],
      [38, null, null, null, null, null, null, null],
    ],
    2: [
      [62, 65, 69, 74, 72, 69, 65, 62],
      [38, null, 50, null, 36, null, 48, null],
    ],
    3: [
      [65, null, 69, 72, 67, null, 70, 74],
      [41, null, null, null, 43, null, null, null],
    ],
    4: [
      [67, null, null, null, 70, null, 69, null],
      [43, null, null, null, 39, null, null, null],
    ],
    5: [
      [74, 69, 65, 69, 74, 69, 65, 69],
      [38, 38, 50, 38, 36, 36, 48, 36],
    ],
    6: [
      [74, null, 78, null, 81, null, 79, 78],
      [38, null, null, null, 45, null, null, null],
    ],
    7: [
      [66, 66, 66, null, 66, 69, 62, 64],
      [38, null, 45, null, 38, null, 45, null],
    ],
    8: [
      [60, 65, 65, 65, 67, 69, 69, null],
      [41, null, null, null, 48, null, null, null],
    ],
    9: [
      [67, null, 69, 67, 64, null, null, null],
      [48, null, null, null, 43, null, null, null],
    ],
    10: [
      [74, 74, 71, 74, 76, 74, 71, 69],
      [43, null, 50, null, 43, null, 50, null],
    ],
  };

  // Default 10+2 ensemble layout from circuitpython/code.8-show.py
  // [x_mm, y_base_mm, z_mm, height_mm, base_diam_mm, density_norm]
  const DEFAULT_TREE_LAYOUT = {
    T01: [-1050, 0, 360, 100, 70, 0.35],
    T02: [-630, 0, 460, 100, 70, 0.35],
    T03: [-210, 0, 520, 100, 70, 0.35],
    T04: [210, 0, 520, 100, 70, 0.35],
    T05: [630, 0, 460, 100, 70, 0.35],
    T06: [1050, 0, 360, 100, 70, 0.35],
    T07: [-840, 140, 140, 100, 70, 0.35],
    T08: [-300, 140, 220, 100, 70, 0.35],
    T09: [300, 140, 220, 100, 70, 0.35],
    T10: [840, 140, 140, 100, 70, 0.35],
    T11: [520, 0, -280, 850, 592, 1.0],
    T12: [-420, 0, -220, 1050, 732, 1.0],
  };

  const TREE_IDS = Object.keys(DEFAULT_TREE_LAYOUT);

  // Exact normalized AITY Christmas Tree silhouette from cutout_patterns/svg/tree.svg (u_x in [-0.5, 0.5], u_y in [0, 1])
  const TREE_SILHOUETTE = [[0.0009, 1.0], [0.0081, 0.9981], [0.0138, 0.9923], [0.0433, 0.9322], [0.1299, 0.9287], [0.1371, 0.9271], [0.142, 0.9224], [0.1431, 0.9151], [0.1388, 0.9104], [0.0708, 0.8697], [0.0933, 0.8073], [0.0924, 0.7998], [0.0823, 0.7923], [0.1094, 0.7616], [0.1456, 0.7308], [0.1771, 0.7094], [0.2008, 0.6968], [0.2268, 0.6848], [0.2353, 0.6774], [0.2375, 0.6723], [0.2372, 0.6664], [0.234, 0.6607], [0.2268, 0.6536], [0.2091, 0.6428], [0.1803, 0.6324], [0.1815, 0.6285], [0.19, 0.6189], [0.2168, 0.5945], [0.246, 0.5742], [0.2784, 0.5567], [0.3221, 0.5386], [0.3293, 0.5318], [0.3307, 0.5267], [0.3299, 0.5199], [0.3216, 0.5096], [0.3087, 0.5015], [0.292, 0.4939], [0.2545, 0.4825], [0.2528, 0.4793], [0.2565, 0.4733], [0.2852, 0.4445], [0.3248, 0.4158], [0.3601, 0.3972], [0.4118, 0.3777], [0.4196, 0.3701], [0.4212, 0.3637], [0.42, 0.3584], [0.411, 0.349], [0.396, 0.3398], [0.3793, 0.3319], [0.3375, 0.3191], [0.3353, 0.3161], [0.3385, 0.3102], [0.3677, 0.2811], [0.4072, 0.2521], [0.4418, 0.2329], [0.4947, 0.2103], [0.4994, 0.2046], [0.5, 0.1964], [0.4986, 0.1926], [0.4938, 0.1881], [0.4794, 0.1803], [0.4486, 0.1708], [0.4195, 0.1646], [0.3896, 0.1603], [0.3594, 0.1583], [0.3286, 0.1585], [0.299, 0.1603], [0.293, 0.1596], [0.2907, 0.1554], [0.2963, 0.1412], [0.2969, 0.1313], [0.2907, 0.1247], [0.2814, 0.1215], [0.2329, 0.1208], [0.1914, 0.1242], [0.1547, 0.1317], [0.1172, 0.1442], [0.1096, 0.1443], [0.1038, 0.1407], [0.1009, 0.1353], [0.1024, 0.1073], [0.1057, 0.0868], [0.1133, 0.0598], [0.1307, 0.02], [0.1302, 0.01], [0.1248, 0.0043], [0.1165, 0.0006], [0.1067, 0.0002], [-0.1021, 0.0], [-0.1156, 0.0007], [-0.1224, 0.0031], [-0.1286, 0.0081], [-0.131, 0.0144], [-0.1294, 0.0212], [-0.1142, 0.0552], [-0.1044, 0.0907], [-0.1014, 0.1142], [-0.1011, 0.1343], [-0.1022, 0.1396], [-0.1071, 0.1437], [-0.1114, 0.1448], [-0.1171, 0.1441], [-0.1586, 0.1305], [-0.1934, 0.1239], [-0.2412, 0.1203], [-0.2783, 0.1212], [-0.2897, 0.1247], [-0.2963, 0.1314], [-0.2964, 0.1392], [-0.2901, 0.1554], [-0.2922, 0.1597], [-0.3348, 0.1581], [-0.3647, 0.1585], [-0.3947, 0.161], [-0.4241, 0.1656], [-0.4522, 0.1719], [-0.4836, 0.1824], [-0.4961, 0.1902], [-0.5, 0.1982], [-0.4978, 0.207], [-0.4919, 0.2119], [-0.4347, 0.2362], [-0.4159, 0.2464], [-0.3921, 0.2617], [-0.3613, 0.2864], [-0.3353, 0.3135], [-0.3345, 0.3168], [-0.3375, 0.3196], [-0.3777, 0.3314], [-0.4066, 0.3461], [-0.415, 0.3528], [-0.4192, 0.3585], [-0.4206, 0.364], [-0.4195, 0.3696], [-0.4157, 0.3744], [-0.4094, 0.3785], [-0.3572, 0.3984], [-0.3373, 0.4083], [-0.3157, 0.4213], [-0.2773, 0.4508], [-0.2539, 0.4764], [-0.2523, 0.4802], [-0.2549, 0.4828], [-0.2934, 0.4945], [-0.3189, 0.5081], [-0.326, 0.5144], [-0.3294, 0.52], [-0.3304, 0.5259], [-0.3284, 0.5324], [-0.3208, 0.5394], [-0.2817, 0.555], [-0.2428, 0.5757], [-0.2146, 0.596], [-0.1905, 0.6174], [-0.182, 0.6273], [-0.1803, 0.6328], [-0.2081, 0.6427], [-0.2286, 0.6552], [-0.2366, 0.6661], [-0.2371, 0.6714], [-0.2351, 0.6772], [-0.2264, 0.6848], [-0.2044, 0.6948], [-0.176, 0.7101], [-0.1431, 0.7321], [-0.1123, 0.7583], [-0.0833, 0.7914], [-0.0926, 0.8005], [-0.0933, 0.8063], [-0.0714, 0.8685], [-0.0809, 0.8755], [-0.1374, 0.9094], [-0.142, 0.9138], [-0.1436, 0.9181], [-0.143, 0.9201], [-0.1423, 0.9215], [-0.1384, 0.9264], [-0.1303, 0.9287], [-0.054, 0.9315], [-0.0434, 0.9328], [-0.0138, 0.9914], [-0.0126, 0.9932], [-0.0073, 0.9987], [-0.0009, 1.0]];

  // Exact normalized 60-LED PCB coordinates from tannenbaum_layout.py
  const LED_NORM_COORDS = [[0.2547, 0.3579], [0.229, 0.3387], [0.2005, 0.3214], [0.1696, 0.3064], [0.1366, 0.2936], [0.1019, 0.2834], [0.0659, 0.2757], [0.0288, 0.2707], [-0.0087, 0.2684], [-0.0464, 0.2689], [-0.0839, 0.2721], [-0.1206, 0.278], [-0.1563, 0.2866], [-0.1904, 0.2977], [-0.2227, 0.3112], [-0.2529, 0.327], [-0.2804, 0.3449], [-0.3052, 0.3648], [0.2182, 0.4185], [0.183, 0.4091], [0.1466, 0.4023], [0.1094, 0.3982], [0.0717, 0.3969], [0.034, 0.3983], [-0.0032, 0.4024], [-0.0396, 0.4092], [-0.0748, 0.4186], [-0.1084, 0.4305], [-0.14, 0.4449], [-0.1693, 0.4614], [-0.1959, 0.48], [-0.2197, 0.5004], [0.2202, 0.5233], [0.1826, 0.5219], [0.1449, 0.5233], [0.1077, 0.5274], [0.0713, 0.5342], [0.0361, 0.5436], [0.0025, 0.5556], [-0.0291, 0.5699], [-0.0584, 0.5864], [-0.085, 0.605], [-0.1088, 0.6254], [-0.1293, 0.6475], [-0.1464, 0.6709], [-0.0189, 0.6631], [0.0104, 0.6797], [0.037, 0.6982], [0.0608, 0.7187], [0.0839, 0.7367], [-0.0408, 0.8517], [-0.0575, 0.8353], [-0.0937, 0.9106], [-0.0662, 0.9046], [0.0009, 0.9382], [0.0004, 0.9567], [0.0938, 0.9119], [0.0665, 0.9055], [0.0381, 0.8503], [0.0552, 0.8341]];

  // Perceptual LED brightness LUT (monitors already apply sRGB gamma, so lift midtones for realistic LED vibrance)
  const GAMMA_LUT = new Uint8Array(256);
  for (let i = 0; i < 256; i++) {
    GAMMA_LUT[i] = i === 0 ? 0 : Math.min(255, Math.max(1, Math.round(Math.pow(i / 255.0, 0.72) * 255.0)));
  }

  function hsvToRgb(h, s, v) {
    h = ((h % 1.0) + 1.0) % 1.0;
    const i = Math.floor(h * 6.0);
    const f = h * 6.0 - i;
    const p = v * (1.0 - s);
    const q = v * (1.0 - f * s);
    const t = v * (1.0 - (1.0 - f) * s);
    switch (i % 6) {
      case 0: return [v, t, p];
      case 1: return [q, v, p];
      case 2: return [p, v, t];
      case 3: return [p, q, v];
      case 4: return [t, p, v];
      default: return [v, p, q];
    }
  }

  function resolveAct(tMs) {
    const t = ((tMs % SHOW_TOTAL_MS) + SHOW_TOTAL_MS) % SHOW_TOTAL_MS;
    for (const [actId, name, startMs, durMs, bpm] of ACTS) {
      if (t >= startMs && t < startMs + durMs) {
        return { actId, name, bpm, localMs: t - startMs };
      }
    }
    return { actId: 1, name: ACTS[0][1], bpm: 72, localMs: 0 };
  }

  // Default modifiable shader function body (mirrors render_frame in code.8-show.py)
  const DEFAULT_RENDER_CODE = `// Modifizierbare 3D-Show-Formel (pro LED in allen 12 Baeumen)
// Verfuegbar: wx, wy, wz (Weltkoordinaten in mm), idx (0..59),
// treeId ("T01".."T12"), isHero (T11/T12), actId (1..6),
// t_s (Sekunden), local_ms, show_ms, beat_frac (0..1), pulse (0..1),
// hsv_to_rgb(h, s, v) -> [r, g, b] in 0..1

let r = 0, g = 0, b = 0;

if (actId === 1) {
  // Akt 1: Erwachen & Puls (Gluehwuermchen auf T01-T10 -> Puls auf T11/T12)
  const phase = ((idx * 0.618 + wx * 0.013 + t_s * 0.9) % 1 + 1) % 1;
  let spark = Math.pow(Math.max(0, Math.sin(phase * Math.PI)), 8);
  if (isHero && local_ms < 90000) {
    spark = 0;
  } else if (isHero) {
    spark = wy < 250 ? 0.6 * pulse : 0;
  }
  const amp = 0.35 * spark + 0.65 * pulse * (local_ms > 60000 ? 1.0 : 0.2);
  r = 1.0 * amp; g = 0.52 * amp; b = 0.12 * amp;

} else if (actId === 2) {
  // Akt 2: Volumetrische 3D-Schnittebene & Doppelhelix durch alle 12 Baeume
  const plane_d = 1100.0 * Math.sin(t_s * 0.9);
  const dist = Math.abs((wx * 0.75 + wy * 0.45 + wz * 0.48) - plane_d);
  const beam = Math.max(0, 1.0 - dist / 140.0);
  const helix = 0.5 + 0.5 * Math.sin(wy * 0.015 - t_s * 3.5 + wx * 0.004);
  [r, g, b] = hsv_to_rgb(0.55 + 0.08 * helix, 0.85, Math.max(beam, 0.35 * helix));

} else if (actId === 3) {
  // Akt 3: S-Welle im Vorfeld + Call-and-Response T11 (Blau) <-> T12 (Gold)
  const wave_x = 1100.0 * Math.sin(t_s * 1.4);
  const dist_x = Math.abs(wx - wave_x);
  const trail = Math.max(0, 1.0 - dist_x / 320.0);
  const turn_gold = Math.sin(t_s * 0.8) >= 0;
  let amp = 0;
  if (treeId === "T12") {
    [r, g, b] = turn_gold ? [1.0, 0.68, 0.15] : [0.08, 0.25, 0.45];
    amp = turn_gold ? 0.85 * pulse : 0.25;
  } else if (treeId === "T11") {
    [r, g, b] = !turn_gold ? [0.15, 0.65, 1.0] : [0.35, 0.25, 0.08];
    amp = !turn_gold ? 0.85 * pulse : 0.25;
  } else {
    [r, g, b] = turn_gold ? [1.0, 0.65, 0.18] : [0.15, 0.68, 1.0];
    amp = trail * (0.4 + 0.6 * pulse);
  }
  r *= amp; g *= amp; b *= amp;

} else if (actId === 4) {
  // Akt 4: Polarlicht & Stille (~70% Negativraum + fallende Schneeflocken)
  const aurora = Math.sin(wx * 0.004 + t_s * 0.35) * Math.cos(wz * 0.005 - t_s * 0.25);
  if (aurora > 0.25) {
    const hue = 0.42 + 0.18 * Math.sin(wx * 0.003 + t_s * 0.2);
    [r, g, b] = hsv_to_rgb(hue, 0.9, (aurora - 0.25) * 0.9);
  }
  const snow_y = 1050.0 - ((t_s * 260.0 + idx * 97.0) % 1150.0);
  if (Math.abs(wy - snow_y) < 35.0 && ((idx + Math.floor(t_s)) % 7 === 0)) {
    r = 0.95; g = 0.98; b = 1.0;
  }

} else if (actId === 5) {
  // Akt 5: Sphaerische 3D-Schallwellen aus der Spitze von T12 (-420, 1050, -220)
  const dx = wx - (-420);
  const dy = wy - 1050;
  const dz = wz - (-220);
  const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
  const front = beat_frac * 2200.0;
  const ring = Math.max(0, 1.0 - Math.abs(dist - front) / 210.0);
  const hue = 0.62 - 0.50 * ring;
  [r, g, b] = hsv_to_rgb(hue, 0.95, Math.max(ring, 0.15 * pulse));

} else if (actId === 6) {
  // Akt 6: Supernova-Wirbel -> sanftes Kerzenflackern (ab 80_000 ms im Akt)
  if (local_ms < 80000) {
    const ang = Math.atan2(wz, wx) + wy * 0.006 - t_s * 4.0;
    const swirl = 0.5 + 0.5 * Math.sin(ang * 2.0);
    [r, g, b] = hsv_to_rgb(0.08 + 0.06 * swirl, 0.75, 0.55 + 0.45 * pulse);
  } else {
    const flicker = 0.45 + 0.35 * Math.sin(t_s * 7.3 + idx * 1.9 + wx * 0.02);
    const amp = flicker * (isHero ? 0.35 : 0.85);
    r = 1.0 * amp; g = 0.55 * amp; b = 0.15 * amp;
  }

} else if (actId === 7) {
  // Akt 7: Zuckerstangen & Silber-Lametta (Rot/Weiss Spirale + Stern)
  const isStar = idx >= 50;
  const isStarOuter = idx === 51 || idx === 52 || idx === 55 || idx === 56 || idx === 59;
  if (isStar) {
    if (isStarOuter) {
      const amp = 0.72 + 0.28 * pulse;
      r = 1.0 * amp; g = 0.94 * amp; b = 0.86 * amp;
    } else {
      const amp = 0.55 + 0.45 * pulse;
      r = 1.0 * amp; g = 0.76 * amp; b = 0.18 * amp;
    }
  } else {
    const stripe = Math.sin(idx * 0.95 + wx * 0.004 - t_s * 5.2);
    const edge = 0.72 + 0.28 * Math.abs(stripe);
    if (stripe >= 0) {
      r = 0.98 * edge; g = 0.06 * edge; b = 0.10 * edge;
    } else {
      r = 0.94 * edge; g = 0.90 * edge; b = 0.84 * edge;
    }
    const tinsel = Math.sin(idx * 12.7 + wx * 0.09 + t_s * 7.5);
    if (tinsel > 0.965) {
      r = 1.0; g = 0.96; b = 0.85;
    }
  }

} else if (actId === 8) {
  // Akt 8: Tannenbaum mit buntem Baumschmuck & warmer Lichterkette
  const isStar = idx >= 50;
  const isStarOuter = idx === 51 || idx === 52 || idx === 55 || idx === 56 || idx === 59;
  if (isStar) {
    const amp = isStarOuter ? (0.75 + 0.25 * pulse) : 0.72;
    r = 1.0 * amp; g = 0.84 * amp; b = 0.26 * amp;
  } else {
    const treeCode = treeId.charCodeAt(1) * 3 + treeId.charCodeAt(2);
    const isBauble = idx < 45 && ((idx + treeCode) % 5 === 0);
    if (isBauble) {
      const kind = ((Math.floor(idx / 5) + treeCode) % 4 + 4) % 4;
      const shim = 0.78 + 0.22 * pulse;
      if (kind === 0)      { r = 1.0 * shim; g = 0.08 * shim; b = 0.12 * shim; } // Rubinrot
      else if (kind === 1) { r = 1.0 * shim; g = 0.72 * shim; b = 0.10 * shim; } // Gold
      else if (kind === 2) { r = 0.12 * shim; g = 0.44 * shim; b = 1.0 * shim; } // Saphirblau
      else                 { r = 0.95 * shim; g = 0.14 * shim; b = 0.54 * shim; } // Beeren-Magenta
    } else {
      const breath = 0.75 + 0.25 * Math.sin(t_s * 1.6 + wx * 0.002);
      r = 0.03 * breath; g = 0.36 * breath; b = 0.07 * breath;
      const chasePos = ((t_s * 18.0 + treeCode * 7.0) % 50 + 50) % 50;
      const dist = Math.min(Math.abs(idx - chasePos), 50 - Math.abs(idx - chasePos));
      if (dist < 2.2) {
        const glow = 1.0 - dist / 2.2;
        r = Math.min(1.0, r + 0.95 * glow);
        g = Math.min(1.0, g + 0.76 * glow);
        b = Math.min(1.0, b + 0.38 * glow);
      }
    }
  }

} else if (actId === 9) {
  // Akt 9: Stern von Bethlehem & goldene Sternschnuppe ueber tiefer Winternacht
  const isStar = idx >= 50;
  const isStarOuter = idx === 51 || idx === 52 || idx === 55 || idx === 56 || idx === 59;
  if (isStar) {
    const breath = 0.76 + 0.24 * Math.sin(t_s * 2.2);
    const boost = treeId === "T12" ? 1.0 : 0.88;
    const amp = breath * boost * (isStarOuter ? 1.0 : 0.84);
    r = 1.0 * amp; g = 0.88 * amp; b = 0.42 * amp;
  } else {
    const starlight = Math.pow(Math.max(0, Math.sin(idx * 2.3 + wx * 0.017 + t_s * 1.4)), 14);
    r = 0.02 + 0.45 * starlight;
    g = 0.05 + 0.55 * starlight;
    b = 0.20 + 0.70 * starlight;
  }
  const u = (t_s % 4.5) / 4.5;
  const cx = -1250.0 + 2500.0 * u;
  const cy = 1080.0 - 1020.0 * u;
  const dx = wx - cx;
  const dy = wy - cy;
  const along = (-dx * 0.925 + dy * 0.379);
  const perp = Math.abs(dx * 0.379 + dy * 0.925);
  if (along >= -90.0 && along <= 540.0 && perp < 170.0) {
    const tail = along < 0 ? (1.0 + along / 90.0) : Math.max(0, 1.0 - along / 540.0);
    const rad = Math.max(0, 1.0 - perp / 170.0);
    const comet = tail * rad;
    r = Math.max(r, 1.0 * comet);
    g = Math.max(g, (0.68 + 0.28 * comet) * comet);
    b = Math.max(b, (0.18 + 0.56 * comet) * comet);
  }

} else {
  // Akt 10: Adventskerzen & Rudolphs Rentierschlitten
  const isFlame = idx >= 32;
  if (isFlame) {
    const flick = 0.55 + 0.45 * Math.sin(t_s * 9.5 + idx * 1.7 + wx * 0.03);
    r = 1.0 * flick;
    g = (0.52 + 0.32 * flick) * flick;
    b = 0.10 * flick;
  } else {
    const warm = 0.72 + 0.28 * Math.sin(t_s * 4.5 + idx * 0.7 + wx * 0.01);
    r = 0.75 * warm;
    g = 0.06 * warm;
    b = 0.04 * warm;
  }
  const sleighX = -1350.0 + ((t_s * 680.0) % 2700.0);
  const sleighY = 520.0 + 260.0 * Math.sin(t_s * 2.4);
  const rDist = Math.hypot(wx - (sleighX + 170.0), wy - sleighY);
  if (rDist < 190.0) {
    const nose = Math.pow(1.0 - rDist / 190.0, 1.2);
    r = Math.max(r, 1.0 * nose);
    g = g * (1.0 - nose) + 0.05 * nose;
    b = b * (1.0 - nose) + 0.08 * nose;
  } else {
    const dxSleigh = sleighX - wx;
    const dySleigh = Math.abs(wy - sleighY);
    if (dxSleigh >= -60.0 && dxSleigh <= 440.0 && dySleigh < 140.0) {
      const trail = (1.0 - Math.max(0, dxSleigh) / 440.0) * (1.0 - dySleigh / 140.0);
      r = Math.max(r, 1.0 * trail);
      g = Math.max(g, 0.86 * trail);
      b = Math.max(b, 0.42 * trail);
    }
  }
}

return [r, g, b];`;

  // Web Audio API Synthesizer for PATTERNS
  class ShowAudioEngine {
    constructor() {
      this.ctx = null;
      this.masterGain = null;
      this.enabled = false;
      this.volume = 0.35;
      this.lastStepKey = "";
    }

    ensureContext() {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return false;
        this.ctx = new AudioCtx();
        this.masterGain = this.ctx.createGain();
        this.masterGain.gain.value = this.enabled ? this.volume * 0.4 : 0;
        this.masterGain.connect(this.ctx.destination);
      }
      if (this.ctx.state === "suspended") {
        this.ctx.resume().catch(() => {});
      }
      return true;
    }

    setEnabled(val) {
      this.enabled = Boolean(val);
      if (this.enabled) {
        this.ensureContext();
      }
      if (this.masterGain && this.ctx) {
        this.masterGain.gain.setTargetAtTime(this.enabled ? this.volume * 0.4 : 0, this.ctx.currentTime, 0.02);
      }
      if (!this.enabled) {
        this.lastStepKey = "";
      }
    }

    setVolume(vol) {
      this.volume = Math.max(0, Math.min(1, vol));
      if (this.masterGain && this.ctx && this.enabled) {
        this.masterGain.gain.setTargetAtTime(this.volume * 0.4, this.ctx.currentTime, 0.02);
      }
    }

    playNote(midi, durSec, isBass) {
      if (!this.ctx || !this.masterGain) return;
      const now = this.ctx.currentTime;
      const freq = 440 * Math.pow(2, (midi - 69) / 12);
      const osc = this.ctx.createOscillator();
      const env = this.ctx.createGain();
      osc.type = isBass ? "triangle" : "sine";
      osc.frequency.setValueAtTime(freq, now);

      const peak = isBass ? 0.35 : 0.25;
      env.gain.setValueAtTime(0.0001, now);
      env.gain.linearRampToValueAtTime(peak, now + 0.015);
      env.gain.exponentialRampToValueAtTime(peak * 0.35, now + 0.18);
      env.gain.exponentialRampToValueAtTime(0.0001, now + Math.max(0.22, durSec));

      osc.connect(env);
      env.connect(this.masterGain);
      osc.start(now);
      osc.stop(now + Math.max(0.25, durSec + 0.05));
    }

    update(showMs, playing) {
      if (!this.enabled || !playing) return;
      if (!this.ensureContext()) return;
      const tAudio = ((showMs % SHOW_TOTAL_MS) + SHOW_TOTAL_MS) % SHOW_TOTAL_MS;
      let { actId, bpm, localMs } = resolveAct(tAudio);
      if (tAudio >= 860_000 && tAudio < 900_000) {
        bpm = 60;
        localMs = tAudio - 860_000;
      }
      const eighthMs = 30_000.0 / bpm;
      const stepTotal = Math.floor(localMs / eighthMs);
      const stepInBar = stepTotal % 8;
      const key = `${actId}:${stepTotal}`;
      if (key === this.lastStepKey) return;
      this.lastStepKey = key;

      const [leadSeq, bassSeq] = PATTERNS[actId] || PATTERNS[1];
      const durSec = Math.min(0.45, eighthMs / 1000.0);
      if (leadSeq[stepInBar] != null) this.playNote(leadSeq[stepInBar], durSec, false);
      if (bassSeq[stepInBar] != null) this.playNote(bassSeq[stepInBar], durSec * 1.4, true);
    }
  }

  function cloneLayout(src) {
    const out = {};
    for (const id of TREE_IDS) {
      out[id] = [...src[id]];
    }
    return out;
  }

  function initShowSimulator() {
    const viewSingleBtn = document.getElementById("mode-tab-single");
    const viewShowBtn = document.getElementById("mode-tab-show");
    const singleWorkspace = document.getElementById("workspace-single");
    const showWorkspace = document.getElementById("workspace-show");
    if (!viewSingleBtn || !viewShowBtn || !singleWorkspace || !showWorkspace) return;

    const canvas = document.getElementById("show-canvas");
    const ctx = canvas.getContext("2d");

    // Controls
    const statusLine = document.getElementById("show-status-line");
    const btnPlay = document.getElementById("show-btn-play");
    const btnPause = document.getElementById("show-btn-pause");
    const btnRestart = document.getElementById("show-btn-restart");
    const timelineSlider = document.getElementById("show-timeline");
    const timelineTime = document.getElementById("show-time-label");
    const stepPreviewsEl = document.getElementById("show-step-previews");
    const timelineSegmentsEl = document.getElementById("show-timeline-segments");
    const dimSlider = document.getElementById("show-dim");
    const dimLabel = document.getElementById("show-dim-val");
    const speedSelect = document.getElementById("show-speed");
    const audioToggle = document.getElementById("show-audio-toggle");
    const volSlider = document.getElementById("show-vol");
    const smallBoostSlider = document.getElementById("show-small-boost");
    const smallBoostLabel = document.getElementById("show-small-boost-val");
    const turnsSlider = document.getElementById("show-turns");
    const turnsLabel = document.getElementById("show-turns-val");
    const actButtons = Array.from(document.querySelectorAll("[data-show-act]"));
    const camButtons = Array.from(document.querySelectorAll("[data-show-cam]"));
    const autoOrbitCheck = document.getElementById("show-auto-orbit");

    // Tree layout editor controls
    const treeSelect = document.getElementById("show-tree-select");
    const inpX = document.getElementById("tree-cfg-x");
    const inpY = document.getElementById("tree-cfg-y");
    const inpZ = document.getElementById("tree-cfg-z");
    const inpH = document.getElementById("tree-cfg-h");
    const inpD = document.getElementById("tree-cfg-d");
    const inpDens = document.getElementById("tree-cfg-dens");
    const btnResetLayout = document.getElementById("show-reset-layout");
    const btnExportLayout = document.getElementById("show-export-layout");

    // Code editor controls
    const panelTabBtns = Array.from(document.querySelectorAll("[data-show-panel]"));
    const panelControls = document.getElementById("show-panel-controls");
    const panelCode = document.getElementById("show-panel-code");
    const codeEditor = document.getElementById("show-code-editor");
    const codeError = document.getElementById("show-code-error");
    const btnApplyCode = document.getElementById("show-btn-apply-code");
    const btnResetCode = document.getElementById("show-btn-reset-code");

    const audio = new ShowAudioEngine();

    const state = {
      active: false,
      playing: true,
      showMs: 0,
      forcedAct: 0,
      dim: 0.85,
      speed: 1.0,
      turns: 5.0,
      smallBoost: 1.8,
      selectedTree: "T12",
      layout: cloneLayout(DEFAULT_TREE_LAYOUT),
      worldCoords: {},
      camera: {
        yaw: 0.35,
        pitch: 0.24,
        zoom: 1.0,
        autoOrbit: false,
      },
      renderFn: null,
      projectedTrees: [],
    };

    const stepThumbEntries = [];
    let thumbRenderQueued = false;
    let lastActiveStepId = "";

    function projectThumbnailPoint(wx, wy, wz, width, height) {
      const cx = 0;
      const cy = 430;
      const cz = 100;
      const x = wx - cx;
      const y = wy - cy;
      const z = wz - cz;

      const yaw = 0.12;
      const pitch = 0.18;
      const cosY = Math.cos(yaw);
      const sinY = Math.sin(yaw);
      const x1 = x * cosY - z * sinY;
      const z1 = x * sinY + z * cosY;

      const cosP = Math.cos(pitch);
      const sinP = Math.sin(pitch);
      const y2 = y * cosP - z1 * sinP;
      const z2 = y * sinP + z1 * cosP;

      const depth = 2400 + z2;
      if (depth < 120) return null;
      const focal = width * 1.02;
      const scale = focal / depth;
      return {
        sx: width * 0.5 + x1 * scale,
        sy: height * 0.62 - y2 * scale,
        scale,
        depth,
      };
    }

    function renderStepThumbnail(entry) {
      if (!state.renderFn) return;
      const { step, canvas: tCanvas, ctx: tCtx } = entry;
      const w = tCanvas.width;
      const h = tCanvas.height;

      tCtx.clearRect(0, 0, w, h);
      const bgGrad = tCtx.createRadialGradient(w * 0.5, h * 0.58, 6, w * 0.5, h * 0.52, w * 0.72);
      bgGrad.addColorStop(0, "#101a24");
      bgGrad.addColorStop(1, "#06090e");
      tCtx.fillStyle = bgGrad;
      tCtx.fillRect(0, 0, w, h);

      // Subtle horizon/ground line for spatial grounding
      const gLeft = projectThumbnailPoint(-1200, 0, 120, w, h);
      const gRight = projectThumbnailPoint(1200, 0, 120, w, h);
      if (gLeft && gRight) {
        tCtx.strokeStyle = "rgba(148, 163, 184, 0.14)";
        tCtx.lineWidth = 1;
        tCtx.beginPath();
        tCtx.moveTo(gLeft.sx, gLeft.sy);
        tCtx.lineTo(gRight.sx, gRight.sy);
        tCtx.stroke();
      }

      const previewMs = step.previewMs;
      const actInfo = ACTS[step.actId - 1];
      const actStartMs = actInfo[2];
      const bpm = actInfo[4];
      const local_ms = Math.max(0, previewMs - actStartMs);
      const t_s = (previewMs % SHOW_TOTAL_MS) / 1000.0;
      const beat = (local_ms / 1000.0) * (bpm / 60.0);
      const beat_frac = beat - Math.floor(beat);
      const pulse = Math.exp(-4.5 * beat_frac);

      const silDrawList = [];
      const ledDrawList = [];

      for (const treeId of TREE_IDS) {
        const [tx, tyBase, tz, hMm, dMm, densityScale] = state.layout[treeId];
        const isHero = treeId === "T11" || treeId === "T12";
        const visScale = isHero ? 1.0 : state.smallBoost;
        const coords = state.worldCoords[treeId];
        if (!coords) continue;
        const scale = state.dim * (isHero ? densityScale : Math.max(0.85, densityScale));

        const baseProj = projectThumbnailPoint(tx, tyBase, tz, w, h);
        const silProj = [];
        for (let sIdx = 0; sIdx < TREE_SILHOUETTE.length; sIdx += 2) {
          const [ux, uy] = TREE_SILHOUETTE[sIdx];
          const sp = projectThumbnailPoint(tx + ux * dMm * visScale, tyBase + uy * hMm * visScale, tz, w, h);
          if (sp) silProj.push(sp);
        }
        if (baseProj && silProj.length >= 3) {
          silDrawList.push({ depth: baseProj.depth, silProj });
        }

        for (let idx = 0; idx < NUM_LEDS; idx++) {
          const [wx, wy, wz] = coords[idx];
          const dispX = tx + (wx - tx) * visScale;
          const dispY = tyBase + (wy - tyBase) * visScale;
          const dispZ = tz + (wz - tz) * visScale;
          const p = projectThumbnailPoint(dispX, dispY, dispZ, w, h);
          if (!p) continue;

          let rgb;
          try {
            rgb = state.renderFn(
              wx, wy, wz, idx, treeId, isHero,
              step.actId, t_s, local_ms, previewMs, beat_frac, pulse, hsvToRgb
            );
          } catch {
            rgb = [0, 0, 0];
          }

          const r = GAMMA_LUT[Math.min(255, Math.max(0, Math.floor((rgb[0] || 0) * scale * 255)))];
          const g = GAMMA_LUT[Math.min(255, Math.max(0, Math.floor((rgb[1] || 0) * scale * 255)))];
          const b = GAMMA_LUT[Math.min(255, Math.max(0, Math.floor((rgb[2] || 0) * scale * 255)))];

          ledDrawList.push({
            sx: p.sx,
            sy: p.sy,
            depth: p.depth,
            scale: p.scale,
            r, g, b,
            isHero,
          });
        }
      }

      // Draw tree silhouettes back-to-front
      silDrawList.sort((a, b) => b.depth - a.depth);
      for (const t of silDrawList) {
        tCtx.beginPath();
        tCtx.moveTo(t.silProj[0].sx, t.silProj[0].sy);
        for (let i = 1; i < t.silProj.length; i++) {
          tCtx.lineTo(t.silProj[i].sx, t.silProj[i].sy);
        }
        tCtx.closePath();
        tCtx.fillStyle = "rgba(17, 25, 21, 0.78)";
        tCtx.fill();
        tCtx.strokeStyle = "rgba(196, 154, 69, 0.34)";
        tCtx.lineWidth = 0.85;
        tCtx.stroke();
      }

      // Draw dim/unlit LEDs
      ledDrawList.sort((a, b) => b.depth - a.depth);
      for (const led of ledDrawList) {
        const lum = Math.max(led.r, led.g, led.b) / 255;
        if (lum <= 0.02) {
          tCtx.beginPath();
          tCtx.arc(led.sx, led.sy, 0.9, 0, Math.PI * 2);
          tCtx.fillStyle = "rgba(46, 62, 54, 0.5)";
          tCtx.fill();
        }
      }

      // Draw lit LEDs with soft additive bloom so colors stay vivid at thumbnail scale
      tCtx.save();
      tCtx.globalCompositeOperation = "lighter";
      for (const led of ledDrawList) {
        const maxC = Math.max(led.r, led.g, led.b);
        const lum = maxC / 255;
        if (lum <= 0.02) continue;

        const invMax = 255 / maxC;
        const hr = Math.round(led.r * invMax);
        const hg = Math.round(led.g * invMax);
        const hb = Math.round(led.b * invMax);

        const baseRadius = Math.max(1.0, led.scale * (led.isHero ? 11.0 : 8.5));
        const haloRadius = baseRadius * (2.1 + lum * 1.4);

        const grad = tCtx.createRadialGradient(led.sx, led.sy, baseRadius * 0.2, led.sx, led.sy, haloRadius);
        grad.addColorStop(0, `rgba(${hr}, ${hg}, ${hb}, ${(0.58 * lum).toFixed(3)})`);
        grad.addColorStop(0.4, `rgba(${hr}, ${hg}, ${hb}, ${(0.24 * lum).toFixed(3)})`);
        grad.addColorStop(1, `rgba(${hr}, ${hg}, ${hb}, 0)`);

        tCtx.beginPath();
        tCtx.arc(led.sx, led.sy, haloRadius, 0, Math.PI * 2);
        tCtx.fillStyle = grad;
        tCtx.fill();

        const whiteMix = Math.min(0.42, Math.pow(lum, 1.5) * 0.42);
        const cr = Math.min(255, Math.round(led.r + (255 - led.r) * whiteMix));
        const cg = Math.min(255, Math.round(led.g + (255 - led.g) * whiteMix));
        const cb = Math.min(255, Math.round(led.b + (255 - led.b) * whiteMix));

        tCtx.beginPath();
        tCtx.arc(led.sx, led.sy, baseRadius, 0, Math.PI * 2);
        tCtx.fillStyle = `rgb(${cr}, ${cg}, ${cb})`;
        tCtx.fill();
      }
      tCtx.restore();
    }

    function renderAllStepThumbnails() {
      thumbRenderQueued = false;
      for (const entry of stepThumbEntries) {
        renderStepThumbnail(entry);
      }
    }

    function scheduleThumbnailRender() {
      if (!stepThumbEntries.length || thumbRenderQueued) return;
      thumbRenderQueued = true;
      requestAnimationFrame(renderAllStepThumbnails);
    }

    function getActiveStepId(showMs) {
      const t = ((showMs % SHOW_TOTAL_MS) + SHOW_TOTAL_MS) % SHOW_TOTAL_MS;
      if (state.forcedAct >= 1 && state.forcedAct <= ACTS.length) {
        if (state.forcedAct === 1) {
          return resolveAct(t).localMs >= 90_000 ? "act1b" : "act1a";
        }
        if (state.forcedAct === 6) {
          return resolveAct(t).localMs >= 80_000 ? "act6b" : "act6a";
        }
        const match = SHOW_STEP_PREVIEWS.find((s) => s.actId === state.forcedAct);
        return match ? match.id : "act1a";
      }
      for (const step of SHOW_STEP_PREVIEWS) {
        if (t >= step.startMs && t < step.endMs) {
          return step.id;
        }
      }
      return SHOW_STEP_PREVIEWS[0].id;
    }

    function updateActiveStepPreview(showMs) {
      if (!stepThumbEntries.length) return;
      const activeId = getActiveStepId(showMs);
      if (activeId === lastActiveStepId) return;
      lastActiveStepId = activeId;
      for (const entry of stepThumbEntries) {
        const isCurrent = entry.step.id === activeId;
        entry.btn.classList.toggle("is-active", isCurrent);
        entry.btn.setAttribute("aria-current", isCurrent ? "step" : "false");
        if (entry.seg) {
          entry.seg.classList.toggle("is-active", isCurrent);
        }
        if (isCurrent && stepPreviewsEl && stepPreviewsEl.scrollWidth > stepPreviewsEl.clientWidth) {
          const targetLeft = entry.btn.offsetLeft - (stepPreviewsEl.clientWidth - entry.btn.offsetWidth) / 2;
          stepPreviewsEl.scrollTo({ left: Math.max(0, targetLeft), behavior: "smooth" });
        }
      }
    }

    function jumpToStep(step) {
      state.showMs = step.jumpMs;
      state.forcedAct = 0;
      for (const b of actButtons) {
        b.classList.toggle("is-active", Number(b.dataset.showAct) === 0);
      }
      timelineSlider.value = String(Math.floor(state.showMs / 1000));
      timelineTime.textContent = `${formatTimeMs(state.showMs)} / ${SHOW_TOTAL_LABEL}`;
      lastActiveStepId = "";
      updateActiveStepPreview(state.showMs);
      syncPermalink();
    }

    function buildStepPreviews() {
      if (!stepPreviewsEl) return;
      stepPreviewsEl.innerHTML = "";
      if (timelineSegmentsEl) timelineSegmentsEl.innerHTML = "";
      stepThumbEntries.length = 0;

      for (const step of SHOW_STEP_PREVIEWS) {
        const startLabel = formatTimeMs(step.startMs);
        const endLabel = step.endMs >= SHOW_TOTAL_MS ? SHOW_TOTAL_LABEL : formatTimeMs(step.endMs);
        const tooltip = `${step.fullTitle} (${startLabel}–${endLabel})`;

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "show-step-thumb";
        btn.setAttribute("role", "listitem");
        btn.dataset.stepId = step.id;
        btn.dataset.stepMs = String(step.jumpMs);
        btn.title = tooltip;
        btn.setAttribute("aria-label", `${step.fullTitle}, ab ${startLabel}`);

        const media = document.createElement("span");
        media.className = "show-step-thumb-media";

        const tCanvas = document.createElement("canvas");
        tCanvas.className = "show-step-thumb-canvas";
        tCanvas.width = 160;
        tCanvas.height = 100;
        tCanvas.setAttribute("aria-hidden", "true");

        const badge = document.createElement("span");
        badge.className = "show-step-thumb-badge";
        badge.textContent = step.shortAct;

        const timeTag = document.createElement("span");
        timeTag.className = "show-step-thumb-time";
        timeTag.textContent = startLabel;

        media.append(tCanvas, badge, timeTag);

        const caption = document.createElement("span");
        caption.className = "show-step-thumb-caption";
        caption.textContent = step.label;

        btn.append(media, caption);
        stepPreviewsEl.appendChild(btn);

        let seg = null;
        if (timelineSegmentsEl) {
          seg = document.createElement("button");
          seg.type = "button";
          seg.className = "show-timeline-seg";
          seg.tabIndex = -1;
          seg.style.flex = `${step.endMs - step.startMs} 0 0`;
          seg.title = tooltip;
          seg.dataset.stepId = step.id;
          timelineSegmentsEl.appendChild(seg);
        }

        const setHover = (hovered) => {
          btn.classList.toggle("is-hovered", hovered);
          if (seg) seg.classList.toggle("is-hovered", hovered);
        };

        btn.addEventListener("pointerenter", () => setHover(true));
        btn.addEventListener("pointerleave", () => setHover(false));
        btn.addEventListener("click", () => jumpToStep(step));

        if (seg) {
          seg.addEventListener("pointerenter", () => setHover(true));
          seg.addEventListener("pointerleave", () => setHover(false));
          seg.addEventListener("click", () => jumpToStep(step));
        }

        stepThumbEntries.push({
          step,
          btn,
          canvas: tCanvas,
          ctx: tCanvas.getContext("2d"),
          seg,
        });
      }
    }

    function rebuildCoords() {
      for (const id of TREE_IDS) {
        const [tx, tyBase, tz, hMm, dMm] = state.layout[id];
        const coords = [];
        for (let i = 0; i < NUM_LEDS; i++) {
          const [ux, uy] = LED_NORM_COORDS[i];
          const wx = tx + ux * dMm;
          const wy = tyBase + uy * hMm;
          const wz = tz;
          coords.push([wx, wy, wz]);
        }
        state.worldCoords[id] = coords;
      }
    }

    function compileRenderCode(codeStr) {
      try {
        const fn = new Function(
          "wx", "wy", "wz", "idx", "treeId", "isHero",
          "actId", "t_s", "local_ms", "show_ms", "beat_frac", "pulse", "hsv_to_rgb",
          codeStr
        );
        // Smoke test
        const res = fn(0, 100, 0, 0, "T01", false, 1, 1.0, 1000, 1000, 0.2, 0.5, hsvToRgb);
        if (!Array.isArray(res) || res.length < 3) {
          throw new Error("Funktion muss [r, g, b] zurueckgeben.");
        }
        state.renderFn = fn;
        codeError.hidden = true;
        codeError.textContent = "";
        scheduleThumbnailRender();
        return true;
      } catch (err) {
        codeError.hidden = false;
        codeError.textContent = `Fehler in Render-Formel: ${err.message}`;
        return false;
      }
    }

    function syncTreeEditorInputs() {
      const cfg = state.layout[state.selectedTree];
      if (!cfg) return;
      treeSelect.value = state.selectedTree;
      inpX.value = cfg[0];
      inpY.value = cfg[1];
      inpZ.value = cfg[2];
      inpH.value = cfg[3];
      inpD.value = cfg[4];
      inpDens.value = cfg[5];
    }

    function populateTreeSelect() {
      treeSelect.innerHTML = "";
      for (const id of TREE_IDS) {
        const opt = document.createElement("option");
        opt.value = id;
        const isHero = id === "T11" || id === "T12";
        opt.textContent = isHero ? `${id} (Hero ${state.layout[id][3]}mm)` : `${id} (Mini ${state.layout[id][3]}mm)`;
        treeSelect.appendChild(opt);
      }
      syncTreeEditorInputs();
    }

    // 3D Projection (centered around stage center [0, 320, 120])
    function projectPoint(wx, wy, wz, width, height) {
      const cx = 0;
      const cy = 280;
      const cz = 120;
      const x = wx - cx;
      const y = wy - cy;
      const z = wz - cz;

      const cosY = Math.cos(state.camera.yaw);
      const sinY = Math.sin(state.camera.yaw);
      const x1 = x * cosY - z * sinY;
      const z1 = x * sinY + z * cosY;

      const cosP = Math.cos(state.camera.pitch);
      const sinP = Math.sin(state.camera.pitch);
      const y2 = y * cosP - z1 * sinP;
      const z2 = y * sinP + z1 * cosP;

      const camDist = 2500 / state.camera.zoom;
      const depth = camDist + z2;
      if (depth < 120) return null;
      const focal = Math.min(width, height) * 1.05;
      const scale = focal / depth;
      return {
        sx: width * 0.5 + x1 * scale,
        sy: height * 0.56 - y2 * scale,
        scale,
        depth,
      };
    }

    function resizeCanvas() {
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.max(240, Math.floor(rect.width));
      const h = Math.max(220, Math.floor(rect.height));
      if (canvas.width !== Math.floor(w * dpr) || canvas.height !== Math.floor(h * dpr)) {
        canvas.width = Math.floor(w * dpr);
        canvas.height = Math.floor(h * dpr);
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return { w, h };
    }

    function drawFrame(nowMs) {
      const { w, h } = resizeCanvas();
      ctx.clearRect(0, 0, w, h);

      // Background subtle radial vignette
      const bgGrad = ctx.createRadialGradient(w * 0.5, h * 0.55, 20, w * 0.5, h * 0.5, Math.max(w, h) * 0.7);
      bgGrad.addColorStop(0, "#101a24");
      bgGrad.addColorStop(1, "#070b10");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, w, h);

      // Draw stage ground grid (y = 0, X: -1200..1200, Z: -500..700)
      ctx.strokeStyle = "rgba(148, 163, 184, 0.12)";
      ctx.lineWidth = 1;
      for (let gx = -1200; gx <= 1200; gx += 300) {
        const p1 = projectPoint(gx, 0, -500, w, h);
        const p2 = projectPoint(gx, 0, 700, w, h);
        if (p1 && p2) {
          ctx.beginPath();
          ctx.moveTo(p1.sx, p1.sy);
          ctx.lineTo(p2.sx, p2.sy);
          ctx.stroke();
        }
      }
      for (let gz = -500; gz <= 700; gz += 300) {
        const p1 = projectPoint(-1200, 0, gz, w, h);
        const p2 = projectPoint(1200, 0, gz, w, h);
        if (p1 && p2) {
          ctx.beginPath();
          ctx.moveTo(p1.sx, p1.sy);
          ctx.lineTo(p2.sx, p2.sy);
          ctx.stroke();
        }
      }

      const showMs = state.showMs;
      const t_s = (showMs % SHOW_TOTAL_MS) / 1000.0;
      const resolved = resolveAct(showMs);
      const actId = state.forcedAct >= 1 && state.forcedAct <= ACTS.length ? state.forcedAct : resolved.actId;
      const bpm = state.forcedAct >= 1 && state.forcedAct <= ACTS.length ? ACTS[actId - 1][4] : resolved.bpm;
      const local_ms = resolved.localMs;

      const beat = (local_ms / 1000.0) * (bpm / 60.0);
      const beat_frac = beat - Math.floor(beat);
      const pulse = Math.exp(-4.5 * beat_frac);

      // Collect drawables for depth sorting
      const ledDrawList = [];
      const treeHitList = [];

      for (const treeId of TREE_IDS) {
        const [tx, tyBase, tz, hMm, dMm, densityScale] = state.layout[treeId];
        const isHero = treeId === "T11" || treeId === "T12";
        const visScale = isHero ? 1.0 : state.smallBoost;
        const coords = state.worldCoords[treeId];
        // Keep all 12 trees visually vibrant in the 3D simulator (densityScale is an ABL hardware limit)
        const scale = state.dim * (isHero ? densityScale : Math.max(0.85, densityScale));

        // Project tree silhouette & center for selection
        const baseProj = projectPoint(tx, tyBase, tz, w, h);
        const tipProj = projectPoint(tx, tyBase + hMm * visScale, tz, w, h);
        const silProj = [];
        for (const [ux, uy] of TREE_SILHOUETTE) {
          const sp = projectPoint(tx + ux * dMm * visScale, tyBase + uy * hMm * visScale, tz, w, h);
          if (sp) silProj.push(sp);
        }

        if (baseProj && tipProj) {
          const isSelected = treeId === state.selectedTree;
          treeHitList.push({
            treeId,
            sx: (baseProj.sx + tipProj.sx) * 0.5,
            sy: (baseProj.sy + tipProj.sy) * 0.5,
            depth: baseProj.depth,
            isSelected,
            baseProj,
            tipProj,
            silProj,
            isHero,
          });
        }

        for (let idx = 0; idx < NUM_LEDS; idx++) {
          const [wx, wy, wz] = coords[idx];
          // Visual display coordinates (apply small-tree boost around tree base if enabled)
          const dispX = tx + (wx - tx) * visScale;
          const dispY = tyBase + (wy - tyBase) * visScale;
          const dispZ = tz + (wz - tz) * visScale;

          const p = projectPoint(dispX, dispY, dispZ, w, h);
          if (!p) continue;

          let rgb;
          try {
            rgb = state.renderFn(
              wx, wy, wz, idx, treeId, isHero,
              actId, t_s, local_ms, showMs, beat_frac, pulse, hsvToRgb
            );
          } catch {
            rgb = [0, 0, 0];
          }

          const r = GAMMA_LUT[Math.min(255, Math.max(0, Math.floor((rgb[0] || 0) * scale * 255)))];
          const g = GAMMA_LUT[Math.min(255, Math.max(0, Math.floor((rgb[1] || 0) * scale * 255)))];
          const b = GAMMA_LUT[Math.min(255, Math.max(0, Math.floor((rgb[2] || 0) * scale * 255)))];

          ledDrawList.push({
            sx: p.sx,
            sy: p.sy,
            depth: p.depth,
            scale: p.scale,
            r, g, b,
            isHero,
          });
        }
      }

      // Draw tree silhouettes & labels (back to front)
      treeHitList.sort((a, b) => b.depth - a.depth);
      state.projectedTrees = treeHitList;

      for (const t of treeHitList) {
        if (t.silProj.length >= 3) {
          ctx.beginPath();
          ctx.moveTo(t.silProj[0].sx, t.silProj[0].sy);
          for (let i = 1; i < t.silProj.length; i++) {
            ctx.lineTo(t.silProj[i].sx, t.silProj[i].sy);
          }
          ctx.closePath();
          ctx.fillStyle = t.isSelected ? "rgba(56, 189, 248, 0.10)" : "rgba(17, 24, 20, 0.55)";
          ctx.fill();
          ctx.strokeStyle = t.isSelected ? "rgba(56, 189, 248, 0.85)" : "rgba(196, 154, 69, 0.45)";
          ctx.lineWidth = t.isSelected ? 1.5 : 1;
          ctx.stroke();
        }

        // Label below base
        ctx.font = t.isSelected ? "600 11px Inter, sans-serif" : "500 10px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillStyle = t.isSelected ? "#38bdf8" : t.isHero ? "#d4a853" : "rgba(148, 163, 184, 0.8)";
        const label = t.treeId === "T12" ? "★ T12" : t.treeId;
        ctx.fillText(label, t.baseProj.sx, t.baseProj.sy + 14);
      }

      // Draw LEDs (back to front)
      ledDrawList.sort((a, b) => b.depth - a.depth);
      for (const led of ledDrawList) {
        const lum = Math.max(led.r, led.g, led.b) / 255;
        const baseRadius = Math.max(1.8, led.scale * (led.isHero ? 6.5 : 4.8));

        if (lum <= 0.02) {
          ctx.beginPath();
          ctx.arc(led.sx, led.sy, baseRadius, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(38, 50, 44, 0.65)";
          ctx.fill();
        }
      }

      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      for (const led of ledDrawList) {
        const maxC = Math.max(led.r, led.g, led.b);
        const lum = maxC / 255;
        if (lum <= 0.02) continue;

        const invMax = 255 / maxC;
        const hr = Math.round(led.r * invMax);
        const hg = Math.round(led.g * invMax);
        const hb = Math.round(led.b * invMax);

        const baseRadius = Math.max(1.8, led.scale * (led.isHero ? 6.5 : 4.8));
        const haloRadius = baseRadius * (2.6 + lum * 2.2);

        const grad = ctx.createRadialGradient(led.sx, led.sy, baseRadius * 0.25, led.sx, led.sy, haloRadius);
        grad.addColorStop(0, `rgba(${hr}, ${hg}, ${hb}, ${(0.75 * lum).toFixed(3)})`);
        grad.addColorStop(0.35, `rgba(${hr}, ${hg}, ${hb}, ${(0.38 * lum).toFixed(3)})`);
        grad.addColorStop(1, `rgba(${hr}, ${hg}, ${hb}, 0)`);

        ctx.beginPath();
        ctx.arc(led.sx, led.sy, haloRadius, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();

        const whiteMix = Math.min(0.75, Math.pow(lum, 1.3) * 0.75);
        const cr = Math.min(255, Math.round(led.r + (255 - led.r) * whiteMix));
        const cg = Math.min(255, Math.round(led.g + (255 - led.g) * whiteMix));
        const cb = Math.min(255, Math.round(led.b + (255 - led.b) * whiteMix));

        ctx.beginPath();
        ctx.arc(led.sx, led.sy, baseRadius, 0, Math.PI * 2);
        ctx.fillStyle = `rgb(${cr}, ${cg}, ${cb})`;
        ctx.fill();
      }
      ctx.restore();

      // Update HUD status
      const m = Math.floor(showMs / 60_000);
      const sec = Math.floor((showMs % 60_000) / 1000);
      const timeStr = `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
      timelineTime.textContent = `${timeStr} / ${SHOW_TOTAL_LABEL}`;
      timelineSlider.value = String(Math.floor(showMs / 1000));
      updateActiveStepPreview(showMs);

      const actName = ACTS[actId - 1][1];
      statusLine.textContent = `${actName} · ${bpm} BPM · ${state.playing ? "Aktiv" : "Pause"} · 12 Bäume (720 LEDs)`;
    }

    // Animation loop
    let lastFrameTime = performance.now();
    let lastPermalinkSync = 0;
    function tick(now) {
      const dt = Math.min(100, Math.max(0, now - lastFrameTime));
      lastFrameTime = now;

      if (state.active) {
        if (state.playing) {
          state.showMs = (state.showMs + dt * state.speed) % SHOW_TOTAL_MS;
        }
        if (state.camera.autoOrbit) {
          state.camera.yaw += dt * 0.00025;
        }
        audio.update(state.showMs, state.playing);
        drawFrame(now);
        if (now - lastPermalinkSync >= 1000) {
          lastPermalinkSync = now;
          syncPermalink();
        }
      }
      requestAnimationFrame(tick);
    }

    // Mode switching & permalink support (#show&t=..&act=..&yaw=..&pitch=..&zoom=..)
    function buildShowHash() {
      const params = new URLSearchParams();
      params.set("t", String(Math.floor(state.showMs / 1000)));
      if (state.forcedAct >= 1 && state.forcedAct <= ACTS.length) {
        params.set("act", String(state.forcedAct));
      }
      params.set("yaw", state.camera.yaw.toFixed(3));
      params.set("pitch", state.camera.pitch.toFixed(3));
      params.set("zoom", state.camera.zoom.toFixed(2));
      return `#show&${params.toString()}`;
    }

    function syncPermalink() {
      if (!state.active || !window.history || !window.history.replaceState) return;
      const targetHash = buildShowHash();
      if (window.location.hash !== targetHash) {
        const url = new URL(window.location.href);
        url.hash = targetHash;
        window.history.replaceState(null, "", url.toString());
      }
    }

    function setMode(mode, updateUrl = true) {
      const isShow = mode === "show";
      state.active = isShow;
      singleWorkspace.hidden = isShow;
      showWorkspace.hidden = !isShow;
      viewSingleBtn.classList.toggle("is-active", !isShow);
      viewShowBtn.classList.toggle("is-active", isShow);
      viewSingleBtn.setAttribute("aria-selected", String(!isShow));
      viewShowBtn.setAttribute("aria-selected", String(isShow));
      if (!isShow) {
        audio.setEnabled(false);
        audioToggle.checked = false;
      }
      if (updateUrl && window.history && window.history.replaceState) {
        const targetHash = isShow ? buildShowHash() : "#single";
        if (window.location.hash !== targetHash) {
          const url = new URL(window.location.href);
          url.hash = targetHash;
          window.history.replaceState(null, "", url.toString());
        }
      }
    }

    function applyUrlPermalink() {
      const url = new URL(window.location.href);
      const hash = url.hash.replace(/^#/, "");
      const hashParams = new URLSearchParams(hash.includes("=") ? hash : "");
      const queryMode = url.searchParams.get("mode");
      const isShow =
        hash === "show" ||
        hash.startsWith("show&") ||
        hashParams.get("mode") === "show" ||
        queryMode === "show";

      const actRaw = hashParams.get("act") ?? url.searchParams.get("act");
      if (actRaw !== null) {
        const actParam = Number(actRaw);
        if (actParam >= 1 && actParam <= ACTS.length) {
          state.forcedAct = actParam;
          state.showMs = ACTS[actParam - 1][2];
          for (const b of actButtons) {
            b.classList.toggle("is-active", Number(b.dataset.showAct) === actParam);
          }
        }
      }

      const tRaw = hashParams.get("t") ?? url.searchParams.get("t");
      if (tRaw !== null && tRaw !== "" && Number.isFinite(Number(tRaw))) {
        const tSec = Math.max(0, Number(tRaw));
        state.showMs = (tSec * 1000) % SHOW_TOTAL_MS;
      }

      const yawRaw = hashParams.get("yaw") ?? url.searchParams.get("yaw");
      if (yawRaw !== null && yawRaw !== "" && Number.isFinite(Number(yawRaw))) {
        state.camera.yaw = Number(yawRaw);
      }

      const pitchRaw = hashParams.get("pitch") ?? url.searchParams.get("pitch");
      if (pitchRaw !== null && pitchRaw !== "" && Number.isFinite(Number(pitchRaw))) {
        state.camera.pitch = Math.max(-0.4, Math.min(1.45, Number(pitchRaw)));
      }

      const zoomRaw = hashParams.get("zoom") ?? url.searchParams.get("zoom");
      if (zoomRaw !== null && zoomRaw !== "" && Number.isFinite(Number(zoomRaw))) {
        state.camera.zoom = Math.max(0.45, Math.min(2.6, Number(zoomRaw)));
      }

      if (isShow) {
        setMode("show", false);
      } else if (hash === "single" || queryMode === "single") {
        setMode("single", false);
      }
      lastActiveStepId = "";
      updateActiveStepPreview(state.showMs);
    }

    viewSingleBtn.addEventListener("click", () => setMode("single", true));
    viewShowBtn.addEventListener("click", () => setMode("show", true));
    window.addEventListener("hashchange", applyUrlPermalink);

    // Transport events
    btnPlay.addEventListener("click", () => { state.playing = true; syncPermalink(); });
    btnPause.addEventListener("click", () => { state.playing = false; syncPermalink(); });
    btnRestart.addEventListener("click", () => {
      state.showMs = 0;
      state.playing = true;
      syncPermalink();
    });

    timelineSlider.addEventListener("input", () => {
      state.showMs = Number(timelineSlider.value) * 1000;
      updateActiveStepPreview(state.showMs);
      syncPermalink();
    });

    dimSlider.addEventListener("input", () => {
      state.dim = Number(dimSlider.value) / 100;
      dimLabel.textContent = `${dimSlider.value}%`;
      scheduleThumbnailRender();
    });

    speedSelect.addEventListener("change", () => {
      state.speed = Number(speedSelect.value) || 1.0;
    });

    audioToggle.addEventListener("change", () => {
      audio.setEnabled(audioToggle.checked);
    });

    volSlider.addEventListener("input", () => {
      audio.setVolume(Number(volSlider.value) / 100);
    });

    smallBoostSlider.addEventListener("input", () => {
      state.smallBoost = Number(smallBoostSlider.value);
      smallBoostLabel.textContent = `${state.smallBoost.toFixed(1)}×`;
      scheduleThumbnailRender();
    });

    turnsSlider.addEventListener("input", () => {
      state.turns = Number(turnsSlider.value);
      turnsLabel.textContent = `${state.turns.toFixed(1)}`;
      rebuildCoords();
      scheduleThumbnailRender();
    });

    for (const btn of actButtons) {
      btn.addEventListener("click", () => {
        const act = Number(btn.dataset.showAct);
        state.forcedAct = act;
        if (act >= 1 && act <= ACTS.length) {
          state.showMs = ACTS[act - 1][2];
        }
        for (const b of actButtons) {
          b.classList.toggle("is-active", Number(b.dataset.showAct) === act);
        }
        lastActiveStepId = "";
        updateActiveStepPreview(state.showMs);
        syncPermalink();
      });
    }

    for (const btn of camButtons) {
      btn.addEventListener("click", () => {
        const preset = btn.dataset.showCam;
        if (preset === "front") {
          state.camera.yaw = 0;
          state.camera.pitch = 0.14;
          state.camera.zoom = 1.0;
        } else if (preset === "iso") {
          state.camera.yaw = 0.48;
          state.camera.pitch = 0.34;
          state.camera.zoom = 1.0;
        } else if (preset === "top") {
          state.camera.yaw = 0;
          state.camera.pitch = 1.35;
          state.camera.zoom = 0.95;
        }
        syncPermalink();
      });
    }

    autoOrbitCheck.addEventListener("change", () => {
      state.camera.autoOrbit = autoOrbitCheck.checked;
    });

    // Canvas pointer orbit & tree click selection
    let dragging = false;
    let dragMoved = false;
    let lastX = 0;
    let lastY = 0;

    canvas.addEventListener("pointerdown", (e) => {
      dragging = true;
      dragMoved = false;
      lastX = e.clientX;
      lastY = e.clientY;
      canvas.setPointerCapture(e.pointerId);
    });

    canvas.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) dragMoved = true;
      lastX = e.clientX;
      lastY = e.clientY;
      state.camera.yaw += dx * 0.008;
      state.camera.pitch = Math.max(-0.4, Math.min(1.45, state.camera.pitch + dy * 0.008));
    });

    canvas.addEventListener("pointerup", (e) => {
      if (!dragging) return;
      dragging = false;
      if (dragMoved) {
        syncPermalink();
      } else {
        const rect = canvas.getBoundingClientRect();
        const cx = e.clientX - rect.left;
        const cy = e.clientY - rect.top;
        let best = null;
        let bestDist = 42;
        for (const t of state.projectedTrees) {
          const d = Math.hypot(t.sx - cx, t.sy - cy);
          if (d < bestDist) {
            bestDist = d;
            best = t.treeId;
          }
        }
        if (best) {
          state.selectedTree = best;
          syncTreeEditorInputs();
        }
      }
    });

    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      state.camera.zoom = Math.max(0.45, Math.min(2.6, state.camera.zoom * factor));
      syncPermalink();
    }, { passive: false });

    // Tree layout editor
    treeSelect.addEventListener("change", () => {
      state.selectedTree = treeSelect.value;
      syncTreeEditorInputs();
    });

    function onTreeInputChanged() {
      const id = state.selectedTree;
      state.layout[id] = [
        Number(inpX.value) || 0,
        Number(inpY.value) || 0,
        Number(inpZ.value) || 0,
        Math.max(20, Number(inpH.value) || 100),
        Math.max(10, Number(inpD.value) || 65),
        Math.max(0.05, Math.min(1.0, Number(inpDens.value) || 0.35)),
      ];
      rebuildCoords();
      scheduleThumbnailRender();
    }

    for (const inp of [inpX, inpY, inpZ, inpH, inpD, inpDens]) {
      inp.addEventListener("input", onTreeInputChanged);
    }

    btnResetLayout.addEventListener("click", () => {
      state.layout = cloneLayout(DEFAULT_TREE_LAYOUT);
      state.turns = 5.0;
      turnsSlider.value = "5.0";
      turnsLabel.textContent = "5.0";
      rebuildCoords();
      populateTreeSelect();
      scheduleThumbnailRender();
    });

    btnExportLayout.addEventListener("click", () => {
      const lines = ["TREE_LAYOUT = {"];
      for (const id of TREE_IDS) {
        const [x, y, z, h, d, dens] = state.layout[id];
        lines.push(`    "${id}": (${Math.round(x)}, ${Math.round(y)}, ${Math.round(z)}, ${Math.round(h)}, ${Math.round(d)}, ${dens.toFixed(2)}),`);
      }
      lines.push("}");
      const text = lines.join("\n");
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
          btnExportLayout.textContent = "✓ Kopiert!";
          setTimeout(() => { btnExportLayout.textContent = "📋 Python TREE_LAYOUT kopieren"; }, 1800);
        });
      }
    });

    // Right-pane sub-tabs (Controls vs Live Render Code)
    for (const btn of panelTabBtns) {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.showPanel;
        const isCode = tab === "code";
        panelControls.hidden = isCode;
        panelCode.hidden = !isCode;
        for (const b of panelTabBtns) {
          b.classList.toggle("is-active", b.dataset.showPanel === tab);
        }
      });
    }

    codeEditor.value = DEFAULT_RENDER_CODE;
    btnApplyCode.addEventListener("click", () => {
      if (compileRenderCode(codeEditor.value)) {
        btnApplyCode.textContent = "✓ Aktiv";
        setTimeout(() => { btnApplyCode.textContent = "▶ Formel anwenden"; }, 1400);
      }
    });

    btnResetCode.addEventListener("click", () => {
      codeEditor.value = DEFAULT_RENDER_CODE;
      compileRenderCode(DEFAULT_RENDER_CODE);
    });

    // Initialize
    rebuildCoords();
    populateTreeSelect();
    buildStepPreviews();
    compileRenderCode(DEFAULT_RENDER_CODE);
    renderAllStepThumbnails();
    applyUrlPermalink();
    updateActiveStepPreview(state.showMs);
    requestAnimationFrame(tick);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initShowSimulator);
  } else {
    initShowSimulator();
  }
})();
