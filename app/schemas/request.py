from pydantic import (
    BaseModel,
    Field,
)


class AnalyzeRequest(
    BaseModel
):
    """
    Conversational RAG request model.
    """

    thread_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "Unique conversation thread ID"
        ),
    )

    text: str = Field(
        ...,
        min_length=1,
        description=(
            "Farmer question text"
        ),
    )


class FeedbackRequest(
    BaseModel
):
    """
    User feedback model.
    """

    query: str = Field(
        ...,
        description=(
            "Original user query"
        ),
    )

    answer: str = Field(
        ...,
        description=(
            "Generated AI answer"
        ),
    )

    feedback: str = Field(
        ...,
        description=(
            "User feedback label"
        ),
    )

    comments: str | None = Field(
        default=None,
        description=(
            "Optional feedback comments"
        ),
    )

    confidence: float | None = Field(
        default=None,
        description=(
            "Answer confidence score"
        ),
    )

    source_document_id: (
        str | None
    ) = Field(
        default=None,
        description=(
            "Related source document ID"
        ),
    )