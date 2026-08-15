from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routes import health, events, blindspots

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    yield
    # Shutdown logic

app = FastAPI(
    title="PerspectiveLens API",
    description="Tamil News Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(events.router)
app.include_router(blindspots.router)

@app.get("/")
async def root():
    return {"message": "Welcome to PerspectiveLens API"}
