from __future__ import annotations

import asyncio
# import logging

from livekit import rtc
from livekit.agents import  room_io,Agent, AgentSession, inference, AutoSubscribe, JobContext, TurnHandlingOptions
from livekit.agents.voice.room_io import AudioInputOptions, RoomOptions
from livekit.plugins import dtln
# logger = logging.getLogger(__name__)


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
        # Pass raw WhisperSTT — AgentSession's Agent.default.stt_node()
        # auto-wraps non-streaming STT with StreamAdapter + VAD.
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
            # aec_warmup_duration=5.0,
            turn_handling=TurnHandlingOptions(
                turn_detection=inference.TurnDetector(
                    version="v1-mini",
                    # unlikely_threshold=0.7,
                ),
                endpointing={
                    "mode": "dynamic",
                    "min_delay": 0.7,
                    "max_delay": 2.5,
                },
                interruption={
                    "enabled": True,
                    "mode": "adaptive",
                },
                preemptive_generation={
                    "enabled": False,
                },
            ),
        )

        # ── Sync agent state to participant attributes (client reads these) ──
        async def _update_attr(key: str, value: str) -> None:
            try:
                await room.local_participant.set_attributes({key: value})
            except Exception as e:
                
                print("Failed to set attribute %s: %s", key, e)

        # Flag so the welcome chime only plays once per session
        _welcome_sent = False

        @self._session.on("agent_state_changed")
        def _on_agent_state(ev):
            nonlocal _welcome_sent
            asyncio.create_task(_update_attr("lk.agent_state", ev.new_state))
            if ev.new_state == "speaking":
                asyncio.create_task(_update_attr("lk.agent_turn", "started"))
                print("[agent] turn started")
            if ev.new_state == "listening" and not _welcome_sent:
                _welcome_sent = True
                asyncio.create_task(
                    _update_attr("lk.agent_ready", "true")
                )
            print("[agent] %s", ev.new_state)

        @self._session.on("user_state_changed")
        def _on_user_state(ev):
            asyncio.create_task(_update_attr("lk.user_state", ev.new_state))
            print("[user] %s", ev.new_state)

        @self._session.on("user_input_transcribed")
        def _on_transcribed(ev):
            if ev.transcript:
                asyncio.create_task(
                    _update_attr("lk.user_transcript", ev.transcript)
                )
                print("[stt] %s", ev.transcript)

        # ── Start processing ──
        await self._session.start(
            agent=agent,
            room=room,
            # room_options=RoomOptions(
            #     audio_input=AudioInputOptions(
            #         sample_rate=24000,
            #         num_channels=1,
            #         # Install a noise cancellation plugin (e.g. livekit-plugins-ai-coustics)
            #         # and uncomment the line below to enable AEC/noise suppression:
            #         # noise_cancellation=...,
            #     ),
            # ),
            
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    # noise_cancellation=dtln.noise_suppression(),
                    sample_rate=48000,
                ),
            ),
        )

        # ── Keep alive until room closes ──
        await asyncio.Future()

    async def aclose(self) -> None:
        if self._session is not None:
            await self._session.aclose()
