# PiWin Requirements (v0.1 — awaiting operator approval, Gate G1)

## 1. The no-decision rule

- PiWin executes the operator's instructions **literally, step by step**.
- It must not: infer missing steps, choose between options, reorder steps, batch
  unapproved actions, or take any action not explicitly requested.
- Exactly one exception: when the operator's prompt is ambiguous, PiWin asks a
  single clarifying question and waits. It never resolves ambiguity by acting.

## 2. Authorization gates

- **Batch gate:** before any GUI action batch runs, PiWin displays the plan
  (target app, action, arguments) and waits for the operator to type `y`.
- **Irreversible gate:** actions matching the irreversible keyword list —
  `publish, upload, post, delete, send, save-over, install, format, pay` —
  require a second, separate confirmation naming the exact target.
- Default is **dry-run**: when a plan has an irreversible step, the first run
  shows what would happen without doing it.

## 3. Target capabilities

- Control **any application** on the operator's PC (window discovery, click,
  type, read screen) — app-agnostic, via Windows UI Automation.
- Video editing by clicking the app's real UI (operator names the app at runtime).
- Web browser use and publishing flows via scriptable browser automation
  (Playwright) where possible; GUI clicking as fallback for non-scriptable apps.
- Terminal collaboration with Mistral Vibe via a shared STATE file handoff.

## 4. Non-goals

- Not a general autonomous agent. No scheduling, no background autonomy, no
  self-directed goals.
- No multi-user or server use. No sandboxing is provided by Pi; this is a
  single-operator, full-trust tool.

## 5. Model power

- Pi configured with a Mistral model via `/login` or an OpenAI-compatible
  endpoint entry in `models.json` (verified against Pi's models documentation).

## 6. Open source

- Repo carries an open-source LICENSE; no secrets ever committed
  (`auth.json`, API keys excluded via `.gitignore`).

## Approval

Operator signs off on these rules at Gate G1 before any extension code is built.
