"""
Synchronous RAG Evaluator for Blueprint Eye evaluation benchmark suite.
Executes dataset queries against live RAG endpoint, performs 3-stage evaluation,
determines structured failure reasons, and persists results to results.json and history/.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("BlueprintEyeEvaluator")


class Evaluator:
    """Synchronous benchmark evaluator for Blueprint Eye."""

    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8000/api/v1/ask",
        dataset_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        self.api_url = api_url
        self.eval_dir = output_dir or (PROJECT_ROOT / "evaluation")
        self.dataset_path = dataset_path or (self.eval_dir / "dataset.json")
        self.history_dir = self.eval_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Loads evaluation dataset entries from dataset.json."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found at: {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded %d questions from %s", len(data), self.dataset_path.name)
        return data

    def evaluate_question(self, item: Dict[str, Any], client: httpx.Client) -> Dict[str, Any]:
        """
        Sends synchronous POST request to /api/v1/ask and evaluates:
        - Stage 1: Retrieval Quality (expected page present in sources/diagnostics)
        - Stage 2: Context Selection Quality (expected page in returned sources)
        - Stage 3: Generation Quality (answer correctness, keyword recall, fallback validity)
        """
        question = item["question"]
        expected_page = item.get("expected_page")
        expected_keywords = [k.lower() for k in item.get("expected_keywords", [])]
        category = item.get("category", "general")

        payload = {"question": question}
        start_time = time.perf_counter()
        
        try:
            resp = client.post(self.api_url, json=payload, timeout=120.0)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if resp.status_code != 200:
                return {
                    "id": item["id"],
                    "category": category,
                    "question": question,
                    "answer": f"[HTTP Error {resp.status_code}]",
                    "sources": [],
                    "latency_ms": latency_ms,
                    "diagnostics": {},
                    "pass": False,
                    "failure_reason": "No answer returned",
                    "stage_scores": {"retrieval": False, "selection": False, "generation": False},
                }
            data = resp.json()
        except (httpx.ConnectError, httpx.NetworkError):
            # Fallback to FastAPI TestClient if uvicorn is not running locally
            from fastapi.testclient import TestClient
            from backend.main import app

            t0 = time.perf_counter()
            test_client = TestClient(app)
            resp = test_client.post("/api/v1/ask", json=payload)
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            if resp.status_code != 200:
                return {
                    "id": item["id"],
                    "category": category,
                    "question": question,
                    "answer": f"[HTTP Error {resp.status_code}]",
                    "sources": [],
                    "latency_ms": latency_ms,
                    "diagnostics": {},
                    "pass": False,
                    "failure_reason": "No answer returned",
                    "stage_scores": {"retrieval": False, "selection": False, "generation": False},
                }
            data = resp.json()
        except Exception as err:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "id": item["id"],
                "category": category,
                "question": question,
                "answer": f"[Connection Exception: {str(err)}]",
                "sources": [],
                "latency_ms": latency_ms,
                "diagnostics": {},
                "pass": False,
                "failure_reason": "No answer returned",
                "stage_scores": {"retrieval": False, "selection": False, "generation": False},
            }

        answer = data.get("answer", "")
        sources = data.get("sources", [])
        diagnostics = data.get("diagnostics") or {}

        returned_pages = [s.get("page") for s in sources if s.get("page") is not None]
        
        # 1. Evaluate Stage 1 & 2 (Retrieval and Selection Page Matching)
        if expected_page is None or category == "negative":
            retrieval_pass = True
            selection_pass = len(sources) == 0
            page_match = len(sources) == 0
        else:
            retrieval_pass = expected_page in returned_pages or diagnostics.get("returned_count", 0) > 0
            selection_pass = expected_page in returned_pages
            page_match = expected_page in returned_pages

        # 2. Evaluate Stage 3 (Keyword Recall & Fallback)
        answer_lower = answer.lower()
        is_fallback_response = "could not find" in answer_lower

        if category == "negative" or expected_page is None:
            fallback_match = is_fallback_response
            keyword_match = True
        else:
            fallback_match = not is_fallback_response
            if expected_keywords:
                matched_count = sum(1 for kw in expected_keywords if kw in answer_lower)
                keyword_match = (matched_count / len(expected_keywords)) >= 0.5
            else:
                keyword_match = True

        length_valid = len(answer.strip()) > 0
        generation_pass = fallback_match and keyword_match and length_valid

        # Overall Question Pass
        overall_pass = page_match and keyword_match and fallback_match and length_valid

        # Determine Structured Failure Reason if Failed
        failure_reason: Optional[str] = None
        if not overall_pass:
            if not length_valid:
                failure_reason = "No answer returned"
            elif (category == "negative" or expected_page is None) and not is_fallback_response:
                failure_reason = "Incorrect fallback behaviour"
            elif not page_match and not is_fallback_response:
                failure_reason = "Wrong source page"
            elif page_match and is_fallback_response:
                failure_reason = "Correct source but incorrect extraction"
            elif page_match and not keyword_match:
                failure_reason = "Missing expected keywords"
            elif not page_match and not is_fallback_response:
                failure_reason = "Hallucinated answer"
            else:
                failure_reason = "Generation failure"

        return {
            "id": item["id"],
            "category": category,
            "question": question,
            "expected_page": expected_page,
            "returned_pages": returned_pages,
            "expected_keywords": item.get("expected_keywords", []),
            "answer": answer,
            "sources": sources,
            "latency_ms": data.get("metrics", {}).get("total_ms", latency_ms),
            "diagnostics": diagnostics,
            "pass": overall_pass,
            "failure_reason": failure_reason,
            "stage_scores": {
                "retrieval": retrieval_pass,
                "selection": selection_pass,
                "generation": generation_pass,
            },
        }

    def run_evaluation(self) -> Path:
        """Executes full evaluation run and saves results.json and history artifact."""
        dataset = self.load_dataset()
        results: List[Dict[str, Any]] = []

        logger.info("Starting synchronous evaluation against %s...", self.api_url)

        with httpx.Client(timeout=120.0) as client:
            for idx, item in enumerate(dataset, start=1):
                logger.info("[%d/%d] Evaluating: '%s'", idx, len(dataset), item['question'][:60])
                res = self.evaluate_question(item, client)
                results.append(res)
                status_str = "PASS" if res["pass"] else f"FAIL ({res['failure_reason']})"
                logger.info("       -> Status: %s (latency: %.1fms)", status_str, res["latency_ms"])

        results_path = self.eval_dir / "results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info("Saved raw evaluation results to %s", results_path)

        # Save timestamped history archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_path = self.history_dir / f"run_{timestamp}.json"
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        logger.info("Saved historical run snapshot to %s", history_path)

        return results_path


if __name__ == "__main__":
    evaluator = Evaluator()
    results_file = evaluator.run_evaluation()

    # Import and run report generator
    from evaluation.report_generator import generate_report
    generate_report(results_file)
