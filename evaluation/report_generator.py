"""
Report Generator for Blueprint Eye evaluation benchmark suite.
Reads results.json and history archives to generate evaluation_report.md
and output a clean terminal visual summary.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("BlueprintEyeReportGenerator")


def load_previous_run(history_dir: Path, current_results_file: Path) -> Optional[List[Dict[str, Any]]]:
    """Finds and loads the latest historical run file prior to the current run."""
    if not history_dir.exists():
        return None
    files = sorted([f for f in history_dir.glob("run_*.json") if f.resolve() != current_results_file.resolve()])
    if not files:
        return None
    latest_file = files[-1]
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded previous benchmark history run from: %s", latest_file.name)
        return data
    except Exception as err:
        logger.warning("Failed loading previous benchmark run %s: %s", latest_file.name, err)
        return None


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes comprehensive summary and category-wise evaluation metrics."""
    total = len(results)
    if total == 0:
        return {}

    passed_count = sum(1 for r in results if r["pass"])
    failed_count = total - passed_count
    accuracy_pct = (passed_count / total) * 100.0

    fallback_count = sum(1 for r in results if "could not find" in str(r.get("answer", "")).lower())
    fallback_rate_pct = (fallback_count / total) * 100.0

    total_latency = sum(r.get("latency_ms", 0.0) for r in results)
    avg_latency_ms = total_latency / total
    avg_latency_sec = avg_latency_ms / 1000.0

    # Source Accuracy (Stage 2)
    source_correct = sum(1 for r in results if r.get("stage_scores", {}).get("selection", False))
    source_accuracy_pct = (source_correct / total) * 100.0

    # Keyword Recall (Stage 3)
    kw_passed = sum(1 for r in results if r.get("stage_scores", {}).get("generation", False))
    keyword_recall_pct = (kw_passed / total) * 100.0

    # Diagnostic averages
    diag_list = [r.get("diagnostics", {}) for r in results if r.get("diagnostics")]
    avg_candidate_chunks = (
        sum(d.get("candidate_chunks", d.get("raw_count", 0)) for d in diag_list) / len(diag_list)
        if diag_list
        else 0.0
    )
    avg_selected_chunks = (
        sum(d.get("selected_chunks", d.get("returned_count", 0)) for d in diag_list) / len(diag_list)
        if diag_list
        else 0.0
    )
    avg_highest_similarity = (
        sum(d.get("highest_similarity", 0.0) for d in diag_list) / len(diag_list)
        if diag_list
        else 0.0
    )

    # Category-wise breakdown
    categories: Dict[str, Dict[str, Any]] = {}
    for r in results:
        cat = r.get("category", "general")
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0, "failed": 0}
        categories[cat]["total"] += 1
        if r["pass"]:
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1

    for cat, data in categories.items():
        data["accuracy_pct"] = (data["passed"] / data["total"]) * 100.0 if data["total"] > 0 else 0.0

    return {
        "total": total,
        "passed": passed_count,
        "failed": failed_count,
        "accuracy_pct": accuracy_pct,
        "fallback_count": fallback_count,
        "fallback_rate_pct": fallback_rate_pct,
        "avg_latency_ms": avg_latency_ms,
        "avg_latency_sec": avg_latency_sec,
        "source_accuracy_pct": source_accuracy_pct,
        "keyword_recall_pct": keyword_recall_pct,
        "avg_candidate_chunks": avg_candidate_chunks,
        "avg_selected_chunks": avg_selected_chunks,
        "avg_highest_similarity": avg_highest_similarity,
        "categories": categories,
    }


