from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness of this FastAPI process only.

    Deliberately does not touch Postiz, so it can distinguish "my API is down"
    from "Postiz is down".
    """
    return HealthResponse(status="ok")
