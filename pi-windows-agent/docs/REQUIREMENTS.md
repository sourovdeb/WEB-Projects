# PiWin Requirements (v0.2 — SCOPE FROZEN at dispatcher-gate milestone; see SAFETY-DISPATCHER.md)

## 1. The no-decision rule

- PiWin executes the operator's instructions **literally, step by step**.
- It must not: infer missing steps, choose between options, reorder steps, batch
  unapproved actions, or take any action not explicitly requested.
- Exactly one exception: when the operator's prompt is ambiguous, PiWin asks a
  single clarifying question and waits. It never resolves ambiguity by acting.

## 2. Authorization gates

- **Dispatcher guard (the one gate):** every side-effecting tool call —
  `ui.*`, `powershell`, `bash`, `edit`, `write`, MCP, Playwright — is blocked
  unless its serialized name+arguments hash-match an approval the operator
  clicked in the UI. Approval is of the call, not of a sentence. See
  `SAFETY-DISPATCHER.md`.
- **Irreversible gate:** actions matching the irreversible keyword list —
  `publish, upload, post, delete, send, save-over, install, format, pay` —
  require a second, separate confirmation naming the exact target.
- Dry-run is a process flag the model cannot clear. Irreversible matching runs
  on real arguments (`publish, upload, post, delete, send, save-over, install,
  format, pay, recycle, share, token-grant`) and needs a second confirm naming
  the exact target. Jev highlights; it can never waive a confirm. A step the
  operator didn't ask for is Removed by default — keeping it means editing the
  form so the step is explicitly theirs.

## 3. Primary interface — form-based UI (operator never writes code)

- A local desktop-style app window (served on localhost only, no external access)
  where the operator builds a task as a **form**:
  - Pick application (dropdown of detected apps: video editor, browser, other)
  - Pick action steps (click-to-add: open file, cut clip, export, upload/publish…)
  - Fill fields (file paths via file picker, text via text boxes, choices via dropdowns)
  - Click **Run**.
- Every step then appears in a live checklist with **Approve / Stop** buttons —
  the same authorization gates as the terminal flow, but clickable.
- Screenshots of what the bot sees shown after each step, in plain language
  ("Clicked Export button in Shotcut — done").
- No terminal, no code, no config files for the operator at any point.
- A free-text box is still available for anything the form can't express; if the
  text is ambiguous, the UI shows the single clarifying question as a form too.
- A checkbox: **"Cross-check result with another AI when done"** — after the task,
  Jev verifies the run log and, if flagged, a configured second AI (e.g. Mistral
  Vibe) suggests fixes, shown as a plain-language report card. See
  `JEV-INTEGRATION.md`.

## 3b. Target capabilities

- Control windows that expose a **usable UI Automation tree** — each app is
  added to a `tested-apps.json` list only after a recorded pilot run against
  it. Custom-rendered UIs (Shotcut timeline, games) are documented as
  unsupported where that proves true.
- Video editing by clicking the app's real UI (operator names the app in the form).
- Web browser use and publishing flows via scriptable browser automation
  (Playwright) where possible; GUI clicking as fallback for non-scriptable apps.
- Terminal collaboration with Mistral Vibe via a shared STATE file handoff
  (background mode for advanced use; the UI is the default).

## 3c. Everything is a step scaffold (added per operator, v0.2 — DEFERRED past v0.1 gate)

> **Scope freeze:** v0.1 ships the dispatcher guard + ONE tested local app.
> Gmail, YouTube, WordPress, MCP/API, skills execution, and the second-model
> cross-check are deferred until the gate passes; they are designed here so the
> guard retrofits cleanly. OAuth/off-machine actions are a separate product
> phase.

Not just editing — **every task** is built from the same step-scaffold GUI:

- A **step library** in the UI: each step type is a card with its own form
  (app action, file op, browser action, email, publish, recycle/cleanup,
  custom…). The operator composes any number of them, in any order, for any
  workflow — recording, editing, publishing, emailing, site updates, cleanup.
- **Per-step references/alternatives (assist):** every step card has an
  optional **"If there's a problem…"** section where the operator can attach
  references (screenshots, a how-to link, a sample file) and alternative
  approaches ("if the Export button is greyed out, render at 720p instead").
  When a step fails or a UI element isn't found, PiWin shows the operator's
  references and alternatives first and picks one **only after the operator
  clicks it** — never silently.
- **Skills selection:** a Skills panel lists available skills (e.g.
  "YouTube upload", "WordPress post", "Silence cutting", "Recycle old
  files"); the operator toggles which skills a task may use. Skills are
  saved step templates (see save-and-test below), not autonomous behaviors.
- **Manual selection of every location:** every path a task touches — input
  files, output folder, export destination, recycle-bin/cleanup target — is
  chosen by the operator via folder picker, never guessed. Includes a
  dedicated **cleanup/recycle step** (move to Recycle Bin) with its own
  confirmation listing every file it will touch.
- **Service integrations — Gmail, YouTube, WordPress** — each usable via two
  modes the operator picks per step: **MCP** (managed connector, e.g. a
  WordPress MCP server) or **API** (direct key-based). Connection screens are
  forms (paste key / sign in once); credentials stored only in Pi's
  `auth.json` / OS key store, gitignored.
- **Save and test:** any composed step sequence (or single step) can be
  **saved as a template** ("My YouTube upload") and **tested on demand** —
  a dry-run that walks the real UI and reports what it *would* do, with no
  irreversible action executed. Tested templates get a green "verified
  on <date>" badge and become selectable skills.

## 4. Non-goals

- Not a general autonomous agent. No scheduling, no background autonomy, no
  self-directed goals.
- No multi-user or server use. The UI listens on localhost only; no remote
  access, no external exposure.
- No sandboxing is provided by Pi; this is a single-operator, full-trust tool.
- The operator never writes, edits, or reads code to use this tool.

## 5. Model power

- Pi configured with a Mistral model via `/login` or an OpenAI-compatible
  endpoint entry in `models.json` (verified against Pi's models documentation).

## 6. Open source

- Repo carries an open-source LICENSE; no secrets ever committed
  (`auth.json`, API keys excluded via `.gitignore`).

## Approval

Operator signs off on these rules at Gate G1 before any extension code is built.
