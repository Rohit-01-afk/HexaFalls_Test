"""
Service layer for handling PDF file uploads, validation, and storage.
"""

import re
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.upload import UploadResponse


class UploadService:
    """Handles PDF validation, safe file storage, and upload response generation."""

    @staticmethod
    async def process_pdf_upload(file: UploadFile) -> UploadResponse:
        """
        Validates uploaded file format, MIME type, and size limit, then saves to storage.

        Args:
            file: FastAPI UploadFile instance.

        Returns:
            UploadResponse model containing upload metadata.

        Raises:
            HTTPException: 400 for bad extension/MIME/path, 413 for oversized file.
        """
        original_filename = file.filename or ""
        logger.info("Upload started for file: %s", original_filename)

        # 1. Validate extension
        clean_filename = Path(original_filename).name
        if not clean_filename.lower().endswith(".pdf"):
            logger.warning(
                "Validation failure: Invalid file extension '%s' for upload: %s",
                clean_filename,
                original_filename,
            )
            logger.info("Upload rejected for file: %s", original_filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file extension. Only .pdf files are allowed.",
            )

        # 2. Validate MIME type
        if file.content_type != "application/pdf":
            logger.warning(
                "Validation failure: Invalid MIME type '%s' for file: %s",
                file.content_type,
                original_filename,
            )
            logger.info("Upload rejected for file: %s", original_filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MIME type. Only application/pdf is allowed.",
            )

        # 3. Generate UUID and safe stored filename
        document_id = str(uuid.uuid4())
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean_filename)
        stored_filename = f"{document_id}_{safe_name}"

        storage_dir = Path(settings.MANUAL_STORAGE_PATH)
        storage_dir.mkdir(parents=True, exist_ok=True)

        target_path = storage_dir / stored_filename

        # Prevent path traversal
        try:
            target_path.resolve().relative_to(storage_dir.resolve())
        except ValueError:
            logger.warning("Validation failure: Path traversal attempt detected: %s", original_filename)
            logger.info("Upload rejected for file: %s", original_filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target storage path.",
            )

        # Prevent overwrite
        if target_path.exists():
            logger.warning("Validation failure: Stored file already exists: %s", stored_filename)
            logger.info("Upload rejected for file: %s", original_filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target file already exists.",
            )

        # 4. Stream and write file while validating maximum size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        total_bytes = 0
        chunk_size = 1024 * 1024  # 1 MB chunk

        try:
            with target_path.open("wb") as out_file:
                while chunk := await file.read(chunk_size):
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        out_file.close()
                        if target_path.exists():
                            target_path.unlink()
                        logger.warning(
                            "Validation failure: File size (%d bytes) exceeds limit of %d MB",
                            total_bytes,
                            settings.MAX_UPLOAD_SIZE_MB,
                        )
                        logger.info("Upload rejected for file: %s", original_filename)
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
                        )
                    out_file.write(chunk)
        except Exception:
            # Clean up partial file on failure if still exists
            if target_path.exists():
                target_path.unlink()
            raise

        logger.info(
            "Upload completed successfully: document_id=%s, filename=%s, size=%d bytes",
            document_id,
            clean_filename,
            total_bytes,
        )

        return UploadResponse(
            document_id=document_id,
            filename=clean_filename,
            stored_filename=stored_filename,
            size=total_bytes,
            status="uploaded",
        )
