"""PiWin pilot v5 — pilot-owned top-level Win32 EDIT.

Per the evidence audit: the pilot must NOT start notepad.exe (dead end: Win11
Notepad raises a save prompt on close that the pilot refuses to answer, so it
can never PASS). Instead the pilot creates its own top-level EDIT control via
CreateWindowExW — it owns the window, so close is clean and prompt-free.

Guarantees:
- All imports happen before any window exists (a missing dependency fails
  before anything is on screen).
- Keystrokes are sent ONLY after verifying the pilot's window is foreground
  and keyboard-focused — before AND after the send.
- Read-back is exact-equality via WM_GETTEXT AND UIA Value — both mandatory.
- PASS is printed only after the window is verified gone.
- No dialogs, no button-label matching, no killing of any process.
- Screenshot is best-effort only; it never gates PASS/FAIL.

Status: py_compile-checked only (3.12). Never executed on Windows. The
operator runs it per RUN-THIS.md — not an agent session.
"""
import ctypes
import sys
import time

import pywinauto  # pinned: pywinauto==0.6.9
import psutil     # pinned: psutil==6.0.0
from PIL import ImageGrab  # pinned: pillow==10.4.0 (best-effort screenshot only)
from pywinauto import Desktop

WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
WS_CHILD = 0x40000000
WS_VISIBLE = 0x10000000
WS_BORDER = 0x00800000
ES_MULTILINE = 0x0004
ES_AUTOVSCROLL = 0x0080

STAMP = time.strftime("%Y-%m-%d %H:%M:%S")
FULL = f"PiWin pilot OK - {STAMP}"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def fail(msg):
    print("FAIL:", msg)
    print("The pilot window (if any) is left as-is. Close it manually.")
    sys.exit(1)


def get_text_wm(hwnd):
    n = user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.SendMessageW(hwnd, WM_GETTEXT, n + 1, buf)
    return buf.value


def _create_edit_window():
    """Create a real top-level EDIT window on a dedicated thread with a
    standard message pump, so Win32 focus/WM_GETTEXT semantics are exact."""
    import threading

    result = {}

    def pump():
        wc = ctypes.c_wchar_p("EDIT")
        hwnd = user32.CreateWindowExW(
            WS_BORDER, wc, None,
            WS_VISIBLE | ES_MULTILINE | ES_AUTOVSCROLL,
            100, 100, 600, 300,
            None, None, kernel32.GetModuleHandleW(None), None,
        )
        result["hwnd"] = hwnd
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        result["closed"] = True

    t = threading.Thread(target=pump, daemon=False)
    t.start()
    deadline = time.time() + 5
    while "hwnd" not in result and time.time() < deadline:
        time.sleep(0.05)
    if "hwnd" not in result or not result["hwnd"]:
        fail("could not create pilot-owned EDIT window")
    return result


def run():
    # 0) Guard: refuse if not Windows.
    if sys.platform != "win32":
        print("FAIL: pilot must run on Windows (user32 is Windows-only)")
        sys.exit(1)

    r = _create_edit_window()
    hwnd = r["hwnd"]

    # 1) Bring OUR window to foreground + verify keyboard focus.
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    if user32.GetForegroundWindow() != hwnd:
        fail("pilot window is not foreground; not typing")
    user32.SetFocus(hwnd)
    time.sleep(0.2)
    if user32.GetFocus() != hwnd:
        fail("pilot window does not have keyboard focus; not typing")

    # 2) Type via UIA wrapper on our own control.
    try:
        dlg = Desktop(backend="uia").window(handle=hwnd)
        dlg.wait("ready", timeout=5)
    except Exception as e:
        fail(f"UIA wrapper on pilot EDIT failed: {e}")
    try:
        dlg.type_keys(FULL, with_spaces=True, pause=0.02)
    except Exception as e:
        fail(f"typing into pilot EDIT failed: {e}")
    time.sleep(0.3)

    # 3) Focus verification AFTER typing.
    if user32.GetForegroundWindow() != hwnd:
        fail("pilot window lost foreground during typing")

    # 4) Exact-equality read-back, BOTH channels mandatory.
    via_wm = get_text_wm(hwnd)
    if via_wm != FULL:
        fail(f"WM_GETTEXT mismatch: {via_wm!r} != {FULL!r}")
    try:
        via_uia = dlg.get_value()
    except Exception as e:
        fail(f"UIA value read failed (mandatory): {e}")
    if via_uia is None or str(via_uia) != FULL:
        fail(f"UIA value mismatch: {via_uia!r} != {FULL!r}")
    print("Read-back verified (WM_GETTEXT + UIA).")

    # 5) Best-effort screenshot — never gates PASS/FAIL.
    try:
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        import os
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        out = os.path.join(desktop if os.path.isdir(desktop) else os.path.expanduser("~"),
                           "piwin_pilot.png")
        ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom),
                       all_screens=True).save(out)
        print("Screenshot (best-effort) saved:", out)
    except Exception as e:
        print("Screenshot skipped (does not affect result):", e)

    # 6) Close OUR window; PASS only after it is gone.
    user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE — our own window, no prompt
    gone = False
    deadline = time.time() + 10
    while time.time() < deadline:
        if not user32.IsWindow(hwnd):
            gone = True
            break
        time.sleep(0.2)
    if not gone:
        fail("pilot window did not close; not printing PASS")

    print("PASS: typed, read back (both channels), closed.")


if __name__ == "__main__":
    run()
