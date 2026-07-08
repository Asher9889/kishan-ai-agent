import httpx

from app.core.config import settings
from app.core.logger import logger


class SerperService:

    async def search(
        self,
        query: str,
    ) -> dict:

        try:

            headers = {
                "X-API-KEY": settings.SERPER_API_KEY,
                "Content-Type": "application/json",
            }

            payload = {
                "q": query
            }

            async with httpx.AsyncClient(
                timeout=20
            ) as client:

                response = await client.post(
                    settings.SERPER_URL,
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()

                result = response.json()

                logger.info(
                    "Serper search success",
                    query=query,
                )

                return result

        except Exception as e:

            logger.exception(
                "Serper search failed",
                query=query,
                error=str(e),
            )

            return {
                "success": False,
                "error": str(e),
                "organic": [],
            }


serper_service = SerperService()