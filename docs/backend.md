# Backend Service Architecture & Answer Generation Pipeline

Version: v0.3.5 (Sprint 6.5 — Answer Generation Layer Stabilization)

---

# 1. Overview

The backend layer of Blueprint Eye processes user queries, executes vector similarity search, filters context candidates, cleanses context text, builds grounded prompts, generates AI model responses, and assembles structured API responses.

---

# 2. Prompt Engineering Workflow (`PromptBuilder`)

`PromptBuilder` is a **pure formatting component**. It operates solely on pre-filtered chunks received from `RetrievalFilter`.

### Core Responsibilities
- Constructing immutable `Prompt` objects containing system instructions, context, and user question.
- Enforcing **Prompt Design Principles**:
  - **Deterministic Structure:** Direct, predictable system prompt without ambiguous guidance.
  - **No Chain-of-Thought:** Explicit prohibition against requesting internal reasoning or step-by-step thinking.
  - **Grounding & Hallucination Prevention:** Strict instruction to answer ONLY from supplied context.
  - **Support Distinction:**
    - *Fully supported information:* Precise technical answer.
    - *Partially supported information:* State available facts clearly without speculation.
    - *Unsupported information:* Reply exactly `"I could not find this information in the manual."`
  - **Terminology Preservation:** Retain model numbers, pin/cable designations, and technical terms.
  - **Concise Technical Explanations:** Produce clean, structured responses.

### Non-Responsibilities (Strict Boundaries)
`PromptBuilder` MUST NEVER:
- Perform vector retrieval or database queries
- Rank or score candidate chunks
- Evaluate retrieval confidence
- Perform similarity thresholding
- Make orchestration or fallback decisions

---

# 3. Context Preparation Pipeline

Before embedding retrieved chunks into the prompt context string, `PromptBuilder` executes context normalization:

1. **Whitespace Normalization:**
   - Standardizes line endings (`\r\n` -> `\n`).
   - Strips redundant header lines and repeated delimiters.
   - Collapses excessive blank lines (`\n{3,}` -> `\n\n`) to preserve paragraph structure.

2. **Chunk Deduplication:**
   - Tracks lowercased text content keys.
   - Skips duplicate chunk content to optimize prompt context window usage.

3. **Header Formatting:**
   When `RAG_INCLUDE_PAGE_HEADERS` is enabled, formats context blocks as:
   ```text
   ==========
   Page 82
   Similarity: 0.71
   Content:
   Step 1: Disconnect cable J7.
   ```
   Preserves chunk boundaries, page numbers, and similarity score ordering.

---

# 4. Answer Formatting & Response Assembly (`RAGService`)

Response formatting and payload assembly remain inside `RAGService (Response Assembly)`.

- `RAGService` handles pipeline orchestration between `SearchService`, `RetrievalFilter`, `PromptBuilder`, and `OllamaService`.
- Soft-threshold retrieval fallback is evaluated in `RAGService`:
  - When candidate chunks score within `settings.RAG_SOFT_THRESHOLD_MARGIN` below `settings.RAG_SIMILARITY_THRESHOLD`, `RAGService` re-filters using `soft_threshold = RAG_SIMILARITY_THRESHOLD - RAG_SOFT_THRESHOLD_MARGIN`.
  - The relaxed threshold chunks must pass through all `RetrievalFilter` controls (deduplication, score sorting, Top-K capping, max context char limits).
  - Response confidence is marked as `"Low"`.
- `RAGService` populates rich source attribution metadata (`SourceReference`) using configurable preview length (`settings.RAG_MAX_PREVIEW_CHARS`, default 250).
