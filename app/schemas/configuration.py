"""Pydantic schemas for configuration endpoints."""

from typing import Literal
from pydantic import BaseModel, HttpUrl


class ConfigurationOption(BaseModel):
    """A single configuration option exposed to the user."""

    key: str
    display_name: str
    type: Literal["radio", "enum", "quantity"]
    values: list[str]
    default: str | None = None
    help_text: str | None = None


class ConfigurationResponse(BaseModel):
    """Response payload for configuration lookups."""

    document_id: str
    workspace_or_version_id: str
    element_id: str
    options: list[ConfigurationOption]


class ConfigurationRequest(BaseModel):
    """Request payload for configuration lookups."""

    onshape_url: HttpUrl
