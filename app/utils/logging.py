# app/utils/logging.py

import logging
import sys

def configure_logging(level: int = logging.INFO):
    """
    Configure global logging for the whole backend.
    Call this once from main.py if needed.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
