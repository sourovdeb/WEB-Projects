"""PiWin GUI helper — guarded front door.

The helper refuses every action unless:
  1. the call carries the UI host's per-launch token, and
  2. for APPROVE-class actions, the canonical-JSON hash of (name, args)
     matches an approval minted in the UI, and
  3. the target window re-check passes (same pid + control identity).

Windows input (pywinauto) is intentionally NOT implemented in the prototype:
execute() raises NotPilotedYet until the Notepad pilot passes on the
operator's machine. The guard logic is complete and unit-tested.

Sole authority for rules: docs/SAFETY-DISPATCHER.md.
"""
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

# v0.1 tool inventory (mirrors docs/SAFETY-DISPATCHER.md exactly)
DENY_TOOLS = {"powershell", "bash", "edit", "write", "mcp", "playwright", "codemode"}
APPROVE_CLASS = "ui"
ALLOW_TOOLS = {"read", "list_windows", "list_controls", "screenshot"}

IRREVERSIBLE_ACTION_CLASSES = {
    "delete-file", "recycle", "publish", "send", "share", "grant-token",
    "save-over", "install", "format", "pay",
}


def canonical_json(name: str, args: dict) -> str:
    """Exactly the encoding both hash sides must use (SAFETY-DISPATCHER.md)."""
    return json.dumps(
        {"name": name, "args": args},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8").decode("utf-8")


def call_hash(name: str, args: dict) -> str:
    return hashlib.sha256(canonical_json(name, args).encode("utf-8")).hexdigest()


class GuardError(Exception):
    """Any refusal. The helper fails closed: no match, no action."""


@dataclass
class Target:
    pid: int
    window_title: str
    control_id: str


@dataclass
class Approval:
    hash: str
    target: Target


@dataclass
class Call:
    name: str
    args: dict
    action_class: str = "ui"          # picked on the FORM, not by the model
    irreversible: bool = False        # derived from action_class by the form
    target: Target = None


class Guard:
    def __init__(self):
        self._approvals: dict[str, Approval] = {}
        self._launch_token: str | None = None  # set by UI host at startup

    def set_launch_token(self, token: str):
        self._launch_token = token

    def mint(self, call: Call) -> str:
        """UI host calls this when the operator clicks Approve."""
        if self._launch_token is None:
            raise GuardError("UI host has not set a launch token")
        h = call_hash(call.name, call.args)
        self._approvals[h] = Approval(hash=h, target=call.target)
        return h

    def clear(self):
        self._approvals.clear()

    def check(self, call: Call, token: str, live_target: Target | None) -> Approval:
        # 1) token — fail closed
        if not self._launch_token or token != self._launch_token:
            raise GuardError("bad or missing launch token")
        # 2) tool class
        if call.name in DENY_TOOLS or call.name.startswith("mcp__"):
            raise GuardError(f"tool {call.name} is DENIED outright in v0.1")
        is_ui = call.name.startswith("ui.")
        if not is_ui and call.name not in ALLOW_TOOLS:
            raise GuardError(f"tool {call.name} is not in the v0.1 inventory")
        # 3) read-only tools pass without approval
        if call.name in ALLOW_TOOLS and not is_ui:
            return Approval(hash="", target=None)
        # 4) ui.* needs the exact approved hash
        h = call_hash(call.name, call.args)
        ap = self._approvals.get(h)
        if ap is None:
            raise GuardError("call was not approved")
        # 5) irreversible double-confirm is enforced at mint time by the UI;
        #    the helper still refuses if the form marked it irreversible
        #    without a confirmed flag the UI host sets (defense in depth).
        if call.irreversible and not call.args.get("__second_confirmed__"):
            raise GuardError("irreversible action class without second confirmation")
        # 6) target re-check
        if ap.target is not None:
            if live_target is None:
                raise GuardError("cannot re-check target; refusing")
            if (live_target.pid, live_target.window_title, live_target.control_id) != (
                ap.target.pid, ap.target.window_title, ap.target.control_id
            ):
                raise GuardError("target changed since approval; stale approval refused")
        return ap


class NotPilotedYet(Exception):
    pass


def execute(call: Call, approval: Approval):
    """The actual Windows input layer. NOT IMPLEMENTED in the prototype.

    Only after pilot.py passes on the operator's machine does this get code.
    """
    raise NotPilotedYet(
        "input layer unimplemented until the Notepad pilot passes (pilot/RUN-THIS.md)"
    )
