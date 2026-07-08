from time import perf_counter

from groq import Groq

from app.core.config import (
    settings,
)

from app.core.logger import (
    logger,
)


class LLMService:

    def __init__(self):

        self.client = Groq(
            api_key=(
                settings.GROQ_API_KEY
            )
        )

        self.model = (
            settings.GROQ_MODEL
        )

        logger.info(
            "Groq LLM client initialized.",
            model=self.model,
        )

    def generate(
        self,
        *,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 700,
    ) -> str:

        start_time = (
            perf_counter()
        )

        try:

            completion = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )

            content = (
                completion
                .choices[0]
                .message
                .content
            )

            if not content:

                raise ValueError(
                    "LLM returned empty response."
                )

            latency = round(
                perf_counter() - start_time,
                3,
            )

            logger.info(
                "LLM generation completed.",
                model=self.model,
                latency_seconds=latency,
            )

            return (
                content.strip()
            )

        except Exception as exc:

            logger.exception(
                "LLM generation failed.",
                model=self.model,
                error=str(exc),
            )

            raise

    def stream_generate(
        self,
        *,
        messages: list,
        temperature: float = 0.3,
        max_tokens: int = 700,
    ):

        start_time = (
            perf_counter()
        )

        try:

            stream = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
            )

            for chunk in stream:

                delta = (
                    chunk
                    .choices[0]
                    .delta
                )

                content = getattr(
                    delta,
                    "content",
                    None,
                )

                if content:

                    yield content

            latency = round(
                perf_counter() - start_time,
                3,
            )

            logger.info(
                "LLM streaming completed.",
                model=self.model,
                latency_seconds=latency,
            )

        except Exception as exc:

            logger.exception(
                "LLM stream generation failed.",
                model=self.model,
                error=str(exc),
            )

            raise


llm_service = (
    LLMService()
)
