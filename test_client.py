import asyncio

from app.livekit_agent.tts.tts_client import TTSClient


async def main():

    client = TTSClient()

    async for chunk in client.stream(
        "आज मौसम साफ रहेगा।"
    ):

        print(len(chunk))

    await client.close()


asyncio.run(main())