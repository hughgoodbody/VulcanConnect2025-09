# app/handlers/export_handler.py

from typing import Optional, Dict
from app.services.step_export_service import export_step
from app.services.zip_export_service import create_zip
from app.config.settings import DEVELOPMENT_MODE


class ExportHandler:
    """
    High-level export logic with DEV-mode mock support.
    """

    @staticmethod
    def export_step_bytes(doc_url: str, configuration: Optional[str] = None) -> bytes:
        """
        Return raw STEP file bytes.
        DEV mode → loads from local_data/4_step_export.step
        LIVE mode → Onshape API
        """
        return export_step(doc_url, configuration)

    @staticmethod
    def export_step_zip(doc_url: str, configuration: Optional[str] = None) -> bytes:
        """
        Create a ZIP containing the STEP file.
        """

        step_bytes = export_step(doc_url, configuration)
        files: Dict[str, bytes] = {"model.step": step_bytes}

        return create_zip(files)
