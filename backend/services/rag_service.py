import time
from typing import Optional, Type

from fastapi import HTTPException, status

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.ask import (
    AskRequest,
    AskResponse,
    RetrievalDiagnostics,
    RetrievalMetrics,
    SourceReference,
)
from backend.schemas.query_intent import QueryIntent
from backend.schemas.search import SearchRequest
from backend.services.ollama_service import OllamaService
from backend.services.prompt_builder import PromptBuilder
from backend.services.query_understanding_service import QueryUnderstandingService
from backend.services.retrieval_filter import RetrievalFilter
from backend.services.search_service import SearchService

FALLBACK_NO_CHUNKS_ANSWER = "I could not find this information in the manual."
FALLBACK_BELOW_THRESHOLD_ANSWER = "I could not find sufficiently relevant information in the manual."


class RAGService:
    """Orchestrates semantic retrieval, query intent analysis, filtering, prompt construction, and LLM text generation."""

    retrieval_filter: Type[RetrievalFilter] = RetrievalFilter

    @classmethod
    def _attach_intent_diagnostics(
        cls, diagnostics: Optional[RetrievalDiagnostics], query_intent: QueryIntent
    ) -> Optional[RetrievalDiagnostics]:
        """Helper to attach query intent analysis metadata onto RetrievalDiagnostics."""
        if diagnostics is None:
            return None
        diagnostics.intent = query_intent.intent.value if hasattr(query_intent.intent, "value") else str(query_intent.intent)
        diagnostics.intent_confidence = query_intent.confidence
        diagnostics.matched_keywords = query_intent.matched_keywords
        diagnostics.intent_reason = query_intent.reason
        return diagnostics

    @classmethod
    async def ask(
        cls,
        request: AskRequest,
        retrieval_filter: Optional[Type[RetrievalFilter]] = None,
        search_service: Optional[Type[SearchService]] = None,
        prompt_builder: Optional[Type[PromptBuilder]] = None,
        ollama_service: Optional[Type[OllamaService]] = None,
        query_understanding_service: Optional[Type[QueryUnderstandingService]] = None,
    ) -> AskResponse:
        """
        Executes complete RAG pipeline for a user question with intent analysis, filtering, confidence, and latency metrics.

        Args:
            request: AskRequest payload containing user question.
            retrieval_filter: Optional override for RetrievalFilter class.
            search_service: Optional override for SearchService class.
            prompt_builder: Optional override for PromptBuilder class.
            ollama_service: Optional override for OllamaService class.
            query_understanding_service: Optional override for QueryUnderstandingService class.

        Returns:
            AskResponse containing question, answer, rich sources, confidence rating, diagnostics, and metrics.

        Raises:
            HTTPException: 422 if question is empty or whitespace-only.
        """
        t_start = time.perf_counter()

        # 1. Validate question input
        raw_q = request.question or ""
        clean_question = raw_q.strip()
        if not clean_question:
            logger.warning("RAG request failed: Empty or whitespace-only question")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Question string cannot be empty or whitespace-only.",
            )

        logger.info("RAG pipeline initiated for question: '%s'", clean_question)

        # Service dependency references
        filter_cls = retrieval_filter or cls.retrieval_filter
        search_cls = search_service or SearchService
        prompt_cls = prompt_builder or PromptBuilder
        ollama_cls = ollama_service or OllamaService
        query_cls = query_understanding_service or QueryUnderstandingService

        # 1.5. Analyze query intent
        query_intent = query_cls.analyze_query(clean_question)

        # 2. Retrieve candidate chunks via SearchService
        t0 = time.perf_counter()
        search_req = SearchRequest(
            query=clean_question,
            top_k=settings.MAX_TOP_K,
            document_id=request.document_id,
        )
        search_res = await search_cls.search(search_req)
        search_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 3. Apply retrieval filtering logic (dedup, threshold, sort, top_k, max_chars)
        t0 = time.perf_counter()
        filter_res = filter_cls.filter_chunks(search_res.results)
        filter_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 4. Handle empty retrieval cases
        raw_count = filter_res.diagnostics.raw_count if filter_res.diagnostics else len(search_res.results)
        returned_count = len(filter_res.filtered_chunks)

        if raw_count == 0:
            # Case 1 / Case 3: No search candidates retrieved
            total_ms = round((time.perf_counter() - t_start) * 1000, 2)
            metrics = RetrievalMetrics(
                search_ms=search_ms,
                filter_ms=filter_ms,
                prompt_ms=0.0,
                generation_ms=0.0,
                total_ms=total_ms,
            )
            logger.info("Empty search retrieval for question: '%s'. Returning fallback response.", clean_question)
            diag = cls._attach_intent_diagnostics(filter_res.diagnostics, query_intent)
            return AskResponse(
                question=clean_question,
                answer=FALLBACK_NO_CHUNKS_ANSWER,
                sources=[],
                confidence="None",
                diagnostics=diag,
                metrics=metrics,
            )

        if returned_count == 0:
            # Case 2: Chunks retrieved but all filtered out below similarity threshold
            if settings.RAG_ENABLE_SOFT_THRESHOLD:
                soft_threshold = max(0.0, settings.RAG_SIMILARITY_THRESHOLD - settings.RAG_SOFT_THRESHOLD_MARGIN)
                soft_filter_res = filter_cls.filter_chunks(search_res.results, similarity_threshold=soft_threshold)

                if soft_filter_res.filtered_chunks:
                    # Execute generation with relaxed threshold chunks (confidence set to "Low")
                    t0 = time.perf_counter()
                    prompt = prompt_cls.build_prompt(clean_question, soft_filter_res.filtered_chunks)
                    prompt_ms = round((time.perf_counter() - t0) * 1000, 2)

                    t0 = time.perf_counter()
                    generated_answer = await ollama_cls.generate_answer(prompt)
                    generation_ms = round((time.perf_counter() - t0) * 1000, 2)

                    total_ms = round((time.perf_counter() - t_start) * 1000, 2)
                    metrics = RetrievalMetrics(
                        search_ms=search_ms,
                        filter_ms=filter_ms,
                        prompt_ms=prompt_ms,
                        generation_ms=generation_ms,
                        total_ms=total_ms,
                    )

                    max_preview = settings.RAG_MAX_PREVIEW_CHARS
                    sources = [
                        SourceReference(
                            page=r.page_number,
                            chunk_id=r.chunk_id,
                            score=r.score,
                            document_id=r.document_id,
                            preview=r.text[:max_preview] + "..." if len(r.text) > max_preview else r.text,
                        )
                        for r in soft_filter_res.filtered_chunks
                    ]

                    logger.info(
                        "Soft threshold RAG completed for question: '%s' (%d sources, confidence=Low, total_ms=%.2f)",
                        clean_question,
                        len(sources),
                        total_ms,
                    )

                    diag = cls._attach_intent_diagnostics(soft_filter_res.diagnostics, query_intent)
                    return AskResponse(
                        question=clean_question,
                        answer=generated_answer,
                        sources=sources,
                        confidence="Low",
                        diagnostics=diag,
                        metrics=metrics,
                    )

            total_ms = round((time.perf_counter() - t_start) * 1000, 2)
            metrics = RetrievalMetrics(
                search_ms=search_ms,
                filter_ms=filter_ms,
                prompt_ms=0.0,
                generation_ms=0.0,
                total_ms=total_ms,
            )
            logger.info("All chunks filtered out below threshold for question: '%s'. Returning threshold fallback.", clean_question)
            diag = cls._attach_intent_diagnostics(filter_res.diagnostics, query_intent)
            return AskResponse(
                question=clean_question,
                answer=FALLBACK_BELOW_THRESHOLD_ANSWER,
                sources=[],
                confidence="None",
                diagnostics=diag,
                metrics=metrics,
            )

        # 5. Construct grounded prompt from filtered chunks
        t0 = time.perf_counter()
        prompt = prompt_cls.build_prompt(clean_question, filter_res.filtered_chunks)
        prompt_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 6. Invoke Ollama model for answer generation
        t0 = time.perf_counter()
        generated_answer = await ollama_cls.generate_answer(prompt)
        generation_ms = round((time.perf_counter() - t0) * 1000, 2)

        total_ms = round((time.perf_counter() - t_start) * 1000, 2)
        metrics = RetrievalMetrics(
            search_ms=search_ms,
            filter_ms=filter_ms,
            prompt_ms=prompt_ms,
            generation_ms=generation_ms,
            total_ms=total_ms,
        )

        # 7. Assemble rich source metadata references
        max_preview = settings.RAG_MAX_PREVIEW_CHARS
        sources = [
            SourceReference(
                page=r.page_number,
                chunk_id=r.chunk_id,
                score=r.score,
                document_id=r.document_id,
                preview=r.text[:max_preview] + "..." if len(r.text) > max_preview else r.text,
            )
            for r in filter_res.filtered_chunks
        ]

        logger.info(
            "RAG pipeline completed successfully for question: '%s' (%d sources, confidence=%s, total_ms=%.2f)",
            clean_question,
            len(sources),
            filter_res.confidence,
            total_ms,
        )

        diag = cls._attach_intent_diagnostics(filter_res.diagnostics, query_intent)
        return AskResponse(
            question=clean_question,
            answer=generated_answer,
            sources=sources,
            confidence=filter_res.confidence,
            diagnostics=diag,
            metrics=metrics,
        )
