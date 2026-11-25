import json
import pathlib
import sys
import types
from unittest.mock import MagicMock

# Mock CircuitPython hardware modules for host testing
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))

mock_board = types.ModuleType("board")
mock_board.D0 = "D0"
mock_board.D5 = "D5"
mock_board.D6 = "D6"
mock_board.D10 = "D10"
sys.modules["board"] = mock_board

class MockNeoPixel:
    GRB = "GRB"
    def __init__(self, pin, n, **kwargs):
        self.buf = [(0, 0, 0)] * n
    def __setitem__(self, idx, val):
        self.buf[idx] = val
    def __getitem__(self, idx):
        return self.buf[idx]
    def __len__(self):
        return len(self.buf)
    def fill(self, val):
        self.buf = [val] * len(self.buf)
    def show(self):
        pass

mock_neopixel = types.ModuleType("neopixel")
mock_neopixel.NeoPixel = MockNeoPixel
mock_neopixel.GRB = "GRB"
sys.modules["neopixel"] = mock_neopixel

mock_pwmio = types.ModuleType("pwmio")
mock_pwmio.PWMOut = MagicMock()
sys.modules["pwmio"] = mock_pwmio

sys.modules["wifi"] = types.ModuleType("wifi")
sys.modules["socketpool"] = types.ModuleType("socketpool")

import importlib.util
spec = importlib.util.spec_from_file_location(
    "code_portal", str(pathlib.Path(__file__).resolve().parent / "code.portal.py")
)
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)


def test_all_13_patterns():
    px = MockNeoPixel("D10", 60)
    st = cp.TreeState()
    for p in range(13):
        st.pattern_id = p
        st.brightness = 80
        st.speed = 50
        cp.render_frame(px, st, 25)
        if p == 0:
            assert all(c == (0, 0, 0) for c in px.buf)
        elif p == 1:
            assert px.buf[0] == (204, 96, 24)
        else:
            assert sum(sum(c) for c in px.buf) > 0
    print("[PASS] test_all_13_patterns")


def test_rtttl_and_audio():
    for i in range(1, 5):
        notes = cp.parse_rtttl_notes(cp.RTTTL_SCORES[i])
        assert len(notes) > 5
        assert any(f > 0 for f, _ in notes)

    pwm = MagicMock()
    player = cp.AudioPlayer(pwm)
    st = cp.TreeState()
    st.melody_id = 1
    st.playback_state = 1
    st.volume = 75
    player.update(st, 100.0)
    assert pwm.duty_cycle > 0
    assert player.play_oneshot(523, 200, 50)
    print("[PASS] test_rtttl_and_audio")


