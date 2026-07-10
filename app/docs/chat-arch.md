VoiceSession
      │
      ▼
await conversation_pipeline.start()

      │
      ▼
TTSPipeline worker starts

      │
      ▼
process_pcm()

      │
      ▼
enqueue(sentence)

      │
      ▼
worker receives sentence

      │
      ▼
calls TTS service