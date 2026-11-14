"""Evaluate a ranked retrieval result for each query in a JSON file."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean


@dataclass
class Query:
    name: str
    ranked: list[str]
    relevant: set[str]


def load_queries(path: Path) -> list[Query]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected a nonempty JSON array of queries")

    queries = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"row {index}: expected a query object")
        name = row.get("query")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"row {index}: query must be a nonempty string")
        for field in ("ranked", "relevant"):
            ids = row.get(field)
            if not isinstance(ids, list) or not all(isinstance(i, str) and i.strip() for i in ids):
                raise ValueError(f"row {index}: {field} must be an array of document IDs")
        if len(row["ranked"]) != len(set(row["ranked"])):
            raise ValueError(f"row {index}: ranked contains duplicate document IDs")
        queries.append(Query(name, row["ranked"], set(row["relevant"])))
    return queries


def precision_at_k(query: Query, k: int) -> float:
    """Divide relevant hits in the first k positions by k, even for short lists."""
    if k < 1:
        raise ValueError("k must be positive")
    hits = sum(doc_id in query.relevant for doc_id in query.ranked[:k])
    return hits / k


def recall_at_k(query: Query, k: int) -> float:
    """Divide relevant hits in the first k positions by all relevant documents."""
    if k < 1:
        raise ValueError("k must be positive")
    if not query.relevant:
        return 0.0
    hits = sum(doc_id in query.relevant for doc_id in query.ranked[:k])
    return hits / len(query.relevant)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="JSON file with query, ranked, relevant fields")
    parser.add_argument("--k", type=int, default=2, help="ranking cutoff (default: 2)")
    parser.add_argument(
        "--metric", choices=("precision", "recall"), default="precision",
        help="retrieval metric (default: precision)",
    )
    args = parser.parse_args()
    metric = precision_at_k if args.metric == "precision" else recall_at_k
    try:
        queries = load_queries(args.dataset)
        score = mean(metric(query, args.k) for query in queries)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"{args.metric}@{args.k} = {score:.4f}")


if __name__ == "__main__":
    main()
