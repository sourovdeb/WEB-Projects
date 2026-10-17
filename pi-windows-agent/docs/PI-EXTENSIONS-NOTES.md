# Pi extension/SDK notes — VERIFIED-LIVE (pi.dev/docs/latest/extensions, /sdk, /codemode)

Everything the PiWin build assumed is confirmed:

## Extension API
- Extensions are TypeScript modules: `export default function (pi: ExtensionAPI)`.
- Load for development: `pi --extension ./hello.ts` (jiti, no compile step).
- Distribute: `~/.pi/agent/extensions/` (user) or project dir; single file or dir with `index.ts`.
- **Tools:** `pi.registerTool({ name, description, paramsSchema (TypeBox), execute })`
  — result needs `content` + `details`; `outputSchema`/`structuredContent` for data
  results; throw or `isError: true` for failures.
- **Authorization gate:** `pi.on("tool_call", ...)` can mutate input or
  `{ block: true, reason }` — exactly our gate mechanism. `ctx.ui.confirm()` exists
  but our UI forwards approvals via RPC's Extension UI protocol.
- Tool annotations (`readOnlyHint`, `destructiveHint`) available for risk policy.
- `exposure`: `direct` (default), `model-only`, `codemode`, `deferred`, `hidden`;
  `namespace` groups `ui.*` tools.
- **Codemode:** QuickJS-sandboxed JS scripts; `tools.<name>()`, `models.classify()`
  for Jev; enable with `"defaultTools": ["+codemode"]`.
- Extensions load in interactive, RPC, JSON, print modes; RPC forwards dialogs —
  our localhost UI drives Pi via RPC mode. Guard terminal-only with `ctx.mode`.

## SDK (alternative to RPC for the UI backend)
- `import { createAgentSession } from "@earendil-works/pi-coding-agent"`
- `session.prompt()`, `session.subscribe(events)`, `session.abort()`,
  `SessionManager.inMemory()`.
- SDK sessions must add built-in extensions explicitly:
  `createCodemodeExtension()`, `createMcpExtension()` via
  `DefaultResourceLoader` `extensionFactories` — needed for Jev calls.

## Decision
UI backend uses the **SDK in-process** (cleaner than RPC for a packaged app);
falls back to RPC mode if packaging constraints demand a subprocess.
