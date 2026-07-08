from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)


class HindiCleaner:

    def clean(
        self,
        raw_text: str,
    ) -> str:

        messages = [

            {
                "role": "system",
                "content": """
You are an expert Hindi agricultural transcript cleaner.

Your job:
lightly normalize noisy Hindi or Hinglish farmer queries.

Rules:

1. Preserve original meaning.

2. Preserve:
   - farmer names
   - village names
   - district names
   - state names
   - crop names
   - agricultural terminology

3. Fix:
   - spacing
   - obvious speech-to-text noise
   - repeated words
   - basic grammar

4. Do NOT rewrite aggressively.

5. Do NOT add new facts.

6. Do NOT over-correct.

7. If input is already understandable,
   keep it mostly unchanged.

8. Return ONLY cleaned Hindi text.
""",
            },

            {
                "role": "user",
                "content": raw_text,
            },
        ]

        try:

            cleaned_text = (
                llm_service.generate(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=200,
                )
            )

            cleaned_text = (
                cleaned_text.strip()
            )

            logger.info(
                "Hindi transcript cleaned.",
                input_length=len(
                    raw_text
                ),
                output_length=len(
                    cleaned_text
                ),
            )

            return cleaned_text

        except Exception as exc:

            logger.exception(
                "Hindi cleaner failed.",
                error=str(exc),
            )

            return raw_text.strip()


hindi_cleaner = (
    HindiCleaner()
)
