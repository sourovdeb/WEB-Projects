# PiWin Dispatcher Guard Spec (v2 — SOLE AUTHORITY)

**This document supersedes every other description of gating, approval, or
safety in this repo.** Where README, ARCHITECTURE.md, REQUIREMENTS.md, or
JEV-INTEGRATION.md disagree with this file, this file wins. The older "typed y
gate", "docs/STATE.md handoff", "any application", and "mechanical necessity"
wording elsewhere is retired; v0.1 implementers read this file only.

**The dispatcher is the guard. Not the prompt, not the model, not Jev.**

## Tool inventory (v0.1) — deny / approve / allow

| Class | Tools | v0.1 policy |
|---|---|---|
| DENY | `powershell`, `bash`, `edit`, `write`, all file-writing tools, all MCP tools, Playwright, `codemode` | **Denied outright. Not approvable.** Hash approval does not exist for these in v0.1, because a same-user shell can rewrite a same-user flag or extension file, and an approved write can replace the approval set itself. |
| APPROVE | `ui.*` calls minted by the UI host | Blocked unless hash-approved by the operator AND carrying a per-launch helper token issued by the UI host. The Python helper independently refuses to act without that token — so the guard does not rest on the Pi hook alone. |
| ALLOW | `read`, `list_windows`, `list_controls`, `screenshot` (unprefixed, read-only) | Read-only; no approval needed. |

Later versions may move a tool from DENY to APPROVE only with the approval set
stored outside the agent's reach (see below).

## The approve rule (for APPROVE-class calls only)

> A `ui.*` call executes only if `sha256(canonical_json(name, args))` matches
> an approval the operator clicked in the UI, **and** the call carries the
> UI host's per-launch token, **and** the target re-check passes.

**Canonical JSON (both sides must use exactly this):** UTF-8,
`json.dumps({"name": <str>, "args": <obj>}, sort_keys=True,
separators=(",", ":"), ensure_ascii=False)`. Integral floats normalize to
integers (1.0 hashes as 1); keys starting with `__` are stripped before
hashing and are never a confirmation channel. Both suites must reproduce
`prototype/tests/hash_vectors.json`. Any encoding difference → mismatch → block.

**Approval set location:** held by the UI host process in memory and written
only to a path the agent cannot write (OS-protected app-data with ACLs denying
the agent's own write tools — moot in v0.1 since write tools are denied). The
Pi `tool_call` hook and the Python helper **both** enforce independently.

**Target re-check:** the helper re-resolves the window by process id + control
identity at execution time. Window title, control, file list, or URL changed
since approval → stale → block and re-ask.

## Irreversible control — action classes, not keywords

Keyword lists are withdrawn (they both miss destructive calls that lack the
words and false-positive on harmless text). The durable signal is the **action
class the operator picked on the form** (e.g. `export`, `delete-file`,
`recycle`, `publish`, `send`, `share`, `grant-token`). Action classes marked
irreversible in the form schema require a second confirm naming the exact
target. No text matching, no model judgment, no Jev waiver can remove this.

## Fail closed without a model

- Dry-run is a process flag **outside** the agent (v0.1: trivially safe because
  the agent has no shell or write tools at all).
- Jev highlights rows. It cannot waive a confirm. Probability under threshold
  means **ask**, never "go ahead". Ambiguity check asks unless the task is
  clearly complete (default = ask).
- No invented steps. Unrequested steps are Removed by default; keeping one
  requires the operator to edit the form so it is explicitly theirs.
  "Mechanical necessity" is not a justification anywhere.

## Abort

A global abort hotkey registered by the UI host (not injectable by the agent)
stops input injection and blocks further calls even if the agent is stuck.

## v0.1 milestone (frozen)

Dispatcher guard above + **one tested local app** (Notepad first, then the
operator's actual target app, recorded in `tested-apps.json`). List windows and
controls, window-only screenshot, click and type approved calls only.
No publish, no MCP, no browser automation, no second model, no hidden-step
skills. Templates must expand into visible steps before Run. Free-text steps
go through the clarifying-question path.

## Application support

Not "any application": windows that expose a usable UI Automation tree, added
to `tested-apps.json` only after a recorded pilot. Custom-rendered UIs and
games are documented as unsupported where that proves true.

## UI host hardening

- Bind `127.0.0.1` only; per-launch random token on every request; reject
  cross-origin requests.
- Credentials: OS key store (Windows Credential Manager) only.
- Screenshots cropped to the target window; never sent to cloud models unless
  the operator opts in per task.
- Agent handoff between sessions: gitignored, schema-validated, **data-only**
  `state.json` (see `docs/STATE.example.md`). No committed instruction files.
