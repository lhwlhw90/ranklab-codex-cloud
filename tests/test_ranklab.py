import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ranklab import Query, load_queries, precision_at_k, recall_at_k


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


class RecallTests(unittest.TestCase):
    def test_cutoff_counts_only_top_k(self):
        query = Query("search", ["A", "B", "C"], {"A", "C", "D"})
        self.assertAlmostEqual(recall_at_k(query, 2), 1 / 3)
        self.assertAlmostEqual(recall_at_k(query, 3), 2 / 3)

    def test_short_ranking_uses_all_relevant_documents_as_denominator(self):
        query = Query("short", ["A"], {"A", "B", "C", "D"})
        self.assertEqual(recall_at_k(query, 2), 0.25)

    def test_empty_relevance_or_ranking(self):
        self.assertEqual(recall_at_k(Query("unlabeled", ["A"], set()), 2), 0)
        self.assertEqual(recall_at_k(Query("empty", [], {"A"}), 2), 0)
        self.assertEqual(recall_at_k(Query("both empty", [], set()), 2), 0)

    def test_all_relevant_documents_found(self):
        self.assertEqual(recall_at_k(Query("complete", ["A", "B"], {"A", "B"}), 5), 1)

    def test_nonpositive_cutoff(self):
        for k in (0, -1):
            for relevant in (set(), {"A"}):
                with self.subTest(k=k, relevant=relevant):
                    with self.assertRaisesRegex(ValueError, "k must be positive"):
                        recall_at_k(Query("q", [], relevant), k)


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

    def test_explicit_precision(self):
        result = self.run_cli(SAMPLE, "--metric", "precision")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "precision@2 = 0.5000\n")

    def test_recall_averages_queries_equally(self):
        for k, score in [(2, "0.6667"), (3, "0.8333")]:
            with self.subTest(k=k):
                result = self.run_cli(SAMPLE, "--metric", "recall", "--k", str(k))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, f"recall@{k} = {score}\n")

    def test_recall_average_includes_empty_relevance(self):
        rows = [
            {"query": "labeled", "ranked": ["A"], "relevant": ["A"]},
            {"query": "unlabeled", "ranked": ["B"], "relevant": []},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "queries.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            result = self.run_cli(path, "--metric", "recall")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "recall@2 = 0.5000\n")

    def test_invalid_metric_exits_with_error(self):
        result = self.run_cli(SAMPLE, "--metric", "f1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", result.stderr)

    def test_invalid_cutoff_exits_with_error(self):
        result = self.run_cli(SAMPLE, "--k", "0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("k must be positive", result.stderr)

    def test_recall_invalid_cutoff_exits_with_error(self):
        for k in (0, -1):
            with self.subTest(k=k):
                result = self.run_cli(SAMPLE, "--metric", "recall", "--k", str(k))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("k must be positive", result.stderr)


if __name__ == "__main__":
    unittest.main()
