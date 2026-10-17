import getpass
import time

from pywinauto import Application
from PIL import ImageGrab

PID_NOTE = "This pilot opens ONE Notepad process, verifies the text inside THAT "
"window only, and closes THAT window only. Other Notepad windows are never touched."
TEXT = "PiWin pilot OK"
STAMP = time.strftime("%Y-%m-%d %H:%M:%S")
FULL = f"{TEXT} - {STAMP}"

app = Application(backend="uia").start("notepad.exe")
pid = app.process  # type: ignore[attr-defined]
print(f"Started Notepad pid={pid}. {PID_NOTE}")

dlg = app.top_window()
dlg.wait("ready", timeout=10)

# Type into only this window, via its handle.
dlg.set_focus()
dlg.type_keys(FULL, with_spaces=True, pause=0.02)
time.sleep(0.5)

# READ THE TEXT BACK from this window's edit control; PASS depends on it.
edit = dlg.child_window(control_type="Edit", found_index=0)
readback = edit.get_value() if hasattr(edit, "get_value") else None
if readback is None:
    texts = [t for t in [c.window_text() for c in edit.iter_children()] if t]
    readback = texts[0] if texts else None
if readback is None and edit.element_info is not None:
    readback = getattr(edit.element_info, "value", None) or (
        getattr(edit.element_info, "name", None)
    )
if readback is None or FULL not in str(readback):
    print("FAIL: could not read the typed text back from the edit control.")
    print(f"  readback={readback!r}")
    print("  Notepad left open for inspection. Close it manually (Don't Save).")
    raise SystemExit(1)
print("Read-back verified:", readback[:60], "...")

# Screenshot ONLY this window's rectangle.
rect = dlg.rectangle()
shot = ImageGrab.grab(
    bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True
)
import os

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
if not os.path.isdir(desktop):  # OneDrive / localized fallback
    desktop = os.path.expanduser("~")
out = os.path.join(desktop, "piwin_pilot.png")
shot.save(out)
print("Window-only screenshot saved:", out)

# Close THIS window only; if a save prompt appears for it, answer Don't Save.
dlg.close()
time.sleep(0.5)
for _ in range(3):
    if not app.windows():
        break
    save_dlg = None
    for w in app.windows():
        if "save" in (w.window_text() or "").lower():
            save_dlg = w
            break
    if save_dlg is None:
        # Classic prompt: button names vary by locale; find "Don't Save"-like button
        for w in app.windows():
            for b in w.children(control_type="Button"):
                if "don" in (b.window_text() or "").lower() or "niet" in (
                    b.window_text() or ""
                ).lower():
                    b.click_input()
                    time.sleep(0.5)
    else:
        save_dlg.print_control_identifiers()
    time.sleep(0.5)

try:
    app.kill(soft=False)  # last resort: only kills this pid's process
except Exception:
    pass
print("PASS: typed, read back, screenshot, and closed pid", pid)
