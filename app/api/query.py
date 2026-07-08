from fastapi import APIRouter
from app.ai.cleaner import hindi_cleaner
from app.ai.extractor import information_extractor
from app.schemas.request import AnalyzeRequest
from app.schemas.response import ApiResponse

router = APIRouter(tags=["Analysis"])


@router.post("/analyze",response_model=ApiResponse)
async def analyze_text(request: AnalyzeRequest,) -> ApiResponse:
    cleaned_text = hindi_cleaner.clean(request.text)
    extracted_data = information_extractor.extract(cleaned_text)
    return ApiResponse(success=True,message="Analysis completed successfully",data=extracted_data)