import assert from "node:assert/strict";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const pwPath = process.env.PW_CORE_PATH || "/tmp/pw-test/node_modules/playwright-core";
const { chromium } = require(pwPath);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DOCS_DIR = path.resolve(__dirname, "..", "docs");

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json",
};

function startStaticServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const reqPath = (req.url || "/").split("?")[0];
      const relPath = reqPath === "/" ? "index.html" : reqPath.replace(/^\/+/, "");
      const filePath = path.join(DOCS_DIR, relPath);
      if (!filePath.startsWith(DOCS_DIR) || !fs.existsSync(filePath)) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      const ext = path.extname(filePath);
      res.writeHead(200, { "Content-Type": MIME_TYPES[ext] || "application/octet-stream" });
      fs.createReadStream(filePath).pipe(res);
    });
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolve({ server, url: `http://127.0.0.1:${port}/` });
    });
  });
}

async function openApp(browser, url, contextOptions) {
  const context = await browser.newContext(contextOptions);
  const page = await context.newPage();

  // Block external CDN requests (Pyodide, CodeMirror, Google Fonts) so tests are fast & offline-safe
  await page.route("**/*", (route) => {
    const reqUrl = route.request().url();
    if (reqUrl.startsWith("http://127.0.0.1")) {
      return route.continue();
    }
    return route.abort();
  });

  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.message));

  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#pcb-leds rect");
  return { context, page, pageErrors };
}

async function assertNoHorizontalOverflow(page, label) {
  const metrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  assert.ok(
    metrics.scrollWidth <= metrics.clientWidth + 1,
    `${label}: horizontal overflow detected (scrollWidth=${metrics.scrollWidth}, clientWidth=${metrics.clientWidth})`
  );
}

