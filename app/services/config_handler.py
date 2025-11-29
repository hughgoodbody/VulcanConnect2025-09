"""High-level handler for configuration lookups."""

from app.core.config import get_settings
from app.schemas.configuration import ConfigurationRequest, ConfigurationResponse
from app.services.onshape import Onshape


def fetch_configuration(request: ConfigurationRequest) -> ConfigurationResponse:
    """Validate request and delegate to the Onshape client."""

    settings = get_settings()
    client = Onshape(settings)
    return client.get_configurations(request.onshape_url)
