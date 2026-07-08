from typing import Any

from unidecode import unidecode

from app.core.logger import (
    logger,
)


class RetrievalFilterService:

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
    # VALIDATE CROP MATCH
    # =====================================

    def validate_crop_match(
        self,
        extracted_crop: str,
        retrieved_crop: str,
    ) -> bool:

        if not extracted_crop:
            return True

        if not retrieved_crop:
            return True

        extracted_crop = (
            extracted_crop
            .strip()
            .lower()
        )

        retrieved_crop = (
            retrieved_crop
            .strip()
            .lower()
        )

        return (
            extracted_crop
            == retrieved_crop
        )

    # =====================================
    # FILTER RESULTS
    # =====================================

    def filter_results(
        self,
        *,
        results: list[
            dict[str, Any]
        ],
        query_analysis: dict[
            str,
            Any,
        ],
    ) -> list[
        dict[str, Any]
    ]:

        """
        Smart metadata-aware filtering
        for agricultural retrieval.
        """

        if not results:
            return []

        # =====================================
        # Query Metadata
        # =====================================

        query_crop = (
            self.normalize_text(
                query_analysis.get(
                    "crop"
                )
                or ""
            )
        )

        query_category = (
            self.normalize_text(
                query_analysis.get(
                    "category"
                )
                or ""
            )
        )

        query_problem = (
            self.normalize_text(
                query_analysis.get(
                    "problem"
                )
                or ""
            )
        )

        query_farmer_name = (
            self.normalize_text(
                query_analysis.get(
                    "farmer_name"
                )
                or ""
            )
        )

        query_location = (
            self.normalize_text(
                query_analysis.get(
                    "location"
                )
                or ""
            )
        )

        query_district = (
            self.normalize_text(
                query_analysis.get(
                    "district"
                )
                or ""
            )
        )

        query_state = (
            self.normalize_text(
                query_analysis.get(
                    "state"
                )
                or ""
            )
        )

        filtered_results = []

        # =====================================
        # Iterate Results
        # =====================================

        for item in results:

            metadata = (
                item.get(
                    "metadata",
                    {},
                )
                or {}
            )

            metadata_crop = (
                self.normalize_text(
                    metadata.get(
                        "crop"
                    )
                    or ""
                )
            )

            metadata_category = (
                self.normalize_text(
                    metadata.get(
                        "category"
                    )
                    or ""
                )
            )

            metadata_problem = (
                self.normalize_text(
                    metadata.get(
                        "problem"
                    )
                    or ""
                )
            )

            metadata_farmer_name = (
                self.normalize_text(
                    metadata.get(
                        "farmer_name"
                    )
                    or ""
                )
            )

            metadata_location = (
                self.normalize_text(
                    metadata.get(
                        "location"
                    )
                    or ""
                )
            )

            metadata_district = (
                self.normalize_text(
                    metadata.get(
                        "district"
                    )
                    or ""
                )
            )

            metadata_state = (
                self.normalize_text(
                    metadata.get(
                        "state"
                    )
                    or ""
                )
            )

            # =================================
            # STRICT CROP VALIDATION
            # =================================

            crop_match = (
                self.validate_crop_match(
                    extracted_crop=(
                        query_crop
                    ),
                    retrieved_crop=(
                        metadata_crop
                    ),
                )
            )

            # =================================
            # REJECT WRONG CROPS
            # =================================

            if not crop_match:

                logger.info(
                    "Rejected due to crop mismatch",
                    query_crop=query_crop,
                    metadata_crop=metadata_crop,
                )

                continue

            score = 0.0

            # =================================
            # Crop Matching
            # =================================

            if (
                query_crop
                and metadata_crop
            ):

                if (
                    query_crop
                    in metadata_crop
                    or metadata_crop
                    in query_crop
                ):

                    score += 5

                else:

                    logger.info(
                        "Crop mismatch",
                        query_crop=query_crop,
                        metadata_crop=metadata_crop,
                    )

                    score -= 2

            # =================================
            # Category Matching
            # =================================

            if (
                query_category
                and metadata_category
            ):

                if (
                    query_category
                    in metadata_category
                    or metadata_category
                    in query_category
                ):

                    score += 2

            # =================================
            # Problem Matching
            # =================================

            if (
                query_problem
                and metadata_problem
            ):

                if (
                    query_problem
                    in metadata_problem
                    or metadata_problem
                    in query_problem
                ):

                    score += 3

            # =================================
            # Farmer Name Matching
            # =================================

            if (
                query_farmer_name
                and metadata_farmer_name
            ):

                if (
                    query_farmer_name
                    in metadata_farmer_name
                    or metadata_farmer_name
                    in query_farmer_name
                ):

                    score += 5

            # =================================
            # Location Matching
            # =================================

            if (
                query_location
                and metadata_location
            ):

                if (
                    query_location
                    in metadata_location
                    or metadata_location
                    in query_location
                ):

                    score += 2

            # =================================
            # District Matching
            # =================================

            if (
                query_district
                and metadata_district
            ):

                if (
                    query_district
                    in metadata_district
                    or metadata_district
                    in query_district
                ):

                    score += 1.5

            # =================================
            # State Matching
            # =================================

            if (
                query_state
                and metadata_state
            ):

                if (
                    query_state
                    in metadata_state
                    or metadata_state
                    in query_state
                ):

                    score += 1.5

            # =================================
            # Semantic Similarity Bonus
            # =================================

            similarity_score = (
                item.get(
                    "score",
                    0.0,
                )
                or 0.0
            )

            if similarity_score > 0:

                score += (
                    similarity_score * 2
                )

            # =================================
            # Save Final Score
            # =================================

            item[
                "metadata_filter_score"
            ] = round(
                score,
                3,
            )

            # =================================
            # Relaxed Filtering
            # =================================

            if score >= 0.15:

                filtered_results.append(
                    item
                )

        # =====================================
        # Sort by Score
        # =====================================

        filtered_results.sort(
            key=lambda x: x.get(
                "metadata_filter_score",
                0,
            ),
            reverse=True,
        )

        # =====================================
        # Fallback Logic
        # =====================================

        if not filtered_results:

            logger.warning(
                "Metadata filtering returned empty results"
            )

            # =================================
            # Farmer query fallback
            # =================================

            if query_farmer_name:

                logger.info(
                    "Using farmer fallback retrieval"
                )

                return results[:5]

            # =================================
            # Semantic fallback
            # =================================

            return results[:3]

        logger.info(
            "Metadata filtering completed",
            original=len(results),
            filtered=len(
                filtered_results
            ),
        )

        return filtered_results


retrieval_filter_service = (
    RetrievalFilterService()
)