# app/handlers/export_handler.py

from typing import Optional, Dict

from app.services.step_export_service import export_step
from app.services.zip_export_service import create_zip


class ExportHandler:
    """
    High-level export operations (STEP, ZIP).
    """

    @staticmethod
    def export_step_bytes(doc_url: str, configuration: Optional[str] = None) -> bytes:
        """
        Export a single STEP file as bytes for the given Onshape URL and optional configuration.
        """
        return export_step(doc_url, configuration)

    @staticmethod
    def export_step_zip(doc_url: str, configuration: Optional[str] = None) -> bytes:
        """
        Export a STEP file and wrap it into a ZIP archive.

        :return: ZIP file bytes containing model.step
        """
        step_bytes = export_step(doc_url, configuration)
        files: Dict[str, bytes] = {"model.step": step_bytes}
        return create_zip(files)
