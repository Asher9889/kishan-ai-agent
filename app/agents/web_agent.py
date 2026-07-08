from app.services.serper_service import (
    serper_service,
)


class WebAgent:

    async def run(
        self,
        query: str,
    ):

        result = await serper_service.search(
            query=query,
        )

        organic_results = result.get(
            "organic",
            [],
        )

        cleaned_results = []

        for item in organic_results[:5]:

            cleaned_results.append({

                "title": item.get(
                    "title",
                    "",
                ),

                "link": item.get(
                    "link",
                    "",
                ),

                "snippet": item.get(
                    "snippet",
                    "",
                ),
            })

        return {
            "type": "WEB",
            "query": query,
            "results": cleaned_results,
        }


web_agent = WebAgent()