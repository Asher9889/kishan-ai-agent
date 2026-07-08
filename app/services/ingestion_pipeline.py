from typing import Any
from uuid import uuid4

from app.ai.embeddings import (
    embedding_service,
)

from app.core.logger import (
    logger,
)

from app.db.chroma import (
    chroma_service,
)


class IngestionPipeline:

    # =====================================
    # BUILD SEARCHABLE TEXT
    # =====================================

    def _build_search_text(
        self,
        record: dict[str, Any],
    ) -> str:

        """
        Build rich semantic searchable text
        from structured agricultural knowledge.
        """

        parts: list[str] = []

        # =================================
        # CORE FIELDS
        # =================================

        for field in [
            "farmer_name",
            "location",
            "district",
            "state",
            "crop",
            "category",
            "problem",
            "solution",
            "summary",
            "knowledge",
        ]:

            value = record.get(field)

            if value:

                cleaned = str(
                    value
                ).strip()

                if cleaned:

                    parts.append(
                        cleaned
                    )

        # =================================
        # KEYWORDS
        # =================================

        keywords = record.get(
            "keywords",
            [],
        )

        if isinstance(
            keywords,
            list,
        ):

            for keyword in keywords:

                keyword = str(
                    keyword
                ).strip()

                if keyword:

                    parts.append(
                        keyword
                    )

        # =================================
        # FINAL SEARCH TEXT
        # =================================

        final_text = " | ".join(
            parts
        )

        logger.info(
            "Search text built",
            text_length=len(
                final_text
            ),
        )

        return final_text

    # =====================================
    # VALIDATION
    # =====================================

    def should_ingest(
        self,
        record: dict[str, Any],
    ) -> bool:

        """
        Validate whether extracted
        knowledge is useful enough
        for semantic storage.
        """

        crop = record.get(
            "crop"
        )

        category = record.get(
            "category"
        )

        solution = record.get(
            "solution"
        )

        summary = record.get(
            "summary"
        )

        confidence = float(
            record.get(
                "confidence_score",
                0.0,
            )
        )

        # =================================
        # Crop Required
        # =================================

        if not crop:

            logger.warning(
                "Knowledge rejected: missing crop"
            )

            return False

        # =================================
        # Category Required
        # =================================

        if not category:

            logger.warning(
                "Knowledge rejected: missing category"
            )

            return False

        # =================================
        # Must have useful content
        # =================================

        if (
            not solution
            and not summary
        ):

            logger.warning(
                (
                    "Knowledge rejected: "
                    "missing solution and summary"
                )
            )

            return False

        # =================================
        # Confidence Threshold
        # =================================

        if confidence < 0.75:

            logger.warning(
                "Knowledge rejected: low confidence",
                confidence=confidence,
            )

            return False

        return True

    # =====================================
    # DUPLICATE DETECTION
    # =====================================

    def _is_duplicate(
        self,
        embedding: list[float],
        threshold: float = 0.92,
    ) -> bool:

        """
        Check semantic similarity.

        NOTE:
        We DO NOT reject ingestion.
        We only log similarity.
        """

        results = (
            chroma_service.search_similar(
                embedding=embedding,
                top_k=1,
            )
        )

        distances = results.get(
            "distances",
            [[]],
        )[0]

        if not distances:

            return False

        distance = float(
            distances[0]
        )

        similarity = (
            1.0 - distance
        )

        logger.info(
            "Similarity check completed",
            similarity=similarity,
            threshold=threshold,
        )

        return (
            similarity >= threshold
        )

    # =====================================
    # INGEST
    # =====================================

    def ingest(
        self,
        record: dict[str, Any],
        document_id: str | None = None,
    ) -> str:

        """
        Generate embedding and store
        agricultural knowledge
        in ChromaDB.
        """

        # =================================
        # VALIDATE
        # =================================

        if not self.should_ingest(
            record
        ):

            raise ValueError(
                "Knowledge validation failed"
            )

        # =================================
        # DOCUMENT ID
        # =================================

        if document_id is None:

            document_id = str(
                uuid4()
            )

        # =================================
        # SEARCHABLE TEXT
        # =================================

        search_text = (
            self._build_search_text(
                record
            )
        )

        if not search_text.strip():

            raise ValueError(
                "No searchable content found"
            )

        logger.info(
            "Generating embedding for ingestion",
            document_id=document_id,
        )

        # =================================
        # EMBEDDING
        # =================================

        embedding = (
            embedding_service.embed(
                search_text
            )
        )

        # =================================
        # DUPLICATE CHECK
        # =================================

        is_duplicate = (
            self._is_duplicate(
                embedding=embedding,
            )
        )

        if is_duplicate:

            logger.warning(
                (
                    "Similar knowledge found, "
                    "but ingestion allowed."
                ),
                document_id=document_id,
            )

        # =================================
        # CLEAN METADATA
        # =================================

        metadata = {

            key: value

            for key, value in record.items()

            if value is not None
            and isinstance(
                value,
                (
                    str,
                    int,
                    float,
                    bool,
                ),
            )
        }

        # =================================
        # STORE
        # =================================

        chroma_service.add_document(
            document_id=document_id,
            text=search_text,
            embedding=embedding,
            metadata=metadata,
        )

        logger.info(
            "Knowledge record ingested",
            document_id=document_id,
            crop=record.get(
                "crop"
            ),
            category=record.get(
                "category"
            ),
            farmer_name=record.get(
                "farmer_name"
            ),
        )

        return document_id


ingestion_pipeline = (
    IngestionPipeline()
)