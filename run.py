import uvicorn
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )