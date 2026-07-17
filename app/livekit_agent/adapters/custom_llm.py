from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from livekit.agents import llm, utils
from livekit.agents._exceptions import (
    APIConnectionError,
    APITimeoutError,
    create_api_error_from_http,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, NOT_GIVEN, NotGivenOr, APIConnectOptions

logger = logging.getLogger(__name__)


class CustomLLM(llm.LLM):
    def __init__(
        self,
        *,
        endpoint_url: str = "http://localhost:8000/v4/ask",
        http_timeout: float = 60.0,
        thread_id: str | None = None,
    ) -> None:
        super().__init__()
        self._endpoint_url = endpoint_url
        self._http_timeout = http_timeout
        self._thread_id = thread_id
        self._client = httpx.AsyncClient(timeout=http_timeout)

    @property
    def model(self) -> str:
        return "krishi-llm"

    @property
    def provider(self) -> str:
        return "krishi-local"

    @property
    def thread_id(self) -> str | None:
        return self._thread_id

    @thread_id.setter
    def thread_id(self, value: str | None) -> None:
        self._thread_id = value

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool] | None = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
        parallel_tool_calls: NotGivenOr[bool] = NOT_GIVEN,
        tool_choice: NotGivenOr[llm.ToolChoice] = NOT_GIVEN,
        extra_kwargs: NotGivenOr[dict[str, Any]] = NOT_GIVEN,
    ) -> llm.LLMStream:
        return CustomLLMStream(
            self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


class CustomLLMStream(llm.LLMStream):
    def __init__(
        self,
        llm: CustomLLM,
        *,
        chat_ctx: llm.ChatContext,
        tools: list[llm.Tool],
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(
            llm=llm,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=conn_options,
        )
        self._llm: CustomLLM = llm

    async def _run(self) -> None:
        messages = self._chat_ctx.messages()
        if not messages:
            return

        last_user = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_user = msg
                break

        if last_user is None:
            return

        text = (last_user.text_content or "").strip()
        if not text:
            return

        thread_id = self._llm.thread_id or "default"

        try:
            async with self._llm._client.stream(
                "POST",
                self._llm._endpoint_url,
                json={"thread_id": thread_id, "text": text},
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise create_api_error_from_http(
                        message=f"/v3/ask returned {response.status_code}",
                        status=response.status_code,
                        body=body.decode() if body else None,
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue

                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break

                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("event")
                    if event_type == "metadata":
                        data = event.get("data", {})
                        if tid := data.get("thread_id"):
                            self._llm._thread_id = tid
                        continue

                    if event_type in ("start", "processing", "ai_start"):
                        continue

                    if event_type == "chunk":
                        token = event.get("data", {}).get("content", "")
                        if token:
                            self._event_ch.send_nowait(
                                llm.ChatChunk(
                                    id=utils.shortuuid("llm_"),
                                    delta=llm.ChoiceDelta(content=token),
                                )
                            )
                        continue

                    if event_type == "complete":
                        data = event.get("data", {})
                        if tid := data.get("thread_id"):
                            self._llm._thread_id = tid
                        continue

        except httpx.TimeoutException as e:
            raise APITimeoutError(
                f"/v3/ask request timed out: {e}"
            ) from e
        except httpx.HTTPStatusError as e:
            raise create_api_error_from_http(
                message=str(e),
                status=e.response.status_code,
                body=e.response.text,
            )
        except httpx.RequestError as e:
            raise APIConnectionError(
                f"/v3/ask request failed: {e}"
            ) from e
