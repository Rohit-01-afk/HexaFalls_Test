"""
Service layer for opening, validating, text extraction, and page image rendering of PDF manuals.
"""

import json
import uuid
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from fastapi import HTTPException, status

from backend.core.config import settings
from backend.core.logging import logger
from backend.schemas.processing import ProcessedPage, ProcessResponse
from backend.services.image_analysis_service import image_analysis_service


class PDFProcessingService:
    """Handles PDF integrity validation, text extraction, page rendering, diagram analysis, and metadata storage."""

    @staticmethod
    def _find_pdf_path(document_id: str) -> Path:
        """
        Locates stored PDF file for document_id in MANUAL_STORAGE_PATH.

        Args:
            document_id: Document UUID identifier.

        Returns:
            Path object pointing to existing PDF file.

        Raises:
            HTTPException: 404 if no matching file is found.
        """
        storage_dir = Path(settings.MANUAL_STORAGE_PATH)
        if not storage_dir.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )

        # Search for files starting with document_id_
        candidates = list(storage_dir.glob(f"{document_id}_*.pdf"))
        if not candidates:
            # Fallback check for exact document_id.pdf
            direct_file = storage_dir / f"{document_id}.pdf"
            if direct_file.exists():
                candidates = [direct_file]

        if not candidates:
            logger.warning("PDF processing failed: Document ID '%s' not found", document_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )

        return candidates[0]

    @classmethod
    async def process_document(cls, document_id: str) -> ProcessResponse:
        """
        Processes uploaded PDF manual by extracting page text, rendering page images, analyzing diagrams, and saving metadata.

        Args:
            document_id: Document UUID identifier.

        Returns:
            ProcessResponse object containing page count and status.

        Raises:
            HTTPException: 404 for missing document, 400 for corrupted or empty PDF.
        """
        logger.info("PDF processing started for document_id: %s", document_id)

        pdf_path = cls._find_pdf_path(document_id)

        # 1. Open and validate PDF document
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as err:
            logger.warning("PDF processing failure: Corrupted PDF file %s: %s", pdf_path.name, str(err))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted PDF file.",
            ) from err

        total_pages = doc.page_count
        if total_pages == 0:
            doc.close()
            logger.warning("PDF processing failure: Document %s has 0 pages", document_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF document contains no pages.",
            )

        # 2. Prepare storage directories for images and metadata
        image_dir = Path(settings.PAGE_IMAGE_STORAGE_PATH) / document_id
        image_dir.mkdir(parents=True, exist_ok=True)

        metadata_dir = Path(settings.METADATA_STORAGE_PATH)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        pages_metadata: List[ProcessedPage] = []

        # 3. Process each page: extract text, render image, and analyze visual diagrams
        try:
            for index in range(total_pages):
                page_num = index + 1
                page = doc.load_page(index)

                # Extract text
                extracted_text = page.get_text("text") or ""

                # Render page image
                pix = page.get_pixmap(dpi=settings.PAGE_IMAGE_DPI)
                image_filename = f"page_{page_num}.{settings.PAGE_IMAGE_FORMAT}"
                image_file_path = image_dir / image_filename

                pix.save(str(image_file_path))

                relative_image_path = f"{settings.PAGE_IMAGE_STORAGE_PATH}/{document_id}/{image_filename}"

                # Perform Gemini diagram / image analysis
                diagram_analysis = await image_analysis_service.analyze_page_image(image_file_path, page_num)
                if diagram_analysis:
                    combined_text = f"{extracted_text}\n\n{diagram_analysis}".strip()
                else:
                    combined_text = extracted_text.strip()

                page_record = ProcessedPage(
                    page_id=str(uuid.uuid4()),
                    document_id=document_id,
                    page_number=page_num,
                    image_path=relative_image_path,
                    text=combined_text,
                )
                pages_metadata.append(page_record)
        except Exception as err:
            doc.close()
            logger.exception("Error while processing pages for document_id %s: %s", document_id, str(err))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing the PDF pages.",
            ) from err

        doc.close()

        # 4. Save metadata JSON
        metadata_file = metadata_dir / f"{document_id}.json"
        metadata_content = {
            "document_id": document_id,
            "total_pages": total_pages,
            "pages": [p.model_dump() for p in pages_metadata],
        }

        with metadata_file.open("w", encoding="utf-8") as f:
            json.dump(metadata_content, f, indent=2)

        logger.info(
            "PDF processing completed successfully for document_id: %s (%d pages processed)",
            document_id,
            total_pages,
        )

        return ProcessResponse(
            document_id=document_id,
            pages=total_pages,
            status="processed",
        )
