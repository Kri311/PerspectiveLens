from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from .routes import health, events, blindspots, sources

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
app.include_router(sources.router)

# Mount the media directory to serve downloaded images
app.mount("/media", StaticFiles(directory="/app/media"), name="media")

@app.get("/")
async def root():
    return {"message": "Welcome to PerspectiveLens API"}
