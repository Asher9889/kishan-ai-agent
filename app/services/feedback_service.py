from app.core.logger import logger
from app.db.mssql import mssql_service
from app.schemas.feedback import FeedbackRequest


class FeedbackService:
    def save(
        self,
        request: FeedbackRequest,
    ) -> None:
        if not mssql_service.is_enabled():
            logger.warning(
                "MSSQL not configured; feedback not persisted."
            )
            return

        sql = """
        INSERT INTO feedback (
            query,
            answer,
            feedback,
            comments,
            confidence,
            source_document_id
        )
        VALUES (
            :query,
            :answer,
            :feedback,
            :comments,
            :confidence,
            :source_document_id
        )
        """

        try:
            mssql_service.execute(
                sql=sql,
                params={
                    "query": request.query,
                    "answer": request.answer,
                    "feedback": request.feedback,
                    "comments": request.comments,
                    "confidence": request.confidence,
                    "source_document_id": request.source_document_id,
                },
            )

            logger.info(
                "Feedback saved to MSSQL",
                feedback=request.feedback,
            )

        except Exception as exc:
            logger.exception(
                "Failed to save feedback to MSSQL",
                error=str(exc),
            )
            # Do not raise the exception.
            # API should still return success.


feedback_service = FeedbackService()