import asyncio
import functools
import http.server
import json
import re
import socketserver
import subprocess
import sys
import threading
import types
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


class _IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.scripts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attr_map = dict(attrs)
        if "id" in attr_map:
            self.ids.add(attr_map["id"])
        if tag == "script" and "src" in attr_map:
            self.scripts.append(attr_map["src"])
        if tag == "link" and "href" in attr_map:
            self.links.append(attr_map["href"])


class TestPagesStructure(unittest.TestCase):
    def test_required_docs_files_exist(self):
        required = [
            "index.html",
            "styles.css",
            "app.js",
            "runtime.js",
            "firmware.js",
            "examples.js",
            "py_libs.js",
            "pcb_outline.js",
            "lib/neopixel.mpy",
        ]
        for name in required:
            path = DOCS / name
            self.assertTrue(path.is_file(), f"Missing docs/{name}")
            self.assertGreater(path.stat().st_size, 0, f"Empty docs/{name}")

        self.assertEqual(
            (DOCS / "lib" / "neopixel.mpy").read_bytes(),
            (ROOT / "circuitpython" / "default" / "lib" / "neopixel.mpy").read_bytes(),
            "docs/lib/neopixel.mpy out of sync with circuitpython/default/lib/neopixel.mpy",
        )

    def test_index_html_elements_and_local_assets(self):
        html = (DOCS / "index.html").read_text(encoding="utf-8")
        parser = _IdCollector()
        parser.feed(html)

        expected_ids = {
            "tree-svg",
            "btn-d5",
            "btn-d6",
            "state-d5",
            "state-d6",
            "latch-d5",
            "latch-d6",
            "example-select",
            "btn-firmware-modal",
            "firmware-modal",
            "btn-firmware-close",
            "btn-firmware-refresh",
            "firmware-release-meta",
            "mcu-tab-xiao_rp2040",
            "mcu-tab-xiao_esp32c6",
            "firmware-mcu-hint",
            "firmware-base-section",
            "btn-install-libs",
            "btn-download-libs-zip",
            "firmware-libs-status",
            "firmware-libs-list",
            "firmware-list",
            "btn-run",
            "btn-stop",
            "btn-reset",
            "btn-download",
            "serial-console",
            "toggle-indices",
            "toggle-traces",
            "led-inspector",
        }
        self.assertTrue(expected_ids.issubset(parser.ids), f"Missing IDs: {expected_ids - parser.ids}")

        for src in parser.scripts:
            if not src.startswith(("http://", "https://")):
                self.assertTrue((DOCS / src).is_file(), f"Missing local script: {src}")

        for href in parser.links:
            if not href.startswith(("http://", "https://")):
                self.assertTrue((DOCS / href).is_file(), f"Missing local stylesheet: {href}")

    def test_js_syntax_with_node(self):
        for name in ("examples.js", "py_libs.js", "pcb_outline.js", "runtime.js", "firmware.js", "app.js"):
            res = subprocess.run(
                ["node", "--check", str(DOCS / name)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, f"JS syntax error in {name}: {res.stderr}")

    def test_firmware_release_parser_and_fetch(self):
        node_script = """
        const assert = require('assert');
        const fw = require(process.argv[1]);

        assert.strictEqual(
          fw.detectRepo({ hostname: 'chatelao.github.io', pathname: '/aity-xmas-2026/' }),
          'chatelao/aity-xmas-2026'
        );
        assert.strictEqual(
          fw.detectRepo({ hostname: 'localhost', pathname: '/' }),
          'chatelao/aity-xmas-2026'
        );
        assert.strictEqual(fw.formatBytes(512), '512 B');
        assert.strictEqual(fw.formatBytes(2048), '2.0 KB');
        assert.strictEqual(
          fw.TARGET_MCUS.find(m => m.id === 'xiao_rp2040').circuitpythonBoardUrl,
          'https://circuitpython.org/board/seeeduino_xiao_rp2040/'
        );
        assert.strictEqual(
          fw.TARGET_MCUS.find(m => m.id === 'xiao_esp32c6').circuitpythonBoardUrl,
          'https://circuitpython.org/board/seeed_xiao_esp32c6/'
        );

        const parsed = fw.parseReleaseAssets({
          tag_name: 'v1.2.3',
          name: 'Release 1.2.3',
          html_url: 'https://github.com/chatelao/aity-xmas-2026/releases/tag/v1.2.3',
          published_at: '2026-11-18T10:00:00Z',
          assets: [
            {
              name: 'TwinkleFox_xiao_rp2040.uf2',
              browser_download_url: 'https://example.com/TwinkleFox_xiao_rp2040.uf2',
              size: 45056,
            },
            {
              name: 'TwinkleFox_xiao_esp32c6.uf2',
              browser_download_url: 'https://example.com/TwinkleFox_xiao_esp32c6.uf2',
              size: 120000,
            },
            {
              name: 'AlphaDemo_xiao_rp2040.uf2',
              browser_download_url: 'https://example.com/AlphaDemo_xiao_rp2040.uf2',
              size: 10240,
            },
            {
              name: 'adafruit-circuitpython-seeeduino_xiao_rp2040-de_DE-10.3.1.uf2',
              browser_download_url: 'https://example.com/cp-rp2040.uf2',
              size: 1925632,
            },
            {
              name: 'adafruit-circuitpython-seeed_xiao_esp32c6-de_DE-10.3.1.bin',
              browser_download_url: 'https://example.com/cp-esp32c6.bin',
              size: 2045680,
            },
            {
              name: 'circuitpython-lib.zip',
              browser_download_url: 'https://example.com/circuitpython-lib.zip',
              size: 8192,
            },
            {
              name: 'neopixel.mpy',
              browser_download_url: 'https://example.com/neopixel.mpy',
              size: 1315,
            },
            {
              name: 'tannenbaum_layout.py',
              browser_download_url: 'https://example.com/tannenbaum_layout.py',
              size: 9997,
            },
          ],
        });

        assert.strictEqual(parsed.tagName, 'v1.2.3');
        assert.strictEqual(parsed.byMcu.xiao_rp2040.length, 2);
        assert.strictEqual(parsed.byMcu.xiao_rp2040[0].exampleName, 'AlphaDemo');
        assert.strictEqual(parsed.byMcu.xiao_rp2040[1].exampleName, 'TwinkleFox');
        assert.strictEqual(parsed.byMcu.xiao_esp32c6.length, 1);
        assert.strictEqual(parsed.byMcu.xiao_esp32c6[0].fileName, 'TwinkleFox_xiao_esp32c6.uf2');
        assert.strictEqual(parsed.baseFirmware.xiao_rp2040.downloadUrl, 'https://example.com/cp-rp2040.uf2');
        assert.strictEqual(parsed.baseFirmware.xiao_esp32c6.downloadUrl, 'https://example.com/cp-esp32c6.bin');
        assert.strictEqual(parsed.libBundle.fileName, 'circuitpython-lib.zip');
        assert.strictEqual(parsed.libFiles.length, 2);

        (async () => {
          const okRes = await fw.fetchLatestRelease('chatelao/aity-xmas-2026', async (url) => {
            assert.strictEqual(url, 'https://api.github.com/repos/chatelao/aity-xmas-2026/releases/latest');
            return {
              ok: true,
              status: 200,
              json: async () => ({ tag_name: 'v1.0.0', assets: [] }),
            };
          });
          assert.strictEqual(okRes.tagName, 'v1.0.0');

          await assert.rejects(
            () => fw.fetchLatestRelease('chatelao/aity-xmas-2026', async () => ({ ok: false, status: 404 })),
            (err) => err.code === 'NO_RELEASE'
          );

          const written = {};
          const mockDirHandle = {
            getDirectoryHandle: async (name) => {
              assert.strictEqual(name, 'lib');
              return {
                getFileHandle: async (fname) => ({
                  createWritable: async () => ({
                    write: async (data) => { written[fname] = data; },
                    close: async () => {},
                  }),
                }),
              };
            },
          };

          const installed = await fw.installLibsToDirectory(mockDirHandle, {
            fetchFn: async (path) => {
              assert.strictEqual(path, 'lib/neopixel.mpy');
              return { ok: true, status: 200, arrayBuffer: async () => new Uint8Array([1, 2, 3]).buffer };
            },
            pyLibs: {
              'tannenbaum_layout.py': '# layout',
              'tannenbaum_palettes.py': '# palettes',
            },
          });
          assert.deepStrictEqual(installed, ['neopixel.mpy', 'tannenbaum_layout.py', 'tannenbaum_palettes.py']);
          assert.strictEqual(written['tannenbaum_layout.py'], '# layout');
          assert.strictEqual(written['tannenbaum_palettes.py'], '# palettes');
          assert.strictEqual(written['neopixel.mpy'].byteLength, 3);
        })().catch((e) => {
          console.error(e);
          process.exit(1);
        });
        """
        res = subprocess.run(
            ["node", "-e", node_script, str(DOCS / "firmware.js")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, f"firmware.js unit tests failed: {res.stderr}")

    def test_examples_match_source_files_verbatim(self):
        ex_js = (DOCS / "examples.js").read_text(encoding="utf-8")
        examples = json.loads(ex_js.split("window.XMAS_EXAMPLES = ", 1)[1].rsplit(";", 1)[0])
        self.assertEqual(len(examples), 6, "Expected all 6 examples")

        for ex in examples:
            src_path = ROOT / ex["file"]
            self.assertTrue(src_path.is_file(), f"Missing source file {ex['file']}")
            self.assertEqual(
                ex["code"],
                src_path.read_text(encoding="utf-8"),
                f"Example {ex['id']} out of sync with {ex['file']}",
            )

    def test_py_libs_match_source_files_verbatim(self):
        libs_js = (DOCS / "py_libs.js").read_text(encoding="utf-8")
        libs = json.loads(libs_js.split("window.XMAS_PY_LIBS = ", 1)[1].rsplit(";", 1)[0])

        for fname in ("tannenbaum_layout.py", "tannenbaum_palettes.py"):
            self.assertIn(fname, libs)
            src = (ROOT / "circuitpython" / "lib" / fname).read_text(encoding="utf-8")
            self.assertEqual(libs[fname], src, f"{fname} out of sync with circuitpython/lib/{fname}")

    def test_pixel_coords_count_in_app_js(self):
        app_js = (DOCS / "app.js").read_text(encoding="utf-8")
        m = re.search(r"const PIXEL_COORDS = \[(.*?)\];", app_js, re.S)
        self.assertIsNotNone(m, "PIXEL_COORDS not found in app.js")
        coords = re.findall(r"\[\s*[-\d.]+\s*,\s*[-\d.]+\s*,\s*\d+\s*\]", m.group(1))
        self.assertEqual(len(coords), 60, f"Expected 60 LEDs in PIXEL_COORDS, got {len(coords)}")


class _MockBridge:
    def __init__(self):
        self.buttons = {"D5": False, "D6": False}
        self.run_id = 1
        self.leds = [(0, 0, 0)] * 60
        self.brightness = 1.0
        self.onboard = (0, 0, 0)
        self.led_frames = 0
        self.stdout = []
        self.stderr = []

    def getButton(self, name):
        return self.buttons[name]

    def getRunId(self):
        return self.run_id

    def updateLeds(self, flat, brightness):
        self.leds = [(flat[i], flat[i + 1], flat[i + 2]) for i in range(0, len(flat), 3)]
        self.brightness = brightness
        self.led_frames += 1

    def updateOnboard(self, r, g, b, brightness):
        self.onboard = (r, g, b)

    def writeStdout(self, text):
        self.stdout.append(text)

    def writeStderr(self, text):
        self.stderr.append(text)


def _load_runtime():
    js_text = (DOCS / "runtime.js").read_text(encoding="utf-8")
    m = re.search(r"const PYTHON_BOOTSTRAP = `(.*?)`;\n", js_text, re.S)
    assert m, "Could not extract PYTHON_BOOTSTRAP"
    bootstrap = m.group(1).replace("\\\\n", "\\n")

    bridge = _MockBridge()
    js_mod = types.ModuleType("js")
    js_mod.__simBridge = bridge

    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    sys.modules["js"] = js_mod
    lib_dir = str((ROOT / "circuitpython" / "lib").resolve())
    if lib_dir not in sys.path:
        sys.path.insert(0, lib_dir)

    ns = {}
    exec(bootstrap, ns)
    # Restore real stdout/stderr for unittest output; _ConsoleWriter is tested via bridge
    sys.stdout = orig_stdout
    sys.stderr = orig_stderr
    return ns, bridge


class TestSimulatorRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ex_js = (DOCS / "examples.js").read_text(encoding="utf-8")
        cls.examples = {
            ex["id"]: ex["code"]
            for ex in json.loads(ex_js.split("window.XMAS_EXAMPLES = ", 1)[1].rsplit(";", 1)[0])
        }

    def _run_sim(self, code, script_coro):
        ns, bridge = _load_runtime()

        async def runner():
            bridge.run_id += 1
            my_id = bridge.run_id
            task = asyncio.create_task(ns["_sim_execute"](code, my_id))
            try:
                await script_coro(bridge)
            finally:
                bridge.run_id += 1
                await task

        asyncio.run(runner())
        return bridge

    def test_example_0_default_pin_scanner(self):
        async def scenario(bridge):
            await asyncio.sleep(0.06)
            # Idle: first 3 LEDs dim white, LED 4 NOT purple
            self.assertEqual(bridge.leds[0], (15, 15, 15))
            self.assertEqual(bridge.leds[4], (0, 0, 0))
            self.assertEqual(bridge.onboard, (0, 0, 20))

            # Press D6 -> LED 0 green, LED 1 blue, onboard green
            bridge.buttons["D6"] = True
            await asyncio.sleep(0.06)
            self.assertEqual(bridge.leds[0], (0, 255, 0))
            self.assertEqual(bridge.leds[1], (0, 0, 80))
            self.assertEqual(bridge.onboard, (0, 255, 0))
            bridge.buttons["D6"] = False

            # Press D5 -> LED 9 red, LED 10 yellow, onboard red
            bridge.buttons["D5"] = True
            await asyncio.sleep(0.06)
            self.assertEqual(bridge.leds[9], (255, 0, 0))
            self.assertEqual(bridge.leds[10], (80, 80, 0))
            self.assertEqual(bridge.onboard, (255, 0, 0))

        bridge = self._run_sim(self.examples["default"], scenario)
        self.assertEqual(bridge.stderr, [])

    def test_example_1_sechs_leds(self):
        async def scenario(bridge):
            await asyncio.sleep(0.05)
            # Initially 3 LEDs lit, LEDs 3..5 off
            self.assertEqual(bridge.leds[0], (255, 0, 0))
            self.assertEqual(bridge.leds[3], (0, 0, 0))

            # Press D5 -> toggle to 6 LEDs
            bridge.buttons["D5"] = True
            await asyncio.sleep(0.08)
            bridge.buttons["D5"] = False
            await asyncio.sleep(0.05)
            self.assertEqual(bridge.leds[3], (255, 255, 0))
            self.assertEqual(bridge.leds[5], (255, 0, 255))

            # Hold D6 -> blank all LEDs
            bridge.buttons["D6"] = True
            await asyncio.sleep(0.05)
            self.assertEqual(bridge.leds[0], (0, 0, 0))
            self.assertEqual(bridge.leds[3], (0, 0, 0))

            # Release D6 -> restored
            bridge.buttons["D6"] = False
            await asyncio.sleep(0.05)
            self.assertEqual(bridge.leds[0], (255, 0, 0))
            self.assertEqual(bridge.leds[3], (255, 255, 0))

        bridge = self._run_sim(self.examples["ex1"], scenario)
        self.assertEqual(bridge.stderr, [])

    def test_example_2_lauflicht(self):
        async def scenario(bridge):
            await asyncio.sleep(0.14)
            self.assertGreater(bridge.led_frames, 2)
            # At least one LED should be lit (head or fading trail)
            self.assertTrue(any(c != (0, 0, 0) for c in bridge.leds))

            # Trigger D5 (reverse) and D6 (cycle speed)
            bridge.buttons["D5"] = True
            await asyncio.sleep(0.03)
            bridge.buttons["D5"] = False
            bridge.buttons["D6"] = True
            await asyncio.sleep(0.03)
            bridge.buttons["D6"] = False
            await asyncio.sleep(0.06)

        bridge = self._run_sim(self.examples["ex2"], scenario)
        self.assertEqual(bridge.stderr, [])

    def test_example_3_segmente(self):
        async def scenario(bridge):
            await asyncio.sleep(0.04)
            # Segment 0 (0..5) lit Feuerrot
            self.assertEqual(bridge.leds[0], (255, 40, 0))
            self.assertEqual(bridge.leds[5], (0, 0, 0))

            # Press D6 -> advance to Segment 1 (5..10) Goldgelb
            bridge.buttons["D6"] = True
            await asyncio.sleep(0.03)
            bridge.buttons["D6"] = False
            await asyncio.sleep(0.03)
            self.assertEqual(bridge.leds[0], (0, 0, 0))
            self.assertEqual(bridge.leds[5], (255, 180, 0))

        bridge = self._run_sim(self.examples["ex3"], scenario)
        self.assertEqual(bridge.stderr, [])

    def test_example_4_koordinaten(self):
        async def scenario(bridge):
            await asyncio.sleep(0.08)
            self.assertGreater(bridge.led_frames, 2)
            self.assertTrue(any(c != (0, 0, 0) for c in bridge.leds))

            # Press D6 -> next epicenter
            bridge.buttons["D6"] = True
            await asyncio.sleep(0.03)
            bridge.buttons["D6"] = False
            await asyncio.sleep(0.05)

        bridge = self._run_sim(self.examples["ex4"], scenario)
        self.assertEqual(bridge.stderr, [])

    def test_example_5_maximal(self):
        async def scenario(bridge):
            await asyncio.sleep(0.06)
            self.assertGreater(bridge.led_frames, 2)
            # Mode 0 plasma lights all 60 LEDs
            self.assertTrue(all(len(c) == 3 for c in bridge.leds))

            # Switch to Mode 1 & Mode 2 via D5, shift palette via D6
            for _ in range(2):
                bridge.buttons["D5"] = True
                await asyncio.sleep(0.03)
                bridge.buttons["D5"] = False
                await asyncio.sleep(0.03)
            bridge.buttons["D6"] = True
            await asyncio.sleep(0.03)
            bridge.buttons["D6"] = False
            await asyncio.sleep(0.04)

        bridge = self._run_sim(self.examples["ex5"], scenario)
        self.assertEqual(bridge.stderr, [])

    def test_custom_near_circuitpython_with_libs_and_ignored_pins(self):
        custom_code = """
import time
import board
import digitalio
import neopixel
from rainbowio import colorwheel
from tannenbaum_layout import fill_segment, SEG_STAR_OUTER
from tannenbaum_palettes import render_twinkle_tree, PAL_RETRO_C9

# Arbitrary pins should be safely ignored
extra_pin = digitalio.DigitalInOut(board.D3)
extra_pin.switch_to_input(pull=digitalio.Pull.UP)

pixels = neopixel.NeoPixel(board.D10, 60, brightness=0.5, auto_write=False)
fill_segment(pixels, SEG_STAR_OUTER, colorwheel(85))
pixels.show()
time.sleep(0.02)
render_twinkle_tree(pixels, 1234, PAL_RETRO_C9)
pixels.show()
"""

        async def scenario(bridge):
            await asyncio.sleep(0.08)

        bridge = self._run_sim(custom_code, scenario)
        self.assertEqual(bridge.stderr, [])
        self.assertGreaterEqual(bridge.led_frames, 2)

    def test_syntax_error_raises_cleanly(self):
        ns, bridge = _load_runtime()
        with self.assertRaises(SyntaxError):
            asyncio.run(ns["_sim_execute"]("def broken(:\n  pass\n", bridge.run_id))


class TestLocalHttpServing(unittest.TestCase):
    def test_serve_docs_over_http(self):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))

        class _QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(DOCS), **kwargs)

            def log_message(self, format, *args):
                pass

        with socketserver.TCPServer(("127.0.0.1", 0), _QuietHandler) as httpd:
            port = httpd.server_address[1]
            t = threading.Thread(target=httpd.serve_forever, daemon=True)
            t.start()
            try:
                for path in ("index.html", "styles.css", "app.js", "runtime.js", "examples.js", "py_libs.js", "pcb_outline.js"):
                    with urlopen(f"http://127.0.0.1:{port}/{path}", timeout=3) as resp:
                        self.assertEqual(resp.status, 200, f"HTTP {resp.status} for {path}")
                        self.assertGreater(len(resp.read()), 0)
            finally:
                httpd.shutdown()


if __name__ == "__main__":
    unittest.main()
