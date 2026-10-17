# PiWin — Windows Agentic Tool (built on Pi)

PiWin is a personal Windows assistant built on [Pi](https://pi.dev) that clicks and
types in applications on your PC — but only in windows on the tested-app list,
and only with calls you approved. **Safety is enforced by the dispatcher guard,
not by the prompt. Sole authority: `docs/SAFETY-DISPATCHER.md`.** **You use it through a simple form: pick your app, pick the
steps, click Run, click Approve. You never write code.**

## Core rules

1. **No decisions.** PiWin executes your instructions literally, step by step. It
   never fills gaps, guesses, or improvises. Unrequested steps are removed by
   default.
2. **Authorization required.** Each call is shown to you (tool, target, args)
   before it runs. In v0.1 only `ui.*` calls are approvable — shell, file-write,
   MCP, and browser tools are denied outright. Irreversible form action classes
   always require a second confirmation naming the exact target.
3. **Ask, don't guess.** If your prompt is unclear, PiWin asks one clarifying question
   instead of acting.
4. **Personal use only.** Built for a single trusted operator on their own machine.
   Pi does not sandbox tool calls — this tool runs with your user permissions, so
   never install it on a machine or for a user you don't fully trust.
5. **Deferred, by design:** publish flows, Gmail/YouTube/WordPress, MCP, browser
   automation, and a second-model cross-check exist only as deferred design in
   `REQUIREMENTS.md` §3c. v0.1 ships none of them.

## Architecture (v0.1)

- **Dispatcher guard first** — safety is enforced in code at the tool-call
  boundary. v0.1 tool inventory: **DENY** shell, file-write, MCP, Playwright
  outright; **APPROVE** `ui.*` calls only (hash-bound to the operator's click,
  plus the UI host's per-launch token, plus target re-check); **ALLOW**
  read-only tools. Sole authority: `docs/SAFETY-DISPATCHER.md`.
- **PiWin UI host** — localhost (127.0.0.1) form app with per-launch token and
  cross-origin rejection; mints call approvals and holds the approval set.
- **Pi core** — the agent, driven by the UI host; in v0.1 it has no shell,
  write, MCP, or browser tools at all (denied, not gated).
- **PiWin GUI helper** — Windows GUI control (find window, click, type,
  window-only screenshot, list controls) for apps on the tested-apps.json
  list only; refuses any call without the UI host's token.
- **Vibe collaboration** — deferred; will use the gitignored, data-only
  `state.json` handoff (see `docs/STATE.example.md`), never a committed
  instruction file.

See the `docs/` folder (`SAFETY-DISPATCHER.md`, `ARCHITECTURE.md`, `REQUIREMENTS.md`, `JEV-INTEGRATION.md`) for the full design.

## Status

Planning spike. **Do not build on this yet** — v0.1 scope is frozen at the dispatcher-guard milestone: one tested local app, pilot verified by read-back, before any publish/MCP/second-model work.
