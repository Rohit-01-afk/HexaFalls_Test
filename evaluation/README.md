# Blueprint Eye Evaluation Framework

The **Blueprint Eye Evaluation Framework** is a standalone, enterprise-grade automated benchmark suite for measuring the end-to-end performance, retrieval precision, context selection efficiency, and answer generation quality of the technical manual assistant.

The evaluation suite runs completely independently of production services by issuing REST API calls to the `/api/v1/ask` endpoint.

---

## Directory Layout

```
evaluation/
├── README.md                 # Evaluation framework usage guide
├── dataset_template.json     # Schema template for dataset extension
├── dataset.json              # Verified gold-standard benchmark dataset
├── evaluator.py              # Synchronous test runner & 3-stage evaluator
├── report_generator.py       # Metrics calculator & report generator
├── results.json              # Single source of truth for latest run
├── evaluation_report.md      # Detailed markdown benchmark report
└── history/                  # Archive of timestamped past evaluation runs
```

---

## Benchmark Metrics & 3-Stage Evaluation

The evaluator measures 3 independent pipeline stages:

1. **Stage 1 (Retrieval Quality)**: Verifies if the target manual page (`expected_page`) was successfully retrieved by `SearchService` / `RetrievalFilter`.
2. **Stage 2 (Context Selection Quality)**: Verifies if `expected_page` was selected into the prompt context by `ContextSelector`.
3. **Stage 3 (Generation Quality)**: Evaluates answer correctness, keyword recall heuristic (`expected_keywords`), non-empty length, and valid fallback responses for negative queries.

### Structured Failure Reasons

When a test case fails, a structured failure reason is recorded:
- `No answer returned`
- `Incorrect fallback behaviour`
- `Wrong source page`
- `Correct source but incorrect extraction`
- `Missing expected keywords`
- `Hallucinated answer`

---

## How to Run the Benchmark

### 1. Start the Production Server

Ensure the live FastAPI / uvicorn server is running:

```powershell
python -m uvicorn backend.main:app --reload
```

### 2. Execute Evaluation

Run `evaluator.py`:

```powershell
python evaluation/evaluator.py
```

This will:
- Synchronously execute all queries in `dataset.json` against `http://127.0.0.1:8000/api/v1/ask`.
- Save raw structured output to `evaluation/results.json`.
- Archive a timestamped snapshot to `evaluation/history/run_<YYYYMMDD_HHMMSS>.json`.
- Generate `evaluation/evaluation_report.md` comparing performance against the previous historical run.
- Display a clean visual terminal banner output.

---

## Category-Wise Benchmarking

Queries in `dataset.json` are grouped across 7 key query types:
- `definition`
- `procedure`
- `list`
- `comparison`
- `summary`
- `negative` (verifies fallback behavior)
- `multi-step`

Category-wise accuracy breakdown is automatically calculated and rendered in `evaluation_report.md`.

---

## Regression Testing Workflow

Every benchmark run is stored inside `evaluation/history/`. When a new run is completed, `report_generator.py` compares current metrics (Accuracy %, Latency, Source Accuracy %, Keyword Recall %, Fallback Rate %) against the most recent run in `history/` and highlights improvements or regressions with visual indicators (🟢 / 🔴).
