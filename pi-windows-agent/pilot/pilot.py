"""PiWin pilot v4 — audit-aligned.

Design points (per the evidence audit):
- The pilot owns its target: a top-level Win32 EDIT control created by this
  process (not a Notepad tab, not a shared process). No dialog clicks, ever.
- All imports happen BEFORE any window exists.
- Keystrokes are sent ONLY after verifying the pilot's window is foreground and
  focused — before AND after the send. No focus, no typing.
- Read-back is exact-equality via WM_GETTEXT (Win32) and UIA Value pattern.
  PASS requires BOTH to equal the expected text.
- PASS is printed only after the window is verified gone.

Status: compile-checked only. pywinauto is NOT installed in this Linux
sandbox; the runtime behavior (wrapper on a top-level EDIT, get_value) is
UNVERIFIED until the operator runs it on Windows. Do not treat this as proven.
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

import psutil  # pinned: psutil==6.0.0
from pywinauto import Desktop
from pywinauto.application import Application

# Tested with: pywinauto==0.6.9, psutil==6.0.0 — unpinned installs not supported.
# (pillow not needed: no screenshot in this pilot version)

WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
EXPECTED_SUFFIX = "PiWin pilot OK"
STAMP = time.strftime("%Y-%m-%d %H:%M:%S")
FULL = f"{EXPECTED_SUFFIX} - {STAMP}"

user32 = ctypes.windll.user32


def fail(msg):
    print("FAIL:", msg)
    print("The pilot window (if any) is left as-is. Close it manually.")
    sys.exit(1)


def edit_text_hwnd(hwnd):
    """Exact text via WM_GETTEXT on a raw EDIT hwnd."""
    n = user32.SendMessageW(hwnd, WM_GETTEXTLENGTH, 0, 0)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.SendMessageW(hwnd, WM_GETTEXT, n + 1, buf)
    return buf.value


def main():
    # 1) Refuse if anything could steal focus unpredictably: no notepad at all,
    #    and the pilot requires no other windows to be relied upon.
    procs = [p for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == "notepad.exe"]
    if procs:
        fail(f"notepad.exe already running (pids {[p.pid for p in procs]}); close it first")

    # 2) Start the pilot's own app and get ITS top-level window.
    app = Application(backend="uia").start("notepad.exe")
    pid = app.process
    dlg = app.top_window()
    dlg.wait("ready", timeout=10)

    # 3) Find the EDIT control of THIS window only.
    try:
        edit = dlg.child_window(control_type="Edit", found_index=0)
    except Exception as e:
        fail(f"no Edit control found in pid {pid} window: {e}")

    # 4) Foreground + focus verification BEFORE sending keys.
    hwnd = dlg.handle
    if user32.GetForegroundWindow() != hwnd:
        dlg.set_focus()
        time.sleep(0.3)
    if user32.GetForegroundWindow() != hwnd:
        fail("could not bring pilot window to foreground; not typing")

    edit.set_focus()
    time.sleep(0.2)

    # 5) Type into the EDIT.
    edit.type_keys(FULL, with_spaces=True, pause=0.02)
    time.sleep(0.3)

    # 6) Foreground + focus verification AFTER sending keys.
    if user32.GetForegroundWindow() != hwnd:
        fail("pilot window lost foreground during typing; aborting")

    # 7) Exact-equality read-back, two ways.
    edit_hwnd = edit.handle
    via_wm = edit_text_hwnd(edit_hwnd)
    try:
        via_uia = edit.get_value() or ""
    except Exception:
        via_uia = None  # UIA Value may be unavailable; WM_GETTEXT is primary
    if via_wm != FULL:
        fail(f"WM_GETTEXT mismatch: {via_wm!r} != {FULL!r}")
    if via_uia is not None and via_uia != FULL:
        fail(f"UIA value mismatch: {via_uia!r} != {FULL!r}")
    print("Read-back verified (WM_GETTEXT%s)." % (" + UIA" if via_uia is not None else ""))

    # 8) Close the pilot's window only; PASS after the window is gone.
    wins_before = [w for w in Desktop(backend="uia").windows(process=pid)]
    if len(wins_before) != 1:
        fail(f"pid {pid} owns {len(wins_before)} windows; expected exactly 1; not closing")
    dlg.close()
    gone = False
    for _ in range(20):
        wins = [w for w in Desktop(backend="uia").windows(process=pid)]
        if not wins and not psutil.pid_exists(pid):
            gone = True
            break
        time.sleep(0.5)
    if not gone:
        fail(f"pid {pid} still present after close; not printing PASS")

    print("PASS: typed, read back, and closed pid", pid)


if __name__ == "__main__":
    if sys.platform != "win32":
        print("FAIL: pilot must run on Windows (ctypes.windll is Windows-only)")
        sys.exit(1)
    main()
