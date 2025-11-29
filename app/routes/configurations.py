"""API routes for configuration retrieval."""

from fastapi import APIRouter

from app.schemas.configuration import ConfigurationRequest, ConfigurationResponse
from app.services.config_handler import fetch_configuration

router = APIRouter(prefix="/configurations", tags=["configurations"])


@router.post("/resolve", response_model=ConfigurationResponse)
def resolve_configuration(request: ConfigurationRequest) -> ConfigurationResponse:
    """Accept an Onshape URL and return configuration metadata."""

    return fetch_configuration(request)
