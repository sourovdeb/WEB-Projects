import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "helper"))

from piwin_helper import (  # noqa: E402
    DENY_TOOLS, Guard, GuardError, Target, Call, NotPilotedYet, execute,
)


def make_guard():
    g = Guard()
    g.set_launch_token("launch-token-1")
    return g


def ui_click(pid=100, title="Notepad", ctrl="Export", extra=None):
    args = {"pid": pid, "window": title, "control": ctrl}
    if extra:
        args.update(extra)
    return Call(name="ui.click", args=args, target=Target(pid, title, ctrl))


class TestDenyFirst(unittest.TestCase):
    def test_shell_denied_even_if_somehow_approved(self):
        g = make_guard()
        for tool in sorted(DENY_TOOLS):
            c = Call(name=tool, args={"cmd": "echo hi"}, target=None)
            with self.assertRaises(GuardError):
                g.check(c, "launch-token-1", None)

    def test_mcp_prefixed_denied(self):
        g = make_guard()
        c = Call(name="mcp__gmail__send", args={}, target=None)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", None)

    def test_unknown_tool_refused(self):
        g = make_guard()
        c = Call(name="omg.new_tool", args={}, target=None)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", None)


class TestApproveBinding(unittest.TestCase):
    def test_unapproved_ui_call_blocked(self):
        g = make_guard()
        with self.assertRaises(GuardError):
            g.check(ui_click(), "launch-token-1", Target(100, "Notepad", "Export"))

    def test_approved_ui_call_passes(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        ap = g.check(c, "launch-token-1", Target(100, "Notepad", "Export"))
        self.assertEqual(ap.target.pid, 100)

    def test_args_tamper_blocked(self):
        g = make_guard()
        g.mint(ui_click())
        tampered = ui_click(ctrl="Delete")
        with self.assertRaises(GuardError):
            g.check(tampered, "launch-token-1", Target(100, "Notepad", "Delete"))

    def test_key_order_irrelevant(self):
        g = make_guard()
        args1 = {"a": 1, "b": {"x": 1, "y": 2}}
        args2 = {"b": {"y": 2, "x": 1}, "a": 1}
        c1 = Call(name="ui.type", args=args1, target=None)
        c2 = Call(name="ui.type", args=args2, target=None)
        g.mint(c1)
        g.check(c2, "launch-token-1", None)  # canonical JSON sorts keys

    def test_bad_token_fails_closed(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "wrong-token", Target(100, "Notepad", "Export"))
        with self.assertRaises(GuardError):
            g.check(c, "", Target(100, "Notepad", "Export"))


class TestTargetRecheck(unittest.TestCase):
    def test_stale_target_refused(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", Target(100, "Notepad", "Export2"))

    def test_no_live_target_refused(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", None)


class TestIrreversible(unittest.TestCase):
    def test_irreversible_without_second_confirm_refused(self):
        g = make_guard()
        c = Call(
            name="ui.click",
            args={"pid": 1, "window": "w", "control": "Delete"},
            action_class="delete-file",
            irreversible=True,
            target=Target(1, "w", "Delete"),
        )
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", Target(1, "w", "Delete"))

    def test_irreversible_with_second_confirm_passes(self):
        g = make_guard()
        c = Call(
            name="ui.click",
            args={"pid": 1, "window": "w", "control": "Delete", "__second_confirmed__": True},
            action_class="delete-file",
            irreversible=True,
            target=Target(1, "w", "Delete"),
        )
        g.mint(c)
        g.check(c, "launch-token-1", Target(1, "w", "Delete"))


class TestReadOnly(unittest.TestCase):
    def test_list_windows_allowed_without_approval(self):
        g = make_guard()
        c = Call(name="list_windows", args={}, target=None)
        g.check(c, "launch-token-1", None)  # no exception


class TestExecuteUnimplemented(unittest.TestCase):
    def test_execute_raises_not_piloted(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        ap = g.check(c, "launch-token-1", Target(100, "Notepad", "Export"))
        with self.assertRaises(NotPilotedYet):
            execute(c, ap)


if __name__ == "__main__":
    unittest.main()
