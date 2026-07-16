import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.database import DEFAULT_MESSAGE, database


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(HealthResponse):
    database: str


class MessageResponse(BaseModel):
    message: str
    environment: str
    source: str


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    database.connect()
    try:
        yield
    finally:
        database.close()


app = FastAPI(
    title="Coditude Assessment Backend",
    description="Python backend for the Coditude DevOps assessment",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "coditude-backend",
        "version": "1.0.0",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="coditude-backend",
    )


@app.get("/ready", response_model=ReadinessResponse)
def ready() -> ReadinessResponse:
    if not database.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Database is not ready",
        )

    return ReadinessResponse(
        status="ready",
        service="coditude-backend",
        database="connected",
    )


@app.get("/api/v1/message", response_model=MessageResponse)
def get_message() -> MessageResponse:
    database_message = database.get_message()

    return MessageResponse(
        message=database_message or DEFAULT_MESSAGE,
        environment=os.getenv("APP_ENV", "local"),
        source="postgresql" if database_message else "application-default",
    )
