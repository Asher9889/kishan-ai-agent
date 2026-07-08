# import os
# from app.core.config import settings
# from livekit import rtc
# import asyncio
# from livekit.agents import WorkerType

# from livekit.agents import (JobContext, WorkerOptions, cli, AutoSubscribe)

# async def read_audio(track):
#     print("Starting audio stream")
#     stream = rtc.AudioStream(track)
#     try:
#         async for event in stream:
#             frame = event.frame
#             pcm = frame.data
#             # print( "PCM BUFFER:", len(pcm))


#     except Exception as e:

#         print("Audio stream error:", e)
#     finally:

#         if hasattr(stream, "aclose"):

#             await stream.aclose()



# async def entrypoint(ctx: JobContext):

#     print("================================")
#     print("NEW LIVEKIT JOB RECEIVED")
#     print("ROOM:", ctx.room.name)
#     print("================================")

#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)


#     print("AI CONNECTED TO ROOM:", ctx.room.name)

#     @ctx.room.on("track_subscribed")

#     def on_track(track, publication, participant):

#         print("Audio track received from:", participant.identity)

#         if track.kind == rtc.TrackKind.KIND_AUDIO:
#             asyncio.create_task(read_audio(track))


# def start_worker():
#     cli.run_app(
#         WorkerOptions(
#             agent_name="agri-ai-agent",

#             entrypoint_fnc=entrypoint,
#             worker_type=WorkerType.ROOM,
#             ws_url=settings.LIVEKIT_URL,

#             api_key=settings.LIVEKIT_API_KEY,

#             api_secret=settings.LIVEKIT_API_SECRET,
#             num_idle_processes=1,

#             host="0.0.0.0",
#             port=9090,
#         )
#     )


# if __name__ == "__main__":
#     start_worker()


from app.core.config import settings
from app.livekit_agent.session import VoiceSession

from livekit.agents import ( JobContext, WorkerOptions, WorkerType, AutoSubscribe, cli )


async def entrypoint(ctx: JobContext):

    session = VoiceSession(ctx)

    await session.start()


def start_worker():

    cli.run_app(
        WorkerOptions(
            agent_name="agri-ai-agent",
            entrypoint_fnc=entrypoint,
            worker_type=WorkerType.ROOM,
            ws_url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            num_idle_processes=1,
            host="0.0.0.0",
            port=9090,
        )
    )


if __name__ == "__main__":
    start_worker()