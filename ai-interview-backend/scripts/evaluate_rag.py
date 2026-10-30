"""Evaluate question-bank retrieval with Recall@K, MRR, hit rate and latency.

Input JSON format:
[
  {"query": "Python async 面试", "relevant_ids": [1, 3]},
  {"query": "Redis 缓存", "relevant_ids": [8]}
]

Run from the backend directory:
    python scripts/evaluate_rag.py --dataset scripts/rag_eval.example.json --k 5
"""

import argparse
import asyncio
import json
import math
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.db.base import get_session_local  # noqa: E402
from app.services.backoffice.question_bank_service import QuestionBankService  # noqa: E402


async def evaluate(dataset: list[dict], k: int, mode: str) -> dict:
    recall_values = []
    reciprocal_ranks = []
    hits = []
    latencies_ms = []

    async with get_session_local()() as db:
        for case in dataset:
            relevant = {int(item) for item in case.get("relevant_ids", [])}
            started = time.perf_counter()
            results = await QuestionBankService.retrieve_questions(
                query=case["query"],
                db=db,
                k=k,
                search_mode=mode,
                min_score=0.0,
            )
            latencies_ms.append((time.perf_counter() - started) * 1000)
            retrieved = [int(item["id"]) for item in results]
            overlap = relevant.intersection(retrieved)
            recall_values.append(len(overlap) / len(relevant) if relevant else 0.0)
            first_rank = next(
                (index + 1 for index, item_id in enumerate(retrieved) if item_id in relevant),
                None,
            )
            reciprocal_ranks.append(1 / first_rank if first_rank else 0.0)
            hits.append(1.0 if overlap else 0.0)

    total = len(dataset) or 1
    return {
        "k": k,
        "cases": len(dataset),
        "search_mode": mode,
        f"recall@{k}": round(sum(recall_values) / total, 4),
        "mrr": round(sum(reciprocal_ranks) / total, 4),
        "hit_rate": round(sum(hits) / total, 4),
        "latency_ms": {
            "avg": round(sum(latencies_ms) / total, 2),
            "p95": round(sorted(latencies_ms)[max(0, math.ceil(len(latencies_ms) * 0.95) - 1)], 2)
            if latencies_ms
            else 0.0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["semantic", "keyword", "hybrid", "advanced"],
        choices=["semantic", "keyword", "hybrid", "advanced"],
    )
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    async def run_all() -> dict:
        results = {}
        for mode in args.modes:
            results[mode] = await evaluate(dataset, args.k, mode)
        hybrid = results.get("hybrid")
        if hybrid and "advanced" in results:
            results["advanced"]["delta_vs_hybrid"] = {
                f"recall@{args.k}": round(results["advanced"][f"recall@{args.k}"] - hybrid[f"recall@{args.k}"], 4),
                "mrr": round(results["advanced"]["mrr"] - hybrid["mrr"], 4),
                "hit_rate": round(results["advanced"]["hit_rate"] - hybrid["hit_rate"], 4),
                "avg_latency_ms": round(
                    results["advanced"]["latency_ms"]["avg"] - hybrid["latency_ms"]["avg"],
                    2,
                ),
            }
        return results

    print(json.dumps(asyncio.run(run_all()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
