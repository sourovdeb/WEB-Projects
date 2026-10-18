# PiWin Pilot — Run Instructions (v4, audit-aligned)

**Project status:** the prototype exists (`prototype/`) — guard logic, UI
host, and 45 passing unit tests — but is **unwired**: the input layer raises
`NotPilotedYet` and nothing drives windows. This pilot is still the gate.

## What this pilot is

The pilot drives a top-level Win32 EDIT control owned by a process the pilot
started, verifies foreground+focus before and after sending keystrokes, reads
the text back by exact equality (WM_GETTEXT, plus UIA where available), and
closes only that window. **No dialog clicks** — if the window won't close,
that's a FAIL, and the window stays for you to inspect.

Compile-checked only. Its runtime behavior (pywinauto on a top-level EDIT,
`get_value`) is **unverified until you run it**. A FAIL here is normal and
useful; do not weaken the checks to force a pass.

## Run

1. Close every Notepad window, including taskbar ones (the pilot refuses if
   `notepad.exe` is already running).
2. Open PowerShell in the `pilot/` folder.
3. Install pinned packages and run (explicit `python` path — `py` may default
   to a Python 3.11 that isn't installed; use the interpreter that has the
   packages):
   ```
   python -m pip install pywinauto==0.6.9 psutil==6.0.0
   python pilot.py
   ```
   If `python` isn't on PATH, try `py -3.12` or the full path to your Python.
4. **Do not type or click while it runs** — keystrokes go to the foreground
   window, and the pilot verifies its own window is foreground before typing.
5. Read the last lines:
   - `PASS: typed, read back, and closed pid ...` — this machine can drive
     an EDIT control via UIA. Paste the output back.
   - `FAIL: ...` — **stop, leave the window alone, paste the full console
     text.** Every FAIL names exactly which check failed.

## Scope of a PASS

This machine, this EDIT control, this run. A PASS does not open Gate G2 for
any other app, does not prove the dispatcher end-to-end (unit tests prove the
guard logic; the wiring does not exist yet), and does not make PiWin usable —
`execute()` stays unimplemented until a PASS is in hand and the target app has
its own recorded run.

## Honest gaps

- The pilot has never been executed anywhere (compile-checked only).
- The helper and UI host use target field names (`window`/`control`) that
  predate the audit; both are internally consistent but unwired to each other
  or to Pi. Wiring happens only after the pilot passes.
- Two ad-hoc artifacts at the repo root (`hash_cases.json`, `py_hashes.json`)
  are leftovers; the authoritative vectors are
  `prototype/tests/hash_vectors.json`.
