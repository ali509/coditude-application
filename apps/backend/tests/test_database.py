from unittest.mock import Mock

from app.database import Database


def test_connection_string_uses_runtime_secret(
    monkeypatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_USERNAME", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("DB_HOST", "database.internal")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "coditude")
    monkeypatch.setenv("DB_SECRET_ARN", "database-secret")

    secrets_manager = Mock()
    secrets_manager.get_secret_value.return_value = {
        "SecretString": (
            '{"username": "dbadmin", "password": "example-password"}'
        )
    }
    monkeypatch.setattr(
        "app.database.boto3.client",
        lambda *args, **kwargs: secrets_manager,
    )

    assert Database._connection_string() == (
        "postgresql://dbadmin:example-password"
        "@database.internal:5432/coditude"
    )
    secrets_manager.get_secret_value.assert_called_once_with(
        SecretId="database-secret"
    )


def test_connection_string_uses_local_credentials(
    monkeypatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_SECRET_ARN", raising=False)
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "coditude")
    monkeypatch.setenv("DB_USERNAME", "local-user")
    monkeypatch.setenv("DB_PASSWORD", "local-password")

    assert Database._connection_string() == (
        "postgresql://local-user:local-password"
        "@localhost:5432/coditude"
    )
