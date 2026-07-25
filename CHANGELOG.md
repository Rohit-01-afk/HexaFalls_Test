## Sprint 7.1 — Query Understanding & Intelligent Retrieval

### Added
- Deterministic QueryUnderstandingService
- QueryIntent model with confidence and reasoning
- Intent diagnostics in `/ask` responses
- Comprehensive unit tests for query classification

### Improved
- RAG pipeline now analyzes user intent before retrieval.
- Better observability through structured diagnostics.
- Preserved strict separation of concerns by keeping SearchService and RetrievalFilter unchanged.

### Notes
- No changes to retrieval ranking or embedding logic.
- No external LLM dependency introduced for intent detection.