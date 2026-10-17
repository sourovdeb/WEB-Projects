# PiWin GUI-Control Pilot (Step 6 / Gate G2)

**Goal:** prove Windows GUI control on YOUR PC before we build anything on top of it.
Two independent options; run Option A first. Everything here is a one-time test.

## Option A — Python + pywinauto (recommended)

1. Install Python from python.org (check "Add to PATH" during install).
2. Open a Command Prompt and run:
   ```
   pip install pywinauto pillow
   ```
3. Save `pilot_a.py` (in this folder) to your Desktop.
4. Double-click `pilot_a.py` (or run `python pilot_a.py`).

**What you should see:** Notepad opens, the text
`PiWin pilot OK - <timestamp>` is typed into it, and a screenshot
`piwin_pilot.png` appears on your Desktop. The script closes Notepad without saving.

## Option B — PowerShell + Windows UI Automation (no install)

1. Save `pilot_b.ps1` (in this folder) to your Desktop.
2. Right-click it → **Run with PowerShell**.
   (If blocked: open PowerShell, `cd Desktop`, `powershell -ExecutionPolicy Bypass -File .\pilot_b.ps1`)

**What you should see:** Notepad opens and the same text is typed into it.

## Report back

Tell me which option(s) ran and what happened — copy any error text. If both fail,
we stop (kill criterion for this phase) and reconsider.

## Safety

Both scripts only touch Notepad, never save anything, and close it afterward.
