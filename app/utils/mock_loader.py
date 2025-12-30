# app/utils/mock_loader.py

import json
import os
from app.config.settings import LOCAL_DATA_PATH


def load_mock_json(filename: str):
    """
    Loads a JSON file from local_data folder.
    Example: load_mock_json("1_configurations.json")
    """
    path = os.path.join(LOCAL_DATA_PATH, filename)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Mock JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
