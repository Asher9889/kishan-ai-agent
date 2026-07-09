import httpx
from array import array
from typing import Callable, Awaitable, Optional
import json
from typing import AsyncGenerator

class ConversationPipeline:

    def __init__(self, chat_id: str) -> None:

        self.client = httpx.AsyncClient(
            base_url="http://localhost:8000",
            timeout=30.0,
        )

        self.conversation_id: str | None = chat_id

    async def process_pcm(self, pcm: array, sample_rate: int) -> None:

        transcript = await self.transcribe(
            pcm=pcm,
            sample_rate=sample_rate,
        )
        
        if not transcript:
            return

        # Next step
        async for token in self.ask_llm(transcript, self.conversation_id):

            print(token, end="", flush=True)

            # 1. Send token to UI
            # await self.ui.send(token)

            # 2. Feed token to TTS
            # await self.tts.feed(token)

        # Tell TTS no more text is coming.
        # await self.tts.finish()

    async def transcribe(self, pcm: array, sample_rate: int) -> str | None:

        print(f"Sending {len(pcm)} PCM samples to Whisper")

        response = await self.client.post("/transcribe-pcm",
            content=pcm.tobytes(),
            headers={
                "Content-Type": "application/json",
                "X-Sample-Rate": str(sample_rate),
            },
        )
        
        response.raise_for_status()

        payload = response.json()

        transcript = (
            payload
            .get("data", {})
            .get("transcript", "")
            .strip()
        )

        if not transcript:
            print("Empty transcript received.")
            return None

        return transcript
    
    

    async def ask_llm(self, prompt: str, conversation_id: str) -> AsyncGenerator[str, None]:

        print(f"Sending prompt to LLM: {prompt} " f"(conversation_id: {conversation_id})")

        full_answer = ""

        async with self.client.stream("POST", "/v3/ask",
            json={
                "thread_id": conversation_id,
                "text": prompt,
            },
            headers={
                "Content-Type": "application/json",
            },
        ) as response:
            
            print("LLM Response Status:", response)
            response.raise_for_status()

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
                    print("Metadata event happens")

                    metadata = event.get("data", {})

                    self.conversation_id = metadata.get("thread_id",conversation_id)

                    continue

                if event_type in ("start", "processing", "ai_start"):
                    continue

                if event_type == "chunk":
                    print("Chunk event happens")
                    token = event["data"]["content"]
                    print("token i am getting is", token)
                    full_answer += token

                    # Stream to caller immediately
                    yield token

                    continue
                
                if event_type == "complete":

                    complete = event.get("data", {})

                    self.conversation_id = complete.get("thread_id", self.conversation_id)

                    # Optional safety check
                    if complete.get("answer"):
                        full_answer = complete["answer"]

                    print("\nLLM Complete")
                    print(full_answer)

                    break

    
    
    # async def ask_llm(self, prompt: str, conversation_id: str) -> str:
    #     print(f"Sending prompt to LLM: {prompt} (conversation_id: {conversation_id})")
    #     response = await self.client.post("/v3/ask",
    #         json={
    #             "text": prompt,
    #             "thread_id": conversation_id,
    #             # "conversation_id": conversation_id,
    #         },
    #     )

    #     response.raise_for_status()

    #     payload = response.json()

    #     print("LLM Response:", payload)

    #     # Store conversation id for subsequent turns
    #     self.conversation_id = payload["data"]["conversation_id"]

    #     return payload["data"]["response"]
        
    async def close(self):

        await self.client.aclose()