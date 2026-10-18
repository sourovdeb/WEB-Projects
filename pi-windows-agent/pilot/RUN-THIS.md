# PiWin Pilot — Run Instructions (v5, pilot-owned EDIT)

**Run this yourself, on your Windows PC — not from an agent session, not on a
machine with anything you can't afford to lose focus.** The pilot types into
whatever window is foreground, after verifying its own window is foreground;
while it runs, do not touch the keyboard or mouse.

## What this pilot is (and is not)

The pilot creates its **own top-level Win32 EDIT control** (CreateWindowExW on
a dedicated pump thread). It does not start Notepad, does not touch any other
process, sends keystrokes only after verifying foreground + keyboard focus
(before and after), reads the text back by **exact equality via WM_GETTEXT
AND UIA — both mandatory**, saves a best-effort screenshot (never gates the
result), closes its own window, and prints PASS only after the window is
verified gone. No dialogs, no button-label matching, no prompts.

**It has never been executed anywhere (py_compile-checked only under
3.12).** A FAIL is a real result; do not weaken any check to force a pass.

## Run

1. Open PowerShell in this `pilot/` folder.
2. Install pinned packages and run (explicit `python` — `py` may default to a
   missing 3.11; use the interpreter that has the packages):
   ```
   python -m pip install pywinauto==0.6.9 pillow==10.4.0 psutil==6.0.0
   python pilot.py
   ```
3. Do not type or click until it finishes.
4. Read the last lines:
   - `PASS: typed, read back (both channels), closed.` — this machine's UIA
     can drive and read back a Win32 EDIT. (Screenshot is best-effort; its
     absence is not a failure.)
   - `FAIL: ...` — stop; the pilot names exactly which check failed. Copy the
     **full console text** and paste it back in the chat.

## Scope of a PASS

This machine, this EDIT control, this run. A PASS does not by itself open
Gate G2 for your real target app (that app needs its own recorded run for
`tested-apps.json`) and does not prove the dispatcher end-to-end — the guard's
logic is unit-tested (45 passing); the wiring does not exist yet.

## After a PASS / FAIL

- **PASS:** the helper's `execute()` gets implemented against pywinauto; the
  UI host, Pi gate, and helper get wired into an installable folder.
- **FAIL:** the FAIL line names the broken step (window creation, focus,
  typing, WM_GETTEXT, UIA read, close). That decides the next change; nothing
  else gets touched.
