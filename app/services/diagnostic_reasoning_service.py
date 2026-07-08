import json

from app.ai.llm import (
    llm_service,
)


class DiagnosticReasoningService:

    def analyze(
        self,
        *,
        query: str,
        analysis: dict,
        memory: list,
    ) -> dict:

        prompt = f"""
You are an expert agricultural
diagnostic reasoning engine.

Your job is to think like:

* crop doctor
* agriculture scientist
* pest expert

Farmer Query:
{query}

Current Extracted Analysis:
{json.dumps(
    analysis,
    ensure_ascii=False,
    indent=2,
)}

Conversation Memory:
{json.dumps(
    memory,
    ensure_ascii=False,
    indent=2,
)}

Your task:

1. Analyze symptoms carefully.

2. Identify MOST likely:

* pests
* diseases
* nutrient deficiencies
* environmental issues

3. Estimate confidence.

4. Explain WHY briefly.

5. Ask BEST next diagnostic questions.

6. If confidence is high,
   then suggest:

* treatment
* prevention

7. If confidence is low,
   continue diagnostic questioning.

IMPORTANT:

* Think step-by-step internally.
* Do NOT hallucinate.
* Avoid generic answers.
* Avoid repetitive questions.
* Be highly contextual.
* Questions should help
  distinguish possibilities.

Return ONLY valid JSON.

JSON FORMAT:

{{
    "possible_causes": [
        {{
            "name": "",
            "confidence": 0.0,
            "why": [],
            "next_questions": []
        }}
    ],

    "overall_confidence": 0.0,

    "should_give_treatment": false,

    "treatment": [],

    "prevention": []
}}
"""

        response = llm_service.generate(
            prompt=prompt,
            temperature=0.4,
            max_tokens=1200,
        )

        try:

            result = json.loads(
                response
            )

            return result

        except Exception:

            return {
                "possible_causes": [],
                "overall_confidence": 0.0,
                "should_give_treatment": False,
                "treatment": [],
                "prevention": [],
            }


diagnostic_reasoning_service = (
    DiagnosticReasoningService()
)