from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    PORT: int = 8080
    LiveKit_AGENT_PORT: int = 9090
    APP_NAME: str
    DEBUG: bool
    LOG_LEVEL: str
    WHISPER_MODEL: str
    TEMP_DIR: str
    MAX_AUDIO_MB: int
    GROQ_API_KEY: str
    GROQ_MODEL: str
    EMBEDDING_MODEL: str
    CHROMA_PATH: str
    CHROMA_COLLECTION: str
    MSSQL_URL: str | None = None
    SERPER_API_KEY: str = ""
    SERPER_URL: str = "https://google.serper.dev/search"

    # livekit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings=Settings()