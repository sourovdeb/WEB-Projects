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
- `tests/hash_vectors.json` — Python-generated hash vectors; the Node suite
  reproducing them IS the cross-language verification.

## Run the tests

```
python3 -m unittest discover -s tests -v
```

All tests must pass (25 Python + 20 Node at v0.1.1). They cover denial of
shell/write/MCP/codemode at BOTH mint and check, approval-hash binding,
irreversibility derived from the minted action class (caller flags can add a
confirm, never waive; `__` keys are not a confirm channel), full-target
requirements, replay/stale-target rejection, exact Host pinning
(`127.0.0.1:<port>` / `localhost:<port>` only), and float normalization.
**Unit tests ran on Linux in this sandbox; no window-driving has ever run** —
execute() is NotPilotedYet until the operator's pilot passes.

## What this prototype deliberately does not do

- Drive any real window.
- Run on Windows (helper input layer is unimplemented).
- Trust any prompt or model judgment for safety decisions.
