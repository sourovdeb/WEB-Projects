import os
import sys
import time

import psutil  # pinned: psutil==6.0.0
from pywinauto import Application, Desktop

# Tested with: pywinauto==0.6.9, pillow==10.4.0, psutil==6.0.0 — unpinned installs are not supported

TEXT = "PiWin pilot OK"
STAMP = time.strftime("%Y-%m-%d %H:%M:%S")
FULL = f"{TEXT} - {STAMP}"


def desktop_dir():
    # NOTE: a Known Folder (SHGetKnownFolderPath) lookup was removed because its
    # GUID could not be verified before running. ~/Desktop fallback only; if the
    # screenshot is missing, check your home folder.
    d = os.path.join(os.path.expanduser("~"), "Desktop")
    return d if os.path.isdir(d) else os.path.expanduser("~")


def fail(msg):
    print("FAIL:", msg)
    print("Any window this script opened is left as-is. Close it manually.")
    sys.exit(1)


# 1) Refuse to start if Notepad is already running (shared-process risk).
procs = [p for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == "notepad.exe"]
if procs:
    fail(
        "Notepad is already running (pid(s): %s). Close every Notepad window "
        "first — this pilot refuses to run against a shared Notepad process."
        % [p.pid for p in procs]
    )

# 2) Start our own process and wait for it.
app = Application(backend="uia").start("notepad.exe")
pid = app.process
print(f"Started Notepad pid={pid} (fresh, no other Notepad was running).")

dlg = app.top_window()
dlg.wait("ready", timeout=10)
dlg.set_focus()
time.sleep(0.3)

# 3) Type, then READ THE TEXT BACK from this window's edit control.
dlg.type_keys(FULL, with_spaces=True, pause=0.02)
time.sleep(0.5)
edit = dlg.child_window(control_type="Edit", found_index=0)
readback = None
for getter in (
    lambda: edit.get_value(),
    lambda: getattr(edit.element_info, "value", None),
):
    try:
        v = getter()
        if v:
            readback = v
            break
    except Exception:
        continue
if not readback or FULL not in str(readback):
    fail(f"could not read typed text back (readback={readback!r}).")
print("Text verified in window:", str(readback)[:60], "...")

# 4) Window-only screenshot.
rect = dlg.rectangle()
from PIL import ImageGrab

out = os.path.join(desktop_dir(), "piwin_pilot.png")
ImageGrab.grab(
    bbox=(rect.left, rect.top, rect.right, rect.bottom), all_screens=True
).save(out)
print("Window screenshot saved:", out)

# 5) Close only if this PID owns exactly one window; handle its Don't Save.
wins = [w for w in Desktop(backend="uia").windows(process=pid)]
if len(wins) != 1:
    fail(f"pid {pid} owns {len(wins)} windows; expected exactly 1. Not closing.")
dlg.close()
time.sleep(0.8)
for _ in range(6):
    wins = [w for w in Desktop(backend="uia").windows(process=pid)]
    if not wins:
        break
    prompt = wins[0]
    answered = False
    for b in prompt.children(control_type="Button"):
        label = (b.window_text() or "").lower()
        if "don" in label or ("save" in label and ("don" in label or "nicht" in label)):
            b.click_input()
            answered = True
            break
    if not answered:
        for b in prompt.children(control_type="Button"):
            if (b.window_text() or "").lower() in ("no", "não", "nein", "non", "niet"):
                b.click_input()
                answered = True
                break
    time.sleep(0.6)

# 6) PASS only after the process is actually gone.
gone = False
for _ in range(20):
    if not psutil.pid_exists(pid):
        gone = True
        break
    try:
        psutil.Process(pid).status()
    except psutil.NoSuchProcess:
        gone = True
        break
    time.sleep(0.5)
if not gone:
    fail(f"pid {pid} still exists after close attempts. Not printing PASS.")

print("PASS: typed, read back, screenshot saved, and pid", pid, "is gone.")
