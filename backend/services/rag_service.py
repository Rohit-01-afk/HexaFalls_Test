"""
Service layer for orchestrating Retrieval-Augmented Generation (RAG) workflows.
"""

from fastapi import HTTPException, status

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.ask import AskRequest, AskResponse, SourceReference
from backend.schemas.search import SearchRequest
from backend.services.ollama_service import OllamaService
from backend.services.prompt_builder import PromptBuilder
from backend.services.search_service import SearchService

FALLBACK_ANSWER = "I could not find this information in the manual."


class RAGService:
    """Orchestrates semantic retrieval, prompt construction, and LLM text generation."""

    @classmethod
    async def ask(cls, request: AskRequest) -> AskResponse:
        """
        Executes complete RAG pipeline for a user question.

        Args:
            request: AskRequest payload containing user question.

        Returns:
            AskResponse containing question, generated answer, and source metadata references.

        Raises:
            HTTPException: 422 if question is empty or whitespace-only.
        """
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

        # 2. Retrieve top-k relevant chunks via SearchService
        search_req = SearchRequest(query=clean_question, top_k=settings.RAG_TOP_K)
        search_res = await SearchService.search(search_req)

        retrieved_count = search_res.count
        logger.info("RAG retrieval step complete: %d chunks found for question: '%s'", retrieved_count, clean_question)

        # 3. Handle empty retrieval (successful 200 OK fallback)
        if retrieved_count == 0 or len(search_res.results) == 0:
            logger.info("Empty retrieval for question: '%s'. Returning fallback response.", clean_question)
            return AskResponse(
                question=clean_question,
                answer=FALLBACK_ANSWER,
                sources=[],
            )

        # 4. Construct grounded prompt
        prompt = PromptBuilder.build_prompt(clean_question, search_res.results)

        # 5. Invoke Ollama model for answer generation
        generated_answer = await OllamaService.generate_answer(prompt)

        # 6. Assemble source metadata references
        sources = [
            SourceReference(
                page=r.page_number,
                chunk_id=r.chunk_id,
                score=r.score,
            )
            for r in search_res.results
        ]

        logger.info(
            "RAG pipeline completed successfully for question: '%s' (%d sources returned)",
            clean_question,
            len(sources),
        )

        return AskResponse(
            question=clean_question,
            answer=generated_answer,
            sources=sources,
        )
