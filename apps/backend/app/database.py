import os
from urllib.parse import quote_plus

from psycopg import Error as PsycopgError
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout


DEFAULT_MESSAGE = "Backend is running successfully"


class Database:
    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None

    def connect(self) -> None:
        database_url = self._connection_string()
        if not database_url:
            return

        self._pool = ConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=int(os.getenv("DB_POOL_MAX_SIZE", "5")),
            open=False,
            kwargs={"autocommit": True, "row_factory": dict_row},
        )
        self._pool.open(wait=True, timeout=15)
        self._initialize_schema()

    @staticmethod
    def _connection_string() -> str | None:
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        required_variables = (
            "DB_HOST",
            "DB_NAME",
            "DB_USERNAME",
            "DB_PASSWORD",
        )
        if not all(os.getenv(variable) for variable in required_variables):
            return None

        username = quote_plus(os.environ["DB_USERNAME"])
        password = quote_plus(os.environ["DB_PASSWORD"])
        host = os.environ["DB_HOST"]
        port = os.getenv("DB_PORT", "5432")
        name = os.environ["DB_NAME"]

        return f"postgresql://{username}:{password}@{host}:{port}/{name}"

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def _initialize_schema(self) -> None:
        if self._pool is None:
            return

        with self._pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_messages (
                        id SMALLINT PRIMARY KEY,
                        message TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO app_messages (id, message)
                    VALUES (1, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (DEFAULT_MESSAGE,),
                )

    def is_ready(self) -> bool:
        if self._pool is None:
            return False

        try:
            with self._pool.connection(timeout=2) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return True
        except (PsycopgError, PoolTimeout):
            return False

    def get_message(self) -> str | None:
        if self._pool is None:
            return None

        with self._pool.connection(timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT message FROM app_messages WHERE id = 1"
                )
                row = cursor.fetchone()

        return row["message"] if row else None


database = Database()
