from typing import Any

import chromadb
from chromadb.api.models.Collection import (
    Collection,
)

from app.core.config import (
    settings,
)
from app.core.logger import (
    logger,
)


class ChromaService:
    def __init__(self) -> None:

        logger.info(
            "Initializing ChromaDB",
            path=settings.CHROMA_PATH,
            collection=(
                settings.CHROMA_COLLECTION
            ),
        )

        self.client = (
            chromadb.PersistentClient(
                path=settings.CHROMA_PATH,
            )
        )

        self.collection: Collection = (
            self.client.get_or_create_collection(
                name=(
                    settings.CHROMA_COLLECTION
                ),
                metadata={
                    "description": (
                        "KrishiGPT agricultural "
                        "knowledge base"
                    )
                },
            )
        )

        logger.info(
            "ChromaDB initialized",
            collection=(
                settings.CHROMA_COLLECTION
            ),
        )

    def add_document(
        self,
        document_id: str,
        text: str,
        embedding: list[float],
        metadata: (
            dict[str, Any]
            | None
        ) = None,
    ) -> None:

        self.collection.upsert(
            ids=[document_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[
                metadata or {}
            ],
        )

        logger.info(
            "Document stored in ChromaDB",
            document_id=document_id,
        )

    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> dict[str, Any]:

        results = (
            self.collection.query(
                query_embeddings=[
                    embedding
                ],
                n_results=top_k,
            )
        )

        logger.info(
            "ChromaDB search completed",
            top_k=top_k,
            results_count=len(
                results["ids"][0]
            ),
        )

        return results

    def search_similar(
        self,
        embedding: list[float],
        top_k: int = 1,
    ) -> dict[str, Any]:
        """
        Search similar vectors
        directly using embeddings.
        """

        results = (
            self.collection.query(
                query_embeddings=[
                    embedding
                ],
                n_results=top_k,
            )
        )

        logger.info(
            "Similarity search completed",
            top_k=top_k,
            results_count=len(
                results["ids"][0]
            ),
        )

        return results

    def count(self) -> int:

        return (
            self.collection.count()
        )


chroma_service = (
    ChromaService()
)