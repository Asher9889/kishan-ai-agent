from typing import List


class QueryDecomposer:

    def decompose(
        self,
        query: str,
    ) -> List[dict]:

        query_lower = query.lower()

        tasks = []

        # =====================================
        # WEB DETECTION
        # =====================================

        web_keywords = [

            "aaj",
            "today",
            "latest",
            "mandi",
            "bhav",
            "rate",
            "price",
            "weather",
            "mausam",
            "news",
            "yojana",
            "scheme",
        ]

        needs_web = any(
            keyword in query_lower
            for keyword in web_keywords
        )

        # =====================================
        # WEB TASK
        # =====================================

        if needs_web:

            tasks.append({

                "type": "WEB",
                "query": query,

            })

        # =====================================
        # RAG TASK
        # =====================================

        tasks.append({

            "type": "RAG",
            "query": query,

        })

        return tasks


query_decomposer = (
    QueryDecomposer()
)