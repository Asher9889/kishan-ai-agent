import httpx
from array import array


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

        print("Transcript:", transcript)

        # Next step
        answer = await self.ask_llm(transcript)
        print("LLM Answer:", answer)
        # await self.speak(answer)

    async def transcribe(self, pcm: array, sample_rate: int) -> str | None:

        print(f"Sending {len(pcm)} PCM samples to Whisper")

        response = await self.client.post("/transcribe-pcm",
            content=pcm.tobytes(),
            headers={
                "Content-Type": "application/octet-stream",
                "X-Sample-Rate": str(sample_rate),
            },
        )

        response.raise_for_status()

        payload = response.json()

        print("Whisper Response:", payload)

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


    async def ask_llm(self, prompt: str) -> str:
        response = await self.client.post("/v3/ask",
            json={
                "message": prompt,
                "role": "user",
                "thread_id": self.conversation_id,
                "conversation_id": self.conversation_id,
            },
        )

        response.raise_for_status()

        payload = response.json()

        print("LLM Response:", payload)

        # Store conversation id for subsequent turns
        self.conversation_id = payload["data"]["conversation_id"]

        return payload["data"]["response"]
        
    async def close(self):

        await self.client.aclose()