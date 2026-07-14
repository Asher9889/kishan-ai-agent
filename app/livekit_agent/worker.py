from app.core.config import settings
from app.livekit_agent.agent_session import LiveKitAgentSession

from livekit.agents import ( JobContext, WorkerOptions, WorkerType, AutoSubscribe, cli )


async def entrypoint(ctx: JobContext):

    session = LiveKitAgentSession(ctx)

    await session.start()


def start_worker():

    cli.run_app(
        WorkerOptions(
            agent_name=settings.LIVEKIT_AGENT_NAME,
            entrypoint_fnc=entrypoint,
            worker_type=WorkerType.ROOM,
            ws_url=settings.LIVEKIT_URL,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            num_idle_processes=1,
            host=settings.HOST,
            port=settings.LiveKit_AGENT_PORT,
        )
    )


if __name__ == "__main__":
    start_worker()