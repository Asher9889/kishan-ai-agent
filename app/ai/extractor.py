import json
import re

from typing import Any

from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)


class InformationExtractor:

    # =====================================
    # CLEAN JSON
    # =====================================

    def _clean_json_response(
        self,
        response: str,
    ) -> str:

        response = response.strip()

        response = re.sub(
            r"^```(?:json)?\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"\s*```$",
            "",
            response,
        )

        return response.strip()

    # =====================================
    # EXTRACT
    # =====================================

    def extract(
        self,
        cleaned_text: str,
    ) -> dict[str, Any]:

        messages = [

            {
                "role": "system",
                "content": """
You extract lightweight agricultural metadata.

Your job is NOT diagnosis.

Return ONLY valid JSON.

Keep extraction minimal.

Do not hallucinate.

If information is missing,
return null.

Language must remain Hindi.
""",
            },

            {
                "role": "user",
                "content": f"""
Extract agricultural metadata from this farmer query.

Return ONLY JSON.

Fields:

- crop
- symptom
- category
- farmer_name
- location
- district
- state
- intent
- urgency
- is_ambiguous

Rules:

1. Keep extraction lightweight.

2. Do not infer diseases.

3. Do not infer treatments.

4. Do not over-analyze.

5. If query is vague,
   set is_ambiguous=true.

6. category must be one of:

[
    "कीट",
    "रोग",
    "पोषण",
    "सिंचाई",
    "मौसम",
    "अन्य"
]

JSON format:

{{
    "crop": null,
    "symptom": null,
    "category": null,
    "farmer_name": null,
    "location": null,
    "district": null,
    "state": null,
    "intent": "problem_solving",
    "urgency": "low",
    "is_ambiguous": true

}}

Farmer Query:

{cleaned_text}
""",
            },
        ]

        try:

            response = (
                llm_service.generate(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=250,
                )
            )

            cleaned_response = (
                self._clean_json_response(
                    response
                )
            )

            result = json.loads(
                cleaned_response
            )

            # =================================
            # SAFETY DEFAULTS
            # =================================

            result.setdefault(
                "crop",
                None,
            )

            result.setdefault(
                "symptom",
                None,
            )

            result.setdefault(
                "category",
                "अन्य",
            )

            result.setdefault(
                "location",
                None,
            )
            result.setdefault(
                "farmer_name",
                None,
            )

            result.setdefault(
                "district",
                None,
            )

            result.setdefault(
                "state",
                None,
            )

            result.setdefault(
                "intent",
                "problem_solving",
            )

            result.setdefault(
                "urgency",
                "low",
            )

            result.setdefault(
                "is_ambiguous",
                True,
            )

            # =================================
            # VALIDATION
            # =================================

            valid_categories = [

                "कीट",
                "रोग",
                "पोषण",
                "सिंचाई",
                "मौसम",
                "अन्य",
            ]

            if (
                result.get(
                    "category"
                )
                not in valid_categories
            ):

                result["category"] = (
                    "अन्य"
                )

            logger.info(
                "Light extraction completed.",
                crop=result.get(
                    "crop"
                ),
                category=result.get(
                    "category"
                ),
                ambiguous=result.get(
                    "is_ambiguous"
                ),
            )

            return result

        except Exception as exc:

            logger.exception(
                "Extractor failed.",
                error=str(exc),
            )

            return {
                "crop": None,
                "symptom": None,
                "category": "अन्य",
                "farmer_name": None,
                "location": None,
                "district": None,
                "state": None,
                "intent": "problem_solving",
                "urgency": "low",
                "is_ambiguous": True,
            }


information_extractor = (
    InformationExtractor()
)
