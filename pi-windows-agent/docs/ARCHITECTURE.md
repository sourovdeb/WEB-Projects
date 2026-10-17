# PiWin Architecture

## Components

```
Operator (you)
   │ form input + click Approve/Stop
   ▼
PiWin UI (localhost web app in a desktop window — the ONLY default interface)
   │ task form → JSON task; approvals via buttons, not typing
   ▼
Pi (agent, driven headless via Pi's RPC mode; terminal remains a background option)
   │ loads extensions
   │ loads extensions
   ├── piwin-gate/        authorization gate extension (TypeScript, Pi SDK)
   │      └── intercepts every ui.* call → shows plan → waits for "y"
   ├── piwin-ui/          GUI tools extension (TypeScript, Pi SDK)
   │      └── shells out to helper (below), returns JSON + screenshot path
   │           ui.find_window  ui.list_windows  ui.list_controls
   │           ui.click        ui.type          ui.read_screen (screenshot)
   ├── piwin-browser/     Playwright-based browser tool for web/publish flows
   └── project instructions file — enforces the no-decision protocol
            (literal execution, one clarifying question on ambiguity)

Jev (TypeSafe) — decision model, built into Pi as a classifier (VERIFIED-LIVE)
   verifies at 4 points: ambiguity check (before planning), per-step plan
   conformance, irreversible-risk scoring, post-task cross-reference of the run
   log. Returns typed answers + probabilities; flags only, never acts.
   On flags, a configured chat AI (Mistral Vibe or any added model) suggests
   fixes via the shared STATE handoff. See JEV-INTEGRATION.md.

piwin-helper/  (Python, runs on Windows)
   find_window | click | type_text | screenshot | list_controls
   built on Windows UI Automation (engine confirmed at pilot step G2)
```

## Flow

1. Operator opens the PiWin app window and builds the task as a form
   (app picker, step picker, file pickers) or types free text; clicks **Run**.
2. Pi (with project instructions) produces a literal step plan; if ambiguous it
   returns the single clarifying question, shown in the UI as a form.
3. The UI shows the plan as a live checklist; operator clicks **Approve** per step
   (or **Stop**).
4. `ui.*` tools drive the target application; each call returns JSON
   (success/fail, screenshot) which the UI displays in plain language.
5. Irreversible keywords trigger a second confirmation in the UI naming the exact
   target.
6. Results and handoff state are written to `docs/STATE.md` for Vibe collaboration.

The operator never opens a terminal, editor, or config file. Setup (installing
Pi, model login) is done once by the build agent and packaged into an installer.

## Model configuration

Pi runs with a Mistral model (`/login` or OpenAI-compatible entry in
`models.json`). Thinking level selectable via `/thinking`.

## Safety posture

- Pi does not sandbox tool calls (verified from Pi docs). PiWin therefore treats
  the operator's typed approval as the only and sufficient guard.
- No network listeners, no remote control, no background services.
- Credentials live only in Pi's `auth.json` (gitignored).
