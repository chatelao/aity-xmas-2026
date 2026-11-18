// AITY Xmas Tree 2026 — Compiled Firmware (.uf2), CircuitPython Base & /lib/ Installer
(function (root) {
  const DEFAULT_REPO = "chatelao/aity-xmas-2026";
  const LIB_FILE_NAMES = ["neopixel.mpy", "tannenbaum_layout.py", "tannenbaum_palettes.py"];

  const TARGET_MCUS = [
    {
      id: "xiao_rp2040",
      name: "Seeed XIAO RP2040",
      shortName: "XIAO RP2040",
      suffix: "_xiao_rp2040.uf2",
      hint: "Hold BOOT, press RESET, then copy the .uf2 file to the RPI-RP2 USB drive.",
      circuitpythonBoardUrl: "https://circuitpython.org/board/seeeduino_xiao_rp2040/",
      circuitpythonPrefix: "adafruit-circuitpython-seeeduino_xiao_rp2040-",
      circuitpythonRepoFile: "circuitpython/adafruit-circuitpython-seeeduino_xiao_rp2040-de_DE-10.3.1.uf2",
      circuitpythonLabel: "CircuitPython 10.3.1 (.uf2)",
      flashToolUrl: null,
      flashToolLabel: null,
    },
    {
      id: "xiao_esp32c6",
      name: "Seeed XIAO ESP32-C6",
      shortName: "XIAO ESP32-C6",
      suffix: "_xiao_esp32c6.uf2",
      hint: "Flash the .bin base firmware at offset 0x0 with WebSerial ESPTool, or use a UF2-compatible loader for .uf2 examples.",
      circuitpythonBoardUrl: "https://circuitpython.org/board/seeed_xiao_esp32c6/",
      circuitpythonPrefix: "adafruit-circuitpython-seeed_xiao_esp32c6-",
      circuitpythonRepoFile: "circuitpython/adafruit-circuitpython-seeed_xiao_esp32c6-de_DE-10.3.1.bin",
      circuitpythonLabel: "CircuitPython 10.3.1 (.bin)",
      flashToolUrl: "https://adafruit.github.io/Adafruit_WebSerial_ESPTool/",
      flashToolLabel: "WebSerial ESPTool ↗",
    },
  ];

  function detectRepo(loc) {
    const locationObj = loc || (typeof window !== "undefined" ? window.location : null);
    if (!locationObj) return DEFAULT_REPO;
    const host = locationObj.hostname || "";
    const parts = (locationObj.pathname || "").split("/").filter(Boolean);
    if (host.endsWith(".github.io") && parts.length >= 1) {
      const owner = host.slice(0, -".github.io".length);
      const repo = parts[0];
      if (owner && repo) return `${owner}/${repo}`;
    }
    return DEFAULT_REPO;
  }

  function getRawRepoUrl(repo, repoPath) {
    const targetRepo = repo || detectRepo();
    return `https://raw.githubusercontent.com/${targetRepo}/main/${repoPath}`;
  }

  function formatBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes < 0) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function parseReleaseAssets(release) {
    const assets = Array.isArray(release?.assets) ? release.assets : [];
    const byMcu = {
      xiao_rp2040: [],
      xiao_esp32c6: [],
    };
    const baseFirmware = {
      xiao_rp2040: null,
      xiao_esp32c6: null,
    };
    let libBundle = null;
    const libFiles = [];

    for (const asset of assets) {
      const name = asset?.name || "";
      const url = asset?.browser_download_url || "";
      if (!name || !url) continue;

      if (name === "circuitpython-lib.zip") {
        libBundle = {
          fileName: name,
          downloadUrl: url,
          size: asset.size,
          sizeLabel: formatBytes(asset.size),
        };
        continue;
      }

      if (LIB_FILE_NAMES.includes(name)) {
        libFiles.push({
          fileName: name,
          downloadUrl: url,
          size: asset.size,
          sizeLabel: formatBytes(asset.size),
        });
        continue;
      }

      let matched = false;
      for (const mcu of TARGET_MCUS) {
        if (name.endsWith(mcu.suffix)) {
          const exampleName = name.slice(0, -mcu.suffix.length);
          byMcu[mcu.id].push({
            exampleName,
            fileName: name,
            downloadUrl: url,
            size: asset.size,
            sizeLabel: formatBytes(asset.size),
          });
          matched = true;
          break;
        }
        if (name.startsWith(mcu.circuitpythonPrefix)) {
          baseFirmware[mcu.id] = {
            fileName: name,
            downloadUrl: url,
            size: asset.size,
            sizeLabel: formatBytes(asset.size),
          };
          matched = true;
          break;
        }
      }
      if (matched) continue;
    }

    for (const mcu of TARGET_MCUS) {
      byMcu[mcu.id].sort((a, b) => a.exampleName.localeCompare(b.exampleName));
    }
    libFiles.sort((a, b) => a.fileName.localeCompare(b.fileName));

    return {
      tagName: release?.tag_name || "",
      releaseName: release?.name || release?.tag_name || "",
      htmlUrl: release?.html_url || "",
      publishedAt: release?.published_at || "",
      byMcu,
      baseFirmware,
      libBundle,
      libFiles,
    };
  }

  async function fetchLatestRelease(repo, fetchFn) {
    const targetRepo = repo || detectRepo();
    const doFetch = fetchFn || (typeof fetch === "function" ? fetch.bind(globalThis) : null);
    if (!doFetch) {
      throw new Error("Fetch API is not available in this environment.");
    }

    const apiUrl = `https://api.github.com/repos/${targetRepo}/releases/latest`;
    const response = await doFetch(apiUrl, {
      headers: {
        Accept: "application/vnd.github+json",
      },
    });

    if (response.status === 404) {
      const err = new Error("No release has been published yet.");
      err.code = "NO_RELEASE";
      err.releasesUrl = `https://github.com/${targetRepo}/releases`;
      throw err;
    }

    if (!response.ok) {
      const err = new Error(`GitHub API error (HTTP ${response.status}).`);
      err.code = "API_ERROR";
      err.status = response.status;
      err.releasesUrl = `https://github.com/${targetRepo}/releases/latest`;
      throw err;
    }

    const data = await response.json();
    return parseReleaseAssets(data);
  }

  async function buildLocalLibPayloads(fetchFn, pyLibs) {
    const doFetch = fetchFn || (typeof fetch === "function" ? fetch.bind(globalThis) : null);
    const libsMap = pyLibs || (typeof window !== "undefined" ? window.XMAS_PY_LIBS : null) || {};
    const payloads = [];

    if (doFetch) {
      const res = await doFetch("lib/neopixel.mpy");
      if (!res.ok) {
        throw new Error(`Failed to load lib/neopixel.mpy (HTTP ${res.status}).`);
      }
      const buf = await res.arrayBuffer();
      payloads.push({ fileName: "neopixel.mpy", data: buf });
    }

    for (const pyName of ["tannenbaum_layout.py", "tannenbaum_palettes.py"]) {
      if (typeof libsMap[pyName] === "string") {
        payloads.push({ fileName: pyName, data: libsMap[pyName] });
      }
    }

    return payloads;
  }

  async function installLibsToDirectory(dirHandle, options = {}) {
    if (!dirHandle) {
      throw new Error("No target directory selected.");
    }
    const payloads = await buildLocalLibPayloads(options.fetchFn, options.pyLibs);
    const libDir = await dirHandle.getDirectoryHandle("lib", { create: true });
    const installed = [];

    for (const item of payloads) {
      const fileHandle = await libDir.getFileHandle(item.fileName, { create: true });
      const writable = await fileHandle.createWritable();
      await writable.write(item.data);
      await writable.close();
      installed.push(item.fileName);
    }

    return installed;
  }

  const UF2_MAGIC_START0 = 0x0a324655;
  const UF2_MAGIC_START1 = 0x9e5d5157;
  const UF2_MAGIC_END = 0x0ab16f30;
  const UF2_FLAG_NOFLASH = 0x00000001;

  function parseUf2ToSegments(arrayBuffer) {
    const view = new DataView(arrayBuffer);
    const totalBytes = arrayBuffer.byteLength;
    if (totalBytes < 512 || totalBytes % 512 !== 0) {
      throw new Error("Invalid UF2 file: size must be a non-empty multiple of 512 bytes.");
    }

    const blocks = [];
    for (let offset = 0; offset < totalBytes; offset += 512) {
      const magic0 = view.getUint32(offset, true);
      const magic1 = view.getUint32(offset + 4, true);
      const magicEnd = view.getUint32(offset + 508, true);
      if (magic0 !== UF2_MAGIC_START0 || magic1 !== UF2_MAGIC_START1 || magicEnd !== UF2_MAGIC_END) {
        throw new Error(`Invalid UF2 block magic at offset ${offset}.`);
      }

      const flags = view.getUint32(offset + 8, true);
      if (flags & UF2_FLAG_NOFLASH) continue;

      const targetAddr = view.getUint32(offset + 12, true);
      const payloadSize = view.getUint32(offset + 16, true);
      if (payloadSize > 476) {
        throw new Error(`Invalid UF2 payload size (${payloadSize}) at offset ${offset}.`);
      }
      const data = new Uint8Array(arrayBuffer, offset + 32, payloadSize);
      blocks.push({ address: targetAddr, data });
    }

    if (blocks.length === 0) {
      throw new Error("UF2 file contains no flashable blocks.");
    }

    blocks.sort((a, b) => a.address - b.address);

    // Merge contiguous blocks into segments
    const segments = [];
    let curAddr = blocks[0].address;
    let curChunks = [blocks[0].data];
    let curLen = blocks[0].data.length;

    for (let i = 1; i < blocks.length; i++) {
      const blk = blocks[i];
      if (blk.address === curAddr + curLen) {
        curChunks.push(blk.data);
        curLen += blk.data.length;
      } else {
        const merged = new Uint8Array(curLen);
        let pos = 0;
        for (const c of curChunks) {
          merged.set(c, pos);
          pos += c.length;
        }
        segments.push({ address: curAddr, data: merged });
        curAddr = blk.address;
        curChunks = [blk.data];
        curLen = blk.data.length;
      }
    }

    const lastMerged = new Uint8Array(curLen);
    let pos = 0;
    for (const c of curChunks) {
      lastMerged.set(c, pos);
      pos += c.length;
    }
    segments.push({ address: curAddr, data: lastMerged });

    return segments;
  }

  function uint8ArrayToBinaryString(u8) {
    let out = "";
    const chunk = 0x8000;
    for (let i = 0; i < u8.length; i += chunk) {
      out += String.fromCharCode.apply(null, u8.subarray(i, i + chunk));
    }
    return out;
  }

  const ESPTOOL_JS_CDN = "https://cdn.jsdelivr.net/npm/esptool-js@0.5.7/bundle.js";

  async function flashEsp32WebSerial(segments, options = {}) {
    if (typeof navigator === "undefined" || !navigator.serial) {
      throw new Error("WebSerial API is not supported in this browser.");
    }
    const log = options.onLog || (() => {});
    const onProgress = options.onProgress || (() => {});
    const baudrate = options.baudrate || 460800;
    const eraseAll = Boolean(options.eraseAll);

    log("Loading esptool-js…");
    const esptoolMod = await import(ESPTOOL_JS_CDN);
    const { ESPLoader, Transport } = esptoolMod;

    log("Requesting serial port…");
    const port = await navigator.serial.requestPort();
    const transport = new Transport(port, true);

    const terminal = {
      clean() {},
      writeLine(data) { log(String(data)); },
      write(data) { log(String(data)); },
    };

    try {
      const esploader = new ESPLoader({
        transport,
        baudrate,
        romBaudrate: 115200,
        terminal,
        debugLogging: false,
      });

      log("Connecting to ESP32-C6 bootloader…");
      const chip = await esploader.main();
      log(`Connected: ${chip}`);

      const fileArray = segments.map((seg) => ({
        address: seg.address >>> 0,
        data: uint8ArrayToBinaryString(seg.data instanceof Uint8Array ? seg.data : new Uint8Array(seg.data)),
      }));

      await esploader.writeFlash({
        fileArray,
        flashSize: "keep",
        flashMode: "keep",
        flashFreq: "keep",
        eraseAll,
        compress: true,
        reportProgress: (_fileIndex, written, total) => {
          if (total > 0) {
            onProgress(Math.round((written / total) * 100), written, total);
          }
        },
      });

      log("Resetting board…");
      if (typeof esploader.after === "function") {
        await esploader.after("hard_reset");
      } else {
        await transport.setDTR(false);
        await transport.setRTS(true);
        await new Promise((r) => setTimeout(r, 100));
        await transport.setRTS(false);
      }
      log("Done! Flash complete.");
    } finally {
      try {
        await transport.disconnect();
      } catch (_e) {
        // Ignore disconnect errors
      }
    }
  }

  const api = {
    DEFAULT_REPO,
    LIB_FILE_NAMES,
    TARGET_MCUS,
    detectRepo,
    getRawRepoUrl,
    formatBytes,
    parseReleaseAssets,
    fetchLatestRelease,
    buildLocalLibPayloads,
    installLibsToDirectory,
    parseUf2ToSegments,
    uint8ArrayToBinaryString,
    flashEsp32WebSerial,
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  root.XmasFirmware = api;
})(typeof window !== "undefined" ? window : globalThis);
