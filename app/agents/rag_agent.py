from app.services.rag_pipeline import (
    process_rag_query,
)


class RagAgent:

    async def run(
        self,
        query: str,
        thread_id: str = None,
    ):

        return await process_rag_query(
            query=query,
            thread_id=thread_id,
        )


rag_agent = RagAgent()