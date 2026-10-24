@echo off
REM Build the PiWin UI .exe (super-lightweight, resizable native window)
REM One-time setup:  pip install pyinstaller pywebview
REM Then run this file. Output: dist\PiWinUI.exe  (single file)

pyinstaller --onefile --noconsole --name PiWinUI ^
  --add-data "ui;ui" ^
  --hidden-import piwin_helper ^
  run_ui.py
echo.
echo Done: dist\PiWinUI.exe
