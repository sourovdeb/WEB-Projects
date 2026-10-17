# PiWin GUI-Control Pilot (Step 6 / Gate G2) — v2

One script: `pilot.py`. Run it on your Windows PC.

```
pip install pywinauto pillow
python pilot.py
```

**What it does:** opens ONE Notepad process, types "PiWin pilot OK - <timestamp>"
into that window, **reads the text back from that window** to verify, saves a
**screenshot of that window only**, then closes that window (answering Don't Save
on its own prompt if one appears). It never touches other Notepad windows and
never closes them. If read-back fails, it prints FAIL and leaves the window open.

**PASS means:** the console prints `Read-back verified: ...` and then
`PASS: typed, read back, screenshot, and closed pid <pid>` — in that order.
A PASS printed before cleanup is not a pass.

**This proves:** UI Automation can drive and read back classic Notepad on your
machine. It does NOT prove "any application" — Shotcut's timeline, games, and
some custom-rendered UIs expose no usable UI Automation tree. After this pilot,
Gate G2 additionally requires a second run against your actual target app, which
is added to a tested-app list.

## Notes

- The old `pilot_a.py`, `pilot_b.ps1` and their instructions were removed:
  pilot_b never typed anything (SendKeys -Keys is not a PowerShell cmdlet),
  closed every notepad process, and told you to bypass execution policy.
