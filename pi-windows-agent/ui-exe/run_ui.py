"""PiWinUI.exe entry point.

Starts the hardened localhost server (server.py) and opens a resizable,
lightweight native window on it via pywebview (Edge WebView2 on Windows).
No browser window, no external exposure, ~2 MB of runtime beyond the page.
"""
import multiprocessing
import threading
import time

import webview  # pip install pywebview

import server  # local server.py


def main():
    # Start the hardened server in a thread (127.0.0.1 only, per-launch token).
    t = threading.Thread(target=server.main, daemon=True)
    t.start()
    time.sleep(0.3)

    # Resizable native window pointing only at our own localhost page.
    webview.create_window(
        "PiWin",
        f"http://127.0.0.1:{server.PORT}/",
        width=1100,
        height=760,
        min_size=(640, 480),
        resizable=True,
        text_select=True,
    )
    webview.start()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # required for onefile PyInstaller
    main()
