import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "helper"))

from piwin_helper import (  # noqa: E402
    DENY_TOOLS, Guard, GuardError, Target, Call, NotPilotedYet, execute,
    call_hash, canonical_json, IRREVERSIBLE_ACTION_CLASSES,
)


def make_guard():
    g = Guard()
    g.set_launch_token("launch-token-1")
    return g


def ui_click(pid=100, window="Notepad", control="Export", action_class="ui", **extra):
    args = {"pid": pid, "window": window, "control": control}
    args.update(extra)
    return Call(name="ui.click", args=args, action_class=action_class,
                target=Target(pid, window, control))


class TestDenyFirst(unittest.TestCase):
    def test_shell_denied_at_check(self):
        g = make_guard()
        for tool in sorted(DENY_TOOLS):
            c = Call(name=tool, args={"cmd": "echo hi"}, target=None)
            with self.assertRaises(GuardError):
                g.check(c, "launch-token-1", None)

    def test_shell_denied_at_mint(self):
        # fix 3: mint() must refuse DENY tools too — no hash ever stored.
        g = make_guard()
        for tool in sorted(DENY_TOOLS):
            c = Call(name=tool, args={"cmd": "echo hi"}, target=None)
            with self.assertRaises(GuardError):
                g.mint(c)

    def test_mcp_prefixed_denied_at_check_and_mint(self):
        g = make_guard()
        c = Call(name="mcp__gmail__send", args={}, target=None)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", None)
        with self.assertRaises(GuardError):
            g.mint(c)

    def test_unknown_tool_refused_at_check_and_mint(self):
        g = make_guard()
        c = Call(name="omg.new_tool", args={}, target=None)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", None)
        with self.assertRaises(GuardError):
            g.mint(c)


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
        tampered = ui_click(control="Delete")
        with self.assertRaises(GuardError):
            g.check(tampered, "launch-token-1", Target(100, "Notepad", "Delete"))

    def test_key_order_irrelevant(self):
        g = make_guard()
        args1 = {"a": 1, "b": {"x": 1, "y": 2}, "window": "w", "pid": 1, "control": "c"}
        args2 = {"b": {"y": 2, "x": 1}, "a": 1, "control": "c", "window": "w", "pid": 1}
        c1 = Call(name="ui.type", args=args1, target=Target(1, "w", "c"))
        c2 = Call(name="ui.type", args=args2, target=Target(1, "w", "c"))
        g.mint(c1)
        g.check(c2, "launch-token-1", Target(1, "w", "c"))

    def test_bad_token_fails_closed(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "wrong-token", Target(100, "Notepad", "Export"))
        with self.assertRaises(GuardError):
            g.check(c, "", Target(100, "Notepad", "Export"))


class TestIrreversibleAtMint(unittest.TestCase):
    """fix 1: irreversibility is recorded at mint from the action class."""

    def test_action_class_gates_even_if_caller_lies(self):
        g = make_guard()
        # caller tries to pass a delete-file step as ordinary
        c = ui_click(control="Delete", action_class="delete-file")
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", Target(100, "Notepad", "Delete"))

    def test_confirm_second_with_exact_target_passes(self):
        g = make_guard()
        c = ui_click(control="Delete", action_class="delete-file")
        h = g.mint(c)
        g.confirm_second(h, Target(100, "Notepad", "Delete"))
        g.check(c, "launch-token-1", Target(100, "Notepad", "Delete"))  # ok

    def test_confirm_second_wrong_target_refused(self):
        g = make_guard()
        c = ui_click(control="Delete", action_class="delete-file")
        h = g.mint(c)
        with self.assertRaises(GuardError):
            g.confirm_second(h, Target(100, "Notepad", "OtherControl"))

    def test_dunder_keys_are_not_a_confirm_channel(self):
        # __second_confirmed__ in args must NOT grant a confirm
        g = make_guard()
        c = ui_click(control="Delete", action_class="delete-file",
                     **{"__second_confirmed__": True})
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", Target(100, "Notepad", "Delete"))

    def test_dunder_keys_stripped_from_hash(self):
        # same args ± __keys produce the SAME hash (stripped, not part of call)
        g = make_guard()
        base = ui_click()
        withdu = ui_click(**{"__anything__": 1})
        self.assertEqual(call_hash("ui.click", base.args),
                         call_hash("ui.click", withdu.args))

    def test_extra_confirm_can_add_never_waive(self):
        g = make_guard()
        c = Call(
            name="ui.click",
            args={"pid": 100, "window": "Notepad", "control": "Export"},
            action_class="ui", extra_confirm=True,
            target=Target(100, "Notepad", "Export"),
        )
        h = g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", Target(100, "Notepad", "Export"))
        g.confirm_second(h, Target(100, "Notepad", "Export"))
        g.check(c, "launch-token-1", Target(100, "Notepad", "Export"))

    def test_irreversible_classes_all_gate(self):
        for cls in sorted(IRREVERSIBLE_ACTION_CLASSES):
            g = make_guard()
            c = ui_click(action_class=cls)
            g.mint(c)
            with self.assertRaises(GuardError):
                g.check(c, "launch-token-1", Target(100, "Notepad", "Export"))


class TestTargetRequired(unittest.TestCase):
    """fix 2: ui.* needs full targets on approval AND live side."""

    def test_mint_without_target_refused(self):
        g = make_guard()
        c = Call(name="ui.click", args={"pid": 1, "window": "w", "control": "c"},
                 target=None)
        with self.assertRaises(GuardError):
            g.mint(c)

    def test_check_without_live_target_refused(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", None)

    def test_stale_target_refused(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", Target(100, "Notepad", "Export2"))

    def test_partial_target_refused(self):
        g = make_guard()
        c = ui_click()
        g.mint(c)
        with self.assertRaises(GuardError):
            g.check(c, "launch-token-1", Target(None, "Notepad", "Export"))


class TestReadOnly(unittest.TestCase):
    def test_list_windows_allowed_without_approval(self):
        g = make_guard()
        c = Call(name="list_windows", args={}, target=None)
        g.check(c, "launch-token-1", None)  # no exception


class TestHashVectors(unittest.TestCase):
    def test_float_normalization(self):
        self.assertEqual(call_hash("ui.click", {"x": 1.0}),
                         call_hash("ui.click", {"x": 1}))

    def test_float_normalization_nested(self):
        self.assertEqual(call_hash("ui.type", {"opts": {"v": 2.0}}),
                         call_hash("ui.type", {"opts": {"v": 2}}))

    def test_vectors_file_reproduced(self):
        import json
        p = os.path.join(os.path.dirname(__file__), "hash_vectors.json")
        with open(p, encoding="utf-8") as f:
            for v in json.load(f):
                self.assertEqual(
                    call_hash(v["name"], v["args"]), v["sha256"],
                    msg=f"vector {v['name']} {v['args']}",
                )


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
