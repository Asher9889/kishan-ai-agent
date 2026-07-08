# from fastapi import APIRouter, File, UploadFile
# from fastapi.responses import JSONResponse

# from app.core.logger import logger
# from app.services.image_pipeline import image_pipeline

# router = APIRouter(tags=["Ask Image"])


# def build_question(structured_data: dict) -> str:
#     crop_name = structured_data.get("crop_name") or "Unknown Crop"

#     scientific_name = (
#         structured_data.get("scientific_name") or "Unknown"
#     )

#     confidence = structured_data.get("crop_confidence") or 0

#     plant_part = structured_data.get("plant_part") or "Unknown"

#     symptoms = structured_data.get("visible_symptoms") or []

#     damage = structured_data.get("visible_damage") or []

#     severity = structured_data.get("severity") or "Unknown"

#     symptom_text = (
#         ", ".join(symptoms)
#         if symptoms
#         else "No visible symptoms extracted from image"
#     )

#     damage_text = (
#         ", ".join(damage)
#         if damage
#         else "No visible damage extracted from image"
#     )

#     try:
#         confidence_percent = round(float(confidence) * 100, 2)
#     except (ValueError, TypeError):
#         confidence_percent = 0.0

#     question = f"""
# Image Analysis Context

# Crop Name:
# {crop_name}

# Scientific Name:
# {scientific_name}

# Crop Identification Confidence:
# {confidence_percent}%

# Affected Plant Part:
# {plant_part}

# Visible Symptoms:
# {symptom_text}

# Visible Damage:
# {damage_text}

# Severity:
# {severity}

# Task:

# Based on the above crop image observations:

# 1. Identify the most likely disease, pest, nutrient deficiency, physiological disorder, or stress condition.
# 2. Explain possible causes.
# 3. Provide treatment recommendations.
# 4. Provide preventive measures.
# 5. Provide farmer advisory suitable for Indian agriculture.
# 6. If image evidence is insufficient, provide the most likely possibilities with uncertainty.
# """

#     return question.strip()


# @router.post("/ask-image")
# async def ask_image(file: UploadFile = File(...)):
#     try:
#         image_bytes = await file.read()

#         structured_data = await image_pipeline.process(
#             image_bytes
#         )

#         question_text = build_question(
#             structured_data
#         )

#         logger.info(
#             "Image converted to question",
#             question=question_text,
#         )

#         return JSONResponse(
#             content={
#                 "success": True,
#                 "image_analysis": structured_data,
#                 "question_text": question_text,
#             }
#         )

#     except Exception as exc:
#         logger.exception(
#             "Image processing failed",
#             error=str(exc),
#         )

#         return JSONResponse(
#             status_code=500,
#             content={
#                 "success": False,
#                 "error": str(exc),
#             },
#         )


from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.core.logger import logger
from app.services.image_pipeline import image_pipeline

router = APIRouter(tags=["Ask Image"])


def build_question(structured_data: dict) -> str:
    crop_name = (
        structured_data.get("crop_name")
        or "Unknown Crop"
    )

    scientific_name = (
        structured_data.get("scientific_name")
        or "Unknown"
    )

    confidence = (
        structured_data.get("crop_confidence")
        or 0
    )

    plant_part = (
        structured_data.get("plant_part")
        or "Unknown"
    )

    symptoms = (
        structured_data.get("visible_symptoms")
        or []
    )

    damage = (
        structured_data.get("visible_damage")
        or []
    )

    severity = (
        structured_data.get("severity")
        or "Unknown"
    )

    symptom_text = (
        ", ".join(symptoms)
        if symptoms
        else "None"
    )

    damage_text = (
        ", ".join(damage)
        if damage
        else "None"
    )

    try:
        confidence_percent = round(
            float(confidence) * 100,
            2,
        )
    except (ValueError, TypeError):
        confidence_percent = 0.0

    question = (
        f"Crop: {crop_name} ({scientific_name}); "
        f"Confidence: {confidence_percent}%; "
        f"Affected Part: {plant_part}; "
        f"Visible Symptoms: {symptom_text}; "
        f"Visible Damage: {damage_text}; "
        f"Severity: {severity}. "
        f"Based on these crop image observations, identify the most likely disease, pest, nutrient deficiency, physiological disorder, or stress condition. "
        f"Explain possible causes. "
        f"Provide treatment recommendations. "
        f"Provide preventive measures. "
        f"Provide farmer advisory suitable for Indian agriculture. "
        f"If image evidence is insufficient, provide the most likely possibilities with uncertainty."
    )

    return question


@router.post("/ask-image")
async def ask_image(
    file: UploadFile = File(...)
):
    try:
        image_bytes = await file.read()

        structured_data = (
            await image_pipeline.process(
                image_bytes
            )
        )

        question_text = build_question(
            structured_data
        )

        logger.info(
            "Image converted to question",
            question=question_text,
        )

        return JSONResponse(
            content={
                "success": True,
                "image_analysis": structured_data,
                "question_text": question_text,
            }
        )

    except Exception as exc:
        logger.exception(
            "Image processing failed",
            error=str(exc),
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )