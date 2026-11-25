// CircuitPython-compatible browser runtime powered by Pyodide
(function () {
  const PYODIDE_INDEX = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";

  class SimRuntime {
    constructor({ onLeds, onOnboardLed, onPrint, onStatus }) {
      this.onLeds = onLeds;
      this.onOnboardLed = onOnboardLed;
      this.onPrint = onPrint;
      this.onStatus = onStatus;
      this.pyodide = null;
      this.initPromise = null;
      this.runId = 0;
      this.running = false;
      this.buttons = { D5: false, D6: false };
      this.treeType = "PCB";
    }

    async init() {
      if (this.pyodide) return this.pyodide;
      if (this.initPromise) return this.initPromise;

      this.initPromise = (async () => {
        this.onStatus("loading", "Loading Python runtime…");
        if (typeof loadPyodide !== "function") {
          throw new Error("Pyodide script failed to load. Check your internet connection.");
        }
        const pyodide = await loadPyodide({ indexURL: PYODIDE_INDEX });

        // Write CircuitPython helper libraries into virtual FS
        if (window.XMAS_PY_LIBS) {
          for (const [filename, content] of Object.entries(window.XMAS_PY_LIBS)) {
            pyodide.FS.writeFile(`/home/pyodide/${filename}`, content);
          }
        }

        // Register JS callbacks on globalThis for Python shim
        window.__simBridge = {
          getButton: (name) => Boolean(this.buttons[name]),
          getRunId: () => this.runId,
          updateLeds: (flatColors, brightness) => {
            this.onLeds(flatColors, brightness);
          },
          updateOnboard: (r, g, b, brightness) => {
            this.onOnboardLed(r, g, b, brightness);
          },
          writeStdout: (text) => {
            this.onPrint(text, "stdout");
          },
          writeStderr: (text) => {
            this.onPrint(text, "stderr");
          },
        };

        // Install CircuitPython shims + AST transformer in Python
        await pyodide.runPythonAsync(PYTHON_BOOTSTRAP);
        this.pyodide = pyodide;
        this.onStatus("ready", "Ready");
        return pyodide;
      })();

      return this.initPromise;
    }

    setButton(name, pressed) {
      this.buttons[name] = Boolean(pressed);
    }

    setTreeType(treeType) {
      this.treeType = treeType === "Holz" ? "Holz" : "PCB";
      if (this.pyodide) {
        try {
          this.pyodide.globals.set("_SIM_TREE_TYPE", this.treeType);
          this.pyodide.runPython(
            "import sys\nif 'tannenbaum_layout' in sys.modules:\n    sys.modules['tannenbaum_layout'].set_tree_type(_SIM_TREE_TYPE)\n"
          );
        } catch (_) {
          // Ignore if layout module is not loaded yet
        }
      }
    }

    stop() {
      this.runId += 1;
      this.running = false;
      this.onStatus("stopped", "Stopped");
    }

    async run(sourceCode) {
      const pyodide = await this.init();
      this.runId += 1;
      const myRunId = this.runId;
      this.running = true;
      this.onStatus("running", "Running");

      try {
        pyodide.globals.set("_SIM_TREE_TYPE", this.treeType);
        await pyodide.runPythonAsync(
          "import tannenbaum_layout as _tl\n_tl.set_tree_type(_SIM_TREE_TYPE)\n"
        );
        pyodide.globals.set("_USER_SOURCE_CODE", sourceCode);
        pyodide.globals.set("_TARGET_RUN_ID", myRunId);
        await pyodide.runPythonAsync("_sim_execute(_USER_SOURCE_CODE, _TARGET_RUN_ID)");
        if (this.runId === myRunId) {
          this.running = false;
          this.onStatus("finished", "Finished");
        }
      } catch (err) {
        if (this.runId === myRunId) {
          this.running = false;
          this.onStatus("error", "Error");
          this.onPrint(String(err), "stderr");
        }
      }
    }
  }

  const PYTHON_BOOTSTRAP = `
import sys
import ast
import time as _real_time
import asyncio
import types
from js import __simBridge as _bridge

class _SimStopped(BaseException):
    pass

class _ConsoleWriter:
    def __init__(self, is_err=False):
        self.is_err = is_err
        self._buf = ""

    def write(self, s):
        if not s:
            return 0
        self._buf += s
        while "\\n" in self._buf:
            line, self._buf = self._buf.split("\\n", 1)
            if self.is_err:
                _bridge.writeStderr(line)
            else:
                _bridge.writeStdout(line)
        return len(s)

    def flush(self):
        if self._buf:
            if self.is_err:
                _bridge.writeStderr(self._buf)
            else:
                _bridge.writeStdout(self._buf)
            self._buf = ""

sys.stdout = _ConsoleWriter(False)
sys.stderr = _ConsoleWriter(True)

# --- 1. board shim ---
class _Pin:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"board.{self.name}"

class _BoardModule(types.ModuleType):
    def __init__(self):
        super().__init__("board")
        self._pins = {}
        for name in (
            "D0","D1","D2","D3","D4","D5","D6","D7","D8","D9","D10",
            "A0","A1","A2","A3","SCK","MOSI","MISO","TX","RX","SDA","SCL",
            "NEOPIXEL","NEOPIXEL_POWER","LED","BUTTON"
        ):
            pin = _Pin(name)
            self._pins[name] = pin
            setattr(self, name, pin)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._pins:
            self._pins[name] = _Pin(name)
        return self._pins[name]

sys.modules["board"] = _BoardModule()

# --- 2. digitalio shim ---
class _Direction:
    INPUT = 0
    OUTPUT = 1

class _Pull:
    NONE = None
    UP = 1
    DOWN = 2

class _DigitalInOut:
    def __init__(self, pin):
        self.pin = pin
        self._pin_name = getattr(pin, "name", str(pin))
        self._direction = _Direction.INPUT
        self._pull = None
        self._out_val = False

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, val):
        self._direction = val

    @property
    def pull(self):
        return self._pull

    @pull.setter
    def pull(self, val):
        self._pull = val

    def switch_to_input(self, pull=None):
        self._direction = _Direction.INPUT
        self._pull = pull

    def switch_to_output(self, value=False, drive_mode=None):
        self._direction = _Direction.OUTPUT
        self._out_val = bool(value)

    @property
    def value(self):
        if self._direction == _Direction.OUTPUT:
            return self._out_val
        # Emulate active-low hardware buttons on D5 and D6
        if self._pin_name in ("D5",):
            return not _bridge.getButton("D5")
        if self._pin_name in ("D6",):
            return not _bridge.getButton("D6")
        # All other pins: idle HIGH if Pull.UP, else LOW
        if self._pull == _Pull.UP:
            return True
        return False

    @value.setter
    def value(self, val):
        self._out_val = bool(val)

    def deinit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()

_digitalio = types.ModuleType("digitalio")
_digitalio.Direction = _Direction
_digitalio.Pull = _Pull
_digitalio.DigitalInOut = _DigitalInOut
sys.modules["digitalio"] = _digitalio

# --- 3. neopixel shim ---
def _norm_color(c):
    if isinstance(c, int):
        return ((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)
    if len(c) >= 3:
        return (max(0, min(255, int(c[0]))), max(0, min(255, int(c[1]))), max(0, min(255, int(c[2]))))
    return (0, 0, 0)

class _NeoPixel:
    def __init__(self, pin, n, *, bpp=3, brightness=1.0, auto_write=True, pixel_order=None):
        self.pin = pin
        self.n = int(n)
        self.bpp = bpp
        self.brightness = float(brightness)
        self.auto_write = bool(auto_write)
        self.pixel_order = pixel_order
        self._pixels = [(0, 0, 0)] * self.n
        self._is_onboard = getattr(pin, "name", "") == "NEOPIXEL"

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        return self._pixels[idx]

    def __setitem__(self, idx, val):
        if isinstance(idx, slice):
            start, stop, step = idx.indices(self.n)
            vals = list(val)
            for k, i in enumerate(range(start, stop, step)):
                self._pixels[i] = _norm_color(vals[k])
        else:
            self._pixels[idx] = _norm_color(val)
        if self.auto_write:
            self._push_to_js()

    def fill(self, color):
        c = _norm_color(color)
        for i in range(self.n):
            self._pixels[i] = c
        if self.auto_write:
            self._push_to_js()

    def _push_to_js(self):
        if self._is_onboard:
            r, g, b = self._pixels[0] if self.n > 0 else (0, 0, 0)
            _bridge.updateOnboard(r, g, b, self.brightness)
        else:
            flat = []
            for r, g, b in self._pixels:
                flat.append(r)
                flat.append(g)
                flat.append(b)
            _bridge.updateLeds(flat, self.brightness)

    async def show(self):
        _sim_check_abort()
        self._push_to_js()
        await asyncio.sleep(0.012)
        _sim_check_abort()

    def deinit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()

_neopixel = types.ModuleType("neopixel")
_neopixel.RGB = "RGB"
_neopixel.GRB = "GRB"
_neopixel.RGBW = "RGBW"
_neopixel.GRBW = "GRBW"
_neopixel.NeoPixel = _NeoPixel
sys.modules["neopixel"] = _neopixel

# --- 4. rainbowio shim ---
def _colorwheel(pos):
    pos = int(pos) & 255
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

_rainbowio = types.ModuleType("rainbowio")
_rainbowio.colorwheel = _colorwheel
sys.modules["rainbowio"] = _rainbowio

# --- 5. Cooperative runtime & AST transformer ---
_current_run_id = 0
_last_yield_t = 0.0

def _sim_check_abort():
    if _bridge.getRunId() != _current_run_id:
        raise _SimStopped()

async def _sim_yield(force=False):
    global _last_yield_t
    _sim_check_abort()
    now = _real_time.monotonic()
    if force or (now - _last_yield_t) >= 0.008:
        _last_yield_t = now
        await asyncio.sleep(0)
        _sim_check_abort()

async def _sim_sleep(seconds):
    _sim_check_abort()
    if seconds <= 0:
        await _sim_yield(force=True)
        return
    end = _real_time.monotonic() + float(seconds)
    while True:
        _sim_check_abort()
        rem = end - _real_time.monotonic()
        if rem <= 0:
            break
        await asyncio.sleep(min(rem, 0.05))
    _sim_check_abort()

class _AsyncTransformer(ast.NodeTransformer):
    def __init__(self, async_funcs, sleep_names):
        self.async_funcs = async_funcs
        self.sleep_names = sleep_names
        self.in_async = True  # top-level is wrapped in async def __sim_main__

    def _is_async_call(self, node):
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "show":
            return True
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "time" and func.attr == "sleep":
                return True
        if isinstance(func, ast.Name):
            if func.id in self.sleep_names or func.id in self.async_funcs:
                return True
        return False

    def visit_FunctionDef(self, node):
        prev = self.in_async
        is_async = node.name in self.async_funcs
        self.in_async = is_async
        self.generic_visit(node)
        self.in_async = prev
        if is_async:
            return ast.AsyncFunctionDef(
                name=node.name,
                args=node.args,
                body=node.body,
                decorator_list=node.decorator_list,
                returns=node.returns,
                type_comment=node.type_comment,
            )
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if self._is_async_call(node):
            # Rewrite time.sleep(...) / sleep(...) to _sim_sleep(...)
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "time" and node.func.attr == "sleep":
                    node.func = ast.Name(id="_sim_sleep", ctx=ast.Load())
            elif isinstance(node.func, ast.Name) and node.func.id in self.sleep_names:
                node.func = ast.Name(id="_sim_sleep", ctx=ast.Load())
            return ast.Await(value=node)
        return node

    def visit_While(self, node):
        self.generic_visit(node)
        if self.in_async:
            yield_stmt = ast.Expr(
                value=ast.Await(
                    value=ast.Call(
                        func=ast.Name(id="_sim_yield", ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    )
                )
            )
            node.body.append(yield_stmt)
        return node

def _find_async_functions(tree):
    sleep_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "time":
            for alias in node.names:
                if alias.name == "sleep":
                    sleep_names.add(alias.asname or alias.name)

    direct_async = set()
    call_graph = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            calls = set()
            is_dir = False
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    f = sub.func
                    if isinstance(f, ast.Attribute) and f.attr == "show":
                        is_dir = True
                    elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "time" and f.attr == "sleep":
                        is_dir = True
                    elif isinstance(f, ast.Name):
                        if f.id in sleep_names:
                            is_dir = True
                        else:
                            calls.add(f.id)
            if is_dir:
                direct_async.add(node.name)
            call_graph[node.name] = calls

    async_funcs = set(direct_async)
    changed = True
    while changed:
        changed = False
        for fname, callees in call_graph.items():
            if fname not in async_funcs and (callees & async_funcs):
                async_funcs.add(fname)
                changed = True
    return async_funcs, sleep_names

async def _sim_execute(source, run_id):
    global _current_run_id, _last_yield_t
    _current_run_id = run_id
    _last_yield_t = _real_time.monotonic()

    # Reset LEDs before starting
    _bridge.updateLeds([0] * 180, 1.0)
    _bridge.updateOnboard(0, 0, 0, 1.0)

    tree = ast.parse(source, filename="code.py")
    async_funcs, sleep_names = _find_async_functions(tree)
    tree = _AsyncTransformer(async_funcs, sleep_names).visit(tree)

    main_fn = ast.AsyncFunctionDef(
        name="__sim_main__",
        args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=tree.body,
        decorator_list=[],
        returns=None,
    )
    wrapper = ast.Module(body=[main_fn], type_ignores=[])
    ast.fix_missing_locations(wrapper)

    env = {
        "__name__": "__main__",
        "_sim_sleep": _sim_sleep,
        "_sim_yield": _sim_yield,
    }
    code_obj = compile(wrapper, "code.py", "exec")
    exec(code_obj, env)
    try:
        await env["__sim_main__"]()
    except _SimStopped:
        pass
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
`;

  window.SimRuntime = SimRuntime;
})();
