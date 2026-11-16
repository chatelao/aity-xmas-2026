// AITY Xmas Tree 2026 — Simulator UI & SVG Tree Renderer
(function () {
  // Exact KiCad PCB coordinates (x_mm, y_mm, segment_id) from tannenbaum_layout.py
  const PIXEL_COORDS = [
    // Seg 0: Stern Innen (0..4)
    [138.7170, -32.1639, 0], [132.2500, -29.5500, 0], [125.6868, -32.2740, 0], [129.3756, -38.1534, 0], [136.1286, -39.8746, 0],
    // Seg 1: Stern Aussen (5..9)
    [136.8149, -32.7819, 1], [132.2500, -27.5500, 1], [127.5889, -32.8920, 1], [128.2000, -39.7714, 1], [134.8820, -38.2811, 1],
    // Seg 2: Zweig Mitte (10..23)
    [147.3545, -81.2933, 2], [144.9116, -82.2311, 2], [142.3839, -82.9084, 2], [139.7993, -83.3177, 2], [137.1861, -83.4547, 2],
    [134.5729, -83.3177, 2], [131.9883, -82.9084, 2], [129.4607, -82.2311, 2], [127.0177, -81.2933, 2], [124.6861, -80.1053, 2],
    [122.4915, -78.6801, 2], [120.4579, -77.0333, 2], [118.6075, -75.1829, 2], [116.9607, -73.1493, 2],
    // Seg 3: Zweig Unten (24..41)
    [149.8776, -87.3257, 3], [148.0930, -89.2395, 3], [146.1180, -90.9563, 3], [143.9745, -92.4572, 3], [141.6858, -93.7259, 3],
    [139.2770, -94.7483, 3], [136.7746, -95.5134, 3], [134.2058, -96.0127, 3], [131.5990, -96.2408, 3], [128.9826, -96.1951, 3],
    [126.3853, -95.8762, 3], [123.8356, -95.2876, 3], [121.3613, -94.4356, 3], [118.9897, -93.3297, 3], [116.7467, -91.9820, 3],
    [114.6568, -90.4071, 3], [112.7430, -88.6225, 3], [111.0262, -86.6476, 3],
    // Seg 4: Zweig Oben (42..54)
    [147.4950, -70.8705, 4], [144.8818, -71.0075, 4], [142.2686, -70.8705, 4], [139.6840, -70.4612, 4], [137.1564, -69.7839, 4],
    [134.7134, -68.8461, 4], [132.3818, -67.6581, 4], [130.1872, -66.2329, 4], [128.1535, -64.5861, 4], [126.3032, -62.7357, 4],
    [124.6564, -60.7021, 4], [123.2312, -58.5075, 4], [122.0432, -56.1759, 4],
    // Seg 5: Stiel (55..59)
    [138.0086, -49.6069, 5], [136.4000, -51.4000, 5], [134.7532, -53.4336, 5], [132.9028, -55.2840, 5], [130.8692, -56.9308, 5],
  ];

  const SEGMENT_NAMES = [
    "Stern Innen",
    "Stern Aussen",
    "Zweig Mitte",
    "Zweig Unten",
    "Zweig Oben",
    "Stiel",
  ];

  const X_MIN = 111.0262;
  const Y_MAX = -27.5500;
  const PAD_X = 8.5;
  const PAD_TOP = 6.5;

  const SVG_NS = "http://www.w3.org/2000/svg";

  function toSvg(x, y) {
    return [x - X_MIN + PAD_X, Y_MAX - y + PAD_TOP];
  }

  function el(tag, attrs = {}) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      node.setAttribute(k, String(v));
    }
    return node;
  }

  // DOM Elements
  const treeSvg = document.getElementById("tree-svg");
  const inspectorEl = document.getElementById("led-inspector");
  const exampleSelect = document.getElementById("example-select");
  const exampleDesc = document.getElementById("example-desc");
  const statusBadge = document.getElementById("status-badge");
  const statusText = document.getElementById("status-text");
  const consoleEl = document.getElementById("serial-console");
  const toggleIndices = document.getElementById("toggle-indices");
  const toggleTraces = document.getElementById("toggle-traces");

  const btnRun = document.getElementById("btn-run");
  const btnStop = document.getElementById("btn-stop");
  const btnReset = document.getElementById("btn-reset");
  const btnDownload = document.getElementById("btn-download");
  const btnClearConsole = document.getElementById("btn-clear-console");

  const btnD5 = document.getElementById("btn-d5");
  const btnD6 = document.getElementById("btn-d6");
  const stateD5 = document.getElementById("state-d5");
  const stateD6 = document.getElementById("state-d6");
  const hintD5 = document.getElementById("hint-d5");
  const hintD6 = document.getElementById("hint-d6");
  const latchD5 = document.getElementById("latch-d5");
  const latchD6 = document.getElementById("latch-d6");

  // LED state for inspection
  const lastRgb = Array.from({ length: 60 }, () => [0, 0, 0]);
  const ledNodes = [];
  let onboardChipNode = null;
  let onboardGlowNode = null;
  let tracesGroup = null;
  let indicesGroup = null;

  // Build Christmas Tree PCB SVG
  function buildTreeSvg() {
    // Defs for soft LED glow filter
    const defs = el("defs");
    const filter = el("filter", { id: "led-glow", x: "-100%", y: "-100%", width: "300%", height: "300%" });
    filter.appendChild(el("feGaussianBlur", { stdDeviation: "1.35", result: "blur" }));
    defs.appendChild(filter);
    treeSvg.appendChild(defs);

    // Stylized Christmas tree PCB silhouette behind the 60 LEDs
    const pcbGroup = el("g", { id: "pcb-board" });
    const treePath = [
      "M 29.7 3.2",
      "L 34.0 9.6 L 40.5 11.2 L 35.8 16.5 L 37.8 22.8 L 31.2 19.6",
      "L 33.4 26.2 L 42.5 34.5 L 49.0 48.0 L 43.2 49.2",
      "L 49.5 58.2 L 44.5 60.2 L 51.8 66.5 L 46.0 72.5",
      "Q 29.7 79.5 13.5 72.5",
      "L 5.2 66.0 L 12.2 59.5 L 7.5 53.0 L 15.0 47.0",
      "L 10.5 36.0 L 20.5 28.0 L 23.0 19.6",
      "L 18.2 22.8 L 20.2 16.5 L 15.5 11.2 L 22.0 9.6 L 26.2 3.2",
      "Z"
    ].join(" ");

    pcbGroup.appendChild(el("path", {
      d: treePath,
      fill: "#0c2b1c",
      stroke: "#c49a45",
      "stroke-width": "0.45",
      "stroke-linejoin": "round",
    }));

    // XIAO MCU module silhouette at bottom trunk
    pcbGroup.appendChild(el("rect", {
      x: 21.2, y: 74.0, width: 17.0, height: 14.5, rx: 1.2,
      fill: "#11161c", stroke: "#c49a45", "stroke-width": "0.35"
    }));
    // USB-C port
    pcbGroup.appendChild(el("rect", {
      x: 26.7, y: 86.8, width: 6.0, height: 2.6, rx: 0.5,
      fill: "#8b949e"
    }));
    const xiaoLabel = el("text", {
      x: 29.7, y: 80.2, "text-anchor": "middle",
      fill: "#c49a45", "font-size": "2.1", "font-family": "JetBrains Mono, monospace", "font-weight": "600"
    });
    xiaoLabel.textContent = "XIAO";
    pcbGroup.appendChild(xiaoLabel);

    const silkLabel = el("text", {
      x: 29.7, y: 83.4, "text-anchor": "middle",
      fill: "#6e8f7b", "font-size": "1.45", "font-family": "JetBrains Mono, monospace"
    });
    silkLabel.textContent = "AITY 2026";
    pcbGroup.appendChild(silkLabel);

    // Onboard RGB LED (board.NEOPIXEL)
    onboardGlowNode = el("circle", {
      cx: 24.4, cy: 83.8, r: 2.0,
      fill: "rgb(0,0,0)", opacity: "0", filter: "url(#led-glow)"
    });
    onboardChipNode = el("rect", {
      x: 23.6, y: 83.0, width: 1.6, height: 1.6, rx: 0.3,
      fill: "#263038", stroke: "#485460", "stroke-width": "0.18"
    });
    pcbGroup.appendChild(onboardGlowNode);
    pcbGroup.appendChild(onboardChipNode);

    treeSvg.appendChild(pcbGroup);

    // Segment copper traces
    tracesGroup = el("g", { id: "pcb-traces", opacity: "0.45" });
    const segRanges = [[0, 5], [5, 10], [10, 24], [24, 42], [42, 55], [55, 60]];
    for (const [start, end] of segRanges) {
      const pts = [];
      for (let i = start; i < end; i++) {
        const [cx, cy] = toSvg(PIXEL_COORDS[i][0], PIXEL_COORDS[i][1]);
        pts.push(`${cx.toFixed(2)},${cy.toFixed(2)}`);
      }
      tracesGroup.appendChild(el("polyline", {
        points: pts.join(" "),
        fill: "none",
        stroke: "#2d6a4f",
        "stroke-width": "0.35",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
      }));
    }
    treeSvg.appendChild(tracesGroup);

    // 60 NeoPixel LEDs
    const ledsGroup = el("g", { id: "pcb-leds" });
    indicesGroup = el("g", { id: "pcb-indices", style: "display:none; pointer-events:none;" });

    for (let i = 0; i < PIXEL_COORDS.length; i++) {
      const [x, y, seg] = PIXEL_COORDS[i];
      const [cx, cy] = toSvg(x, y);

      const glow = el("circle", {
        cx: cx.toFixed(3),
        cy: cy.toFixed(3),
        r: "2.35",
        fill: "rgb(0,0,0)",
        opacity: "0",
        filter: "url(#led-glow)",
      });

      const chip = el("rect", {
        x: (cx - 0.85).toFixed(3),
        y: (cy - 0.85).toFixed(3),
        width: "1.7",
        height: "1.7",
        rx: "0.35",
        fill: "#26322c",
        stroke: "#4d6b59",
        "stroke-width": "0.18",
        style: "cursor: crosshair;",
      });

      chip.addEventListener("mouseenter", () => {
        const [r, g, b] = lastRgb[i];
        inspectorEl.textContent = `LED #${i} · ${SEGMENT_NAMES[seg]} · RGB(${r}, ${g}, ${b})`;
      });
      chip.addEventListener("mouseleave", () => {
        inspectorEl.textContent = "Hover an LED to inspect index & RGB";
      });

      ledsGroup.appendChild(glow);
      ledsGroup.appendChild(chip);
      ledNodes.push({ glow, chip });

      const lbl = el("text", {
        x: cx.toFixed(3),
        y: (cy - 1.35).toFixed(3),
        "text-anchor": "middle",
        fill: "#d4e3da",
        "font-size": "1.35",
        "font-family": "JetBrains Mono, monospace",
        "font-weight": "600",
      });
      lbl.textContent = String(i);
      indicesGroup.appendChild(lbl);
    }

    treeSvg.appendChild(ledsGroup);
    treeSvg.appendChild(indicesGroup);
  }

  // Perceptual LED color mapping so low brightness (0.2) still looks vivid like a real WS2812B
  function perceptualLedColor(r, g, b, brightness) {
    const bGain = Math.pow(Math.max(0, Math.min(1, brightness)), 0.55);
    const sr = Math.min(255, Math.round(r * bGain));
    const sg = Math.min(255, Math.round(g * bGain));
    const sb = Math.min(255, Math.round(b * bGain));
    return [sr, sg, sb];
  }

  function updateTreeLeds(flatColors, brightness) {
    const count = Math.min(60, Math.floor(flatColors.length / 3));
    for (let i = 0; i < count; i++) {
      const r = flatColors[i * 3];
      const g = flatColors[i * 3 + 1];
      const b = flatColors[i * 3 + 2];
      lastRgb[i] = [r, g, b];

      const [sr, sg, sb] = perceptualLedColor(r, g, b, brightness);
      const maxC = Math.max(sr, sg, sb);
      const { glow, chip } = ledNodes[i];

      if (maxC <= 2) {
        chip.setAttribute("fill", "#26322c");
        chip.setAttribute("stroke", "#4d6b59");
        glow.setAttribute("opacity", "0");
      } else {
        // Boost core luminance slightly for realistic LED die appearance
        const coreR = Math.min(255, Math.round(sr + (255 - sr) * 0.15 * (maxC / 255)));
        const coreG = Math.min(255, Math.round(sg + (255 - sg) * 0.15 * (maxC / 255)));
        const coreB = Math.min(255, Math.round(sb + (255 - sb) * 0.15 * (maxC / 255)));
        chip.setAttribute("fill", `rgb(${coreR},${coreG},${coreB})`);
        chip.setAttribute("stroke", `rgb(${sr},${sg},${sb})`);
        glow.setAttribute("fill", `rgb(${sr},${sg},${sb})`);
        glow.setAttribute("opacity", (0.25 + 0.7 * (maxC / 255)).toFixed(2));
      }
    }
  }

  function updateOnboardLed(r, g, b, brightness) {
    if (!onboardChipNode || !onboardGlowNode) return;
    const [sr, sg, sb] = perceptualLedColor(r, g, b, brightness);
    const maxC = Math.max(sr, sg, sb);
    if (maxC <= 2) {
      onboardChipNode.setAttribute("fill", "#263038");
      onboardGlowNode.setAttribute("opacity", "0");
    } else {
      onboardChipNode.setAttribute("fill", `rgb(${sr},${sg},${sb})`);
      onboardGlowNode.setAttribute("fill", `rgb(${sr},${sg},${sb})`);
      onboardGlowNode.setAttribute("opacity", (0.3 + 0.65 * (maxC / 255)).toFixed(2));
    }
  }

  // Serial Console helpers
  function appendConsole(text, kind = "stdout") {
    const span = document.createElement("span");
    if (kind === "stderr") span.className = "log-err";
    else if (kind === "sys") span.className = "log-sys";
    span.textContent = text + "\n";
    consoleEl.appendChild(span);
    // Cap console lines to keep DOM fast
    while (consoleEl.childNodes.length > 250) {
      consoleEl.removeChild(consoleEl.firstChild);
    }
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }

  function clearConsole() {
    consoleEl.textContent = "";
  }

  function setStatus(state, text) {
    statusBadge.className = `status-badge status-${state}`;
    statusText.textContent = text;
  }

  // Initialize CodeMirror (or fallback textarea)
  let editor = null;
  const fallbackArea = document.getElementById("code-fallback");

  function initEditor() {
    if (typeof CodeMirror === "function") {
      editor = CodeMirror(document.getElementById("editor-container"), {
        mode: "python",
        theme: "material-darker",
        lineNumbers: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        extraKeys: {
          "Ctrl-Enter": () => runCurrentCode(),
          "Cmd-Enter": () => runCurrentCode(),
          Tab: (cm) => cm.replaceSelection("    ", "end"),
        },
      });
      fallbackArea.style.display = "none";
    }
  }

  function getCode() {
    return editor ? editor.getValue() : fallbackArea.value;
  }

  function setCode(code) {
    if (editor) {
      editor.setValue(code);
    } else {
      fallbackArea.value = code;
    }
  }

  // Runtime instance
  const runtime = new window.SimRuntime({
    onLeds: updateTreeLeds,
    onOnboardLed: updateOnboardLed,
    onPrint: appendConsole,
    onStatus: setStatus,
  });

  function runCurrentCode() {
    clearConsole();
    appendConsole("--- Running code.py ---", "sys");
    runtime.run(getCode());
  }

  // Populate Examples
  const examples = window.XMAS_EXAMPLES || [];
  let currentExample = examples[5] || examples[0]; // Default to 5: Maximal

  for (const ex of examples) {
    const opt = document.createElement("option");
    opt.value = ex.id;
    opt.textContent = ex.name;
    exampleSelect.appendChild(opt);
  }

  function loadExample(id, autoRun = true) {
    const ex = examples.find((e) => e.id === id) || examples[0];
    if (!ex) return;
    currentExample = ex;
    exampleSelect.value = ex.id;
    exampleDesc.textContent = ex.description;
    hintD5.textContent = `D5: ${ex.d5}`;
    hintD6.textContent = `D6: ${ex.d6}`;
    setCode(ex.code);
    if (autoRun) {
      runCurrentCode();
    }
  }

  // Emulated Board Buttons (D5 and D6, active-low)
  function bindBoardButton(name, btnEl, stateEl, latchEl) {
    let pointerHeld = false;

    const sync = () => {
      const pressed = pointerHeld || latchEl.checked;
      runtime.setButton(name, pressed);
      btnEl.classList.toggle("is-pressed", pressed);
      btnEl.setAttribute("aria-pressed", String(pressed));
      stateEl.textContent = pressed ? "LOW" : "HIGH";
    };

    btnEl.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      btnEl.setPointerCapture?.(e.pointerId);
      pointerHeld = true;
      sync();
    });

    const release = () => {
      if (pointerHeld) {
        pointerHeld = false;
        sync();
      }
    };

    btnEl.addEventListener("pointerup", release);
    btnEl.addEventListener("pointercancel", release);
    btnEl.addEventListener("lostpointercapture", release);
    latchEl.addEventListener("change", sync);

    return {
      setKeyHeld: (held) => {
        pointerHeld = held;
        sync();
      },
    };
  }

  // Boot
  buildTreeSvg();
  initEditor();

  const d5Ctrl = bindBoardButton("D5", btnD5, stateD5, latchD5);
  const d6Ctrl = bindBoardButton("D6", btnD6, stateD6, latchD6);

  // Keyboard shortcuts 5 / 6 when editor is not focused
  window.addEventListener("keydown", (e) => {
    const tag = document.activeElement?.tagName;
    if (tag === "TEXTAREA" || tag === "INPUT" || tag === "SELECT") return;
    if (e.key === "5" && !e.repeat) d5Ctrl.setKeyHeld(true);
    if (e.key === "6" && !e.repeat) d6Ctrl.setKeyHeld(true);
  });

  window.addEventListener("keyup", (e) => {
    if (e.key === "5") d5Ctrl.setKeyHeld(false);
    if (e.key === "6") d6Ctrl.setKeyHeld(false);
  });

  // Toolbar & Toggle events
  toggleIndices.addEventListener("change", () => {
    indicesGroup.style.display = toggleIndices.checked ? "block" : "none";
  });

  toggleTraces.addEventListener("change", () => {
    tracesGroup.style.display = toggleTraces.checked ? "block" : "none";
  });

  exampleSelect.addEventListener("change", () => {
    loadExample(exampleSelect.value, true);
  });

  btnRun.addEventListener("click", runCurrentCode);
  btnStop.addEventListener("click", () => {
    runtime.stop();
    appendConsole("--- Stopped ---", "sys");
  });
  btnReset.addEventListener("click", () => {
    if (currentExample) {
      setCode(currentExample.code);
      runCurrentCode();
    }
  });
  btnClearConsole.addEventListener("click", clearConsole);

  btnDownload.addEventListener("click", () => {
    const blob = new Blob([getCode()], { type: "text/x-python;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "code.py";
    a.click();
    URL.revokeObjectURL(url);
  });

  // Load initial example and start Pyodide
  loadExample(currentExample.id, false);
  appendConsole("Initializing Python runtime (Pyodide)…", "sys");
  runtime.init()
    .then(() => runCurrentCode())
    .catch((err) => {
      setStatus("error", "Load failed");
      appendConsole(String(err), "stderr");
    });
})();
