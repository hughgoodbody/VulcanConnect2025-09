import io
import logging
from datetime import date
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from starlette.concurrency import run_in_threadpool

from backend.apps.frames_export.main_frames_export import main_frames_exporter
from backend.apps.batch_drawings.main_batch_drawings import (
    export_drawings_to_memory_zip,
)
from backend.schema.cls_ui_schema import FrameUIState

logger = logging.getLogger(__name__)

app = FastAPI(title="VulcanConnect API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


class FramesExportRequest(BaseModel):
    """Payload for exporting frames from an Onshape document."""

    document_url: HttpUrl
    export_step: bool = False


class ExportStatus(BaseModel):
    status: str
    messages: List[str] = []


class DrawingsExportRequest(BaseModel):
    """Payload for exporting a batch of drawings from an Onshape document."""

    document_url: HttpUrl
    export_pdf: bool = True
    export_dwg: bool = True
    export_dxf: bool = False


class ProfilesExportRequest(BaseModel):
    """Placeholder payload for profiles export (not yet implemented)."""

    document_url: HttpUrl


@app.get("/health", response_model=ExportStatus)
async def healthcheck() -> ExportStatus:
    """Simple readiness probe for uptime checks."""

    return ExportStatus(status="ok", messages=["API reachable"])


@app.post("/api/frames/export")
async def export_frames(payload: FramesExportRequest) -> StreamingResponse:
    """
    Export frame members for a given Onshape document as a ZIP file.

    The ZIP includes NC1 + material CSVs and (optionally) STEP files.
    Designed to be called from a WordPress/Elementor form or fetch() request.
    """

    ui_state = FrameUIState()
    ui_state.url_input = str(payload.document_url)

    frames_options = {"STEP Option": payload.export_step}
    progress: List[str] = []

    def notifier(message: str) -> None:
        logger.info(message)
        progress.append(message)

    await run_in_threadpool(
        main_frames_exporter,
        ui_state.url_input,
        ui_state,
        frames_options,
        notifier,
    )

    if not ui_state.frames_zip:
        raise HTTPException(status_code=500, detail="Export did not produce a ZIP file.")

    buffer = io.BytesIO(ui_state.frames_zip)
    buffer.seek(0)

    filename = f"Frames_Export_{date.today().strftime('%Y%m%d')}.zip"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if progress:
        headers["X-Export-Progress"] = " | ".join(progress[-5:])

    return StreamingResponse(buffer, media_type="application/zip", headers=headers)


@app.post("/api/drawings/export")
async def export_drawings(payload: DrawingsExportRequest) -> StreamingResponse:
    """Export all drawings for a document as a ZIP of the selected formats."""

    export_formats = {
        "PDF": payload.export_pdf,
        "DWG": payload.export_dwg,
        "DXF": payload.export_dxf,
    }
    progress: List[str] = []

    def notifier(message: str) -> None:
        logger.info(message)
        progress.append(message)

    drawings_zip: bytes = await run_in_threadpool(
        export_drawings_to_memory_zip,
        str(payload.document_url),
        export_formats,
        notifier,
    )

    if not drawings_zip:
        raise HTTPException(status_code=500, detail="Export did not produce a ZIP file.")

    buffer = io.BytesIO(drawings_zip)
    buffer.seek(0)

    filename = f"Batch_Drawings_Export_{date.today().strftime('%Y%m%d')}.zip"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if progress:
        headers["X-Export-Progress"] = " | ".join(progress[-5:])

    return StreamingResponse(buffer, media_type="application/zip", headers=headers)


@app.post("/api/profiles/export")
async def export_profiles(payload: ProfilesExportRequest) -> ExportStatus:
    """Placeholder endpoint for profiles export until implementation is available."""

    # The legacy NiceGUI implementation did not provide a reusable backend routine for
    # profiles export. This endpoint is exposed so the WordPress UI can be wired now,
    # and the backend logic can be filled in when ready.
    raise HTTPException(
        status_code=501,
        detail="Profiles export is not implemented yet. Please keep this endpoint wired and update once backend support is added.",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8051)
