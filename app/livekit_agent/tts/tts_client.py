from typing import AsyncGenerator

import httpx


class TTSClient:

    def __init__(self):

        self.client = httpx.AsyncClient(
            base_url="http://localhost:8001",
            timeout=None,  # streaming request
        )

    async def stream(
        self,
        text: str,
    ) -> AsyncGenerator[bytes, None]:

        async with self.client.stream(
            "POST",
            "/v1/tts/stream",
            json={
                "text": text,
            },
        ) as response:

            response.raise_for_status()

            async for chunk in response.aiter_bytes():

                if not chunk:
                    continue

                yield chunk

    async def close(self):

        await self.client.aclose()