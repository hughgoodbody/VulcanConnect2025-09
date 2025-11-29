"""FastAPI entrypoint for the Onshape configurator."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.routes.configurations import router as configurations_router

app = FastAPI(title=get_settings().app_name)

# Allow embedding from WordPress and Elementor front-ends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Simple liveness endpoint."""

    return {"status": "ok"}


app.include_router(configurations_router)
