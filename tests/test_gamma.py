"""CIE L*, WS2812B white-balance, C dithering LUTs, and MappedPixels pipeline tests."""
import pathlib
import re
import subprocess
import sys
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "circuitpython" / "lib"))
sys.path.insert(0, str(ROOT / "tools"))

board = types.ModuleType("board")
for pin in ("D0", "D5", "D6", "D10"):
    setattr(board, pin, pin)
sys.modules.setdefault("board", board)

import tannenbaum_layout as tl  # noqa: E402


class FakeStrip(list):
    def __init__(self, n=60):
        super().__init__([(0, 0, 0)] * n)
        self.brightness = 1.0
        self.auto_write = False
        self.shown = 0

    def fill(self, c):
        for i in range(len(self)):
            self[i] = c

    def show(self):
        self.shown += 1


def _parse_c_array(text, name):
    m = re.search(rf"{name}\[256\][^=]*=\s*\{{(.*?)\}}", text, re.S)
    assert m, f"missing {name} in gamma_lut.h"
    return [int(v) for v in m.group(1).replace("\n", "").split(",") if v.strip()]


def _parse_js_array(text, name):
    m = re.search(rf"const {name} = new Uint8Array\(\[(.*?)\]\)", text, re.S)
    assert m, f"missing {name} in gamma_lut.js"
    return [int(v) for v in m.group(1).replace("\n", "").split(",") if v.strip()]


class GammaTests(unittest.TestCase):
    def test_cie_lstar_and_white_balance_properties(self):
        self.assertEqual(tl.CURVE, "cie_lstar")
        self.assertEqual(tl.WHITE_BALANCE, (255, 176, 240))

        for lut, max_val in (
            (tl.GAMMA_LUT, 255),
            (tl.GAMMA_LUT_R, 255),
            (tl.GAMMA_LUT_G, 176),
            (tl.GAMMA_LUT_B, 240),
        ):
            self.assertEqual(len(lut), 256)
            self.assertEqual(lut[0], 0)
            self.assertEqual(lut[255], max_val)
            self.assertTrue(all(lut[i] <= lut[i + 1] for i in range(255)))
            self.assertTrue(all(lut[i] >= 1 for i in range(1, 256)), "non-zero input must never vanish")

        # CIE L* at 50% (128/255) is ~18.6% linear light -> ~47 for R, ~33 for G
        self.assertAlmostEqual(tl.GAMMA_LUT_R[128], 47, delta=1)
        self.assertLess(tl.GAMMA_LUT_G[128], tl.GAMMA_LUT_R[128])
        # Linear toe for L* <= 8 (i <= 20)
        self.assertAlmostEqual(tl.cie_lstar_to_linear(8.0 / 100.0), 8.0 / 903.3, places=6)

    def test_c_and_js_tables_match(self):
        h = (ROOT / "esp32c6-portal/main/include/gamma_lut.h").read_text()
        js = (ROOT / "docs/gamma_lut.js").read_text()

        self.assertEqual(_parse_c_array(h, "GAMMA_LUT_R"), list(tl.GAMMA_LUT_R))
        self.assertEqual(_parse_c_array(h, "GAMMA_LUT_G"), list(tl.GAMMA_LUT_G))
        self.assertEqual(_parse_c_array(h, "GAMMA_LUT_B"), list(tl.GAMMA_LUT_B))

        self.assertEqual(_parse_js_array(js, "LUT"), list(tl.GAMMA_LUT))
        self.assertEqual(_parse_js_array(js, "LUT_R"), list(tl.GAMMA_LUT_R))
        self.assertEqual(_parse_js_array(js, "LUT_G"), list(tl.GAMMA_LUT_G))
        self.assertEqual(_parse_js_array(js, "LUT_B"), list(tl.GAMMA_LUT_B))

        # C 8.3 fixed-point dither LUTs: 0->0, 255->wb*8, monotonic, >=1 for i>0
        for name, wb in (("LED_DITHER_LUT_R", 255), ("LED_DITHER_LUT_G", 176), ("LED_DITHER_LUT_B", 240)):
            fp = _parse_c_array(h, name)
            self.assertEqual(len(fp), 256)
            self.assertEqual(fp[0], 0)
            self.assertEqual(fp[255], wb * 8)
            self.assertTrue(all(fp[i] <= fp[i + 1] for i in range(255)))
            self.assertTrue(all(fp[i] >= 1 for i in range(1, 256)))

    def test_generator_check_passes(self):
        res = subprocess.run(
            [sys.executable, str(ROOT / "tools/gen_gamma_tables.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_mapped_pixels_corrects_once_at_show(self):
        raw = FakeStrip()
        mp = tl.MappedPixels(raw, tree_type="PCB", gamma=True, brightness=0.5)
        mp[3] = (200, 100, 50)
        self.assertEqual(mp[3], (200, 100, 50), "read-back must be uncorrected (no double correction on fades)")
        self.assertEqual(raw[3], (0, 0, 0), "hardware untouched until show()")
        mp.show()
        self.assertEqual(raw[3], (tl.GAMMA_LUT_R[100], tl.GAMMA_LUT_G[50], tl.GAMMA_LUT_B[25]))
        self.assertEqual(raw.shown, 1)
        # fade via read-modify-write stays stable
        mp[3] = tuple(v // 2 for v in mp[3])
        self.assertEqual(mp[3], (100, 50, 25))

    def test_holz_mapping_preserved(self):
        raw = FakeStrip()
        mp = tl.MappedPixels(raw, tree_type="Holz", gamma=True)
        mp[18] = (255, 255, 255)
        mp.show()
        self.assertEqual(raw[31], tl.WHITE_BALANCE)
        self.assertEqual(raw[18], (0, 0, 0))

    def test_gamma_false_is_passthrough(self):
        raw = FakeStrip()
        mp = tl.MappedPixels(raw, tree_type="PCB")
        mp[1] = (10, 20, 30)
        self.assertEqual(raw[1], (10, 20, 30))

    def test_hsv_not_double_corrected(self):
        tl._gamma_in_wrapper = True
        try:
            self.assertEqual(tl.hsv_to_rgb_gamma(0.0, 1.0, 1.0), (255, 0, 0))
            self.assertEqual(tl.hsv_to_rgb_gamma(0.0, 1.0, 0.5)[0], 127)
        finally:
            tl._gamma_in_wrapper = False
        self.assertEqual(tl.hsv_to_rgb_gamma(0.0, 1.0, 0.5)[0], tl.GAMMA_LUT_R[127])


if __name__ == "__main__":
    unittest.main()
