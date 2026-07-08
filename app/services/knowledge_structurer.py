import json
import re

from app.core.logger import logger
from app.ai.llm import llm_service


class KnowledgeStructurer:

    SYSTEM_PROMPT = """
You are India's top agricultural intelligence extraction system.

Your task is to deeply understand farmer agricultural knowledge written in:

* Hindi
* Hinglish
* English
* Mixed rural language

Extract:

1. crop
2. category
3. problem
4. solution
5. summary
6. language
7. keywords

IMPORTANT RULES:

* Infer meaning semantically.
* Normalize crop names into standard Hindi names.
* Understand informal farming language.
* Never leave fields empty if reasonably inferred.
* Generate concise summary.
* Generate useful agriculture keywords.
* Return ONLY valid JSON.
* Do NOT return markdown.
* Do NOT explain anything.

IMPORTANT CROP VALIDATION:

A crop name must be a REAL and SPECIFIC crop.

VALID crop examples:

* गेहूं
* धान
* मक्का
* चना
* सरसों
* गन्ना
* आलू
* टमाटर

INVALID generic terms:

* फसल
* खेती
* कृषि
* पौधा
* crop
* farming
* plant

If the exact crop is unclear or generic,
return:

"crop": ""

Category examples:

* सिंचाई
* पोषण
* रोग नियंत्रण
* कीट नियंत्रण
* खरपतवार नियंत्रण
* मिट्टी प्रबंधन
* जैविक खेती
* बीज उपचार

Return this exact JSON format:

{
    "crop": "",
    "category": "",
    "problem": "",
    "solution": "",
    "summary": "",
    "language": "",
    "keywords": []
}
"""

    # =====================================
    # CLEAN RESPONSE
    # =====================================

    @staticmethod
    def clean_response(text: str) -> str:
        return (
            text.replace("```json", "")
            .replace("```", "")
            .strip()
        )

    # =====================================
    # EXTRACT JSON
    # =====================================

    @staticmethod
    def extract_json(text: str) -> dict:
        """
        Safely extract JSON
        from LLM response.
        """

        try:
            text = KnowledgeStructurer.clean_response(text)

            match = re.search(
                r"\{[\s\S]*\}",
                text,
            )

            if not match:
                raise ValueError("No JSON found")

            return json.loads(match.group())

        except Exception as e:

            logger.exception(
                "JSON extraction failed",
                error=str(e),
                response=text,
            )

            return {}

    # =====================================
    # STRUCTURE KNOWLEDGE
    # =====================================

    async def structure(
        self,
        knowledge: str,
    ) -> dict:

        try:

            knowledge = (knowledge or "").strip()

            # =================================
            # BASIC VALIDATION
            # =================================

            if len(knowledge) < 15:
                return self.fallback_response(
                    knowledge
                )

            # =================================
            # USER PROMPT
            # =================================

            prompt = f"""
Analyze the following agricultural knowledge and return structured JSON.

Farmer Knowledge:
{knowledge}

Return ONLY valid JSON.
"""

            # =================================
            # MESSAGES
            # =================================

            messages = [
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]

            # =================================
            # LLM GENERATION
            # =================================

            response = llm_service.generate(
                messages=messages,
                temperature=0,
                max_tokens=700,
            )

            logger.info(
                "Raw LLM response",
                response=response,
            )

            print(
                "\n================ RAW LLM RESPONSE ================\n"
            )
            print(response)
            print(
                "\n==================================================\n"
            )

            # =================================
            # EXTRACT STRUCTURED DATA
            # =================================

            structured = self.extract_json(
                response
            )

            if not structured:

                logger.warning(
                    "Structured extraction failed"
                )

                return self.fallback_response(
                    knowledge
                )

            # =================================
            # CLEAN KEYWORDS
            # =================================

            keywords = structured.get(
                "keywords",
                [],
            )

            if not isinstance(
                keywords,
                list,
            ):
                keywords = []

            keywords = list(
                dict.fromkeys(
                    [
                        str(k).strip()
                        for k in keywords
                        if str(k).strip()
                    ]
                )
            )

            # =================================
            # FINAL RESPONSE
            # =================================

            final_data = {
                "crop": str(
                    structured.get(
                        "crop",
                        "",
                    )
                ).strip(),

                "category": str(
                    structured.get(
                        "category",
                        "",
                    )
                ).strip(),

                "problem": str(
                    structured.get(
                        "problem",
                        "",
                    )
                ).strip(),

                "solution": str(
                    structured.get(
                        "solution",
                        "",
                    )
                ).strip(),

                "summary": str(
                    structured.get(
                        "summary",
                        knowledge[:300],
                    )
                ).strip(),

                "language": str(
                    structured.get(
                        "language",
                        "unknown",
                    )
                ).strip(),

                "keywords": keywords,

                "confidence_score": 0.95,

                "trust_score": 0.95,
            }

            logger.info(
                "Knowledge structuring completed",
                crop=final_data.get(
                    "crop"
                ),
                category=final_data.get(
                    "category"
                ),
            )

            return final_data

        except Exception as e:

            logger.exception(
                "Knowledge structuring failed",
                error=str(e),
            )

            return self.fallback_response(
                knowledge
            )

    # =====================================
    # FALLBACK RESPONSE
    # =====================================

    @staticmethod
    def fallback_response(
        knowledge: str,
    ) -> dict:

        return {
            "crop": "",
            "category": "",
            "problem": "",
            "solution": "",
            "summary": knowledge[:300],
            "language": "unknown",
            "keywords": [],
            "confidence_score": 0.20,
            "trust_score": 0.20,
        }


knowledge_structurer = KnowledgeStructurer()