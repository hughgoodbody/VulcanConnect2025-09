# app/utils/file_ops.py

import io
from flask import send_file


def bytes_to_download_response(data: bytes, filename: str, mimetype: str):
    """
    Wrap raw bytes into a Flask send_file() response.
    """
    buffer = io.BytesIO(data)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )
