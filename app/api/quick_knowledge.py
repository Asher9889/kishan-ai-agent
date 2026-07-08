from fastapi import APIRouter

from app.schemas.response import ApiResponse

from app.schemas.quick_knowledge import (
QuickKnowledgeRequest,
)

from app.services.ingestion_pipeline import (
ingestion_pipeline,
)

from app.services.knowledge_structurer import (
knowledge_structurer,
)

from app.ai.cleaner import HindiCleaner

from app.core.logger import logger

router = APIRouter(
tags=["Quick Knowledge"],
)

cleaner = HindiCleaner()

@router.post(
"/quick-upload",
response_model=ApiResponse,
)
async def quick_upload(
request: QuickKnowledgeRequest,
) -> ApiResponse:


    try:

        logger.info(
            "Quick knowledge upload started"
        )

        # =====================================
        # VALIDATE INPUT
        # =====================================

        if not request.knowledge:

            return ApiResponse(
                success=False,
                message="Knowledge is required",
                data={},
            )

        # =====================================
        # CLEAN KNOWLEDGE
        # =====================================

        cleaned_knowledge = cleaner.clean(
            request.knowledge
        )

        cleaned_knowledge = (
            cleaned_knowledge.strip()
        )

        # =====================================
        # VALIDATE CLEANED TEXT
        # =====================================

        if (
            not cleaned_knowledge
            or len(
                cleaned_knowledge.split()
            ) < 5
        ):

            logger.warning(
                "Knowledge too short",
                knowledge=cleaned_knowledge,
            )

            return ApiResponse(
                success=False,
                message=(
                    "Knowledge too short"
                ),
                data={},
            )

        # =====================================
        # STRUCTURE KNOWLEDGE
        # =====================================

        logger.info(
            "Structuring knowledge"
        )

        structured_data = (
            await knowledge_structurer.structure(
                knowledge=cleaned_knowledge,
            )
        )

        logger.info(
            "Knowledge structured successfully",
            crop=structured_data.get(
                "crop"
            ),
            category=structured_data.get(
                "category"
            ),
        )

        # =====================================
        # SEMANTIC CROP VALIDATION
        # =====================================

        crop = (
            structured_data.get(
                "crop",
                "",
            )
            .strip()
            .lower()
        )

        generic_crop_terms = {
            "फसल",
            "खेती",
            "कृषि",
            "पौधा",
            "crop",
            "farming",
            "plant",
        }

        if (
            not crop
            or crop in generic_crop_terms
        ):

            logger.warning(
                "Invalid crop detected",
                extracted_crop=crop,
                knowledge=cleaned_knowledge,
            )

            return ApiResponse(
                success=False,
                message=(
                    "Specific crop name not found. "
                    "कृपया गेहूं, धान, मक्का जैसी फसल का नाम लिखें।"
                ),
                data={
                    "crop_detected": False,
                    "detected_crop": crop,
                },
            )

        # =====================================
        # FINAL RECORD
        # =====================================

        final_record = {

            "farmer_name": (
                request.userinfo.name.strip()
                if (
                    request.userinfo
                    and request.userinfo.name
                )
                else None
            ),

            "location": (
                request.userinfo.location.strip()
                if (
                    request.userinfo
                    and request.userinfo.location
                )
                else None
            ),

            "district": (
                request.userinfo.district.strip()
                if (
                    request.userinfo
                    and request.userinfo.district
                )
                else None
            ),

            "state": (
                request.userinfo.state.strip()
                if (
                    request.userinfo
                    and request.userinfo.state
                )
                else None
            ),

            "knowledge": cleaned_knowledge,

            "crop": structured_data.get(
                "crop",
                "",
            ),

            "category": structured_data.get(
                "category",
                "",
            ),

            "problem": structured_data.get(
                "problem",
                "",
            ),

            "solution": structured_data.get(
                "solution",
                "",
            ),

            "summary": structured_data.get(
                "summary",
                cleaned_knowledge[:300],
            ),

            "language": structured_data.get(
                "language",
                "unknown",
            ),

            "keywords": structured_data.get(
                "keywords",
                [],
            ),

            "confidence_score": structured_data.get(
                "confidence_score",
                0.80,
            ),

            "trust_score": structured_data.get(
                "trust_score",
                0.80,
            ),
        }

        # =====================================
        # INGEST RECORD
        # =====================================

        logger.info(
            "Ingesting structured knowledge"
        )

        ingestion_pipeline.ingest(
            record=final_record,
        )

        logger.info(
            "Quick knowledge upload completed",
            crop=final_record.get(
                "crop"
            ),
            category=final_record.get(
                "category"
            ),
        )

        # =====================================
        # RESPONSE
        # =====================================

        return ApiResponse(
            success=True,
            message=(
                "Knowledge uploaded successfully"
            ),
            data=final_record,
        )

    except Exception as e:

        logger.exception(
            "Quick upload failed",
            error=str(e),
        )

        return ApiResponse(
            success=False,
            message="Knowledge upload failed",
            data={
                "error": str(e),
            },
        )
