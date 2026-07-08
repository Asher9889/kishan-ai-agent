import re
from pathlib import Path
from uuid import uuid4

import fitz

from app.core.logger import logger
from app.services.ingestion_pipeline import (
    ingestion_pipeline,
)


class PDFPipeline:

    def extract_pages(
        self,
        pdf_path: Path,
    ) -> list[dict]:

        pages = []

        document = fitz.open(
            pdf_path
        )

        for index, page in enumerate(
            document
        ):
            text = page.get_text()

            pages.append(
                {
                    "page": index + 1,
                    "text": text,
                }
            )

        document.close()

        return pages

    def clean_text(
        self,
        text: str,
    ) -> str:

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def semantic_chunk(
        self,
        text: str,
        max_chunk_size: int = 700,
    ) -> list[str]:

        paragraphs = re.split(
            r"\n\s*\n",
            text,
        )

        chunks: list[str] = []

        current_chunk = ""

        for para in paragraphs:

            para = self.clean_text(
                para
            )

            if not para:
                continue

            if (
                len(current_chunk)
                + len(para)
                < max_chunk_size
            ):
                current_chunk += (
                    "\n" + para
                )

            else:
                if current_chunk:
                    chunks.append(
                        current_chunk.strip()
                    )

                current_chunk = para

        if current_chunk:
            chunks.append(
                current_chunk.strip()
            )

        return chunks

    def detect_topic(
        self,
        text: str,
    ) -> str:

        lines = text.split("\n")

        for line in lines[:5]:

            line = line.strip()

            if (
                5
                < len(line)
                < 80
            ):
                return line

        return "General Agriculture"

    def ingest_pdf(
        self,
        pdf_path: Path,
        source_name: str,
    ) -> int:

        logger.info(
            "Starting smart PDF ingestion",
            source=source_name,
        )

        pages = self.extract_pages(
            pdf_path
        )

        ingested_count = 0

        for page_data in pages:

            page_number = page_data[
                "page"
            ]

            raw_text = page_data[
                "text"
            ]

            chunks = self.semantic_chunk(
                raw_text
            )

            for chunk in chunks:

                topic = self.detect_topic(
                    chunk
                )

                record = {
                    "category": (
                        "PDF Knowledge"
                    ),
                    "summary": chunk,
                    "source": source_name,
                    "source_type": "pdf",
                    "page": page_number,
                    "topic": topic,
                    "confidence_score": 1.0,
                }

                try:
                    ingestion_pipeline.ingest(
                        record=record,
                        document_id=str(
                            uuid4()
                        ),
                    )

                    ingested_count += 1

                except Exception as exc:

                    logger.warning(
                        "PDF chunk ingestion failed",
                        error=str(exc),
                    )

        logger.info(
            "Smart PDF ingestion completed",
            chunks=ingested_count,
        )

        return ingested_count


pdf_pipeline = PDFPipeline()