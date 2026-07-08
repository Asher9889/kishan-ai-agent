from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Original farmer query",
    )

    answer: str = Field(
        ...,
        min_length=1,
        description="Final answer returned to the farmer",
    )

    feedback: Literal[
        "helpful",
        "not_helpful",
        "wrong",
    ]

    comments: str | None = Field(
        default=None,
        description="Optional farmer comments",
    )

    confidence: float | None = Field(
        default=None,
        description="Answer confidence score",
    )

    source_document_id: str | None = Field(
        default=None,
        description="Best matched document ID",
    )