import json

from app.ai.llm import llm_service
from app.core.logger import logger


class AgricultureGuardrail:

    SYSTEM_PROMPT = """
You are an Agriculture Domain Classifier.

Determine whether the user's query is related to agriculture.

Agriculture includes:
- Crops
- Farming
- Farmers
- Soil
- Fertilizers
- Irrigation
- Seeds
- Plant diseases
- Plant nutrition
- Pests
- Livestock
- Horticulture
- Farm machinery
- Agricultural schemes
- Harvesting
- Crop protection
- Weather affecting crops

Return ONLY valid JSON.

Example:

{
  "is_agriculture": true,
  "confidence": 0.95
}
"""

    @classmethod
    def validate(cls, question: str) -> tuple[bool, float]:
        try:

            prompt = f"""
Question:
{question}

Return JSON only.
"""

            response = llm_service.generate(
                system_prompt=cls.SYSTEM_PROMPT,
                prompt=prompt,
                temperature=0
            )

            response = response.strip()

            result = json.loads(response)

            is_agri = bool(
                result.get("is_agriculture", False)
            )

            confidence = float(
                result.get("confidence", 0)
            )

            return is_agri, confidence

        except Exception as e:
            logger.exception(
                f"AgricultureGuardrail Error: {e}"
            )

            return False, 0.0