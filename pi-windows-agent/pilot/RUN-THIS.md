# PiWin Pilot — Run Instructions (final)

The project is **not functional as an assistant**. The dispatcher, UI host, and
helper do not exist. This pilot is the only runnable piece, and a PASS only
shows that Notepad can be driven on this machine. **Do not build PiWin yet.**

## Run the pilot

1. **Close every Notepad window, including ones in the taskbar.** The script
   refuses to start if `notepad.exe` is already running, and it does not kill
   processes.
2. Open PowerShell in the pilot folder (the one containing `pilot.py`).
3. Install the **pinned** packages, then run it:
   ```
   py -m pip install pywinauto==0.6.9 pillow==10.4.0 psutil==6.0.0
   py pilot.py
   ```
4. **Do not type or click while it runs** — it sends keystrokes to whatever
   window has focus.
5. Read the last lines:
   - `PASS: typed, read back, screenshot saved, and pid ... is gone.`
     This machine can drive Notepad. Check that `piwin_pilot.png` is on your
     Desktop (or home folder if Desktop was not found).
   - `FAIL:` — **stop. Leave the window alone and copy the full console text.**
     FAIL is the *expected* result on current Windows: Windows 11 Notepad often
     has no classic Edit control, so the read-back check stops and leaves the
     window open — that is the safe outcome. A PASS is not established for any
     machine until it runs there. **Do not weaken the check to force a pass.**

## After the run

Send the full console text back. That result decides the next change:
- A read-back failure on Windows 11 Notepad is useful data — it means classic
  Notepad is no longer a reliable pilot target and a different app (with a
  real UI Automation tree) must be chosen for the pilot.
- A PASS covers exactly this machine and this app. It does not open Gate G2
  for any second app and does not prove the dispatcher, which does not exist.

## Not allowed while the pilot is pending

Do not install the agent, do not start any extension, and do not run this
while any Notepad window is open.