def test_dns_and_http_portal():
    ap_ip = bytes([192, 168, 4, 1])
    query_a = (
        b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        b"\x07example\x03com\x00\x00\x01\x00\x01"
    )
    resp = cp.build_dns_response(query_a, ap_ip)
    assert len(resp) == len(query_a) + 16
    assert resp[7] == 1
    assert resp[-4:] == ap_ip

    query_aaaa = query_a[:-3] + b"\x1c\x00\x01"
    resp_aaaa = cp.build_dns_response(query_aaaa, ap_ip)
    assert len(resp_aaaa) == len(query_aaaa)
    assert resp_aaaa[7] == 0

    st = cp.TreeState()
    audio = cp.AudioPlayer(MagicMock())
    gz = pathlib.Path(__file__).resolve().with_name("web_ui.html.gz").read_bytes()

    # Probe redirect
    r_probe = cp.handle_http_request(b"GET /generate_204 HTTP/1.1\r\nHost: connectivitycheck.gstatic.com\r\n\r\n", st, audio, "192.168.4.1", 1, gz)
    assert b"302 Found" in r_probe and b"http://192.168.4.1/" in r_probe

    # Root UI
    r_root = cp.handle_http_request(b"GET / HTTP/1.1\r\nHost: 192.168.4.1\r\n\r\n", st, audio, "192.168.4.1", 1, gz)
    assert b"200 OK" in r_root and b"Content-Encoding: gzip" in r_root and r_root.endswith(gz)

    # Lighting POST (including tree_type)
    body = b'{"pattern_id":12,"palette_id":4,"brightness":90}'
    r_led = cp.handle_http_request(b"POST /api/lighting HTTP/1.1\r\nHost: 192.168.4.1\r\n\r\n" + body, st, audio, "192.168.4.1", 1, gz)
    assert b"200 OK" in r_led and st.pattern_id == 12 and st.palette_id == 4 and st.brightness == 90
    assert st.tree_type == "PCB" and b'"tree_type": "PCB"' in r_led

    r_holz = cp.handle_http_request(b'POST /api/lighting HTTP/1.1\r\nHost: 192.168.4.1\r\n\r\n{"tree_type":"Holz"}', st, audio, "192.168.4.1", 1, gz)
    assert b"200 OK" in r_holz and st.tree_type == "Holz" and b'"tree_type": "Holz"' in r_holz

    r_bad_tt = cp.handle_http_request(b'POST /api/lighting HTTP/1.1\r\nHost: 192.168.4.1\r\n\r\n{"tree_type":"Invalid"}', st, audio, "192.168.4.1", 1, gz)
    assert b"400 Bad Request" in r_bad_tt

    # Presets CRUD
    r_save = cp.handle_http_request(b'POST /api/presets HTTP/1.1\r\nHost: 192.168.4.1\r\n\r\n{"name":"CP Test"}', st, audio, "192.168.4.1", 1, gz)
    assert b"CP Test" in r_save
    assert len(st.presets) == 4
    print("[PASS] test_dns_and_http_portal")


def test_tree_type_pcb_vs_holz():
    import tannenbaum_layout as tl

    assert tl.get_tree_type() == "PCB"
    assert tl.map_pixel_index(18) == 18
    assert tl.map_pixel_index(18, "Holz") == 31
    assert tl.map_pixel_index(31, "Holz") == 18
    assert tl.map_pixel_index(0, "Holz") == 0
    assert tl.map_pixel_index(32, "Holz") == 32

    class DummyStrip(list):
        def __init__(self):
            super().__init__([(0, 0, 0)] * 60)
            self.brightness = 0.5
            self.auto_write = False

        def fill(self, c):
            for idx in range(len(self)):
                self[idx] = c

        def show(self):
            pass

    raw = DummyStrip()
    mapped = tl.wrap_pixels(raw)
    tl.set_tree_type("Holz")
    mapped[18] = (255, 0, 0)
    assert raw[31] == (255, 0, 0) and raw[18] == (0, 0, 0)
    tl.set_tree_type("PCB")

    # Also verify code.portal.render_frame reverses 18..31 for Holz
    st_pcb = cp.TreeState()
    st_pcb.pattern_id = 6  # Comet Chase
    st_pcb.brightness = 100
    st_pcb.tree_type = "PCB"
    px_pcb = DummyStrip()
    cp.render_frame(px_pcb, st_pcb, 10)

    st_holz = cp.TreeState()
    st_holz.pattern_id = 6
    st_holz.brightness = 100
    st_holz.tree_type = "Holz"
    px_holz = DummyStrip()
    cp.render_frame(px_holz, st_holz, 10)

    assert px_holz[:18] == px_pcb[:18]
    assert px_holz[18:32] == list(reversed(px_pcb[18:32]))
    assert px_holz[32:] == px_pcb[32:]
    print("[PASS] test_tree_type_pcb_vs_holz")


if __name__ == "__main__":
    test_all_13_patterns()
    test_rtttl_and_audio()
    test_dns_and_http_portal()
    test_tree_type_pcb_vs_holz()
    print("\nAll CircuitPython Captive Portal tests PASSED!")
