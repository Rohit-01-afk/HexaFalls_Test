"""
Service layer for page-boundary-aware text chunking with sliding windows.
"""

import json
import uuid
from pathlib import Path
from typing import List
from fastapi import HTTPException, status

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.chunking import Chunk, ChunkGenerationResponse


class ChunkingService:
    """Handles text chunk generation preserving page boundaries and metadata offsets."""

    @staticmethod
    async def generate_chunks(document_id: str) -> ChunkGenerationResponse:
        """
        Loads document page metadata, performs page-boundary-aware chunking, and saves chunk dataset.

        Args:
            document_id: Document UUID identifier.

        Returns:
            ChunkGenerationResponse object containing total chunks count and status.

        Raises:
            HTTPException: 404 if metadata is missing, 400 if metadata is empty/invalid.
        """
        logger.info("Chunk generation started for document_id: %s", document_id)

        metadata_file = Path(settings.METADATA_STORAGE_PATH) / f"{document_id}.json"
        if not metadata_file.exists():
            logger.warning("Chunking failed: Metadata file for document_id '%s' not found", document_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processed metadata for document ID '{document_id}' not found.",
            )

        try:
            with metadata_file.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as err:
            logger.warning("Chunking failed: Invalid metadata JSON for document_id '%s': %s", document_id, str(err))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document metadata file is corrupted or invalid.",
            ) from err

        pages = metadata.get("pages")
        if not isinstance(pages, list) or len(pages) == 0:
            logger.warning("Chunking failed: Document_id '%s' metadata contains 0 pages", document_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document metadata contains no pages.",
            )

        chunk_size = settings.CHUNK_SIZE
        chunk_overlap = settings.CHUNK_OVERLAP
        step = max(1, chunk_size - chunk_overlap)

        all_chunks: List[Chunk] = []

        # Iterate over each page separately to enforce strict page boundaries
        for page in pages:
            page_num = page.get("page_number")
            page_text = page.get("text", "")

            if not page_text or not page_text.strip():
                continue

            text_len = len(page_text)
            start_idx = 0

            while start_idx < text_len:
                end_idx = min(start_idx + chunk_size, text_len)
                chunk_str = page_text[start_idx:end_idx]

                if chunk_str:
                    chunk_obj = Chunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        page_number=page_num,
                        text=chunk_str,
                        start_char=start_idx,
                        end_char=end_idx,
                        token_count=len(chunk_str.split()),
                    )
                    all_chunks.append(chunk_obj)

                if end_idx >= text_len:
                    break

                start_idx += step

        # Save chunks JSON artifact
        chunk_dir = Path(settings.CHUNK_STORAGE_PATH)
        chunk_dir.mkdir(parents=True, exist_ok=True)
        chunk_file = chunk_dir / f"{document_id}.json"

        chunk_data = {
            "document_id": document_id,
            "total_chunks": len(all_chunks),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "chunks": [c.model_dump() for c in all_chunks],
        }

        with chunk_file.open("w", encoding="utf-8") as f:
            json.dump(chunk_data, f, indent=2)

        logger.info(
            "Chunk generation completed successfully for document_id: %s (%d chunks created)",
            document_id,
            len(all_chunks),
        )

        return ChunkGenerationResponse(
            document_id=document_id,
            chunks=len(all_chunks),
            status="chunked",
        )
