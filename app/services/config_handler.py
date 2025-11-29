"""High-level handler for configuration lookups."""

from app.core.config import get_settings
from app.schemas.configuration import ConfigurationRequest, ConfigurationResponse
from app.services.onshape_client import OnshapeClient


def fetch_configuration(request: ConfigurationRequest) -> ConfigurationResponse:
    """Validate request and delegate to the Onshape client."""

    settings = get_settings()
    client = OnshapeClient(settings)
    return client.fetch_configurations(request.onshape_url)
