# PiWin v0.1 Prototype

**Not usable as an assistant.** This is the dispatcher guard, helper protocol,
and UI host implemented and unit-tested on the guard logic only. No GUI
driving exists until the Notepad pilot passes on the operator's machine
(`pilot/RUN-THIS.md`).

## What exists here

- `helper/piwin_helper.py` — GUI helper (Python). Token check, action-class
  gates, canonical-JSON approval hashing, target re-check stubs. The actual
  Windows input calls are NOT implemented — they are behind the same guarded
  interface and only get written after the pilot passes.
- `guard/piwin_gate.ts` — Pi extension sketch implementing the same
  deny/approve/allow inventory at the tool_call boundary.
- `ui-host/` — minimal localhost UI host (Node, no dependencies) that mints
  per-launch tokens and records approvals.
- `tests/` — unit tests for the guard logic, run on Linux in this sandbox.

## Run the tests

```
python3 -m unittest discover -s tests -v
```

All tests must pass; they cover denial of shell/write tools, approval-hash
binding, replay/stale-target rejection, and fail-closed defaults.

## What this prototype deliberately does not do

- Drive any real window.
- Run on Windows (helper input layer is unimplemented).
- Trust any prompt or model judgment for safety decisions.
