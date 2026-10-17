# PiWin Architecture

## Components

```
Operator (you)
   │ form input + click Approve/Stop
   ▼
PiWin UI (localhost web app in a desktop window — the ONLY default interface)
   │ task form → JSON task; approvals via buttons, not typing
   ▼
Pi (agent, driven headless via the Pi SDK in-process; terminal remains a background option)
   ├── piwin-gate/        DISPATCHER GUARD (see SAFETY-DISPATCHER.md)
      └── tool_call hook: blocks EVERY side-effecting call (ui.*, powershell,
           bash, edit, write, MCP, Playwright) unless its serialized name+args
           hash-match an approval made in the UI; re-checks the target window
           at execution time
   ├── piwin-ui/          GUI tools extension (TypeScript, Pi SDK)
   │      └── shells out to helper (below), returns JSON + screenshot path
   │           ui.find_window  ui.list_windows  ui.list_controls
   │           ui.click        ui.type          ui.read_screen (screenshot)
   └── project instructions file — enforces the no-decision protocol
            (literal execution, one clarifying question on ambiguity)

Jev (TypeSafe) — decision model, built into Pi as a classifier (VERIFIED-LIVE)
   verifies at 4 points: ambiguity check (before planning), per-step plan
   conformance, irreversible-risk scoring, post-task cross-reference of the run
   log. Returns typed answers + probabilities; flags only, never acts.
   On flags, a configured chat AI suggests fixes as clickable UI report rows
   (never a shared state file). DEFERRED — see JEV-INTEGRATION.md.

piwin-helper/  (Python, runs on Windows) — refuses any call without the UI
   host's per-launch token
   find_window | click | type_text | screenshot | list_controls
   built on Windows UI Automation (engine UNVERIFIED until pilot passes; apps
   are supported only via tested-apps.json)
```

> **SUPERSEDED portions removed.** The typed-`y` batch gate, the
> docs/STATE.md handoff, "app-agnostic / any application", the Playwright
> publish component, and the "engine confirmed at G2" claim are retired.
> The UI Automation engine is UNVERIFIED until the pilot runs. v0.1 has no
> publish/browser/second-model components. This diagram shows the v0.1 shape.
> Sole authority: SAFETY-DISPATCHER.md.

## Flow

1. Operator opens the PiWin app window and builds the task as a form
   (app picker, step picker, file pickers) or types free text; clicks **Run**.
2. Pi produces a literal step plan; if ambiguous it returns the single
   clarifying question, shown in the UI as a form. (v0.1 target app must be on
   tested-apps.json; unrequested steps are Removed by default.)
3. The UI shows each pending call (tool, target pid, arguments); the operator's
   Approve click mints a hash of the serialized call (canonical JSON defined in
   SAFETY-DISPATCHER.md). Unapproved calls are blocked by the tool_call hook AND
   the helper's token check.
4. `ui.*` tools drive the target application; each call returns JSON
   (success/fail, screenshot) which the UI displays in plain language.
5. Irreversible form action classes (not keyword matching) trigger a second
   confirmation naming the exact target.
6. Session handoff is the gitignored, data-only `state.json`
   (STATE.example.md); nothing committed carries agent instructions.

The operator never opens a terminal, editor, or config file. Setup (installing
Pi, model login) is done once by the build agent and packaged into an installer.

## Deferred (post-gate)

Publish/browser flows, Gmail/YouTube/WordPress MCP or API, skills execution,
and the Jev + second-model cross-check are deferred design only (REQUIREMENTS
§3c, JEV-INTEGRATION.md as revised). None ship in v0.1.

## Model configuration

Pi runs with a Mistral model (`/login` or OpenAI-compatible entry in
`models.json`). Thinking level selectable via `/thinking`.

## Safety posture

- Pi does not sandbox tool calls (verified from Pi docs). The **dispatcher guard
  (SAFETY-DISPATCHER.md) is the guard** — code-enforced at the tool-call boundary,
  covering every side-effecting tool. The operator's approval is bound to the
  serialized call hash, not to a sentence. Prompt instructions and Jev are
  advisory only and can never waive a confirm.
- The UI host binds 127.0.0.1 only, requires a per-launch token, rejects
  cross-origin requests. It is a listener and is hardened as one.
- Credentials live in the OS key store (Windows Credential Manager); never in
  the repo. Screenshots are cropped to the target window and never sent to
  cloud models by default.
