import random
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from actions import ACTION_META, apply_action  # noqa: E402
from oracle import evaluate_one  # noqa: E402

SEED = "<script>alert(1)</script>"


class ActionTests(unittest.TestCase):
    def test_catalog_has_27(self):
        self.assertEqual(len(ACTION_META), 27)
        for i in range(1, 28):
            self.assertIn(i, ACTION_META)

    def test_a1_inserts_before_javascript(self):
        out = apply_action(1, '<a href="javascript:alert(1)">x</a>')
        self.assertIn("&#14", out)
        self.assertRegex(out, r"(?i)javascript")
        self.assertIn("alert", out)

    def test_a18_is_not_noop(self):
        out = apply_action(18, SEED)
        self.assertIn("\\u", out)
        self.assertNotEqual(out, SEED)

    def test_a21_does_not_double_call(self):
        out = apply_action(21, SEED)
        self.assertIn("top['al'+'ert']", out)
        self.assertNotIn("(1)(1)", out)
        self.assertIn("(1)", out)

    def test_each_action_returns_str(self):
        rng = random.Random(0)
        for action_id in range(1, 28):
            out = apply_action(action_id, SEED, rng=rng)
            self.assertIsInstance(out, str)
            self.assertTrue(len(out) > 0)

    def test_priority_actions_still_execute(self):
        """Mutations that must keep a <script>alert(1)</script> payload executing."""
        keepers = [14, 18, 21, 22, 23, 27]
        for action_id in keepers:
            mutated = apply_action(action_id, SEED, rng=random.Random(0))
            result = evaluate_one(mutated)
            self.assertTrue(
                result.executed,
                f"{ACTION_META[action_id]['name']} lost execution: {mutated!r}",
            )

    def test_img_onerror_still_executes_after_double_tag(self):
        seed = "<img src=x onerror=alert(1)>"
        mutated = apply_action(9, seed, rng=random.Random(0))
        result = evaluate_one(mutated)
        self.assertTrue(result.executed, mutated)


if __name__ == "__main__":
    unittest.main()
