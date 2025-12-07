# app/onshape/api_switch.py

from typing import Any, Dict
from app.onshape.onshape import Onshape
from app.utils.mock_loader import load_mock_json
from app.config.settings import DEVELOPMENT_MODE, CREDS_PATH, API_BASE


def api_or_mock(
        mock_filename: str,
        method: str = None,
        path: str = None,
        query: Dict[str, Any] = None,
        body: Dict[str, Any] = None
    ):
    """
    Central switch:
    - In dev mode → return JSON from file
    - In prod mode → perform real Onshape API call
    """

    if DEVELOPMENT_MODE:
        return load_mock_json(mock_filename)

    # real API call
    onshape = Onshape(API_BASE, creds=CREDS_PATH, logging=False)
    response = onshape.request(method, path, query=query, body=body)
    response.raise_for_status()
    return response.json()
