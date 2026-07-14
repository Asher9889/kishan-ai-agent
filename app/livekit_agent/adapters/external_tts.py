from __future__ import annotations

import asyncio
from typing import ClassVar

import httpx
from livekit import rtc
from livekit.agents import tts, utils
from livekit.agents._exceptions import (
    APIConnectionError,
    APITimeoutError,
    create_api_error_from_http,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions


class ExternalTTS(tts.TTS):
    def __init__(
        self,
        *,
        endpoint_url: str = "http://localhost:8001/v1/tts/stream",
        sample_rate: int = 44100,
        num_channels: int = 1,
        http_timeout: float | None = None,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(
                streaming=False,
                aligned_transcript=False,
            ),
            sample_rate=sample_rate,
            num_channels=num_channels,
        )
        self._endpoint_url = endpoint_url
        self._client = httpx.AsyncClient(timeout=http_timeout)

    @property
    def model(self) -> str:
        return "indic-parler-tts"

    @property
    def provider(self) -> str:
        return "krishi-local"

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return ExternalTTSChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class ExternalTTSChunkedStream(tts.ChunkedStream):
    _tts_request_span_name: ClassVar[str] = "tts_external"

    def __init__(
        self,
        *,
        tts: ExternalTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: ExternalTTS = tts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        text = self._input_text.strip()
        if not text:
            return

        output_emitter.initialize(
            request_id=utils.shortuuid("tts_"),
            sample_rate=self._tts.sample_rate,
            num_channels=self._tts.num_channels,
            mime_type="audio/pcm",
        )

        try:
            async with self._tts._client.stream(
                "POST",
                self._tts._endpoint_url,
                json={"text": text},
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise create_api_error_from_http(
                        message=f"/v1/tts/stream returned {response.status_code}",
                        status=response.status_code,
                        body=body.decode() if body else None,
                    )

                async for chunk in response.aiter_bytes():
                    if not chunk:
                        continue
                    output_emitter.push(chunk)

        except httpx.TimeoutException as e:
            raise APITimeoutError(
                f"/v1/tts/stream request timed out: {e}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise create_api_error_from_http(
                message=str(e),
                status=e.response.status_code,
                body=e.response.text,
            )
        except httpx.RequestError as e:
            raise APIConnectionError(
                f"/v1/tts/stream request failed: {e}"
            ) from e

        output_emitter.flush()
