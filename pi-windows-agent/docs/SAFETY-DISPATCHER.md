# PiWin Dispatcher Guard Spec (v1 — replaces prompt-based safety)

**The dispatcher is the guard. Not the prompt, not the model, not Jev.**

Pi is documented as unsandboxed, and PiWin enables `powershell`. Therefore safety
must be enforced in code at the tool-call boundary, identical for every tool.

## The one rule

> Every side-effecting tool call is **blocked** unless its serialized name and
> arguments hash-match an approval the operator made in the UI.

- Coverage: `ui.*`, `powershell`, `bash`, `edit`, `write`, any file-mutating tool,
  Playwright, and every MCP tool. No exemptions, no allowlist bypass, no
  "trusted tool" shortcut.
- Mechanism: the `tool_call` hook (VERIFIED-LIVE: can mutate input or return
  `{ block: true, reason }`) computes `sha256(canonical_json(toolName, args))`
  and compares it to the approval set. No match → block, fail closed.
- The operator approves **the serialized call**, never a sentence like
  "click Export". The UI renders the call (tool, target window/process id,
  arguments) for approval; the hash is bound to that exact call.

## Re-check at execution time

Approval is bound to the target, not just the call:

- Before executing an approved `ui.*` call, the helper re-resolves the target
  window/control by **process id + control identity**. If the window title,
  control, file list, or URL changed since approval, the approval is stale →
  block and re-ask.

## Fail closed without a model

- Irreversible matching runs on the **real arguments** — keywords:
  `publish, upload, post, delete, send, save-over, install, format, pay,
  recycle, share, token-grant` — inside any tool's args, not just `ui.*`.
  These require a second confirm naming the exact target.
- Dry-run is a **process flag the model cannot clear** (set outside the agent
  process; the model has no tool that writes it).
- Jev may highlight a row in the UI. It **cannot waive a confirm**, and a
  probability under 0.5 is "ask", never "go ahead". The ambiguity check asks
  unless the task is clearly complete (default = ask).
- No invented steps. "Mechanical necessity" is removed as a justification.
  If Pi or Jev adds a step the operator didn't, the **default is Remove**;
  keeping it requires the operator to edit the form so the step is explicitly
  theirs.

## Abort

A global abort hotkey (registered by the UI host, not injectable by the agent)
stops input injection and blocks further calls, even if the agent is stuck.

## Milestone freeze (v0.1)

Defensible v0.1 is: **one local app** — list its windows and controls, take a
window-only screenshot, click and type only approved calls, with the dispatcher
guard above. No publish, no MCP, no second model, no skills that run hidden
steps. Saved templates are fine **if they expand into visible steps before Run**.
Free-text custom steps go through the same clarifying-question path as any other
ambiguity.

Deferred to after the gate passes: Gmail, YouTube, WordPress (OAuth, stored
tokens, off-machine actions are a different product), skills execution,
second-model cross-check.

## Application support claim

"Any application" is withdrawn. PiWin targets **windows that expose a usable UI
Automation tree**; each app is added to a `tested-apps.json` list only after a
recorded pilot run against it (Notepad first, then the operator's actual target
app). Apps that fail (custom-rendered timelines, games) are documented as
unsupported rather than silently attempted.

## Localhost UI hardening

- Bind to `127.0.0.1` only (never `0.0.0.0`).
- Per-launch random token required on every request.
- Reject cross-origin requests (`Origin`/`Host` checks) — a page the operator
  already has open must not be able to talk to the agent.

## Data handling

- Credentials: OS key store (Windows Credential Manager) — decided; not
  `auth.json`-only, not the repo. `.gitignore` covers screenshots, Playwright
  storage state, token JSON, runtime state files.
- Screenshots are cropped to the **target window only**, never full-desktop, and
  are not sent to cloud models (Jev or second AI) by default; opt-in per task.
