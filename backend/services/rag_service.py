import time
import uuid
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
from backend.schemas.evidence import SelectedEvidence
from backend.schemas.query_intent import QueryIntent
from backend.schemas.search import SearchRequest
from backend.services.context_selector import ContextSelector
from backend.services.evidence_service import EvidencePreparer
from backend.services.gemini_service import GeminiService
from backend.services.groq_service import GroqService
from backend.services.prompt_builder import PromptBuilder
from backend.services.query_understanding_service import QueryUnderstandingService
from backend.services.recovery_handler import RecoveryHandler
from backend.services.response_validator import ResponseValidator
from backend.services.retrieval_filter import RetrievalFilter
from backend.services.search_service import SearchService

FALLBACK_NO_CHUNKS_ANSWER = "I could not find this information in the manual."
FALLBACK_BELOW_THRESHOLD_ANSWER = "I could not find sufficiently relevant information in the manual."


class RAGService:
    """Orchestrates semantic retrieval, query intent analysis, filtering, context selection, evidence preparation, prompt construction, LLM generation, validation, and recovery."""

    retrieval_filter: Type[RetrievalFilter] = RetrievalFilter

    @classmethod
    def _attach_intent_diagnostics(
        cls,
        diagnostics: Optional[RetrievalDiagnostics],
        query_intent: QueryIntent,
        selected_evidence: Optional[SelectedEvidence] = None,
    ) -> Optional[RetrievalDiagnostics]:
        """Helper to attach query intent analysis metadata and context selection diagnostics onto RetrievalDiagnostics."""
        if diagnostics is None:
            return None
        diagnostics.intent = query_intent.intent.value if hasattr(query_intent.intent, "value") else str(query_intent.intent)
        diagnostics.intent_confidence = query_intent.confidence
        diagnostics.matched_keywords = query_intent.matched_keywords
        diagnostics.intent_reason = query_intent.reason
        if selected_evidence is not None:
            diagnostics.selected_chunks = selected_evidence.selected_count
            diagnostics.candidate_chunks = selected_evidence.candidate_count
            diagnostics.selection_strategy = selected_evidence.selection_strategy
            diagnostics.highest_similarity = selected_evidence.highest_score
        return diagnostics


    @classmethod
    def _log_lifecycle(
        cls,
        generation_id: str,
        question: str,
        retrieved_count: int,
        filtered_count: int,
        primary_count: int,
        supporting_count: int,
        generated_answer: str,
        validation_valid: Optional[bool],
        validation_reason: Optional[str],
        recovery_invoked: bool,
        final_answer: str,
        total_ms: float,
    ) -> None:
        """Helper to log the end-to-end RAG pipeline lifecycle block if DEBUG_RAG_PIPELINE is enabled."""
        if getattr(settings, "DEBUG_RAG_PIPELINE", False):
            logger.info(
                "\n===== RAG PIPELINE LIFECYCLE =====\n\nGeneration ID: %s\n\nQuestion: %s\n\nRetrieved chunks: %d\n\nFiltered chunks: %d\n\nPrimary evidence count: %d\n\nSupporting evidence count: %d\n\nGenerated answer: %s\n\nValidation result: Valid=%s, Reason=%s\n\nRecovery invoked: %s\n\nFinal returned answer: %s\n\nPipeline latency: %.2fms\n",
                generation_id,
                question,
                retrieved_count,
                filtered_count,
                primary_count,
                supporting_count,
                generated_answer,
                validation_valid,
                validation_reason,
                "Yes" if recovery_invoked else "No",
                final_answer,
                total_ms,
            )

    @classmethod
    async def ask(
        cls,
        request: AskRequest,
        retrieval_filter: Optional[Type[RetrievalFilter]] = None,
        search_service: Optional[Type[SearchService]] = None,
        prompt_builder: Optional[Type[PromptBuilder]] = None,
        groq_service: Optional[Type[GroqService]] = None,
        gemini_service: Optional[Type[GeminiService]] = None,
        query_understanding_service: Optional[Type[QueryUnderstandingService]] = None,
        evidence_preparer: Optional[Type[EvidencePreparer]] = None,
        response_validator: Optional[Type[ResponseValidator]] = None,
        recovery_handler: Optional[Type[RecoveryHandler]] = None,
        context_selector: Optional[Type[ContextSelector]] = None,
    ) -> AskResponse:
        """
        Executes complete Answer Generation Pipeline for a user question.

        Args:
            request: AskRequest payload containing user question.
            retrieval_filter: Optional override for RetrievalFilter class.
            search_service: Optional override for SearchService class.
            prompt_builder: Optional override for PromptBuilder class.
            groq_service: Optional override for GroqService class.
            gemini_service: Optional override for GeminiService class.
            query_understanding_service: Optional override for QueryUnderstandingService class.
            evidence_preparer: Optional override for EvidencePreparer class.
            response_validator: Optional override for ResponseValidator class.
            recovery_handler: Optional override for RecoveryHandler class.
            context_selector: Optional override for ContextSelector class.

        Returns:
            AskResponse containing question, answer, rich sources, confidence rating, diagnostics, and metrics.

        Raises:
            HTTPException: 422 if question is empty or whitespace-only.
        """
        t_start = time.perf_counter()
        generation_id = f"gen-{uuid.uuid4().hex[:12]}"


        # 1. Validate question input
        raw_q = request.question or ""
        clean_question = raw_q.strip()
        if not clean_question:
            logger.warning("RAG request failed: Empty or whitespace-only question")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Question string cannot be empty or whitespace-only.",
            )

        logger.info("RAG pipeline initiated (gen_id=%s) for question: '%s'", generation_id, clean_question)

        # Service dependency references
        filter_cls = retrieval_filter or cls.retrieval_filter
        search_cls = search_service or SearchService
        prompt_cls = prompt_builder or PromptBuilder
        groq_cls = groq_service or GroqService
        gemini_cls = gemini_service or GeminiService
        query_cls = query_understanding_service or QueryUnderstandingService
        evidence_cls = evidence_preparer or EvidencePreparer
        validator_cls = response_validator or ResponseValidator
        recovery_cls = recovery_handler or RecoveryHandler
        selector_cls = context_selector or ContextSelector

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

        # 4. Apply intelligent context selection
        selected_evidence = selector_cls.select_context(filter_res.filtered_chunks)

        # 4.5. Handle empty retrieval / selection cases
        raw_count = filter_res.diagnostics.raw_count if filter_res.diagnostics else len(search_res.results)
        returned_count = selected_evidence.selected_count

        if raw_count == 0:
            total_ms = round((time.perf_counter() - t_start) * 1000, 2)
            metrics = RetrievalMetrics(
                search_ms=search_ms,
                filter_ms=filter_ms,
                prompt_ms=0.0,
                generation_ms=0.0,
                total_ms=total_ms,
            )
            logger.info("Empty search retrieval for question: '%s'. Returning fallback response.", clean_question)
            diag = cls._attach_intent_diagnostics(filter_res.diagnostics, query_intent, selected_evidence=selected_evidence)
            cls._log_lifecycle(
                generation_id=generation_id,
                question=clean_question,
                retrieved_count=0,
                filtered_count=0,
                primary_count=0,
                supporting_count=0,
                generated_answer="[None - Empty search retrieval]",
                validation_valid=None,
                validation_reason=None,
                recovery_invoked=False,
                final_answer=FALLBACK_NO_CHUNKS_ANSWER,
                total_ms=total_ms,
            )
            return AskResponse(
                question=clean_question,
                answer=FALLBACK_NO_CHUNKS_ANSWER,
                sources=[],
                confidence="None",
                diagnostics=diag,
                metrics=metrics,
            )

        if returned_count == 0:
            if settings.RAG_ENABLE_SOFT_THRESHOLD:
                soft_threshold = max(0.0, settings.RAG_SIMILARITY_THRESHOLD - settings.RAG_SOFT_THRESHOLD_MARGIN)
                soft_filter_res = filter_cls.filter_chunks(search_res.results, similarity_threshold=soft_threshold)
                soft_selected = selector_cls.select_context(soft_filter_res.filtered_chunks, top3_threshold=soft_threshold)

                if soft_selected.selected_count > 0:
                    selected_evidence = soft_selected
                    returned_count = selected_evidence.selected_count
                    # 5a. Evidence Preparation
                    t0 = time.perf_counter()
                    evidence = evidence_cls.prepare_evidence(selected_evidence.chunks, generation_id=generation_id)
                    logger.info(
                        "Evidence Prepared (gen_id=%s, soft): primary=%d, supporting=%d",
                        generation_id,
                        evidence.primary_count,
                        evidence.supporting_count,
                    )

                    prompt = prompt_cls.build_prompt(
                        clean_question,
                        selected_evidence,
                        intent=query_intent,
                        generation_id=generation_id,
                    )
                    prompt_ms = round((time.perf_counter() - t0) * 1000, 2)

                    # 6a. Generation
                    t0 = time.perf_counter()
                    initial_generated_answer = await groq_cls.generate_answer(
                        prompt,
                        raw_chunk_count=raw_count,
                        filtered_chunk_count=returned_count,
                        primary_evidence_count=evidence.primary_count,
                        supporting_evidence_count=evidence.supporting_count,
                        generation_id=generation_id,
                    )

                    # 7a. Response Validation & Recovery
                    validation = validator_cls.validate_response(initial_generated_answer, generation_id=generation_id)
                    final_answer = initial_generated_answer
                    recovery_invoked = False

                    if not validation.valid:
                        recovery_invoked = True
                        recovery_res = await recovery_cls.attempt_recovery(
                            generation_id=generation_id,
                            question=clean_question,
                            evidence=evidence,
                            intent=query_intent,
                            initial_validation=validation,
                            raw_chunk_count=raw_count,
                            filtered_chunk_count=returned_count,
                            prompt_builder=prompt_cls,
                            groq_service=groq_cls,
                            response_validator=validator_cls,
                        )
                        final_answer = recovery_res.answer

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
                        for r in selected_evidence.chunks
                    ]

                    diag = cls._attach_intent_diagnostics(soft_filter_res.diagnostics, query_intent, selected_evidence=selected_evidence)
                    cls._log_lifecycle(
                        generation_id=generation_id,
                        question=clean_question,
                        retrieved_count=raw_count,
                        filtered_count=returned_count,
                        primary_count=evidence.primary_count,
                        supporting_count=evidence.supporting_count,
                        generated_answer=initial_generated_answer,
                        validation_valid=validation.valid,
                        validation_reason=validation.reason.value if hasattr(validation.reason, "value") else str(validation.reason),
                        recovery_invoked=recovery_invoked,
                        final_answer=final_answer,
                        total_ms=total_ms,
                    )
                    return AskResponse(
                        question=clean_question,
                        answer=final_answer,
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
            logger.info("All chunks filtered out or unselected for question: '%s'. Returning threshold fallback.", clean_question)
            diag = cls._attach_intent_diagnostics(filter_res.diagnostics, query_intent, selected_evidence=selected_evidence)
            cls._log_lifecycle(
                generation_id=generation_id,
                question=clean_question,
                retrieved_count=raw_count,
                filtered_count=0,
                primary_count=0,
                supporting_count=0,
                generated_answer="[None - All chunks below threshold or unselected]",
                validation_valid=None,
                validation_reason=None,
                recovery_invoked=False,
                final_answer=FALLBACK_BELOW_THRESHOLD_ANSWER,
                total_ms=total_ms,
            )
            return AskResponse(
                question=clean_question,
                answer=FALLBACK_BELOW_THRESHOLD_ANSWER,
                sources=[],
                confidence="None",
                diagnostics=diag,
                metrics=metrics,
            )

        # 5. Evidence Preparation & Prompt Construction
        t0 = time.perf_counter()
        evidence = evidence_cls.prepare_evidence(selected_evidence.chunks, generation_id=generation_id)
        logger.info(
            "Evidence Prepared (gen_id=%s): primary=%d, supporting=%d",
            generation_id,
            evidence.primary_count,
            evidence.supporting_count,
        )

        prompt = prompt_cls.build_prompt(
            clean_question,
            selected_evidence,
            intent=query_intent,
            generation_id=generation_id,
        )
        prompt_ms = round((time.perf_counter() - t0) * 1000, 2)

        # 6. LLM Generation
        t0 = time.perf_counter()
        initial_generated_answer = await groq_cls.generate_answer(
            prompt,
            raw_chunk_count=raw_count,
            filtered_chunk_count=returned_count,
            primary_evidence_count=evidence.primary_count,
            supporting_evidence_count=evidence.supporting_count,
            generation_id=generation_id,
        )

        # 7. Response Validation & Recovery Retry if Invalid
        validation = validator_cls.validate_response(initial_generated_answer, generation_id=generation_id)
        final_answer = initial_generated_answer
        recovery_invoked = False

        if not validation.valid:
            recovery_invoked = True
            recovery_res = await recovery_cls.attempt_recovery(
                generation_id=generation_id,
                question=clean_question,
                evidence=evidence,
                intent=query_intent,
                initial_validation=validation,
                raw_chunk_count=raw_count,
                filtered_chunk_count=returned_count,
                prompt_builder=prompt_cls,
                groq_service=groq_cls,
                response_validator=validator_cls,
            )
            final_answer = recovery_res.answer

        generation_ms = round((time.perf_counter() - t0) * 1000, 2)
        total_ms = round((time.perf_counter() - t_start) * 1000, 2)

        metrics = RetrievalMetrics(
            search_ms=search_ms,
            filter_ms=filter_ms,
            prompt_ms=prompt_ms,
            generation_ms=generation_ms,
            total_ms=total_ms,
        )

        # 8. Assemble rich source metadata references
        max_preview = settings.RAG_MAX_PREVIEW_CHARS
        sources = [
            SourceReference(
                page=r.page_number,
                chunk_id=r.chunk_id,
                score=r.score,
                document_id=r.document_id,
                preview=r.text[:max_preview] + "..." if len(r.text) > max_preview else r.text,
            )
            for r in selected_evidence.chunks
        ]

        logger.info(
            "RAG pipeline completed (gen_id=%s) for question: '%s' (%d sources, confidence=%s, total_ms=%.2f)",
            generation_id,
            clean_question,
            len(sources),
            filter_res.confidence,
            total_ms,
        )

        diag = cls._attach_intent_diagnostics(filter_res.diagnostics, query_intent, selected_evidence=selected_evidence)
        cls._log_lifecycle(
            generation_id=generation_id,
            question=clean_question,
            retrieved_count=raw_count,
            filtered_count=returned_count,
            primary_count=evidence.primary_count,
            supporting_count=evidence.supporting_count,
            generated_answer=initial_generated_answer,
            validation_valid=validation.valid,
            validation_reason=validation.reason.value if hasattr(validation.reason, "value") else str(validation.reason),
            recovery_invoked=recovery_invoked,
            final_answer=final_answer,
            total_ms=total_ms,
        )
        return AskResponse(
            question=clean_question,
            answer=final_answer,
            sources=sources,
            confidence=filter_res.confidence,
            diagnostics=diag,
            metrics=metrics,
        )
