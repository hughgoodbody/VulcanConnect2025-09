"""Client for communicating with the Onshape API."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Mapping
from urllib.parse import urlparse

import requests

from app.core.config import Settings
from app.schemas.configuration import ConfigurationOption, ConfigurationResponse


class OnshapeUrlError(ValueError):
    """Raised when an Onshape URL cannot be parsed."""


class OnshapeClient:
    """A lightweight Onshape API client tailored for configuration retrieval."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def parse_url(self, onshape_url: str) -> tuple[str, str, str]:
        """Extract document, workspace/version, and element IDs from an Onshape URL."""

        parsed = urlparse(onshape_url)
        parts = parsed.path.strip("/").split("/")
        try:
            doc_index = parts.index("documents") + 1
            document_id = parts[doc_index]
            workspace_or_version_id = parts[doc_index + 2]
            element_id = parts[doc_index + 4]
        except (ValueError, IndexError) as exc:  # ValueError from .index
            raise OnshapeUrlError("Could not parse Onshape URL components") from exc
        return document_id, workspace_or_version_id, element_id

    def _headers(self, method: str, path: str) -> Mapping[str, str]:
        """Build signed request headers when API keys are provided."""

        if not (self.settings.onshape_access_key and self.settings.onshape_secret_key):
            return {}

        nonce = str(int(time.time() * 1000))
        message = f"{method}\n{path}\n{nonce}\n{self.settings.onshape_base_url}".encode()
        signature = hmac.new(
            self.settings.onshape_secret_key.encode(), message, hashlib.sha256
        ).hexdigest()
        return {
            "On-Nonce": nonce,
            "On-Token": self.settings.onshape_access_key,
            "On-TokenSignature": signature,
            "Accept": "application/json",
        }

    def fetch_configurations(self, onshape_url: str) -> ConfigurationResponse:
        """Fetch configuration options for an Onshape element.

        Notes:
            This method expects the Onshape URL to follow the standard pattern and
            requires API credentials when accessing private documents. The return
            shape matches what the frontend needs to render radio, enum, and
            quantity controls.
        """

        document_id, workspace_or_version_id, element_id = self.parse_url(onshape_url)

        # Onshape API path for configuration list
        api_path = (
            f"/api/parts/d/{document_id}/w/{workspace_or_version_id}"
            f"/e/{element_id}/configurations"
        )
        url = f"{self.settings.onshape_base_url}{api_path}"

        response = requests.get(
            url,
            headers=self._headers("GET", api_path),
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data: Mapping[str, Any] = response.json()

        # Transform the Onshape payload into UI-friendly options.
        options = [
            ConfigurationOption(
                key=item.get("parameterId", ""),
                display_name=item.get("name", item.get("parameterId", "")),
                type=self._map_parameter_type(item.get("type", "enum")),
                values=[v.get("value", "") for v in item.get("values", [])],
                default=self._extract_default(item),
                help_text=item.get("description"),
            )
            for item in data.get("configurationParameters", [])
        ]

        return ConfigurationResponse(
            document_id=document_id,
            workspace_or_version_id=workspace_or_version_id,
            element_id=element_id,
            options=options,
        )

    @staticmethod
    def _map_parameter_type(onshape_type: str) -> str:
        """Map Onshape parameter types to UI widget types."""

        if onshape_type.lower() in {"enum", "boolean"}:
            return "radio"
        if onshape_type.lower() in {"quantity", "length", "angle"}:
            return "quantity"
        return "enum"

    @staticmethod
    def _extract_default(parameter: Mapping[str, Any]) -> str | None:
        """Extract a default value from the Onshape parameter object."""

        default_value = parameter.get("defaultValue")
        if isinstance(default_value, Mapping):
            return str(default_value.get("value"))
        if default_value is not None:
            return str(default_value)
        return None
