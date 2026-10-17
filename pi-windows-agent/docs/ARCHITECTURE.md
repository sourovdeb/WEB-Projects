# PiWin Architecture

## Components

```
Operator (you)
   │ typed approvals
   ▼
Pi (terminal agent, native Windows, powershell tool)
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

piwin-helper/  (Python, runs on Windows)
   find_window | click | type_text | screenshot | list_controls
   built on Windows UI Automation (engine confirmed at pilot step G2)
```

## Flow

1. Operator gives a task in Pi's terminal.
2. Pi (with project instructions) produces a literal step plan; if ambiguous it
   asks one question and stops.
3. Gate extension prints the plan; operator types `y`.
4. `ui.*` tools drive the target application; each call returns JSON
   (success/fail, screenshot path) so the model verifies its own actions.
5. Irreversible keywords trigger a second confirmation naming the exact target.
6. Results and handoff state are written to `docs/STATE.md` for Vibe collaboration.

## Model configuration

Pi runs with a Mistral model (`/login` or OpenAI-compatible entry in
`models.json`). Thinking level selectable via `/thinking`.

## Safety posture

- Pi does not sandbox tool calls (verified from Pi docs). PiWin therefore treats
  the operator's typed approval as the only and sufficient guard.
- No network listeners, no remote control, no background services.
- Credentials live only in Pi's `auth.json` (gitignored).
