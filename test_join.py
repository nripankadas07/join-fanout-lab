import itertools
import random
import tempfile
import unittest
from pathlib import Path

import polars as pl
from join_fanout_lab import analyze, load, main, write_html


class JoinTest(unittest.TestCase):
    def test_actual_polars_oracle(self):
        rng = random.Random(17)
        for nulls, how in itertools.product(
            (False, True), ("inner", "left", "right", "full", "semi", "anti")
        ):
            for _ in range(12):
                left = [
                    {"k": rng.choice([None, 0, 1, 2]), "zone": rng.choice(["A", "B"])}
                    for i in range(9)
                ]
                right = [
                    {"k": rng.choice([None, 0, 1, 3]), "zone": rng.choice(["A", "B"])}
                    for i in range(8)
                ]
                data = {
                    "left": left,
                    "right": right,
                    "keys": ["k", "zone"],
                    "how": how,
                    "nulls_equal": nulls,
                }
                actual = (
                    pl.DataFrame(left)
                    .join(
                        pl.DataFrame(right),
                        on=["k", "zone"],
                        how=how,
                        nulls_equal=nulls,
                    )
                    .height
                )
                self.assertEqual(analyze(data)["output_rows"], actual, (how, nulls))

    def test_explosive_key_is_explained_without_expanding(self):
        d = {
            "left": [{"k": "A"}] * 400,
            "right": [{"k": "A"}] * 500,
            "keys": ["k"],
            "max_rows": 1000,
        }
        r = analyze(d)
        self.assertEqual(r["output_rows"], 200000)
        self.assertEqual(r["many_to_many_keys"], 1)
        self.assertTrue(r["over_budget"])
        self.assertEqual(r["top_keys"][0]["matched_pairs"], 200000)

    def test_null_rows_are_not_a_single_matching_group_by_default(self):
        d = {
            "left": [{"k": None}] * 2,
            "right": [{"k": None}] * 3,
            "keys": ["k"],
            "how": "full",
        }
        self.assertEqual(analyze(d)["output_rows"], 5)
        d["nulls_equal"] = True
        self.assertEqual(analyze(d)["output_rows"], 6)

    def test_empty_side_and_budget_boundary(self):
        d = {
            "left": [],
            "right": [{"k": "a"}],
            "keys": ["k"],
            "how": "full",
            "max_rows": 1,
        }
        r = analyze(d)
        self.assertEqual(r["output_rows"], 1)
        self.assertFalse(r["over_budget"])

    def test_refuses_ambiguous_coercion(self):
        for values in [(True, 1), ("1", 1), (1, 1.0)]:
            with self.assertRaises(ValueError):
                analyze(
                    {
                        "left": [{"k": values[0]}],
                        "right": [{"k": values[1]}],
                        "keys": ["k"],
                    }
                )

    def test_invalid_missing_key_and_duplicate_json(self):
        with self.assertRaises(ValueError):
            analyze({"left": [{}], "right": [], "keys": ["k"]})
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x"
            p.write_text('{"left":[],"left":[]}')
            with self.assertRaises(ValueError):
                load(p)

    def test_cli_failure_and_html_escape(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "x"
            p.write_text("{}")
            self.assertEqual(main([str(p)]), 2)
            out = Path(t) / "r.html"
            write_html(analyze({"left":[{"k":"</script><img onerror=alert(1)>"}],"right":[],"keys":["k"],"how":"left"}), out)
            self.assertNotIn("<img onerror", out.read_text())
            self.assertIn("&lt;img", out.read_text())


if __name__ == "__main__":
    unittest.main()
