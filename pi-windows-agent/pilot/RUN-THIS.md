# PiWin GUI-Control Pilot (Step 6) — v3

One script: `pilot.py`. Run it on your Windows PC **with every Notepad window
closed** — it refuses to start if any `notepad.exe` process exists, to avoid
sharing a process with your unsaved work.

```
pip install pywinauto pillow psutil
python pilot.py
```

Version pins (install exactly these; unpinned installs are not supported):
`pywinauto==0.6.9`, `pillow==10.4.0`, `psutil==6.0.0`.

**What it does:** opens ONE fresh Notepad process, types "PiWin pilot OK -
<timestamp>" into it, reads the text back from that window to verify, saves a
screenshot of that window only, then closes that window (handling its own
Don't Save prompt) — but only if that PID owns exactly one window.

**PASS means** the console ends with:
`PASS: typed, read back, screenshot saved, and pid <pid> is gone.`
PASS is printed only after psutil confirms the process no longer exists. Any
`FAIL:` line means exactly what it says; the window is left as-is.

**Scope of a PASS:** it covers UI Automation driving classic Notepad on that
machine, that run. It does NOT open Gate G2 for any second app (the target app
needs its own recorded run), and it does not prove the dispatcher guard, which
does not exist yet.
