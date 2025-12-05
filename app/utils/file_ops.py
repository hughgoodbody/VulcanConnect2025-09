# app/utils/file_ops.py

import io
from flask import send_file


def bytes_to_download_response(data: bytes, filename: str, mimetype: str):
    buf = io.BytesIO(data)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype,
    )
