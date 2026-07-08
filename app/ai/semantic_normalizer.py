import numpy as np

from app.ai.embeddings import (
    embedding_service,
)

from app.core.logger import (
    logger,
)


class SemanticNormalizer:

    # =====================================
    # CANONICAL CROPS
    # =====================================

    CANONICAL_CROPS = [

        "गन्ना",
        "गेहूँ",
        "धान",
        "चना",
        "बाजरा",
        "प्याज",
    ]

    # =====================================
    # SYNONYMS
    # =====================================

    CROP_SYNONYMS = {

        "गेहु": "गेहूँ",
        "गेहूं": "गेहूँ",
        "गेंहू": "गेहूँ",

        "धाना": "धान",
        "राइस": "धान",

        "शुगरकेन": "गन्ना",

        "अनियन": "प्याज",
        "प्याज़": "प्याज",
    }

    def __init__(self):

        self.crop_embeddings = {}

        for crop in (
            self.CANONICAL_CROPS
        ):

            embedding = (
                embedding_service.embed(
                    crop
                )
            )

            self.crop_embeddings[
                crop
            ] = np.array(
                embedding
            )

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
    # NORMALIZE TEXT
    # =====================================

    def normalize_text(
        self,
        text: str,
    ) -> str:

        return (
            text
            .strip()
            .lower()
        )

    # =====================================
    # NORMALIZE CROP
    # =====================================

    def normalize_crop(
        self,
        crop: str | None,
        threshold: float = 0.82,
    ) -> str | None:

        if not crop:

            return crop

        normalized_crop = (
            self.normalize_text(
                crop
            )
        )

        # =============================
        # EXACT MATCH
        # =============================

        for canonical_crop in (
            self.CANONICAL_CROPS
        ):

            if (
                normalized_crop
                == self.normalize_text(
                    canonical_crop
                )
            ):

                return canonical_crop

        # =============================
        # SYNONYM MATCH
        # =============================

        if (
            normalized_crop
            in self.CROP_SYNONYMS
        ):

            return (
                self.CROP_SYNONYMS[
                    normalized_crop
                ]
            )

        # =============================
        # EMBEDDING FALLBACK
        # =============================

        try:

            query_embedding = (
                np.array(
                    embedding_service.embed(
                        crop
                    )
                )
            )

            best_crop = crop

            best_score = 0.0

            for (

                canonical_crop,
                canonical_embedding,

            ) in (
                self.crop_embeddings.items()
            ):

                similarity = (

                    self.cosine_similarity(
                        query_embedding,
                        canonical_embedding,
                    )
                )

                if (
                    similarity
                    > best_score
                ):

                    best_score = (
                        similarity
                    )

                    best_crop = (
                        canonical_crop
                    )

            # =========================
            # SAFE MATCH
            # =========================

            if (
                best_score
                >= threshold
            ):

                logger.info(
                    "Crop normalized.",
                    original=crop,
                    normalized=best_crop,
                    similarity=round(
                        best_score,
                        4,
                    ),
                )

                return best_crop

            logger.info(
                "Crop normalization skipped.",
                crop=crop,
            )

            return crop

        except Exception as exc:

            logger.exception(
                "Crop normalization failed.",
                error=str(exc),
            )

            return crop


semantic_normalizer = (
    SemanticNormalizer()
)
