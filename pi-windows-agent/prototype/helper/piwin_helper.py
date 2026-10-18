"""PiWin GUI helper — guarded front door. (v0.1.1 — audit fixes applied)

Fixes over v0.1:
 1. Irreversibility derives from the ACTION CLASS recorded on the approval at
    mint. A caller flag can ADD a confirm requirement, never waive it. The
    confirm bit lives on Approval.second_confirmed, set only by
    confirm_second(hash, target) naming the exact target. Keys starting with
    "__" are stripped before hashing and are NOT a confirm channel.
 2. ui.* calls require pid/window/control on BOTH the approval and the live
    target, all three matching. Enforced at mint and check.
 3. mint() refuses DENY and unknown tools via the same _inventory_check as
    check(). No sha256 for a denied tool can ever be stored.

Rules: docs/SAFETY-DISPATCHER.md only. Input layer stays NotPilotedYet until
the pilot passes on the operator's machine.
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Any

DENY_TOOLS = {"powershell", "bash", "edit", "write", "mcp", "playwright", "codemode"}
ALLOW_TOOLS = {"read", "list_windows", "list_controls", "screenshot"}

IRREVERSIBLE_ACTION_CLASSES = {
    "delete-file", "recycle", "publish", "send", "share", "grant-token",
    "save-over", "install", "format", "pay", "export",
}
REQUIRED_TARGET_FIELDS = ("pid", "window", "control")


def _normalize(v: Any) -> Any:
    """Hash-side normalization shared with the Node UI host:
    integral floats -> ints, recursively; keys sorted by canonical_json."""
    if isinstance(v, bool):  # bool is an int subclass; keep distinct
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, dict):
        return {k: _normalize(x) for k, x in v.items() if not k.startswith("__")}
    if isinstance(v, list):
        return [_normalize(x) for x in v]
    return v


def canonical_json(name: str, args: dict) -> str:
    """Exactly the encoding both hash sides must use (SAFETY-DISPATCHER.md).
    "__"-prefixed keys are stripped; integral floats normalize to ints."""
    payload = {"name": name, "args": _normalize(args)}
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def call_hash(name: str, args: dict) -> str:
    return hashlib.sha256(canonical_json(name, args).encode("utf-8")).hexdigest()


class GuardError(Exception):
    """Any refusal. The helper fails closed: no match, no action."""


@dataclass(frozen=True)
class Target:
    pid: int
    window: str
    control: str


@dataclass
class Approval:
    hash: str
    target: Target
    action_class: str
    requires_second: bool
    second_confirmed: bool = False  # set ONLY via confirm_second()


@dataclass
class Call:
    name: str
    args: dict
    action_class: str = "ui"
    extra_confirm: bool = False      # caller may ADD a confirm, never waive
    target: Target | None = None


class Guard:
    def __init__(self):
        self._approvals: dict[str, Approval] = {}
        self._launch_token: str | None = None

    def set_launch_token(self, token: str):
        self._launch_token = token

    def _inventory_check(self, name: str):
        if name in DENY_TOOLS or name.startswith("mcp__"):
            raise GuardError(f"tool {name} is DENIED outright in v0.1")
        if name.startswith("ui."):
            return
        if name in ALLOW_TOOLS:
            return
        raise GuardError(f"tool {name} is not in the v0.1 inventory")

    @staticmethod
    def _require_target(target: Target, what: str) -> Target:
        if target is None:
            raise GuardError(f"{what} requires pid/window/control")
        for f in REQUIRED_TARGET_FIELDS:
            if getattr(target, f) is None:
                raise GuardError(f"{what} target missing {f}")
        return target

    def mint(self, call: Call) -> str:
        """UI host calls this when the operator clicks Approve."""
        if self._launch_token is None:
            raise GuardError("UI host has not set a launch token")
        self._inventory_check(call.name)            # fix 3
        self._require_target(call.target, f"mint of {call.name}") if call.name.startswith("ui.") else None
        requires = (
            call.action_class in IRREVERSIBLE_ACTION_CLASSES
            or call.extra_confirm   # fix 1: caller can add, never waive
        )
        h = call_hash(call.name, call.args)          # __ keys stripped inside
        self._approvals[h] = Approval(
            hash=h, target=call.target, action_class=call.action_class,
            requires_second=requires, second_confirmed=False,
        )
        return h

    def confirm_second(self, h: str, target: Target):
        """The ONLY way to set the second confirm — must name the exact target."""
        ap = self._approvals.get(h)
        if ap is None:
            raise GuardError("no such approval")
        self._require_target(target, "second confirmation")
        if (target.pid, target.window, target.control) != (
            ap.target.pid, ap.target.window, ap.target.control
        ):
            raise GuardError("second confirmation target mismatch")
        ap.second_confirmed = True

    def clear(self):
        self._approvals.clear()

    def check(self, call: Call, token: str, live_target: Target | None) -> Approval:
        if not self._launch_token or token != self._launch_token:
            raise GuardError("bad or missing launch token")
        self._inventory_check(call.name)
        is_ui = call.name.startswith("ui.")
        if not is_ui and call.name in ALLOW_TOOLS:
            return Approval(hash="", target=None, action_class="read",
                            requires_second=False, second_confirmed=True)
        # ui.*: hash must match a minted approval
        h = call_hash(call.name, call.args)
        ap = self._approvals.get(h)
        if ap is None:
            raise GuardError("call was not approved")
        # fix 1: irreversibility from the MINTED approval, not caller flags
        if ap.requires_second and not ap.second_confirmed:
            raise GuardError(
                f"action class {ap.action_class!r} requires a second confirmation "
                "naming the exact target (confirm_second)"
            )
        # fix 2: both sides carry full targets; all fields match
        self._require_target(ap.target, "approval")
        self._require_target(live_target, "live target")
        if (live_target.pid, live_target.window, live_target.control) != (
            ap.target.pid, ap.target.window, ap.target.control
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
