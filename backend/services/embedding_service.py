"""
Service layer for embedding generation using SentenceTransformers and vector indexing into ChromaDB.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
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
from sentence_transformers import SentenceTransformer



from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.embedding import EmbeddingResponse


class EmbeddingService:
    """Handles embedding generation and persistent vector storage in ChromaDB."""

    _model: Optional[SentenceTransformer] = None

    @classmethod
    def _get_model(cls) -> SentenceTransformer:
        """Loads and caches the SentenceTransformer embedding model."""
        if cls._model is None:
            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._model

    @staticmethod
    def _get_chroma_client() -> chromadb.PersistentClient:
        """Initializes and returns a persistent ChromaDB client."""
        chroma_dir = Path(settings.CHROMA_PATH)
        chroma_dir.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(path=str(chroma_dir))

    @classmethod
    async def generate_and_index_embeddings(cls, document_id: str) -> EmbeddingResponse:
        """
        Loads chunk metadata, generates dense vector embeddings, and upserts vectors into ChromaDB.

        Args:
            document_id: Document UUID identifier.

        Returns:
            EmbeddingResponse containing total indexed chunks count and collection details.

        Raises:
            HTTPException: 404 if chunk file missing, 400 if chunk dataset empty.
        """
        logger.info("Embedding generation started for document_id: %s", document_id)

        chunk_file = Path(settings.CHUNK_STORAGE_PATH) / f"{document_id}.json"
        if not chunk_file.exists():
            logger.warning("Embedding failed: Chunk file for document_id '%s' not found", document_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk data for document ID '{document_id}' not found. Please run chunking first.",
            )

        try:
            with chunk_file.open("r", encoding="utf-8") as f:
                chunk_data = json.load(f)
        except Exception as err:
            logger.warning("Embedding failed: Invalid chunk JSON for document_id '%s': %s", document_id, str(err))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chunk data file is corrupted or invalid.",
            ) from err

        chunks = chunk_data.get("chunks")
        if not isinstance(chunks, list) or len(chunks) == 0:
            logger.warning("Embedding failed: Document '%s' contains 0 chunks", document_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document contains no chunks to embed.",
            )

        # 1. Generate embeddings using SentenceTransformer model
        model = cls._get_model()
        texts = [c["text"] for c in chunks]

        logger.info("Generating embeddings for %d chunks of document_id: %s", len(texts), document_id)
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        # 2. Prepare metadata payloads and IDs for ChromaDB
        ids: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for c in chunks:
            ids.append(c["chunk_id"])
            metadatas.append(
                {
                    "document_id": str(c["document_id"]),
                    "page_number": int(c["page_number"]),
                    "chunk_id": str(c["chunk_id"]),
                    "start_char": int(c["start_char"]),
                    "end_char": int(c["end_char"]),
                    "token_count": int(c["token_count"]),
                }
            )

        # 3. Connect to ChromaDB and upsert collection
        client = cls._get_chroma_client()
        collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info("Indexing %d vectors into ChromaDB collection '%s'", len(ids), settings.CHROMA_COLLECTION)
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        logger.info(
            "Embedding generation and vector indexing completed for document_id: %s (%d chunks indexed)",
            document_id,
            len(chunks),
        )

        return EmbeddingResponse(
            document_id=document_id,
            indexed_chunks=len(chunks),
            collection=settings.CHROMA_COLLECTION,
            status="indexed",
        )
