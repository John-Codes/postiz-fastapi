import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.health.routes import router as health_router
from app.posts.routes import router as posts_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("postiz-fastapi starting")
    yield
    logger.info("postiz-fastapi shutting down")


app = FastAPI(title="Postiz FastAPI", version="0.1.0", lifespan=lifespan)
app.include_router(health_router)
app.include_router(posts_router)
