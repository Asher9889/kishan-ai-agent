# from sqlalchemy import create_engine, text
# from sqlalchemy.engine import Engine

# from app.core.config import settings
# from app.core.logger import logger


# class MSSQLService:
#     def __init__(self) -> None:
#         self.engine: Engine | None = None

#         if settings.MSSQL_URL:
#             logger.info("Initializing MSSQL connection")
#             self.engine = create_engine(
#                 settings.MSSQL_URL,
#                 pool_pre_ping=True,
#                 future=True,
#             )
#             logger.info("MSSQL connection initialized")

#     def is_enabled(self) -> bool:
#         return self.engine is not None

#     def execute(
#         self,
#         sql: str,
#         params: dict | None = None,
#     ) -> None:
#         if self.engine is None:
#             raise RuntimeError(
#                 "MSSQL is not configured."
#             )

#         with self.engine.begin() as conn:
#             conn.execute(text(sql), params or {})


# mssql_service = MSSQLService()

# ============================
from sqlalchemy import (
    create_engine,
    text,
)

from sqlalchemy.engine import (
    Engine,
)

from app.core.config import (
    settings,
)

from app.core.logger import (
    logger,
)


class MSSQLService:

    def __init__(
        self,
    ) -> None:

        self.engine: (
            Engine | None
        ) = None

        if settings.MSSQL_URL:

            logger.info(
                "Initializing MSSQL connection"
            )

            self.engine = create_engine(
                settings.MSSQL_URL,
                pool_pre_ping=True,
                future=True,
            )

            logger.info(
                "MSSQL connection initialized"
            )

    def is_enabled(
        self,
    ) -> bool:

        return (
            self.engine
            is not None
        )

    def execute(
        self,
        sql: str,
        params: (
            dict | None
        ) = None,
    ) -> None:

        if self.engine is None:

            raise RuntimeError(
                "MSSQL is not configured."
            )

        with self.engine.begin() as conn:

            conn.execute(
                text(sql),
                params or {},
            )

    def fetch_all(
        self,
        sql,
        params: (
            dict | None
        ) = None,
    ) -> list[dict]:

        if self.engine is None:

            raise RuntimeError(
                "MSSQL is not configured."
            )

        with self.engine.connect() as conn:

            result = conn.execute(
                sql,
                params or {},
            )

            rows = (
                result.mappings().all()
            )

            return [
                dict(row)
                for row in rows
            ]


mssql_service = (
    MSSQLService()
)