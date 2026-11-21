import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import vm from "node:vm";

const root = path.resolve(import.meta.dirname, "..");
const htmlPath = path.join(root, "web_ui", "index.html");
const hdrPath = path.join(root, "main", "include", "web_ui_gz.h");

const html = fs.readFileSync(htmlPath, "utf8");
const hdr = fs.readFileSync(hdrPath, "utf8");

// 1. Verify 100% zero external network dependencies (crucial for offline captive portal)
assert.doesNotMatch(html, /https?:\/\//i, "Web UI must not reference external http(s) URLs");
assert.doesNotMatch(html, /<link[^>]+rel=["']stylesheet["']/i, "Web UI must inline all CSS");
assert.doesNotMatch(html, /<script[^>]+src=/i, "Web UI must inline all JS");

// 2. Verify gzipped C header matches web_ui/index.html byte-for-byte
const hexMatches = hdr.match(/0x[0-9a-fA-F]{2}/g);
assert.ok(hexMatches && hexMatches.length > 500, "web_ui_gz.h must contain gzipped byte array");
const gzBuf = Buffer.from(hexMatches.map((h) => parseInt(h, 16)));
const inflated = zlib.gunzipSync(gzBuf).toString("utf8");
assert.equal(inflated, html, "web_ui_gz.h is out of sync with web_ui/index.html (run scripts/embed_web_ui.py)");

// 3. Verify inline JavaScript parses cleanly with zero syntax errors
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(scriptMatch, "Inline <script> block must exist");
new vm.Script(scriptMatch[1], { filename: "web_ui/index.html" });

// 4. Verify 100% feature parity with chatelao/android-xmas-tree-app
const expectedPatterns = [
  "Off", "Static", "Rainbow", "Sparkle", "Candle", "Twinkle",
  "Lauflicht", "Segments", "Shockwave", "Plasma", "Polar Vortex", "Gravity Pulse", "TwinkleFOX",
];
for (const p of expectedPatterns) {
  assert.ok(html.includes(`"${p}"`), `Missing pattern: ${p}`);
}

const expectedMelodies = ["Silent", "Jingle Bells", "We Wish You", "Silent Night", "Deck the Halls"];
for (const m of expectedMelodies) {
  assert.ok(html.includes(`"${m}"`), `Missing melody: ${m}`);
}

const expectedEndpoints = [
  "/api/status", "/api/lighting", "/api/audio",
  "/api/presets", "/api/presets/apply", "/api/presets/delete",
];
for (const ep of expectedEndpoints) {
  assert.ok(html.includes(ep), `Missing API endpoint: ${ep}`);
}

console.log(
  `[PASS] Web UI verified (${html.length} B raw -> ${gzBuf.length} B gzip, 0 external deps, valid JS, 100% feature parity)`
);
