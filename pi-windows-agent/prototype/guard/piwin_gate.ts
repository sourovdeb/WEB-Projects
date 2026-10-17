// PiWin dispatcher-guard extension sketch (Pi tool_call hook).
// Implements the SAME deny/approve/allow inventory as the helper and UI host.
// This file is a spec-faithful sketch: it typechecks against Pi's documented
// ExtensionAPI surface (pi.on("tool_call", ...) -> { block, reason }), but is
// NOT loadable until PiWin is assembled on the operator's machine after the
// pilot passes. Rules: docs/SAFETY-DISPATCHER.md only.

const DENY_TOOLS = new Set(["powershell", "bash", "edit", "write", "mcp", "playwright", "codemode"]);
const ALLOW_TOOLS = new Set(["read", "list_windows", "list_controls", "screenshot"]);

export default function piwinGate(pi) {
  pi.on("tool_call", async (event, ctx) => {
    const name = event.toolName;

    // DENY class: blocked outright, no approval path exists in v0.1.
    if (DENY_TOOLS.has(name) || name.startsWith("mcp__")) {
      return { block: true, reason: `${name} is DENIED outright in PiWin v0.1` };
    }

    // APPROVE class: ui.* must match a hash the UI host minted.
    if (name.startsWith("ui.")) {
      const approval = await ctx.uiHostApprovalFor(name, event.args); // provided by UI host bridge
      if (!approval) {
        return { block: true, reason: `${name} call was not approved in the PiWin UI (hash mismatch)` };
      }
      return undefined; // allow; the helper re-checks token + target independently
    }

    // ALLOW class: read-only.
    if (ALLOW_TOOLS.has(name)) return undefined;

    // Unknown tool: fail closed.
    return { block: true, reason: `${name} is not in the PiWin v0.1 inventory` };
  });
}
