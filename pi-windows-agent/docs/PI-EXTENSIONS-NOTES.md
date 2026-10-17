# Pi extension/SDK notes — BACKGROUND REFERENCE ONLY

**These are engineering notes about Pi's capabilities, not PiWin's design.**
Nothing here overrides `SAFETY-DISPATCHER.md`. In particular:
- The RPC `ctx.ui.confirm()` path is NOT the PiWin gate. The gate is the
  tool_call hook + helper token in SAFETY-DISPATCHER.md.
- v0.1 does NOT enable codemode, MCP, `powershell`, or any file-write tool.
  A later version may revisit DENY-class tools only under the conditions in
  SAFETY-DISPATCHER.md — never from this file.

Originally VERIFIED-LIVE from pi.dev/docs/latest/extensions, /sdk, /codemode:

Everything the PiWin build assumed is confirmed:

## Extension API
- Extensions are TypeScript modules:
  `export default function (pi: ExtensionAPI)`. (Background — the registration
  hooks below are how the guard will be implemented; the guard's rules come
  from SAFETY-DISPATCHER.md, not from this file.)
- Load for development: `pi --extension ./hello.ts` (jiti, no compile step).
- Distribute: `~/.pi/agent/extensions/` (user) or project dir; single file or dir with `index.ts`.
- **Tools:** `pi.registerTool({ name, description, paramsSchema (TypeBox), execute })`
  — result needs `content` + `details`; `outputSchema`/`structuredContent` for data
  results; throw or `isError: true` for failures.
- **Guard mechanism:** `pi.on("tool_call", ...)` can mutate input or
  `{ block: true, reason }` — the hook the dispatcher guard will use. The
  operator-facing approvals are clicked in the PiWin UI host, which mints
  the hashes; `ctx.ui.confirm()` is unused.
- Tool annotations (`readOnlyHint`, `destructiveHint`) available for risk policy.
- `exposure`: `direct` (default), `model-only`, `codemode`, `deferred`, `hidden`;
  `namespace` groups `ui.*` tools.
- **Codemode:** QuickJS-sandboxed JS scripts; `tools.<name>()`, `models.classify()`
  for Jev. PiWin does NOT enable it in v0.1 (`defaultTools` stays without `+codemode`).
- Extensions load in interactive, RPC, JSON, print modes. PiWin uses the SDK
  in-process, not RPC. Guard terminal-only behavior with `ctx.mode`.

## SDK (alternative to RPC for the UI backend)
- `import { createAgentSession } from "@earendil-works/pi-coding-agent"`
- `session.prompt()`, `session.subscribe(events)`, `session.abort()`,
  `SessionManager.inMemory()`.
- SDK sessions must add built-in extensions explicitly:
  `createCodemodeExtension()`, `createMcpExtension()` via
  `DefaultResourceLoader` `extensionFactories` — needed for Jev calls.

## Decision (v0.1)
UI backend uses the **SDK in-process**. RPC mode is not used. The SDK session
loads only the piwin extensions; DENY-class tools and MCP are not registered
at all.
