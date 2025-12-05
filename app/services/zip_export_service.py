# app/services/zip_export_service.py

import io
import zipfile
from typing import Dict


def create_zip(files: Dict[str, bytes]) -> bytes:
    """
    Create a ZIP archive in memory.

    :param files: Mapping of {filename: file_bytes}
    :return: ZIP archive as bytes.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buffer.seek(0)
    return buffer.read()
