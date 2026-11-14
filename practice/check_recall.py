"""通过命令行验收 Recall@K 练习。运行 python3 practice/check_recall.py。"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "queries.json"


class RecallExercise(unittest.TestCase):
    def assert_cli_output(self, data_file, expected, *flags, k=2):
        result = subprocess.run(
            [sys.executable, "ranklab.py", str(data_file), "--k", str(k), *flags],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr.strip())
        self.assertEqual(result.stdout.strip(), expected)

    def assert_recall(self, queries, expected):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "queries.json"
            path.write_text(json.dumps(queries), encoding="utf-8")
            self.assert_cli_output(path, expected, "--metric", "recall")

    def test_default_precision(self):
        self.assert_cli_output(EXAMPLE, "precision@2 = 0.5000")

    def test_explicit_precision(self):
        self.assert_cli_output(EXAMPLE, "precision@2 = 0.5000", "--metric", "precision")

    def test_sample_macro_recall(self):
        self.assert_cli_output(EXAMPLE, "recall@2 = 0.6667", "--metric", "recall")
        self.assert_cli_output(EXAMPLE, "recall@3 = 0.8333", "--metric", "recall", k=3)

    def test_empty_relevant_counts_in_average(self):
        self.assert_recall(
            [
                {"query": "q1", "ranked": ["A"], "relevant": ["A"]},
                {"query": "q2", "ranked": ["B"], "relevant": []},
            ],
            "recall@2 = 0.5000",
        )

    def test_empty_ranked(self):
        self.assert_recall(
            [{"query": "q1", "ranked": [], "relevant": ["A"]}],
            "recall@2 = 0.0000",
        )

    def test_short_ranked(self):
        self.assert_recall(
            [{"query": "q1", "ranked": ["A"], "relevant": ["A", "B", "C", "D"]}],
            "recall@2 = 0.2500",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
