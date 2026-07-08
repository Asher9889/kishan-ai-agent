from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logger import logger

class EmbeddingService:
    def __init__(self) -> None:
        logger.info(
            "Loading embedding Model",
            model=settings.EMBEDDING_MODEL,
        )
        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL
        )
        logger.info(
            "Embedding Model loaded",
            model=settings.EMBEDDING_MODEL,
            dimension=self.model.get_sentence_embedding_dimension(),
        )
    
    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(
            text,
            normalize_embeddings= True,
            convert_to_numpy= True,
        )

        logger.info(
            "Embedding generated",
            input_length=len(text),
            dimension=len(vector),
        )

        return vector.tolist()
    
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
    

embedding_service = EmbeddingService()

