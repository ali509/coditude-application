import json
import os
from urllib.parse import quote_plus

import boto3
from botocore.config import Config
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

        host = os.getenv("DB_HOST")
        name = os.getenv("DB_NAME")
        if not host or not name:
            return None

        credentials = Database._credentials()
        if credentials is None:
            return None

        username = quote_plus(credentials["username"])
        password = quote_plus(credentials["password"])
        port = os.getenv("DB_PORT", "5432")

        return f"postgresql://{username}:{password}@{host}:{port}/{name}"

    @staticmethod
    def _credentials() -> dict[str, str] | None:
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        if username and password:
            return {"username": username, "password": password}

        secret_arn = os.getenv("DB_SECRET_ARN")
        if not secret_arn:
            return None

        client = boto3.client(
            "secretsmanager",
            region_name=os.getenv("AWS_REGION"),
            config=Config(
                connect_timeout=3,
                read_timeout=5,
                retries={"total_max_attempts": 2, "mode": "standard"},
            ),
        )
        response = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response["SecretString"])

        return {
            "username": secret["username"],
            "password": secret["password"],
        }

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
