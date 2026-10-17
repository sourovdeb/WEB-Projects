# PiWin — Windows Agentic Tool (built on Pi)

A personal, open-source Windows assistant built on [Pi](https://pi.dev) that operates
any application on your PC by clicking and typing like a human — but only with your
explicit authorization.

## Core rules

1. **No decisions.** PiWin executes your instructions literally, step by step. It never
   fills gaps, guesses, or improvises.
2. **Authorization required.** Every GUI action batch is shown to you first. Nothing
   runs until you approve. Irreversible actions (publish, upload, delete, send,
   save-over) always require a second explicit confirmation.
3. **Ask, don't guess.** If your prompt is unclear, PiWin asks one clarifying question
   instead of acting.
4. **Personal use only.** Built for a single trusted operator on their own machine.
   Pi does not sandbox tool calls — this tool runs with your user permissions, so
   never install it on a machine or for a user you don't fully trust.

## Architecture

- **Pi core** — terminal agent, run natively on Windows with the `powershell` tool.
- **PiWin GUI helper** — app-agnostic Windows GUI control (find window, click, type,
  screenshot, list controls) exposed to Pi as `ui.*` tools via a Pi extension.
- **Authorization gate** — extension that intercepts every GUI action and waits for
  your typed approval.
- **Browser mode** — scriptable browser automation (Playwright) for web flows;
  clicking is reserved for non-scriptable apps.
- **Vibe collaboration** — shared `docs/STATE.md` handoff so Pi and Mistral Vibe work
  together in the terminal.

See `docs/ARCHITECTURE.md` and `docs/REQUIREMENTS.md` for the full design.

## Status

Planning phase — see the workflow spec in this repo's PR.
