from __future__ import annotations

import asyncio

from livekit import rtc
from livekit.agents import Agent, AgentSession,inference, AutoSubscribe, JobContext, TurnHandlingOptions


class LiveKitAgentSession:
    """New session powered by livekit.agents.AgentSession + Agent.

    All three adapters wired:
      - STT:  WhisperSTT   → POST /transcribe-pcm
      - LLM:  CustomLLM    → POST /v3/ask  (SSE)
      - TTS:  ExternalTTS  → POST /v1/tts/stream
    """

    def __init__(self, ctx: JobContext) -> None:
        self.ctx = ctx
        self._session: AgentSession | None = None

    async def start(self) -> None:
        await self.ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        room = self.ctx.room

        # ── STT (Phase 1) ──
        from app.livekit_agent.adapters.whisper_stt import WhisperSTT

        stt = WhisperSTT()

        # ── LLM (Phase 2) ──
        from app.livekit_agent.adapters.custom_llm import CustomLLM

        llm = CustomLLM()
        llm.thread_id = room.name

        # ── TTS (Phase 3) ──
        from app.livekit_agent.adapters.external_tts import ExternalTTS

        tts = ExternalTTS()

        # ── Agent definition ──
        # instructions only used if a native LLM is plugged in;
        # our CustomLLM delegates to /v3/ask which manages its own system prompt.
        agent = Agent(
            instructions="",
        )

        # ── AgentSession (orchestrator) ──
        self._session = AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            turn_handling={
                "turn_detection": inference.TurnDetector(version="v1-mini"),
                # "turn_detection": "vad",
                "endpointing": {
                    "mode": "dynamic",
                    "min_delay": 1.0,
                    "max_delay": 3.0,
                },
                "interruption": {
                    "enabled": True,
                    "mode": "adaptive",
                },
                "preemptive_generation": {
                    "enabled": False,
                },
            }
        )

        # ── Event listeners ──
        @self._session.on("agent_state_changed")
        def _on_agent_state(ev):
            print(f"[agent] {ev.new_state}")

        @self._session.on("user_state_changed")
        def _on_user_state(ev):
            print(f"[user] {ev.new_state}")

        @self._session.on("user_input_transcribed")
        def _on_transcribed(ev):
            if ev.transcript:
                print(f"[stt] {ev.transcript}")

        # ── Start processing ──
        await self._session.start(agent=agent, room=room)

        # ── Keep alive until room closes ──
        await asyncio.Future()

    async def aclose(self) -> None:
        if self._session is not None:
            await self._session.aclose()
