import asyncio

from app.livekit_agent.speech_pipeline import SpeechPipeline
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext

from app.livekit_agent.audio_reader import AudioReader


class VoiceSession:

    def __init__(self, ctx: JobContext):

        self.ctx = ctx
        self.audio_queue = asyncio.Queue()
        self.audio_readers: dict[str, AudioReader] = {}
        self.reader_tasks: set[asyncio.Task] = set()
        self.speech_pipeline = SpeechPipeline(queue=self.audio_queue)

    async def start(self) -> None:

        print("================================")
        print("NEW LIVEKIT JOB RECEIVED")
        print(f"ROOM: {self.ctx.room.name}")
        print("================================")

        await self.ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        print(f"AI CONNECTED TO ROOM: {self.ctx.room.name}")

        asyncio.create_task(
            self.speech_pipeline.start() # starts listening the audio.
        )

        self.register_room_events()

        # Keep the session alive until LiveKit closes the room.
        await asyncio.Future()

    def register_room_events(self) -> None:

        @self.ctx.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track, # actual media track
            publication: rtc.RemoteTrackPublication, # metadata about the track
            participant: rtc.RemoteParticipant, # Identity: 6a42747506d1be540a5282b8
        ):

            # return if not audio track
            if track.kind != rtc.TrackKind.KIND_AUDIO:
                return

            print(f"Subscribed to audio from {participant.identity}")

            reader = AudioReader(
                participant=participant,
                track=track,
                queue=self.audio_queue,
            )

            #storing the reader in a dictionary to manage multiple participants
            self.audio_readers[participant.identity] = reader 

            task = asyncio.create_task( # run this in background
                reader.start() # is an async function. not awaited here to allow concurrent reading from multiple participants
            )

            self.reader_tasks.add(task) #storing the task in a set to manage multiple tasks

            task.add_done_callback(
                self.reader_tasks.discard
            )

        @self.ctx.room.on("track_unsubscribed")
        def on_track_unsubscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):

            print(
                f"Audio track removed: {participant.identity}"
            )

            reader = self.audio_readers.pop(
                participant.identity,
                None,
            )

            if reader:
                asyncio.create_task(reader.stop())
    
        @self.ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            print(f"Participant disconnected: {participant.identity}")