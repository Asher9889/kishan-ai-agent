from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable response message")
    data: dict[str, Any] | None = Field(
        default=None,
        description="Optional response payload",
    )