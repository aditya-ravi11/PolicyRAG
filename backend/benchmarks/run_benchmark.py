#!/usr/bin/env python3
"""
PolicyRAG Automated Evaluation Benchmark

Runs ground-truth queries against the live API and reports quality metrics.

Usage:
    python -m benchmarks.run_benchmark --api-url http://localhost:8080
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"


@dataclass
class BenchmarkResult:
    query_id: str
    query: str
    category: str
    passed: bool
    faithfulness: float = 0.0
    citation_precision: float = 0.0
    citation_recall: float = 0.0
    context_relevance: float = 0.0
    overall_trust: float = 0.0
    has_citations: bool = False
    topic_coverage: float = 0.0
    latency_ms: float = 0.0
    error: str = ""


@dataclass
class BenchmarkReport:
    results: list[BenchmarkResult] = field(default_factory=list)
    total_queries: int = 0
    passed: int = 0
    failed: int = 0
    avg_faithfulness: float = 0.0
    avg_trust_score: float = 0.0
    avg_latency_ms: float = 0.0
    avg_citation_precision: float = 0.0
    avg_citation_recall: float = 0.0


def check_topic_coverage(answer: str, expected_topics: list[str]) -> float:
    """Check what fraction of expected topics appear in the answer."""
    answer_lower = answer.lower()
    hits = sum(1 for topic in expected_topics if topic.lower() in answer_lower)
    return hits / len(expected_topics) if expected_topics else 1.0


def run_single_query(client: httpx.Client, api_url: str, gt_entry: dict) -> BenchmarkResult:
    """Run a single benchmark query."""
    query = gt_entry["query"]
    result = BenchmarkResult(
        query_id=gt_entry["id"],
        query=query,
        category=gt_entry.get("category", "unknown"),
        passed=False,
    )

    try:
        start = time.time()
        resp = client.post(
            f"{api_url}/api/v1/query",
            json={"query": query, "no_cache": True},
            timeout=120.0,
        )
        result.latency_ms = (time.time() - start) * 1000

        if resp.status_code != 200:
            result.error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        data = resp.json()
        answer = data.get("answer", "")
        evaluation = data.get("evaluation", {})
        citations = data.get("citations", [])

        result.faithfulness = evaluation.get("faithfulness") or 0.0
        result.citation_precision = evaluation.get("citation_precision") or 0.0
        result.citation_recall = evaluation.get("citation_recall") or 0.0
        result.context_relevance = evaluation.get("context_relevance") or 0.0
        result.overall_trust = evaluation.get("overall_trust_score") or 0.0
        result.has_citations = len(citations) > 0
        result.topic_coverage = check_topic_coverage(answer, gt_entry.get("expected_topics", []))

        # Pass/fail criteria
        min_faith = gt_entry.get("min_faithfulness", 0.6)
        requires_citation = gt_entry.get("requires_citation", True)

        passed = True
        if result.faithfulness < min_faith:
            passed = False
        if requires_citation and not result.has_citations:
            passed = False
        if result.topic_coverage < 0.3:
            passed = False

        result.passed = passed

    except Exception as e:
        result.error = str(e)

    return result


def run_benchmark(api_url: str) -> BenchmarkReport:
    """Run the full benchmark suite."""
    with open(GROUND_TRUTH_PATH) as f:
        ground_truth = json.load(f)

    report = BenchmarkReport(total_queries=len(ground_truth))
    client = httpx.Client()

    print(f"\nRunning {len(ground_truth)} benchmark queries against {api_url}\n")
    print(f"{'ID':<10} {'Category':<18} {'Faith':>6} {'Trust':>6} {'CPrec':>6} {'Topics':>6} {'ms':>8} {'Status'}")
    print("-" * 80)

    for gt_entry in ground_truth:
        result = run_single_query(client, api_url, gt_entry)
        report.results.append(result)

        if result.passed:
            report.passed += 1
            status = "PASS"
        else:
            report.failed += 1
            status = f"FAIL ({result.error[:30]})" if result.error else "FAIL"

        print(
            f"{result.query_id:<10} {result.category:<18} "
            f"{result.faithfulness:>5.1%} {result.overall_trust:>5.1%} "
            f"{result.citation_precision:>5.1%} {result.topic_coverage:>5.1%} "
            f"{result.latency_ms:>7.0f} {status}"
        )

    client.close()

    # Compute averages
    valid = [r for r in report.results if not r.error]
    if valid:
        report.avg_faithfulness = sum(r.faithfulness for r in valid) / len(valid)
        report.avg_trust_score = sum(r.overall_trust for r in valid) / len(valid)
        report.avg_latency_ms = sum(r.latency_ms for r in valid) / len(valid)
        report.avg_citation_precision = sum(r.citation_precision for r in valid) / len(valid)
        report.avg_citation_recall = sum(r.citation_recall for r in valid) / len(valid)

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"  Total queries:        {report.total_queries}")
    print(f"  Passed:               {report.passed}/{report.total_queries} ({report.passed/report.total_queries:.0%})")
    print(f"  Avg faithfulness:     {report.avg_faithfulness:.1%}")
    print(f"  Avg trust score:      {report.avg_trust_score:.1%}")
    print(f"  Avg citation prec:    {report.avg_citation_precision:.1%}")
    print(f"  Avg citation recall:  {report.avg_citation_recall:.1%}")
    print(f"  Avg latency:          {report.avg_latency_ms:.0f}ms")

    return report


def main():
    parser = argparse.ArgumentParser(description="PolicyRAG Evaluation Benchmark")
    parser.add_argument("--api-url", default="http://localhost:8080", help="Backend API URL")
    parser.add_argument("--output", default=None, help="Save JSON report to file")
    args = parser.parse_args()

    report = run_benchmark(args.api_url)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {
                    "total": report.total_queries,
                    "passed": report.passed,
                    "failed": report.failed,
                    "avg_faithfulness": round(report.avg_faithfulness, 3),
                    "avg_trust_score": round(report.avg_trust_score, 3),
                    "avg_citation_precision": round(report.avg_citation_precision, 3),
                    "avg_citation_recall": round(report.avg_citation_recall, 3),
                    "avg_latency_ms": round(report.avg_latency_ms, 1),
                    "results": [
                        {
                            "id": r.query_id,
                            "query": r.query,
                            "category": r.category,
                            "passed": r.passed,
                            "faithfulness": r.faithfulness,
                            "trust": r.overall_trust,
                            "latency_ms": round(r.latency_ms, 1),
                            "error": r.error,
                        }
                        for r in report.results
                    ],
                },
                f,
                indent=2,
            )
        print(f"\nReport saved to {args.output}")

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
