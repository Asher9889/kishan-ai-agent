from pydantic import (
    BaseModel,
    Field,
)


class AnalyzeRequest(
    BaseModel
):
    """
    Conversational RAG request
    model.
    """

    thread_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "Unique conversation thread ID"
        ),
        examples=[
            "thread_001"
        ],
    )

    text: str = Field(
        ...,
        min_length=1,
        description=(
            "Farmer question text"
        ),
        examples=[
            (
                "गन्ने की फसल में "
                "कौन सी खाद डालें?"
            )
        ],
    )


class FeedbackRequest(
    BaseModel
):

    query: str

    answer: str

    feedback: str

    comments: str | None = None

    confidence: float | None = None

    source_document_id: (
        str | None
    ) = None