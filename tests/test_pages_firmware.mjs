import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const root = path.resolve(import.meta.dirname, "..");
const docsDir = path.join(root, "docs");

// 1. Load docs/firmware.js
const fw = require(path.join(docsDir, "firmware.js"));

// 2. Verify docs/app.js parses cleanly
new vm.Script(fs.readFileSync(path.join(docsDir, "app.js"), "utf8"), { filename: "docs/app.js" });

// 3. Verify docs/index.html contains all required modal IDs
const html = fs.readFileSync(path.join(docsDir, "index.html"), "utf8");
for (const id of [
  "btn-install-portal",
  "btn-install-libs",
  "firmware-packages-section",
  "firmware-packages-list",
  "btn-flash-cp-webserial",
  "btn-flash-file-webserial",
]) {
  assert.ok(html.includes(`id="${id}"`), `Missing #${id} in docs/index.html`);
}

// 4. Verify parseReleaseAssets handles v1.2.1 + software_*.zip assets
const mockRelease = {
  tag_name: "v1.2.1",
  name: "v1.2.1",
  html_url: "https://github.com/chatelao/aity-xmas-2026/releases/tag/v1.2.1",
  published_at: "2026-11-21T15:26:00Z",
  assets: [
    { name: "circuitpython-captive-portal-bundle.zip", browser_download_url: "https://example.com/cp.zip", size: 1331653 },
    { name: "code.portal.py", browser_download_url: "https://example.com/code.portal.py", size: 27836 },
    { name: "web_ui.html.gz", browser_download_url: "https://example.com/web_ui.html.gz", size: 8523 },
    { name: "XmasTreePortal_xiao_esp32c6.bin", browser_download_url: "https://example.com/portal.bin", size: 991120 },
    { name: "XmasTreePortal_xiao_esp32c6.uf2", browser_download_url: "https://example.com/portal.uf2", size: 1982464 },
    { name: "software_xiao_esp32c6.zip", browser_download_url: "https://example.com/sw_c6.zip", size: 1500000 },
    { name: "software_xiao_rp2040.zip", browser_download_url: "https://example.com/sw_rp.zip", size: 1200000 },
  ],
};

const parsed = fw.parseReleaseAssets(mockRelease);
assert.equal(parsed.byMcu.xiao_esp32c6.length, 1);
assert.equal(parsed.byMcu.xiao_esp32c6[0].fileName, "XmasTreePortal_xiao_esp32c6.uf2");
assert.equal(parsed.packages.length, 6);
assert.ok(parsed.packages.some((p) => p.fileName === "circuitpython-captive-portal-bundle.zip"));
assert.ok(parsed.packages.some((p) => p.fileName === "XmasTreePortal_xiao_esp32c6.bin"));
assert.ok(parsed.packages.some((p) => p.fileName === "software_xiao_esp32c6.zip"));
assert.ok(parsed.packages.some((p) => p.fileName === "software_xiao_rp2040.zip"));

// 5. Verify installCaptivePortalToDirectory writes all 5 files from docs/lib and docs/portal
const writtenFiles = new Map();
function makeDirHandle(prefix = "") {
  return {
    name: prefix || "CIRCUITPY",
    async getDirectoryHandle(name) {
      return makeDirHandle(prefix ? `${prefix}/${name}` : name);
    },
    async getFileHandle(name) {
      const full = prefix ? `${prefix}/${name}` : name;
      return {
        async createWritable() {
          let buf = null;
          return {
            async write(data) { buf = data; },
            async close() { writtenFiles.set(full, buf); },
          };
        },
      };
    },
  };
}

const localFetch = async (relPath) => {
  const fullPath = path.join(docsDir, relPath);
  const data = fs.readFileSync(fullPath);
  return {
    ok: true,
    status: 200,
    async text() { return data.toString("utf8"); },
    async arrayBuffer() { return data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength); },
  };
};

// Load py_libs.js into a sandbox to get window.XMAS_PY_LIBS
const pyLibsCtx = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(docsDir, "py_libs.js"), "utf8"), pyLibsCtx);

const installed = await fw.installCaptivePortalToDirectory(makeDirHandle(), {
  fetchFn: localFetch,
  pyLibs: pyLibsCtx.window.XMAS_PY_LIBS,
});

assert.deepEqual(installed, [
  "lib/neopixel.mpy",
  "lib/tannenbaum_layout.py",
  "lib/tannenbaum_palettes.py",
  "code.py",
  "web_ui.html.gz",
]);
assert.equal(writtenFiles.size, 5);
assert.ok(writtenFiles.get("code.py").includes("AP_SSID"));
assert.equal(new Uint8Array(writtenFiles.get("web_ui.html.gz"))[0], 0x1f);
assert.equal(new Uint8Array(writtenFiles.get("web_ui.html.gz"))[1], 0x8b);

console.log("[PASS] GitHub Pages Web UI firmware/package installer verified!");
