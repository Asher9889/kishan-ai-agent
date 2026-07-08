from typing import Any

import numpy as np

from app.ai.embeddings import (
    embedding_service,
)

from app.core.logger import (
    logger,
)


class MemoryRelevanceService:

    # =====================================
    # COSINE SIMILARITY
    # =====================================

    def cosine_similarity(
        self,
        a: np.ndarray,
        b: np.ndarray,
    ) -> float:

        denominator = (
            np.linalg.norm(a)
            * np.linalg.norm(b)
        )

        if denominator == 0:
            return 0.0

        return float(
            np.dot(a, b)
            / denominator
        )

    # =====================================
    # RECENCY SCORE
    # =====================================

    def recency_score(
        self,
        index: int,
        total: int,
    ) -> float:

        """
        More recent messages
        get higher score.
        """

        distance = (
            total - index
        )

        return max(
            0.1,
            1 / distance,
        )

    # =====================================
    # CONTEXT REFERENCE BOOST
    # =====================================

    def reference_boost(
        self,
        query: str,
    ) -> float:

        reference_words = [

            "वही",
            "उसमें",
            "उसका",
            "पहले वाला",
            "फिर",
            "यह",
            "ये",
            "इसमें",
        ]

        for word in (
            reference_words
        ):

            if word in query:

                return 0.25

        return 0.0

    # =====================================
    # MEMORY FILTER
    # =====================================

    def filter_relevant_memory(
        self,
        *,
        current_query: str,
        messages: list[
            dict[str, Any]
        ],
        threshold: float = 0.45,
        max_messages: int = 6,
    ) -> list[dict[str, Any]]:

        if not messages:

            return []

        try:

            query_embedding = (
                np.array(
                    embedding_service.embed(
                        current_query
                    )
                )
            )

            scored_messages = []

            total_messages = (
                len(messages)
            )

            reference_bonus = (
                self.reference_boost(
                    current_query
                )
            )

            for idx, message in enumerate(
                messages
            ):

                content = (
                    message.get(
                        "message",
                        "",
                    )
                )

                if not content:
                    continue

                try:

                    message_embedding = (
                        np.array(
                            embedding_service.embed(
                                content
                            )
                        )
                    )

                    semantic_score = (
                        self.cosine_similarity(
                            query_embedding,
                            message_embedding,
                        )
                    )

                    recency = (
                        self.recency_score(
                            idx + 1,
                            total_messages,
                        )
                    )

                    # =========================
                    # ROLE BOOST
                    # =========================

                    role = message.get(
                        "role",
                        "user",
                    )

                    role_boost = (
                        0.05
                        if role == "user"
                        else 0.0
                    )

                    # =========================
                    # FINAL SCORE
                    # =========================

                    final_score = (

                        semantic_score * 0.7
                        + recency * 0.2
                        + role_boost
                        + reference_bonus
                    )

                    if (
                        final_score
                        >= threshold
                    ):

                        enriched_message = {
                            **message,
                            "semantic_score": round(
                                semantic_score,
                                4,
                            ),
                            "recency_score": round(
                                recency,
                                4,
                            ),
                            "final_score": round(
                                final_score,
                                4,
                            ),
                        }

                        scored_messages.append(
                            enriched_message
                        )

                except Exception as exc:

                    logger.exception(
                        "Memory scoring failed.",
                        error=str(exc),
                    )

            # =================================
            # SORT BY FINAL SCORE
            # =================================

            scored_messages.sort(
                key=lambda x: x[
                    "final_score"
                ],
                reverse=True,
            )

            filtered = (
                scored_messages[
                    :max_messages
                ]
            )

            logger.info(
                "Relevant memory filtered.",
                total_messages=len(
                    messages
                ),
                selected=len(filtered),
            )

            return filtered

        except Exception as exc:

            logger.exception(
                "Memory relevance failed.",
                error=str(exc),
            )

            return []


memory_relevance_service = (
    MemoryRelevanceService()
)
