"""PiWin pilot — prove the input layer on a pilot-owned Win32 EDIT window.

This pilot does NOT touch Notepad or any installed application. It creates
its own top-level Win32 EDIT control (a real UI Automation tree), types into
it through pywinauto, reads the text back through both Win32 and UI
Automation, takes a window-only screenshot, and destroys the window. There
are no dialogs to dismiss and no button labels to match.

PASS is printed only if ALL of these hold:
  1. the text read back EQUALS the text typed (exact match, both via
     WM_GETTEXT and via the UI Automation value pattern),
  2. the pilot's EDIT was the foreground window and the focused window
     immediately before AND after the keystrokes were sent, and
  3. the window is gone afterward.

Every dependency is imported before any window is created, so a missing
package fails the pilot before it can do anything. The pilot refuses to send
a single keystroke unless its own window is foreground at send time.

Run it from your own terminal, not from an agent session, and do not type
or click while it runs. Instructions: pilot/RUN-THIS.md.
"""
import ctypes
import os
import sys
import time
from ctypes import wintypes

if sys.platform != "win32":
    sys.exit("FAIL: this pilot runs on Windows only.")

try:
    from pywinauto import Application
    from PIL import ImageGrab
except ImportError as exc:
    sys.exit(
        f"FAIL: missing dependency ({exc}). Install the pinned packages "
        "first — see RUN-THIS.md."
    )

# --- Win32 via ctypes (no extra dependencies) -----------------------------
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
ES_AUTOHSCROLL = 0x0080
SW_SHOW = 5
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
PM_REMOVE = 0x0001

user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = (
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
)
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.ShowWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetFocus.restype = wintypes.HWND
user32.IsWindow.argtypes = (wintypes.HWND,)
user32.IsWindow.restype = wintypes.BOOL
user32.DestroyWindow.argtypes = (wintypes.HWND,)
user32.DestroyWindow.restype = wintypes.BOOL
user32.SendMessageW.argtypes = (
    wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
)
user32.SendMessageW.restype = wintypes.LRESULT
user32.PeekMessageW.argtypes = (
    ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT,
    wintypes.UINT, wintypes.UINT,
)
user32.PeekMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = (ctypes.POINTER(wintypes.MSG),)
user32.TranslateMessage.restype = wintypes.BOOL
user32.DispatchMessageW.argtypes = (ctypes.POINTER(wintypes.MSG),)
user32.DispatchMessageW.restype = wintypes.LRESULT
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)

TEXT = "PiWin pilot OK " + time.strftime("%Y-%m-%d %H%M%S")
HWND = None


def pump(seconds):
    """Process this thread's messages so the EDIT control can paint/react."""
    msg = wintypes.MSG()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.01)


def desktop_dir():
    d = os.path.join(os.path.expanduser("~"), "Desktop")
    return d if os.path.isdir(d) else os.path.expanduser("~")


def cleanup():
    if HWND is not None and user32.IsWindow(HWND):
        user32.DestroyWindow(HWND)
        pump(0.2)
        if user32.IsWindow(HWND):
            print("WARNING: the pilot window could not be destroyed; close it manually.")


def fail(msg):
    print("FAIL:", msg)
    cleanup()
    print("The pilot window (if any) was its own; nothing else was touched.")
    sys.exit(1)


# 1) Create the pilot-owned EDIT window. The system EDIT class needs no
#    registration and exposes a real UI Automation tree.
hInstance = kernel32.GetModuleHandleW(None)
HWND = user32.CreateWindowExW(
    0, "EDIT", "",
    WS_OVERLAPPEDWINDOW | WS_VISIBLE | ES_AUTOHSCROLL,
    100, 100, 560, 220,
    None, None, hInstance, None,
)
if not HWND:
    fail(f"CreateWindowExW failed (GetLastError={ctypes.get_last_error()}).")
print("Pilot window created: a pilot-owned Win32 EDIT control (no other app is involved).")
user32.ShowWindow(HWND, SW_SHOW)
pump(0.5)

# 2) Attach pywinauto's UIA engine to it.
app = Application(backend="uia").connect(handle=HWND)
edit = app.window(handle=HWND)
edit.wait("ready", timeout=10)

# 3) Make the pilot's EDIT the foreground window; refuse to type otherwise.
for _ in range(20):
    user32.SetForegroundWindow(HWND)
    pump(0.1)
    if user32.GetForegroundWindow() == HWND:
        break
else:
    fail("could not make the pilot's EDIT the foreground window; no keystroke was sent.")

edit.set_focus()
pump(0.1)
fg_before = user32.GetForegroundWindow()
focus_before = user32.GetFocus()
if fg_before != HWND or focus_before != HWND:
    fail("foreground/focus check failed before typing; no keystroke was sent.")
print("Foreground and keyboard focus verified on the pilot's EDIT. Typing...")

# 4) Type the text (real keystroke injection through pywinauto).
edit.type_keys(TEXT, with_spaces=True, pause=0.02)
pump(0.5)
fg_after = user32.GetForegroundWindow()
focus_after = user32.GetFocus()
if fg_after != HWND or focus_after != HWND:
    fail("foreground/focus was lost during typing; refusing to trust the result.")

# 5) Read the text back — exact equality, via BOTH Win32 and UI Automation.
length = user32.SendMessageW(HWND, WM_GETTEXTLENGTH, 0, 0)
buf = ctypes.create_unicode_buffer(length + 1)
user32.SendMessageW(HWND, WM_GETTEXT, length + 1, ctypes.addressof(buf))
win32_text = buf.value
try:
    uia_text = edit.get_value()
except Exception as exc:  # noqa: BLE001 — any UIA read failure is a pilot FAIL
    fail(f"UI Automation read-back failed ({exc!r}); the UIA tree did not yield the text.")
if uia_text is None:
    fail("UI Automation read-back returned no value for the Edit control.")
uia_text = str(uia_text)

print("WM_GETTEXT read-back:", win32_text)
print("UIA ValuePattern read-back:", uia_text)
if win32_text != TEXT:
    fail(f"Win32 read-back does not equal the typed text exactly (typed {TEXT!r}).")
if uia_text != TEXT:
    fail("UIA read-back does not equal the typed text exactly.")

# 6) Window-only screenshot (best effort — not a PASS criterion).
try:
    rect = edit.rectangle()
    out = os.path.join(desktop_dir(), "piwin_pilot.png")
    ImageGrab.grab(
        bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True
    ).save(out)
    print("Window screenshot saved:", out)
except Exception as exc:  # noqa: BLE001 — the screenshot never gates PASS/FAIL
    print(f"WARNING: window screenshot failed ({exc!r}); not a PASS criterion.")

# 7) Destroy the pilot's own window and require it gone.
user32.DestroyWindow(HWND)
pump(0.3)
if user32.IsWindow(HWND):
    fail("the pilot window still exists after DestroyWindow.")

print("PASS: read-back equaled the typed text exactly (Win32 and UIA), the")
print(f"pilot's EDIT was foreground at send time, and the window is gone. Text: {TEXT}")
