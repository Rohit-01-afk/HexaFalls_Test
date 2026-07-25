# Blueprint Eye Evaluation Report

## Benchmark Executive Summary

| Metric | Value | Delta vs Previous Run |
| :--- | :--- | :--- |
| **Questions Tested** | 15 | - |
| **Passed Questions** | 10 | - |
| **Failed Questions** | 5 | - |
| **Overall Accuracy** | **66.7%** | No change |
| **Source Page Accuracy** | 73.3% | No change |
| **Keyword Recall** | 66.7% | No change |
| **Fallback Rate** | 40.0% (6 queries) | No change |
| **Average Latency** | 11.03 sec (11027.2 ms) | No change |
| **Avg Selected Chunks** | 2.6 | - |
| **Avg Highest Similarity** | 0.53 | - |

---

## Category-Wise Performance

| Category | Total Questions | Passed | Failed | Accuracy % |
| :--- | :--- | :--- | :--- | :--- |
| `comparison` | 1 | 1 | 0 | **100.0%** |
| `definition` | 2 | 2 | 0 | **100.0%** |
| `list` | 3 | 1 | 2 | **33.3%** |
| `multi-step` | 2 | 1 | 1 | **50.0%** |
| `negative` | 2 | 2 | 0 | **100.0%** |
| `procedure` | 3 | 1 | 2 | **33.3%** |
| `summary` | 2 | 2 | 0 | **100.0%** |

---

## Detailed Itemized Results

| ID | Category | Question | Exp Page | Ret Page | Status | Failure Reason |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `definition` | What is the stage filtration purpose of the H... | 6 | 6, 6, 6 | 🟢 PASS | - |
| 2 | `definition` | What is the function of the negative ion gene... | 10 | 10, 10, 10 | 🟢 PASS | - |
| 3 | `procedure` | How do you activate and deactivate the child ... | 9 | 9, 9, 9 | 🟢 PASS | - |
| 4 | `procedure` | How do you reset the filter indicator after r... | 12 | 13, 13, 13 | 🔴 FAIL | `Generation failure` |
| 5 | `procedure` | What app should be downloaded for Wi-Fi smart... | 10 | 11, 11, 11 | 🔴 FAIL | `Generation failure` |
| 6 | `list` | What are the three fan speed settings availab... | 9 | 9, 9, 9 | 🟢 PASS | - |
| 7 | `list` | What timer settings can be selected using the... | 12 | 9, 9, 9 | 🔴 FAIL | `Generation failure` |
| 8 | `list` | What items must be removed from the air purif... | 8 | 15, 15, 15 | 🔴 FAIL | `Generation failure` |
| 9 | `comparison` | What indicator light color shows that child l... | 9 | 9, 9, 9 | 🟢 PASS | - |
| 10 | `summary` | What basic safety precautions should be follo... | 4 | 4, 4, 4 | 🟢 PASS | - |
| 11 | `summary` | How frequently is it recommended to replace t... | 13 | 13, 13, 13 | 🟢 PASS | - |
| 12 | `negative` | What is the recommended torque specification ... | None | None | 🟢 PASS | - |
| 13 | `negative` | How do you calibrate the refrigerant expansio... | None | None | 🟢 PASS | - |
| 14 | `multi-step` | What pre-operation steps are required to posi... | 8 | 8, 8, 8 | 🔴 FAIL | `Missing expected keywords` |
| 15 | `multi-step` | What are the step-by-step instructions for re... | 13 | 13, 13, 13 | 🟢 PASS | - |

---

## Benchmark Limitations

1. **Heuristic Keyword Verification**: Keyword recall checks for required technical terms in generated text. High keyword recall correlates with correctness but does not replace expert domain review.
2. **Semantic Verification Boundary**: Evaluation checks exact source page references and deterministic extraction rules. Semantic nuance may require manual validation.
3. **Source Metadata Dependency**: Source accuracy metrics rely on page metadata extracted during PDF ingestion.
4. **Synthesis vs Extraction**: Summary queries evaluate presence of key concepts; exact sentence structures may vary.

