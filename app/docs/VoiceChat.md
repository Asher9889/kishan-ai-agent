worker.py
      │
      ▼
VoiceSession
      │
      ├──────────────┐
      ▼              ▼
AudioReader     SpeechPipeline
                      │
                      ▼
                  Transcript
                      │
                      ▼
                     LLM
                      │
                      ▼
                     TTS