def generate_report(results_file: Optional[Path] = None) -> Tuple[Path, str]:
    """Generates evaluation_report.md and prints visual summary banner."""
    eval_dir = PROJECT_ROOT / "evaluation"
    results_path = results_file or (eval_dir / "results.json")
    report_path = eval_dir / "evaluation_report.md"
    history_dir = eval_dir / "history"

    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found at: {results_path}")

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    curr_metrics = calculate_metrics(results)
    prev_results = load_previous_run(history_dir, results_path)
    prev_metrics = calculate_metrics(prev_results) if prev_results else None

    # Format Markdown Report
    lines: List[str] = []
    lines.append("# Blueprint Eye Evaluation Report\n")
    lines.append("## Benchmark Executive Summary\n")
    lines.append("| Metric | Value | Delta vs Previous Run |")
    lines.append("| :--- | :--- | :--- |")

    def format_delta(curr: float, prev: Optional[float], unit: str = "%", is_lower_better: bool = False) -> str:
        if prev is None:
            return "N/A (First Run)"
        diff = curr - prev
        if abs(diff) < 0.01:
            return "No change"
        sign = "+" if diff > 0 else ""
        text = f"{sign}{diff:.1f}{unit}"
        if (diff > 0 and not is_lower_better) or (diff < 0 and is_lower_better):
            return f"🟢 **{text}**"
        return f"🔴 **{text}**"

    lines.append(f"| **Questions Tested** | {curr_metrics['total']} | - |")
    lines.append(f"| **Passed Questions** | {curr_metrics['passed']} | - |")
    lines.append(f"| **Failed Questions** | {curr_metrics['failed']} | - |")
    lines.append(f"| **Overall Accuracy** | **{curr_metrics['accuracy_pct']:.1f}%** | {format_delta(curr_metrics['accuracy_pct'], prev_metrics.get('accuracy_pct') if prev_metrics else None)} |")
    lines.append(f"| **Source Page Accuracy** | {curr_metrics['source_accuracy_pct']:.1f}% | {format_delta(curr_metrics['source_accuracy_pct'], prev_metrics.get('source_accuracy_pct') if prev_metrics else None)} |")
    lines.append(f"| **Keyword Recall** | {curr_metrics['keyword_recall_pct']:.1f}% | {format_delta(curr_metrics['keyword_recall_pct'], prev_metrics.get('keyword_recall_pct') if prev_metrics else None)} |")
    lines.append(f"| **Fallback Rate** | {curr_metrics['fallback_rate_pct']:.1f}% ({curr_metrics['fallback_count']} queries) | {format_delta(curr_metrics['fallback_rate_pct'], prev_metrics.get('fallback_rate_pct') if prev_metrics else None, is_lower_better=True)} |")
    lines.append(f"| **Average Latency** | {curr_metrics['avg_latency_sec']:.2f} sec ({curr_metrics['avg_latency_ms']:.1f} ms) | {format_delta(curr_metrics['avg_latency_sec'], prev_metrics.get('avg_latency_sec') if prev_metrics else None, unit='s', is_lower_better=True)} |")
    lines.append(f"| **Avg Selected Chunks** | {curr_metrics['avg_selected_chunks']:.1f} | - |")
    lines.append(f"| **Avg Highest Similarity** | {curr_metrics['avg_highest_similarity']:.2f} | - |")
    lines.append("\n---\n")

    # Category Breakdown Table
    lines.append("## Category-Wise Performance\n")
    lines.append("| Category | Total Questions | Passed | Failed | Accuracy % |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for cat, c_data in sorted(curr_metrics["categories"].items()):
        lines.append(f"| `{cat}` | {c_data['total']} | {c_data['passed']} | {c_data['failed']} | **{c_data['accuracy_pct']:.1f}%** |")
    lines.append("\n---\n")

    # Detailed Question Breakdown
    lines.append("## Detailed Itemized Results\n")
    lines.append("| ID | Category | Question | Exp Page | Ret Page | Status | Failure Reason |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for r in results:
        exp_p = str(r.get("expected_page")) if r.get("expected_page") is not None else "None"
        ret_p = ", ".join(str(p) for p in r.get("returned_pages", [])) if r.get("returned_pages") else "None"
        status_md = "🟢 PASS" if r["pass"] else "🔴 FAIL"
        fail_reason_md = f"`{r['failure_reason']}`" if r.get("failure_reason") else "-"
        q_snippet = r["question"][:45] + "..." if len(r["question"]) > 45 else r["question"]
        lines.append(f"| {r['id']} | `{r['category']}` | {q_snippet} | {exp_p} | {ret_p} | {status_md} | {fail_reason_md} |")

    lines.append("\n---\n")

    # Limitations Section
    lines.append("## Benchmark Limitations\n")
    lines.append("1. **Heuristic Keyword Verification**: Keyword recall checks for required technical terms in generated text. High keyword recall correlates with correctness but does not replace expert domain review.")
    lines.append("2. **Semantic Verification Boundary**: Evaluation checks exact source page references and deterministic extraction rules. Semantic nuance may require manual validation.")
    lines.append("3. **Source Metadata Dependency**: Source accuracy metrics rely on page metadata extracted during PDF ingestion.")
    lines.append("4. **Synthesis vs Extraction**: Summary queries evaluate presence of key concepts; exact sentence structures may vary.")
    lines.append("\n")

    report_content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    logger.info("Generated markdown report: %s", report_path)

    # Render Visual Terminal Banner
    terminal_banner = (
        f"========================================\n"
        f"Blueprint Eye Benchmark\n"
        f"========================================\n"
        f"Accuracy            {curr_metrics['accuracy_pct']:>5.0f}%\n"
        f"Source Accuracy     {curr_metrics['source_accuracy_pct']:>5.0f}%\n"
        f"Fallback Rate        {curr_metrics['fallback_rate_pct']:>5.0f}%\n"
        f"Avg Response Time  {curr_metrics['avg_latency_sec']:>5.2f} sec\n"
        f"========================================\n"
        f"PASS  {curr_metrics['passed']:>2d}\n"
        f"FAIL   {curr_metrics['failed']:>2d}\n"
        f"========================================\n"
    )
    print("\n" + terminal_banner)

    return report_path, terminal_banner


if __name__ == "__main__":
    generate_report()
