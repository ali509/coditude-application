from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class MessageResponse(BaseModel):
    message: str
    environment: str


app = FastAPI(
    title="Coditude Assessment Backend",
    description="Python backend for the Coditude DevOps assessment",
    version="1.0.0",
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


@app.get("/api/v1/message", response_model=MessageResponse)
def get_message() -> MessageResponse:
    return MessageResponse(
        message="Backend is running successfully",
        environment="local",
    )
