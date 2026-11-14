import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ranklab import Query, load_queries, precision_at_k


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "queries.json"


class PrecisionTests(unittest.TestCase):
    def test_cutoff_counts_only_top_k(self):
        query = Query("search", ["A", "B", "C"], {"A", "C", "D"})
        self.assertEqual(precision_at_k(query, 2), 0.5)

    def test_missing_positions_are_misses(self):
        self.assertEqual(precision_at_k(Query("short", ["A"], {"A"}), 4), 0.25)

    def test_empty_relevance_or_ranking(self):
        self.assertEqual(precision_at_k(Query("unlabeled", ["A"], set()), 2), 0)
        self.assertEqual(precision_at_k(Query("empty", [], {"A"}), 2), 0)

    def test_nonpositive_cutoff(self):
        for k in (0, -1):
            with self.subTest(k=k), self.assertRaisesRegex(ValueError, "k must be positive"):
                precision_at_k(Query("q", [], set()), k)


class InputTests(unittest.TestCase):
    def test_invalid_dataset(self):
        invalid_cases = [
            ([], "nonempty JSON array"),
            ([{"query": "q", "ranked": ["A", "A"], "relevant": ["A"]}], "duplicate"),
            ([{"query": "q", "ranked": ["A"]}], "relevant"),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            for rows, message in invalid_cases:
                with self.subTest(rows=rows), self.assertRaisesRegex(ValueError, message):
                    path.write_text(json.dumps(rows), encoding="utf-8")
                    load_queries(path)


class CliTests(unittest.TestCase):
    def run_cli(self, dataset, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "ranklab.py"), str(dataset), *args],
            capture_output=True,
            text=True,
        )

    def test_default_cli(self):
        result = self.run_cli(SAMPLE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "precision@2 = 0.5000\n")

    def test_cli_averages_queries_equally(self):
        for k, score in [(1, "1.0000"), (3, "0.5000")]:
            with self.subTest(k=k):
                result = self.run_cli(SAMPLE, "--k", str(k))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, f"precision@{k} = {score}\n")

    def test_invalid_cutoff_exits_with_error(self):
        result = self.run_cli(SAMPLE, "--k", "0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("k must be positive", result.stderr)


if __name__ == "__main__":
    unittest.main()