async function runTests() {
  const { server, url } = await startStaticServer();
  const executablePath = process.env.CHROMIUM_PATH || "/usr/bin/chromium";
  const browser = await chromium.launch({ headless: true, executablePath });

  try {
    // 1. Resolution & Layout Tests
    const viewports = [
      { name: "desktop-1440x900", width: 1440, height: 900, hasTouch: false, isMobile: false, stacked: false },
      { name: "tablet-768x1024", width: 768, height: 1024, hasTouch: true, isMobile: true, stacked: true },
      { name: "mobile-390x844", width: 390, height: 844, hasTouch: true, isMobile: true, stacked: true },
      { name: "small-mobile-320x568", width: 320, height: 568, hasTouch: true, isMobile: true, stacked: true },
      { name: "mobile-landscape-844x390", width: 844, height: 390, hasTouch: true, isMobile: true, stacked: true },
    ];

    for (const vp of viewports) {
      const { context, page, pageErrors } = await openApp(browser, url, {
        viewport: { width: vp.width, height: vp.height },
        hasTouch: vp.hasTouch,
        isMobile: vp.isMobile,
      });
      try {
        assert.deepEqual(pageErrors, [], `${vp.name}: unexpected page errors`);
        await assertNoHorizontalOverflow(page, vp.name);

        const layout = await page.evaluate(() => {
          const treeRect = document.querySelector(".pane-tree").getBoundingClientRect();
          const edRect = document.querySelector(".pane-editor").getBoundingClientRect();
          const btnD5Rect = document.getElementById("btn-d5").getBoundingClientRect();
          const btnRunRect = document.getElementById("btn-run").getBoundingClientRect();
          const ledCount = document.querySelectorAll("#pcb-leds rect").length;
          return { treeRect, edRect, btnD5Rect, btnRunRect, ledCount };
        });

        assert.equal(layout.ledCount, 60, `${vp.name}: expected 60 LEDs`);
        if (vp.stacked) {
          assert.ok(layout.edRect.top >= layout.treeRect.bottom - 2, `${vp.name}: panes should stack vertically`);
        } else {
          assert.ok(layout.edRect.left >= layout.treeRect.right - 2, `${vp.name}: panes should be side-by-side`);
        }
        if (vp.width <= 600) {
          assert.ok(layout.btnD5Rect.height >= 44, `${vp.name}: D5 touch target height >= 44px`);
          assert.ok(layout.btnRunRect.height >= 40, `${vp.name}: Run touch target height >= 40px`);
        }
        console.log(`PASS viewport: ${vp.name}`);
      } finally {
        await context.close();
      }
    }

    // 2. Mobile Touch Interaction Tests
    {
      const { context, page } = await openApp(browser, url, {
        viewport: { width: 390, height: 844 },
        hasTouch: true,
        isMobile: true,
      });
      try {
        // Touch hold & release on BTN D5
        await page.evaluate(() => {
          const btn = document.getElementById("btn-d5");
          btn.dispatchEvent(new TouchEvent("touchstart", { bubbles: true, cancelable: true }));
        });
        assert.equal(await page.textContent("#state-d5"), "LOW");
        assert.equal(await page.getAttribute("#btn-d5", "aria-pressed"), "true");

        await page.evaluate(() => {
          const btn = document.getElementById("btn-d5");
          btn.dispatchEvent(new TouchEvent("touchend", { bubbles: true, cancelable: true }));
        });
        assert.equal(await page.textContent("#state-d5"), "HIGH");
        assert.equal(await page.getAttribute("#btn-d5", "aria-pressed"), "false");

        // Tap latch-d6 to hold D6 LOW, then untap
        await page.tap("#latch-d6");
        assert.equal(await page.textContent("#state-d6"), "LOW");
        await page.tap("#latch-d6");
        assert.equal(await page.textContent("#state-d6"), "HIGH");

        // Tap an LED chip to inspect it on mobile
        const firstLed = page.locator("#pcb-leds rect").first();
        await firstLed.tap();
        const inspectorText = await page.textContent("#led-inspector");
        assert.match(inspectorText, /^LED #0 · .+ · RGB\(\d+, \d+, \d+\)$/);

        // Tap toggles for LED indices and PCB traces
        await page.tap("#toggle-indices");
        assert.equal(await page.evaluate(() => document.getElementById("pcb-indices").style.display), "block");
        await page.tap("#toggle-traces");
        assert.equal(await page.evaluate(() => document.getElementById("pcb-traces").style.display), "none");

        console.log("PASS mobile touch interactions");
      } finally {
        await context.close();
      }
    }

    // 3. Keyboard Interaction Tests
    {
      const { context, page } = await openApp(browser, url, {
        viewport: { width: 1280, height: 800 },
        hasTouch: false,
        isMobile: false,
      });
      try {
        // Keys 5 and 6 when editor is unfocused
        await page.keyboard.down("5");
        assert.equal(await page.textContent("#state-d5"), "LOW");
        await page.keyboard.up("5");
        assert.equal(await page.textContent("#state-d5"), "HIGH");

        await page.keyboard.down("6");
        assert.equal(await page.textContent("#state-d6"), "LOW");
        await page.keyboard.up("6");
        assert.equal(await page.textContent("#state-d6"), "HIGH");

        // Key 5 should NOT trigger D5 when code textarea is focused
        await page.focus("#code-fallback");
        await page.keyboard.down("5");
        assert.equal(await page.textContent("#state-d5"), "HIGH");
        await page.keyboard.up("5");

        // Focused BTN D5 responds to Space and Enter
        await page.focus("#btn-d5");
        await page.keyboard.down(" ");
        assert.equal(await page.textContent("#state-d5"), "LOW");
        await page.keyboard.up(" ");
        assert.equal(await page.textContent("#state-d5"), "HIGH");

        await page.keyboard.down("Enter");
        assert.equal(await page.textContent("#state-d5"), "LOW");
        await page.keyboard.up("Enter");
        assert.equal(await page.textContent("#state-d5"), "HIGH");

        // Window blur releases held key 5
        await page.focus("body");
        await page.keyboard.down("5");
        assert.equal(await page.textContent("#state-d5"), "LOW");
        await page.evaluate(() => window.dispatchEvent(new Event("blur")));
        assert.equal(await page.textContent("#state-d5"), "HIGH");

        console.log("PASS keyboard interactions");
      } finally {
        await context.close();
      }
    }

    console.log("ALL GH PAGES RESPONSIVE, TOUCH & KEYBOARD TESTS PASSED");
  } finally {
    await browser.close();
    server.close();
  }
}

runTests().catch((err) => {
  console.error(err);
  process.exit(1);
});
