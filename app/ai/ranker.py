from typing import Any

from app.core.logger import (
    logger,
)


class RankingService:

    # =====================================
    # DISTANCE → SIMILARITY
    # =====================================

    def similarity_score(
        self,
        distance: float,
    ) -> float:

        similarity = (
            1.0 - float(distance)
        )

        return max(
            0.0,
            min(
                1.0,
                similarity,
            ),
        )

    # =====================================
    # METADATA MATCH SCORE
    # =====================================

    def metadata_score(
        self,
        item: dict[str, Any],
        query_context: dict,
    ) -> float:

        metadata = (
            item.get(
                "metadata",
                {},
            )
            or {}
        )

        score = 0.0

        query_crop = (
            str(
                query_context.get(
                    "crop",
                    "",
                )
            )
            .lower()
        )

        query_category = (
            str(
                query_context.get(
                    "category",
                    "",
                )
            )
            .lower()
        )

        query_symptom = (
            str(
                query_context.get(
                    "symptom",
                    "",
                )
            )
            .lower()
        )

        metadata_crop = (
            str(
                metadata.get(
                    "crop",
                    "",
                )
            )
            .lower()
        )

        metadata_category = (
            str(
                metadata.get(
                    "category",
                    "",
                )
            )
            .lower()
        )

        metadata_problem = (
            str(
                metadata.get(
                    "problem",
                    "",
                )
            )
            .lower()
        )

        # =========================
        # CROP MATCH
        # =========================

        if (
            query_crop
            and query_crop
            in metadata_crop
        ):

            score += 0.25

        # =========================
        # CATEGORY MATCH
        # =========================

        if (
            query_category
            and query_category
            in metadata_category
        ):

            score += 0.15

        # =========================
        # SYMPTOM MATCH
        # =========================

        if (
            query_symptom
            and query_symptom
            in metadata_problem
        ):

            score += 0.20

        return score

    # =====================================
    # TRUST SCORE
    # =====================================

    def trust_score(
        self,
        metadata: dict,
    ) -> float:

        try:

            return float(
                metadata.get(
                    "trust_score",
                    0.75,
                )
            )

        except Exception:

            return 0.75

    # =====================================
    # CONFIDENCE SCORE
    # =====================================

    def confidence_score(
        self,
        metadata: dict,
    ) -> float:

        try:

            return float(
                metadata.get(
                    "confidence_score",
                    0.75,
                )
            )

        except Exception:

            return 0.75

    # =====================================
    # COMPUTE FINAL SCORE
    # =====================================

    def compute_score(
        self,
        item: dict[str, Any],
        query_context: dict,
    ) -> float:

        metadata = (
            item.get(
                "metadata",
                {},
            )
            or {}
        )

        distance = float(
            item.get(
                "distance",
                1.0,
            )
        )

        similarity = (
            self.similarity_score(
                distance
            )
        )

        metadata_match = (
            self.metadata_score(
                item,
                query_context,
            )
        )

        trust = (
            self.trust_score(
                metadata
            )
        )

        confidence = (
            self.confidence_score(
                metadata
            )
        )

        # =========================
        # FINAL SCORE
        # =========================

        final_score = (

            similarity * 0.45
            + metadata_match * 0.30
            + trust * 0.15
            + confidence * 0.10
        )

        return round(
            final_score,
            4,
        )

    # =====================================
    # REMOVE DUPLICATES
    # =====================================

    def deduplicate(
        self,
        ranked_items: list[
            dict[str, Any]
        ],
    ):

        unique_items = []

        seen_documents = set()

        for item in ranked_items:

            document = (
                item.get(
                    "document",
                    "",
                )
                .strip()
            )

            short_key = (
                document[:150]
            )

            if (
                short_key
                in seen_documents
            ):

                continue

            seen_documents.add(
                short_key
            )

            unique_items.append(
                item
            )

        return unique_items

    # =====================================
    # RANK
    # =====================================

    def rank(
        self,
        *,
        items: list[
            dict[str, Any]
        ],
        query_context: dict,
        top_k: int = 5,
    ) -> list[
        dict[str, Any]
    ]:

        ranked_items = []

        for item in items:

            score = (
                self.compute_score(
                    item,
                    query_context,
                )
            )

            enriched_item = {
                **item,
                "ranking_score": score,
            }

            ranked_items.append(
                enriched_item
            )

        # =============================
        # SORT
        # =============================

        ranked_items.sort(
            key=lambda x: x[
                "ranking_score"
            ],
            reverse=True,
        )

        # =============================
        # REMOVE DUPLICATES
        # =============================

        ranked_items = (
            self.deduplicate(
                ranked_items
            )
        )

        # =============================
        # FINAL RESULTS
        # =============================

        final_results = (
            ranked_items[:top_k]
        )

        logger.info(
            "Ranking completed.",
            results_count=len(
                final_results
            ),
            top_score=(
                final_results[0][
                    "ranking_score"
                ]
                if final_results
                else None
            ),
        )

        return final_results

    # =====================================
    # GET BEST
    # =====================================

    def get_best(
        self,
        *,
        items: list[
            dict[str, Any]
        ],
        query_context: dict,
    ) -> (
        dict[str, Any]
        | None
    ):

        ranked = self.rank(
            items=items,
            query_context=query_context,
            top_k=1,
        )

        if not ranked:

            return None

        return ranked[0]


ranking_service = (
    RankingService()
)
