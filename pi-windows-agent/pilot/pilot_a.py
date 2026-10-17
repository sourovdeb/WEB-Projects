import time

from pywinauto import Application
from PIL import ImageGrab

TEXT = "PiWin pilot OK"
STAMP = time.strftime("%Y-%m-%d %H:%M:%S")
FULL = f"{TEXT} - {STAMP}"

app = Application(backend="uia").start("notepad.exe")
dlg = app.window(title_re=".*Notepad")
dlg.wait("ready", timeout=10)
dlg.type_keys(FULL, with_spaces=True, pause=0.02)
time.sleep(1)

shot = rf"C:\Users\{__import__('getpass').getuser()}\Desktop\piwin_pilot.png"
ImageGrab.grab().save(shot)
print("Screenshot saved:", shot)

dlg.close()
dlg.wait_not("visible", timeout=5)
print("PASS:", FULL)
