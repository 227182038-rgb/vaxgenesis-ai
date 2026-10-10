"""VaxGenesis AI - FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from vaxgenesis import __version__
from vaxgenesis.config import settings

# v2 hexagonal router (always available)
from vaxgenesis.hexagon.api.routes import router as v2_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    from vaxgenesis.core.logging import configure_logging, get_logger
    configure_logging()
    logger = get_logger(__name__)
    logger.info("app.starting", version=__version__, env=settings.environment)
    yield
    logger.info("app.stopping")


def create_app() -> FastAPI:
    app = FastAPI(
        title="VaxGenesis AI",
        description="Self-learning vaccine digital twin platform",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # v2 hexagonal routes
    app.include_router(v2_router, prefix="/api")

    @app.get("/")
    async def root():
        return {"name": "VaxGenesis AI", "version": __version__}

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
