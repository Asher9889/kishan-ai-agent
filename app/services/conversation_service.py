import json
from typing import Any

from app.core.logger import logger
from app.db.mssql import mssql_service


class ConversationService:
    def save(
        self,
        *,
        input_type: str,
        original_query: str,
        cleaned_query: str | None = None,
        transcription: str | None = None,
        analysis: dict[str, Any] | None = None,
        retrieved_count: int | None = None,
        best_match_score: float | None = None,
        final_answer: str | None = None,
        answer_confidence: float | None = None,
        source: dict[str, Any] | None = None,
    ) -> None:
        if not mssql_service.is_enabled():
            logger.warning(
                "MSSQL not configured; conversation not persisted."
            )
            return

        sql = """
        INSERT INTO conversations (
            input_type,
            original_query,
            cleaned_query,
            transcription,
            analysis_json,
            retrieved_count,
            best_match_score,
            final_answer,
            answer_confidence,
            source_json
        )
        VALUES (
            :input_type,
            :original_query,
            :cleaned_query,
            :transcription,
            :analysis_json,
            :retrieved_count,
            :best_match_score,
            :final_answer,
            :answer_confidence,
            :source_json
        )
        """

        try:
            mssql_service.execute(
                sql=sql,
                params={
                    "input_type": input_type,
                    "original_query": original_query,
                    "cleaned_query": cleaned_query,
                    "transcription": transcription,
                    "analysis_json": (
                        json.dumps(
                            analysis,
                            ensure_ascii=False,
                        )
                        if analysis
                        else None
                    ),
                    "retrieved_count": retrieved_count,
                    "best_match_score": best_match_score,
                    "final_answer": final_answer,
                    "answer_confidence": answer_confidence,
                    "source_json": (
                        json.dumps(
                            source,
                            ensure_ascii=False,
                        )
                        if source
                        else None
                    ),
                },
            )

            logger.info(
                "Conversation saved to MSSQL",
                input_type=input_type,
                retrieved_count=retrieved_count,
            )

        except Exception as exc:
            logger.exception(
                "Failed to save conversation",
                error=str(exc),
            )
            # Do not raise. Core API should still succeed.


conversation_service = ConversationService()