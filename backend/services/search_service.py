"""
Service layer for semantic vector search using SentenceTransformers query embeddings and ChromaDB.
"""

import re
import sys
from typing import List, Optional
from unittest.mock import MagicMock

# Patch grpc if DLL load is blocked by AppLocker policy
try:
    import grpc  # noqa: F401
except (ImportError, Exception):
    mock_grpc = MagicMock()
    mock_grpc.__version__ = "1.65.0"
    sys.modules["grpc"] = mock_grpc

# Patch regex module if compiled _regex.pyd is blocked by AppLocker policy
try:
    import regex  # noqa: F401
except (ImportError, Exception):
    sys.modules["regex"] = re

import chromadb
from fastapi import HTTPException, status

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.search import SearchRequest, SearchResponse, SearchResult
from backend.services.embedding_service import EmbeddingService


class SearchService:
    """Handles query embedding, ChromaDB vector querying, score computation, and top-k retrieval."""

    @classmethod
    async def search(cls, request: SearchRequest) -> SearchResponse:
        """
        Executes semantic vector search for a natural-language query against ChromaDB.

        Args:
            request: SearchRequest model containing query and optional top_k.

        Returns:
            SearchResponse object containing matched SearchResult items sorted by score.

        Raises:
            HTTPException: 400 for empty query or invalid top_k boundary.
        """
        # 1. Validate query string
        raw_query = request.query or ""
        clean_query = raw_query.strip()
        if not clean_query:
            logger.warning("Search failed: Empty or whitespace-only query provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query string cannot be empty or whitespace-only.",
            )

        # 2. Validate top_k parameter
        top_k = request.top_k if request.top_k is not None else settings.DEFAULT_TOP_K
        if top_k < 1 or top_k > settings.MAX_TOP_K:
            logger.warning("Search failed: Invalid top_k value %s", top_k)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"top_k must be between 1 and {settings.MAX_TOP_K}.",
            )

        logger.info("Executing semantic search for query: '%s' (top_k=%d)", clean_query, top_k)

        # 3. Generate query embedding vector
        model = EmbeddingService._get_model()
        query_vector = model.encode([clean_query], show_progress_bar=False).tolist()[0]

        # 4. Connect to ChromaDB vector store
        client = EmbeddingService._get_chroma_client()
        try:
            collection = client.get_collection(name=settings.CHROMA_COLLECTION)
        except Exception:
            # Collection does not exist yet (no documents embedded)
            logger.info("Search executed against non-existent collection '%s'", settings.CHROMA_COLLECTION)
            return SearchResponse(query=clean_query, count=0, results=[])

        if collection.count() == 0:
            logger.info("Search executed against empty collection '%s'", settings.CHROMA_COLLECTION)
            return SearchResponse(query=clean_query, count=0, results=[])

        # 5. Query ChromaDB for top-k matches
        raw_results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        matched_results: List[SearchResult] = []

        if raw_results and raw_results.get("ids") and len(raw_results["ids"]) > 0:
            ids_list = raw_results["ids"][0]
            docs_list = raw_results["documents"][0] if raw_results.get("documents") else []
            metas_list = raw_results["metadatas"][0] if raw_results.get("metadatas") else []
            dists_list = raw_results["distances"][0] if raw_results.get("distances") else []

            for i in range(len(ids_list)):
                chunk_id = ids_list[i]
                doc_text = docs_list[i] if i < len(docs_list) else ""
                meta = metas_list[i] if i < len(metas_list) else {}
                dist = dists_list[i] if i < len(dists_list) else 1.0

                # Convert cosine distance d (0..2) to similarity score (1 - d) capped between 0 and 1
                score = round(max(0.0, 1.0 - float(dist)), 4)

                matched_results.append(
                    SearchResult(
                        document_id=str(meta.get("document_id", "")),
                        chunk_id=str(meta.get("chunk_id", chunk_id)),
                        page_number=int(meta.get("page_number", 1)),
                        score=score,
                        text=str(doc_text),
                    )
                )

        # Sort results by similarity score descending
        matched_results.sort(key=lambda r: r.score, reverse=True)

        logger.info(
            "Semantic search completed for query '%s': %d matching chunks retrieved",
            clean_query,
            len(matched_results),
        )

        return SearchResponse(
            query=clean_query,
            count=len(matched_results),
            results=matched_results,
        )
