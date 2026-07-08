# File: app/services/retrieval_pipeline.py

from typing import Any

from unidecode import unidecode

from app.ai.embeddings import (
    embedding_service,
)

from app.core.logger import (
    logger,
)

from app.db.chroma import (
    chroma_service,
)


class RetrievalPipeline:

    # =====================================
    # NORMALIZE TEXT
    # =====================================

    def normalize_text(
        self,
        text: str,
    ) -> str:

        text = (
            str(text)
            .strip()
            .lower()
        )

        return unidecode(text)

    # =====================================
    # BUILD SEARCH QUERY
    # =====================================

    def build_search_query(
        self,
        *,
        query: str,
        query_analysis: dict,
    ) -> str:

        parts = [query]

        for field in [
            "crop",
            "category",
            "symptom",
            "farmer_name",
            "location",
            "district",
            "state",
        ]:

            value = (
                query_analysis.get(field)
                or ""
            )

            value = str(
                value
            ).strip()

            if value:

                parts.append(value)

        expanded_query = (
            " | ".join(parts)
        )

        return expanded_query

    # =====================================
    # METADATA SCORE
    # =====================================

    def metadata_score(
        self,
        metadata: dict,
        query_analysis: dict,
    ) -> float:

        score = 0.0

        # =====================================
        # QUERY VALUES
        # =====================================

        crop = self.normalize_text(
            query_analysis.get("crop")
            or ""
        )

        category = self.normalize_text(
            query_analysis.get("category")
            or ""
        )

        symptom = self.normalize_text(
            query_analysis.get("symptom")
            or ""
        )

        farmer_name = self.normalize_text(
            query_analysis.get("farmer_name")
            or ""
        )

        location = self.normalize_text(
            query_analysis.get("location")
            or ""
        )

        district = self.normalize_text(
            query_analysis.get("district")
            or ""
        )

        state = self.normalize_text(
            query_analysis.get("state")
            or ""
        )

        # =====================================
        # METADATA VALUES
        # =====================================

        metadata_crop = (
            self.normalize_text(
                metadata.get(
                    "crop",
                    "",
                )
            )
        )

        metadata_category = (
            self.normalize_text(
                metadata.get(
                    "category",
                    "",
                )
            )
        )

        metadata_problem = (
            self.normalize_text(
                metadata.get(
                    "problem",
                    "",
                )
            )
        )

        metadata_farmer_name = (
            self.normalize_text(
                metadata.get(
                    "farmer_name",
                    "",
                )
            )
        )

        metadata_location = (
            self.normalize_text(
                metadata.get(
                    "location",
                    "",
                )
            )
        )

        metadata_district = (
            self.normalize_text(
                metadata.get(
                    "district",
                    "",
                )
            )
        )

        metadata_state = (
            self.normalize_text(
                metadata.get(
                    "state",
                    "",
                )
            )
        )

        # =====================================
        # CROP MATCH
        # =====================================

        if (
            crop
            and crop
            in metadata_crop
        ):

            score += 0.35

        # =====================================
        # CATEGORY MATCH
        # =====================================

        if (
            category
            and category
            in metadata_category
        ):

            score += 0.20

        # =====================================
        # SYMPTOM MATCH
        # =====================================

        if (
            symptom
            and symptom
            in metadata_problem
        ):

            score += 0.25

        # =====================================
        # FARMER NAME MATCH
        # =====================================

        if (
            farmer_name
            and farmer_name
            in metadata_farmer_name
        ):

            score += 0.25

        # =====================================
        # LOCATION MATCH
        # =====================================

        if (
            location
            and location
            in metadata_location
        ):

            score += 0.10

        # =====================================
        # DISTRICT MATCH
        # =====================================

        if (
            district
            and district
            in metadata_district
        ):

            score += 0.10

        # =====================================
        # STATE MATCH
        # =====================================

        if (
            state
            and state
            in metadata_state
        ):

            score += 0.10

        return score

    # =====================================
    # RETRIEVE
    # =====================================

    def retrieve(
        self,
        *,
        query: str,
        query_analysis: dict,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:

        logger.info(
            "Generating query embedding.",
            query=query,
            top_k=top_k,
        )

        try:

            # =============================
            # BUILD EXPANDED QUERY
            # =============================

            search_query = (
                self.build_search_query(
                    query=query,
                    query_analysis=query_analysis,
                )
            )

            logger.info(
                "Expanded retrieval query",
                search_query=search_query,
            )

            # =============================
            # QUERY EMBEDDING
            # =============================

            query_embedding = (
                embedding_service.embed(
                    search_query
                )
            )

            # =============================
            # VECTOR SEARCH
            # =============================

            results = (
                chroma_service.search(
                    embedding=query_embedding,
                    top_k=top_k * 2,
                )
            )

            ids = results.get(
                "ids",
                [[]],
            )[0]

            documents = results.get(
                "documents",
                [[]],
            )[0]

            metadatas = results.get(
                "metadatas",
                [[]],
            )[0]

            distances = results.get(
                "distances",
                [[]],
            )[0]

            retrieved_items = []

            # =============================
            # ENRICH RESULTS
            # =============================

            for index, document_id in enumerate(
                ids
            ):

                metadata = (
                    metadatas[index]
                    or {}
                )

                distance = (
                    distances[index]
                )

                semantic_score = max(
                    0.0,
                    1 - float(distance),
                )

                metadata_boost = (
                    self.metadata_score(
                        metadata,
                        query_analysis,
                    )
                )

                final_score = (
                    semantic_score * 0.7
                    + metadata_boost
                )

                retrieved_items.append(
                    {
                        "document_id": document_id,

                        "document": documents[
                            index
                        ],

                        "metadata": metadata,

                        "distance": distance,

                        "score": round(
                            final_score,
                            4,
                        ),

                        "semantic_score": round(
                            semantic_score,
                            4,
                        ),

                        "metadata_score": round(
                            metadata_boost,
                            4,
                        ),

                        "final_score": round(
                            final_score,
                            4,
                        ),
                    }
                )

            # =============================
            # RERANK
            # =============================

            retrieved_items.sort(
                key=lambda x: x[
                    "final_score"
                ],
                reverse=True,
            )

            # =============================
            # FINAL RESULTS
            # =============================

            final_results = (
                retrieved_items[:top_k]
            )

            logger.info(
                "Retrieval completed.",
                total_results=len(
                    final_results
                ),
            )

            return final_results

        except Exception as exc:

            logger.exception(
                "Retrieval pipeline failed.",
                error=str(exc),
            )

            return []


retrieval_pipeline = (
    RetrievalPipeline()
)