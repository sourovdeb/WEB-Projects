# PiWin UI (.exe)

Resizable, super-lightweight Windows executable wrapping the form UI.

**Design from the operator's sketch (2026-10-24):** Select Model, Select
Skills, How Many Sub Agents?, Mode: Fast/Slow/Superslow, Select Git Repo,
Select MCP, Select Extension, "check to Select Typesafe" (Jev), Steps list
with "Click to Select More Steps", "Click to Ask help to build the prompt",
and a Steps & Instructions textarea.

## Build the .exe (on your Windows PC)

One-time:
```
python -m pip install pyinstaller pywebview
```
Then, in this folder:
```
build_exe.bat
```
Output: `dist\PiWinUI.exe` — single file, double-click to run.

## What it does / doesn't

- Resizable window (min 640x480), dark theme, grid re-flows on resize.
- The server inside enforces the guard's network rules: 127.0.0.1 only,
  per-launch token, exact Host pinning, cross-origin rejection, and the
  same deny/approve/allow inventory (it imports the prototype helper's
  constants and hashing).
- **Buttons are demo-wired**: Run/dry-run log honest messages; nothing
  reaches any agent. The Run path stays blocked until the dispatcher is
  wired to a live Pi session after the pilot PASS.
