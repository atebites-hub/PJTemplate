"""FastAPI ASGI application factory and ``app`` instance."""

from fastapi import FastAPI

from server.logging.telemetry import telemetry_lifespan

app = FastAPI(
    title="yourapp",
    lifespan=telemetry_lifespan,
)
