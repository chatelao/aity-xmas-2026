// AITY Xmas Tree 2026 — Simulator UI & SVG Tree Renderer
(function () {
  // Exact PCB coordinates (x_mm, y_mm, segment_id) from tannenbaum_layout.py
  const PIXEL_COORDS = [
    // Seg 0: Zweig Unten (0..17)
    [38.862, 8.912, 0], [37.076, 6.998, 0], [35.100, 5.281, 0], [32.956, 3.781, 0], [30.667, 2.512, 0], [28.257, 1.491, 0], [25.754, 0.726, 0], [23.184, 0.227, 0], [20.577, 0.000, 0], [17.960, 0.046, 0], [15.362, 0.365, 0], [12.812, 0.955, 0], [10.337, 1.807, 0], [7.965, 2.914, 0], [5.722, 4.262, 0], [3.631, 5.838, 0], [1.717, 7.623, 0], [0.000, 9.599, 0],
    // Seg 1: Zweig Mitte (18..31)
    [36.328, 14.954, 1], [33.885, 14.017, 1], [31.357, 13.340, 1], [28.773, 12.932, 1], [26.159, 12.796, 1], [23.546, 12.934, 1], [20.961, 13.344, 1], [18.434, 14.022, 1], [15.991, 14.961, 1], [13.660, 16.149, 1], [11.465, 17.576, 1], [9.432, 19.223, 1], [7.582, 21.074, 1], [5.936, 23.109, 1],
    // Seg 2: Zweig Oben (32..44)
    [36.468, 25.383, 2], [33.855, 25.247, 2], [31.243, 25.385, 2], [28.658, 25.795, 2], [26.131, 26.473, 2], [23.688, 27.412, 2], [21.357, 28.601, 2], [19.163, 30.027, 2], [17.130, 31.674, 2], [15.280, 33.525, 2], [13.634, 35.559, 2], [12.209, 37.754, 2], [11.022, 40.087, 2],
    // Seg 3: Stiel / Verbindungsbogen (45..49)
    [19.869, 39.313, 3], [21.903, 40.961, 3], [23.754, 42.812, 3], [25.401, 44.846, 3], [27.009, 46.640, 3],
    // Seg 4: Stern (50..59)
    [18.349, 58.095, 4], [17.189, 56.466, 4], [14.681, 63.964, 4], [16.589, 63.365, 4], [21.247, 66.711, 4], [21.207, 68.551, 4], [27.692, 64.094, 4], [25.796, 63.456, 4], [23.828, 57.956, 4], [25.013, 56.345, 4],
  ];

  const SEGMENT_NAMES = [
    "Zweig Unten",
    "Zweig Mitte",
    "Zweig Oben",
    "Stiel",
    "Stern",
  ];

  const OUTLINE = window.XMAS_PCB_OUTLINE;

  function toSvg(x, y) {
    // Convert tannenbaum_layout.py (bottom-left origin, y up) to SVG outline coords
    return [x + (111.0262 - OUTLINE.xOrigin), (68.551 - y) + (27.5500 - OUTLINE.yOrigin)];
  }

  const SVG_NS = "http://www.w3.org/2000/svg";

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
  const treeTypeSelect = document.getElementById("tree-type-select");

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
  const tracePolylines = [];
  let treeType = "PCB";
  let onboardChipNode = null;
  let onboardGlowNode = null;
  let tracesGroup = null;
  let indicesGroup = null;

  function mapPhysicalIndex(i) {
    if (treeType === "Holz" && i >= 18 && i < 32) {
      return 49 - i;
    }
    return i;
  }

  // Build Christmas Tree PCB SVG
  function buildTreeSvg() {
    treeSvg.setAttribute("viewBox", OUTLINE.viewBox);

    // Defs for multi-layer LED bloom filters
    const defs = el("defs");
    const wideFilter = el("filter", { id: "led-glow-wide", x: "-250%", y: "-250%", width: "600%", height: "600%" });
    wideFilter.appendChild(el("feGaussianBlur", { stdDeviation: "2.55", result: "blur" }));
    defs.appendChild(wideFilter);

    const tightFilter = el("filter", { id: "led-glow-tight", x: "-150%", y: "-150%", width: "400%", height: "400%" });
    tightFilter.appendChild(el("feGaussianBlur", { stdDeviation: "0.95", result: "blur" }));
    defs.appendChild(tightFilter);
    treeSvg.appendChild(defs);

    // Exact KiCad Edge.Cuts PCB outline + Design patterns (F.Cu gold & F.SilkS)
    const pcbGroup = el("g", { id: "pcb-board" });
    pcbGroup.appendChild(el("path", {
      d: OUTLINE.edgePath,
      fill: "#111613",
      stroke: "#c49a45",
      "stroke-width": "0.35",
      "stroke-linejoin": "round",
    }));

    if (OUTLINE.goldPath) {
      pcbGroup.appendChild(el("path", {
        d: OUTLINE.goldPath,
        fill: "#cfa24e",
        "fill-rule": "evenodd",
        opacity: "0.82",
        "pointer-events": "none",
      }));
    }

    if (OUTLINE.silkPath) {
      pcbGroup.appendChild(el("path", {
        d: OUTLINE.silkPath,
        fill: "#dfd0b4",
        "fill-rule": "evenodd",
        opacity: "0.45",
        "pointer-events": "none",
      }));
    }

    treeSvg.appendChild(pcbGroup);

    // Segment copper traces
    tracesGroup = el("g", { id: "pcb-traces", opacity: "0.32" });
    const segRanges = [[0, 18], [18, 32], [32, 45], [45, 50], [50, 60]];
    for (const [start, end] of segRanges) {
      const pts = [];
      for (let i = start; i < end; i++) {
        const coordIdx = mapPhysicalIndex(i);
        const [cx, cy] = toSvg(PIXEL_COORDS[coordIdx][0], PIXEL_COORDS[coordIdx][1]);
        pts.push(`${cx.toFixed(2)},${cy.toFixed(2)}`);
      }
      const poly = el("polyline", {
        points: pts.join(" "),
        fill: "none",
        stroke: "#255942",
        "stroke-width": "0.35",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
      });
      tracePolylines.push({ start, end, poly });
      tracesGroup.appendChild(poly);
    }
    treeSvg.appendChild(tracesGroup);

    // 60 NeoPixel LEDs
    const ledsGroup = el("g", { id: "pcb-leds" });
    indicesGroup = el("g", { id: "pcb-indices", style: "display:none; pointer-events:none;" });

    for (let i = 0; i < PIXEL_COORDS.length; i++) {
      const coordIdx = mapPhysicalIndex(i);
      const [x, y, seg] = PIXEL_COORDS[coordIdx];
      const [cx, cy] = toSvg(x, y);

      const outerGlow = el("circle", {
        cx: cx.toFixed(3),
        cy: cy.toFixed(3),
        r: "4.6",
        fill: "rgb(0,0,0)",
        opacity: "0",
        filter: "url(#led-glow-wide)",
        style: "mix-blend-mode: screen; pointer-events: none;",
      });

      const innerGlow = el("circle", {
        cx: cx.toFixed(3),
        cy: cy.toFixed(3),
        r: "2.2",
        fill: "rgb(0,0,0)",
        opacity: "0",
        filter: "url(#led-glow-tight)",
        style: "mix-blend-mode: screen; pointer-events: none;",
      });

      const chip = el("rect", {
        x: (cx - 0.85).toFixed(3),
        y: (cy - 0.85).toFixed(3),
        width: "1.7",
        height: "1.7",
        rx: "0.35",
        fill: "#1e2622",
        stroke: "#3c4f44",
        "stroke-width": "0.18",
        style: "cursor: crosshair;",
      });

      const inspectLed = () => {
        const [r, g, b] = lastRgb[i];
        const logIdx = mapPhysicalIndex(i);
        const idxInfo = logIdx !== i ? `#${i} (logisch #${logIdx})` : `#${i}`;
        inspectorEl.textContent = `LED ${idxInfo} · ${SEGMENT_NAMES[seg]} · RGB(${r}, ${g}, ${b})`;
      };
      chip.addEventListener("mouseenter", inspectLed);
      chip.addEventListener("pointerdown", inspectLed);
      chip.addEventListener("click", inspectLed);
      chip.addEventListener("mouseleave", () => {
        inspectorEl.textContent = "Maus über eine LED bewegen oder antippen, um Index & RGB zu sehen";
      });

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

      ledsGroup.appendChild(outerGlow);
      ledsGroup.appendChild(innerGlow);
      ledsGroup.appendChild(chip);
      ledNodes.push({ outerGlow, innerGlow, chip, lbl });
    }

    treeSvg.appendChild(ledsGroup);
    treeSvg.appendChild(indicesGroup);
  }

  function updateTreeTypeVisuals() {
    for (const { start, end, poly } of tracePolylines) {
      const pts = [];
      for (let i = start; i < end; i++) {
        const coordIdx = mapPhysicalIndex(i);
        const [cx, cy] = toSvg(PIXEL_COORDS[coordIdx][0], PIXEL_COORDS[coordIdx][1]);
        pts.push(`${cx.toFixed(2)},${cy.toFixed(2)}`);
      }
      poly.setAttribute("points", pts.join(" "));
    }
    for (let i = 0; i < ledNodes.length; i++) {
      const coordIdx = mapPhysicalIndex(i);
      const [x, y] = PIXEL_COORDS[coordIdx];
      const [cx, cy] = toSvg(x, y);
      const node = ledNodes[i];
      node.outerGlow.setAttribute("cx", cx.toFixed(3));
      node.outerGlow.setAttribute("cy", cy.toFixed(3));
      node.innerGlow.setAttribute("cx", cx.toFixed(3));
      node.innerGlow.setAttribute("cy", cy.toFixed(3));
      node.chip.setAttribute("x", (cx - 0.85).toFixed(3));
      node.chip.setAttribute("y", (cy - 0.85).toFixed(3));
      node.lbl.setAttribute("x", cx.toFixed(3));
      node.lbl.setAttribute("y", (cy - 1.35).toFixed(3));
    }
  }

  // Perceptual LED color & bloom mapping modelled on the real linear light output of a WS2812B/SK6812
  function perceptualLedVisuals(r, g, b, brightness) {
    if (Math.max(r, g, b) === 0 || brightness <= 0.002) {
      return { on: false };
    }
    // Physical WS2812B dies emit brighter green/blue than red; firmware white balance (255,176,240)
    // compensates for this, so invert WB here to show the perceived neutral light on an sRGB monitor.
    const wb = (window.XMAS_GAMMA && window.XMAS_GAMMA.WHITE_BALANCE) || [255, 255, 255];
    const er = Math.min(255, (r * 255) / wb[0]);
    const eg = Math.min(255, (g * 255) / wb[1]);
    const eb = Math.min(255, (b * 255) / wb[2]);
    const maxEff = Math.max(er, eg, eb);

    // WS2812B light output is linear in the PWM value; the monitor encodes with sRGB (~gamma 2.2).
    // Firmware values are already CIE-L* corrected (tannenbaum_layout.py), so show them truthfully.
    const rawLum = (maxEff / 255) * Math.max(0, Math.min(1, brightness));
    const lum = Math.min(1, Math.pow(rawLum, 1 / 2.2));

    // Preserve pure vivid hue for the colored bloom
    const invMax = 255 / maxEff;
    const hueR = Math.round(er * invMax);
    const hueG = Math.round(eg * invMax);
    const hueB = Math.round(eb * invMax);

    // Hot LED die core: saturates toward white-hot at high luminance
    const dieScale = Math.min(1, 0.35 + 0.65 * lum);
    const whiteMix = Math.min(0.78, Math.pow(lum, 1.35) * 0.78);
    const baseR = hueR * dieScale;
    const baseG = hueG * dieScale;
    const baseB = hueB * dieScale;
    const coreR = Math.min(255, Math.round(baseR + (255 - baseR) * whiteMix));
    const coreG = Math.min(255, Math.round(baseG + (255 - baseG) * whiteMix));
    const coreB = Math.min(255, Math.round(baseB + (255 - baseB) * whiteMix));

    return {
      on: true,
      lum,
      hueColor: `rgb(${hueR},${hueG},${hueB})`,
      coreColor: `rgb(${coreR},${coreG},${coreB})`,
      rimColor: `rgb(${Math.round(baseR)},${Math.round(baseG)},${Math.round(baseB)})`,
      innerOpacity: (0.95 * Math.pow(lum, 0.65)).toFixed(2),
      outerOpacity: (0.72 * Math.pow(lum, 0.85)).toFixed(2),
    };
  }

  function updateTreeLeds(flatColors, brightness) {
    const count = Math.min(60, Math.floor(flatColors.length / 3));
    for (let i = 0; i < count; i++) {
      const r = flatColors[i * 3];
      const g = flatColors[i * 3 + 1];
      const b = flatColors[i * 3 + 2];
      lastRgb[i] = [r, g, b];

      const vis = perceptualLedVisuals(r, g, b, brightness);
      const { outerGlow, innerGlow, chip } = ledNodes[i];

      if (!vis.on) {
        chip.setAttribute("fill", "#1e2622");
        chip.setAttribute("stroke", "#3c4f44");
        innerGlow.setAttribute("opacity", "0");
        outerGlow.setAttribute("opacity", "0");
      } else {
        chip.setAttribute("fill", vis.coreColor);
        chip.setAttribute("stroke", vis.rimColor);
        innerGlow.setAttribute("fill", vis.hueColor);
        innerGlow.setAttribute("opacity", vis.innerOpacity);
        outerGlow.setAttribute("fill", vis.hueColor);
        outerGlow.setAttribute("opacity", vis.outerOpacity);
      }
    }
  }

  function updateOnboardLed(r, g, b, brightness) {
    if (!onboardChipNode || !onboardGlowNode) return;
    const vis = perceptualLedVisuals(r, g, b, brightness);
    if (!vis.on) {
      onboardChipNode.setAttribute("fill", "#263038");
      onboardGlowNode.setAttribute("opacity", "0");
    } else {
      onboardChipNode.setAttribute("fill", vis.coreColor);
      onboardGlowNode.setAttribute("fill", vis.hueColor);
      onboardGlowNode.setAttribute("opacity", vis.innerOpacity);
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
  function getExampleFromHash() {
    const hashId = decodeURIComponent((window.location.hash || "").replace(/^#/, ""));
    return examples.find((e) => e.id === hashId) || null;
  }
  let currentExample = getExampleFromHash() || examples[5] || examples[0]; // Default to 5: Maximal

  for (const ex of examples) {
    const opt = document.createElement("option");
    opt.value = ex.id;
    opt.textContent = ex.name;
    exampleSelect.appendChild(opt);
  }

  function loadExample(id, autoRun = true, updateHash = true) {
    const ex = examples.find((e) => e.id === id) || examples[0];
    if (!ex) return;
    currentExample = ex;
    exampleSelect.value = ex.id;
    exampleDesc.textContent = ex.description;
    hintD5.textContent = `D5: ${ex.d5}`;
    hintD6.textContent = `D6: ${ex.d6}`;
    setCode(ex.code);
    if (updateHash && window.location.hash !== `#${ex.id}`) {
      history.replaceState(null, "", `#${encodeURIComponent(ex.id)}`);
    }
    if (autoRun) {
      runCurrentCode();
    }
  }

  // Emulated Board Buttons (D5 and D6, active-low)
  function bindBoardButton(name, btnEl, stateEl, latchEl) {
    let pointerHeld = false;
    let keyHeld = false;

    const sync = () => {
      const pressed = pointerHeld || keyHeld || latchEl.checked;
      runtime.setButton(name, pressed);
      btnEl.classList.toggle("is-pressed", pressed);
      btnEl.setAttribute("aria-pressed", String(pressed));
      stateEl.textContent = pressed ? "LOW" : "HIGH";
    };

    const pressPointer = (e) => {
      e.preventDefault();
      if (e.pointerId !== undefined) {
        btnEl.setPointerCapture?.(e.pointerId);
      }
      if (!pointerHeld) {
        pointerHeld = true;
        sync();
      }
    };

    const releasePointer = () => {
      if (pointerHeld) {
        pointerHeld = false;
        sync();
      }
    };

    btnEl.addEventListener("pointerdown", pressPointer);
    btnEl.addEventListener("pointerup", releasePointer);
    btnEl.addEventListener("pointercancel", releasePointer);
    btnEl.addEventListener("lostpointercapture", releasePointer);
    btnEl.addEventListener("touchstart", pressPointer, { passive: false });
    btnEl.addEventListener("touchend", releasePointer);
    btnEl.addEventListener("touchcancel", releasePointer);

    btnEl.addEventListener("keydown", (e) => {
      if ((e.key === " " || e.key === "Enter") && !e.repeat) {
        e.preventDefault();
        keyHeld = true;
        sync();
      }
    });
    btnEl.addEventListener("keyup", (e) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        keyHeld = false;
        sync();
      }
    });
    btnEl.addEventListener("blur", () => {
      if (keyHeld) {
        keyHeld = false;
        sync();
      }
    });

    latchEl.addEventListener("change", sync);

    return {
      setKeyHeld: (held) => {
        if (keyHeld !== held) {
          keyHeld = held;
          sync();
        }
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

  window.addEventListener("blur", () => {
    d5Ctrl.setKeyHeld(false);
    d6Ctrl.setKeyHeld(false);
  });

  // Toolbar & Toggle events
  toggleIndices.addEventListener("change", () => {
    indicesGroup.style.display = toggleIndices.checked ? "block" : "none";
  });

  toggleTraces.addEventListener("change", () => {
    tracesGroup.style.display = toggleTraces.checked ? "block" : "none";
  });

  if (treeTypeSelect) {
    treeTypeSelect.addEventListener("change", () => {
      treeType = treeTypeSelect.value === "Holz" ? "Holz" : "PCB";
      updateTreeTypeVisuals();
      runtime.setTreeType(treeType);
    });
  }

  exampleSelect.addEventListener("change", () => {
    loadExample(exampleSelect.value, true);
  });

  window.addEventListener("hashchange", () => {
    const ex = getExampleFromHash();
    if (ex && ex.id !== currentExample?.id) {
      loadExample(ex.id, true, false);
    }
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

  // Compiled Firmware (.uf2) Release Modal
  const btnFirmwareModal = document.getElementById("btn-firmware-modal");
  const firmwareModal = document.getElementById("firmware-modal");
  const btnFirmwareClose = document.getElementById("btn-firmware-close");
  const btnFirmwareRefresh = document.getElementById("btn-firmware-refresh");
  const firmwareReleaseMeta = document.getElementById("firmware-release-meta");
  const firmwareMcuHint = document.getElementById("firmware-mcu-hint");
  const firmwareBaseSection = document.getElementById("firmware-base-section");
  const firmwareWebSerialSection = document.getElementById("firmware-webserial-section");
  const btnFlashCpWebSerial = document.getElementById("btn-flash-cp-webserial");
  const btnFlashFileWebSerial = document.getElementById("btn-flash-file-webserial");
  const webSerialFileInput = document.getElementById("webserial-file-input");
  const webSerialEraseCheck = document.getElementById("webserial-erase-check");
  const webSerialProgressWrap = document.getElementById("webserial-progress-wrap");
  const webSerialProgress = document.getElementById("webserial-progress");
  const webSerialProgressLabel = document.getElementById("webserial-progress-label");
  const webSerialLog = document.getElementById("webserial-log");
  const btnInstallPortal = document.getElementById("btn-install-portal");
  const btnInstallLibs = document.getElementById("btn-install-libs");
  const btnDownloadLibsZip = document.getElementById("btn-download-libs-zip");
  const firmwareLibsStatus = document.getElementById("firmware-libs-status");
  const firmwareLibsList = document.getElementById("firmware-libs-list");
  const firmwarePackagesSection = document.getElementById("firmware-packages-section");
  const firmwarePackagesList = document.getElementById("firmware-packages-list");
  const firmwareList = document.getElementById("firmware-list");
  const mcuTabs = Array.from(document.querySelectorAll(".mcu-tab"));

  let selectedMcu = "xiao_rp2040";
  let releaseState = { status: "idle", data: null, error: null };
  let isFlashing = false;

  function renderMcuHint() {
    const mcu = window.XmasFirmware?.TARGET_MCUS?.find((m) => m.id === selectedMcu);
    firmwareMcuHint.textContent = mcu ? mcu.hint : "";
  }

  function renderWebSerialSection() {
    if (!firmwareWebSerialSection) return;
    const isEsp = selectedMcu === "xiao_esp32c6";
    firmwareWebSerialSection.hidden = !isEsp;
    if (!isEsp) return;

    const hasSerial = typeof navigator !== "undefined" && "serial" in navigator;
    if (btnFlashCpWebSerial) btnFlashCpWebSerial.disabled = !hasSerial || isFlashing;
    if (btnFlashFileWebSerial) btnFlashFileWebSerial.disabled = !hasSerial || isFlashing;

    if (!hasSerial && webSerialLog) {
      webSerialLog.hidden = false;
      webSerialLog.textContent =
        "WebSerial is not available in this browser. Use Chrome, Edge, Opera, or Firefox 151+.";
    }
  }

  function renderBaseFirmwareSection() {
    if (!firmwareBaseSection || !window.XmasFirmware) return;
    const mcu = window.XmasFirmware.TARGET_MCUS.find((m) => m.id === selectedMcu);
    firmwareBaseSection.textContent = "";
    if (!mcu) return;

    const relAsset = releaseState.data?.baseFirmware?.[mcu.id] || null;
    const downloadUrl = relAsset
      ? relAsset.downloadUrl
      : window.XmasFirmware.getRawRepoUrl(null, mcu.circuitpythonRepoFile);
    const fileName = relAsset
      ? relAsset.fileName
      : mcu.circuitpythonRepoFile.split("/").pop();

    const row = document.createElement("div");
    row.className = "firmware-item";

    const info = document.createElement("div");
    info.className = "firmware-item-info";

    const title = document.createElement("div");
    title.className = "firmware-item-name";
    title.textContent = mcu.circuitpythonLabel;

    const meta = document.createElement("div");
    meta.className = "firmware-item-meta";
    meta.textContent = relAsset?.sizeLabel ? `${fileName} · ${relAsset.sizeLabel}` : fileName;

    info.appendChild(title);
    info.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "firmware-base-actions";

    const boardLink = document.createElement("a");
    boardLink.className = "action-btn action-ghost";
    boardLink.href = mcu.circuitpythonBoardUrl;
    boardLink.target = "_blank";
    boardLink.rel = "noopener noreferrer";
    boardLink.textContent = "circuitpython.org ↗";
    actions.appendChild(boardLink);

    const dl = document.createElement("a");
    dl.className = "action-btn action-secondary firmware-dl-btn";
    dl.href = downloadUrl;
    dl.download = fileName;
    dl.target = "_blank";
    dl.rel = "noopener noreferrer";
    dl.textContent = "↓ Base";
    actions.appendChild(dl);

    row.appendChild(info);
    row.appendChild(actions);
    firmwareBaseSection.appendChild(row);
  }

  function renderLibsSection() {
    if (!firmwareLibsList || !window.XmasFirmware) return;
    firmwareLibsList.textContent = "";

    const libBundle = releaseState.data?.libBundle || null;
    if (btnDownloadLibsZip) {
      if (libBundle) {
        btnDownloadLibsZip.href = libBundle.downloadUrl;
        btnDownloadLibsZip.download = libBundle.fileName;
        btnDownloadLibsZip.textContent = libBundle.sizeLabel
          ? `↓ libs.zip (${libBundle.sizeLabel})`
          : "↓ libs.zip";
        btnDownloadLibsZip.hidden = false;
      } else {
        btnDownloadLibsZip.hidden = true;
      }
    }

    if (btnInstallLibs) {
      const hasPicker = typeof window.showDirectoryPicker === "function";
      btnInstallLibs.disabled = !hasPicker;
      if (!hasPicker) {
        btnInstallLibs.title = "Direct folder install requires Chrome, Edge, or Opera (File System Access API)";
      }
    }

    const relLibsByName = new Map(
      (releaseState.data?.libFiles || []).map((f) => [f.fileName, f])
    );

    for (const fileName of window.XmasFirmware.LIB_FILE_NAMES) {
      const relAsset = relLibsByName.get(fileName);
      const fallbackPath =
        fileName === "neopixel.mpy"
          ? "lib/neopixel.mpy"
          : window.XmasFirmware.getRawRepoUrl(null, `circuitpython/lib/${fileName}`);

      const chip = document.createElement("a");
      chip.className = "firmware-lib-chip";
      chip.href = relAsset ? relAsset.downloadUrl : fallbackPath;
      chip.download = fileName;
      chip.target = "_blank";
      chip.rel = "noopener noreferrer";
      chip.textContent = relAsset?.sizeLabel
        ? `↓ ${fileName} (${relAsset.sizeLabel})`
        : `↓ ${fileName}`;
      firmwareLibsList.appendChild(chip);
    }
  }

  function renderFirmwareModal() {
    renderMcuHint();
    renderBaseFirmwareSection();
    renderWebSerialSection();
    renderLibsSection();
    firmwareList.textContent = "";

    if (releaseState.status === "loading") {
      firmwareReleaseMeta.textContent = "Checking latest release…";
      const msg = document.createElement("div");
      msg.className = "firmware-empty";
      msg.textContent = "Loading compiled examples from GitHub Releases…";
      firmwareList.appendChild(msg);
      return;
    }

    if (releaseState.status === "error") {
      const err = releaseState.error;
      firmwareReleaseMeta.textContent = "Release unavailable";
      const box = document.createElement("div");
      box.className = "firmware-empty firmware-error";

      const p = document.createElement("p");
      p.textContent = err?.message || "Could not load the latest release.";
      box.appendChild(p);

      const link = document.createElement("a");
      link.className = "action-btn action-secondary";
      link.href = err?.releasesUrl || `https://github.com/${window.XmasFirmware?.DEFAULT_REPO || "chatelao/aity-xmas-2026"}/releases`;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Open GitHub Releases ↗";
      box.appendChild(link);

      firmwareList.appendChild(box);
      return;
    }

    if (releaseState.status !== "ready" || !releaseState.data) {
      return;
    }

    const rel = releaseState.data;
    firmwareReleaseMeta.textContent = "";
    const tagSpan = document.createElement("span");
    tagSpan.className = "release-tag";
    tagSpan.textContent = rel.tagName || "latest";
    firmwareReleaseMeta.appendChild(tagSpan);

    if (rel.publishedAt) {
      const dateStr = new Date(rel.publishedAt).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
      const dateSpan = document.createElement("span");
      dateSpan.className = "release-date";
      dateSpan.textContent = ` · ${dateStr}`;
      firmwareReleaseMeta.appendChild(dateSpan);
    }

    if (rel.htmlUrl) {
      const sep = document.createTextNode(" · ");
      firmwareReleaseMeta.appendChild(sep);
      const relLink = document.createElement("a");
      relLink.className = "release-link";
      relLink.href = rel.htmlUrl;
      relLink.target = "_blank";
      relLink.rel = "noopener noreferrer";
      relLink.textContent = "View release ↗";
      firmwareReleaseMeta.appendChild(relLink);
    }

    const items = rel.byMcu[selectedMcu] || [];
    if (items.length === 0) {
      const empty = document.createElement("div");
      empty.className = "firmware-empty";
      empty.textContent = "No compiled .uf2 examples found for this target MCU in the latest release.";
      firmwareList.appendChild(empty);
      return;
    }

    for (const item of items) {
      const row = document.createElement("div");
      row.className = "firmware-item";

      const info = document.createElement("div");
      info.className = "firmware-item-info";

      const title = document.createElement("div");
      title.className = "firmware-item-name";
      title.textContent = item.exampleName;

      const meta = document.createElement("div");
      meta.className = "firmware-item-meta";
      meta.textContent = item.sizeLabel ? `${item.fileName} · ${item.sizeLabel}` : item.fileName;

      info.appendChild(title);
      info.appendChild(meta);

      const dl = document.createElement("a");
      dl.className = "action-btn action-primary firmware-dl-btn";
      dl.href = item.downloadUrl;
      dl.download = item.fileName;
      dl.target = "_blank";
      dl.rel = "noopener noreferrer";
      dl.textContent = "↓ .uf2";

      row.appendChild(info);
      row.appendChild(dl);
      firmwareList.appendChild(row);
    }

    if (firmwarePackagesSection && firmwarePackagesList) {
      const pkgs = Array.isArray(release.packages) ? release.packages : [];
      firmwarePackagesList.textContent = "";
      firmwarePackagesSection.hidden = pkgs.length === 0;
      for (const pkg of pkgs) {
        const row = document.createElement("div");
        row.className = "firmware-item";
        const info = document.createElement("div");
        info.className = "firmware-item-info";
        const title = document.createElement("div");
        title.className = "firmware-item-name";
        title.textContent = pkg.fileName;
        const meta = document.createElement("div");
        meta.className = "firmware-item-meta";
        meta.textContent = pkg.sizeLabel || "Release asset";
        info.appendChild(title);
        info.appendChild(meta);

        const dl = document.createElement("a");
        dl.className = "action-btn action-secondary firmware-dl-btn";
        dl.href = pkg.downloadUrl;
        dl.download = pkg.fileName;
        dl.target = "_blank";
        dl.rel = "noopener noreferrer";
        dl.textContent = "↓ Download";
        row.appendChild(info);
        row.appendChild(dl);
        firmwarePackagesList.appendChild(row);
      }
    }
  }

  async function handleInstallPortal() {
    if (!firmwareLibsStatus || !window.XmasFirmware) return;
    if (typeof window.showDirectoryPicker !== "function") {
      firmwareLibsStatus.className = "firmware-libs-status is-error";
      firmwareLibsStatus.textContent =
        "Direct folder install requires Chrome, Edge, or Opera. Please download circuitpython-captive-portal-bundle.zip below.";
      return;
    }

    try {
      firmwareLibsStatus.className = "firmware-libs-status";
      firmwareLibsStatus.textContent = "Select the CIRCUITPY root drive (or WebDAV folder)…";
      const dirHandle = await window.showDirectoryPicker({ mode: "readwrite" });
      firmwareLibsStatus.textContent = "Installing code.py, web_ui.html.gz, and /lib/…";
      const installed = await window.XmasFirmware.installCaptivePortalToDirectory(dirHandle);
      firmwareLibsStatus.className = "firmware-libs-status is-success";
      firmwareLibsStatus.textContent = `Installed Captive Portal (${installed.length} files) to ${dirHandle.name}: ${installed.join(", ")}`;
    } catch (err) {
      if (err?.name === "AbortError") {
        firmwareLibsStatus.className = "firmware-libs-status";
        firmwareLibsStatus.textContent = "";
        return;
      }
      firmwareLibsStatus.className = "firmware-libs-status is-error";
      firmwareLibsStatus.textContent = `Install failed: ${err?.message || err}`;
    }
  }

  async function handleInstallLibs() {
    if (!firmwareLibsStatus || !window.XmasFirmware) return;
    if (typeof window.showDirectoryPicker !== "function") {
      firmwareLibsStatus.className = "firmware-libs-status is-error";
      firmwareLibsStatus.textContent =
        "Direct folder install requires Chrome, Edge, or Opera. Please download the /lib/ files below.";
      return;
    }

    try {
      firmwareLibsStatus.className = "firmware-libs-status";
      firmwareLibsStatus.textContent = "Select the CIRCUITPY root drive…";
      const dirHandle = await window.showDirectoryPicker({ mode: "readwrite" });
      firmwareLibsStatus.textContent = "Installing libraries to /lib/…";
      const installed = await window.XmasFirmware.installLibsToDirectory(dirHandle);
      firmwareLibsStatus.className = "firmware-libs-status is-success";
      firmwareLibsStatus.textContent = `Installed ${installed.length} files to ${dirHandle.name}/lib/: ${installed.join(", ")}`;
    } catch (err) {
      if (err?.name === "AbortError") {
        firmwareLibsStatus.className = "firmware-libs-status";
        firmwareLibsStatus.textContent = "";
        return;
      }
      firmwareLibsStatus.className = "firmware-libs-status is-error";
      firmwareLibsStatus.textContent = `Install failed: ${err?.message || err}`;
    }
  }

  function appendWebSerialLog(line) {
    if (!webSerialLog) return;
    webSerialLog.hidden = false;
    webSerialLog.textContent += (webSerialLog.textContent ? "\n" : "") + line;
    webSerialLog.scrollTop = webSerialLog.scrollHeight;
  }

  async function runWebSerialFlash(segmentsPromise, label) {
    if (isFlashing || !window.XmasFirmware) return;
    isFlashing = true;
    renderWebSerialSection();
    if (webSerialLog) {
      webSerialLog.hidden = false;
      webSerialLog.textContent = "";
    }
    if (webSerialProgressWrap && webSerialProgress && webSerialProgressLabel) {
      webSerialProgressWrap.hidden = false;
      webSerialProgress.value = 0;
      webSerialProgressLabel.textContent = "0%";
    }

    try {
      appendWebSerialLog(`Preparing ${label}…`);
      const segments = await segmentsPromise;
      const eraseAll = Boolean(webSerialEraseCheck?.checked);
      await window.XmasFirmware.flashEsp32WebSerial(segments, {
        eraseAll,
        onLog: appendWebSerialLog,
        onProgress: (pct) => {
          if (webSerialProgress && webSerialProgressLabel) {
            webSerialProgress.value = pct;
            webSerialProgressLabel.textContent = `${pct}%`;
          }
        },
      });
    } catch (err) {
      if (err?.name !== "NotFoundError") {
        appendWebSerialLog(`Error: ${err?.message || err}`);
      } else {
        appendWebSerialLog("Serial port selection cancelled.");
      }
    } finally {
      isFlashing = false;
      renderWebSerialSection();
    }
  }

  async function loadLatestFirmware(force = false) {
    if (releaseState.status === "loading") return;
    if (!force && releaseState.status === "ready") {
      renderFirmwareModal();
      return;
    }

    releaseState = { status: "loading", data: null, error: null };
    renderFirmwareModal();
    try {
      const data = await window.XmasFirmware.fetchLatestRelease();
      releaseState = { status: "ready", data, error: null };
    } catch (err) {
      releaseState = { status: "error", data: null, error: err };
    }
    renderFirmwareModal();
  }

  function openFirmwareModal() {
    firmwareModal.hidden = false;
    loadLatestFirmware(false);
    btnFirmwareClose.focus();
  }

  function closeFirmwareModal() {
    firmwareModal.hidden = true;
    btnFirmwareModal.focus();
  }

  if (btnFirmwareModal && firmwareModal) {
    btnFirmwareModal.addEventListener("click", openFirmwareModal);
    btnFirmwareClose.addEventListener("click", closeFirmwareModal);
    btnFirmwareRefresh.addEventListener("click", () => loadLatestFirmware(true));
    if (btnInstallPortal) {
      btnInstallPortal.addEventListener("click", handleInstallPortal);
    }
    if (btnInstallLibs) {
      btnInstallLibs.addEventListener("click", handleInstallLibs);
    }
    if (btnFlashCpWebSerial) {
      btnFlashCpWebSerial.addEventListener("click", () => {
        const mcu = window.XmasFirmware.TARGET_MCUS.find((m) => m.id === "xiao_esp32c6");
        const rawUrl = window.XmasFirmware.getRawRepoUrl(null, mcu.circuitpythonRepoFile);
        runWebSerialFlash(async () => {
          const res = await fetch(rawUrl);
          if (!res.ok) throw new Error(`Failed to fetch base firmware (HTTP ${res.status}).`);
          const buf = await res.arrayBuffer();
          return [{ address: 0x0, data: new Uint8Array(buf) }];
        }, mcu.circuitpythonLabel);
      });
    }
    if (btnFlashFileWebSerial && webSerialFileInput) {
      btnFlashFileWebSerial.addEventListener("click", () => {
        webSerialFileInput.value = "";
        webSerialFileInput.click();
      });
      webSerialFileInput.addEventListener("change", () => {
        const file = webSerialFileInput.files?.[0];
        if (!file) return;
        runWebSerialFlash(async () => {
          const buf = await file.arrayBuffer();
          if (file.name.toLowerCase().endsWith(".uf2")) {
            return window.XmasFirmware.parseUf2ToSegments(buf);
          }
          return [{ address: 0x0, data: new Uint8Array(buf) }];
        }, file.name);
      });
    }

    firmwareModal.addEventListener("click", (e) => {
      if (e.target === firmwareModal) {
        closeFirmwareModal();
      }
    });

    window.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !firmwareModal.hidden) {
        closeFirmwareModal();
      }
    });

    for (const tab of mcuTabs) {
      tab.addEventListener("click", () => {
        const mcu = tab.dataset.mcu;
        if (!mcu || mcu === selectedMcu) return;
        selectedMcu = mcu;
        for (const t of mcuTabs) {
          const active = t.dataset.mcu === selectedMcu;
          t.classList.toggle("is-active", active);
          t.setAttribute("aria-selected", String(active));
        }
        renderFirmwareModal();
      });
    }
  }

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
