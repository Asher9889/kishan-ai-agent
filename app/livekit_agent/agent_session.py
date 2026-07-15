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

        # ── Sync agent state to participant attributes (client reads these) ──
        async def _update_attr(key: str, value: str) -> None:
            try:
                await room.local_participant.set_attributes({key: value})
            except Exception:
                pass


        @self._session.on("agent_turn_started")
        def _on_agent_turn_started(ev):
            asyncio.create_task(_update_attr("lk.agent_turn", "started"))
            print("[agent] turn started")
        # Flag so the welcome chime only plays once per session
        _welcome_sent = False

        @self._session.on("agent_state_changed")
        def _on_agent_state(ev):
            nonlocal _welcome_sent
            asyncio.create_task(_update_attr("lk.agent_state", ev.new_state))
            if ev.new_state == "listening" and not _welcome_sent:
                _welcome_sent = True
                # ── Option A: signal client to play a chime ──
                asyncio.create_task(
                    _update_attr("lk.agent_ready", "true")
                )
                # ── Option B: agent speaks a welcome message ──
                self._session.say("Welcome, how can I help you?")
            print(f"[agent] {ev.new_state}")

        @self._session.on("user_state_changed")
        def _on_user_state(ev):
            asyncio.create_task(_update_attr("lk.user_state", ev.new_state))
            print(f"[user] {ev.new_state}")

        @self._session.on("user_input_transcribed")
        def _on_transcribed(ev):
            if ev.transcript:
                asyncio.create_task(
                    _update_attr("lk.user_transcript", ev.transcript)
                )
                print(f"[stt] {ev.transcript}")

        # ── Start processing ──
        await self._session.start(agent=agent, room=room)

        # ── Keep alive until room closes ──
        await asyncio.Future()

    async def aclose(self) -> None:
        if self._session is not None:
            await self._session.aclose()
