from pydantic import BaseModel, Field


class KnowledgeRecord(BaseModel):
    farmer_name: str | None = None

    location: str | None = None

    district: str | None = None

    state: str | None = None

    crop: str | None = None

    season: str | None = None

    category: str = Field(
        ...,
        min_length=1,
    )

    problem: str | None = None

    solution: str | None = None

    summary: str | None = None

    language: str = "hi"

    confidence_score: float = 0.9

    trust_score: float = 0.9