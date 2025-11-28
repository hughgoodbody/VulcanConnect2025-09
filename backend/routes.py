from nicegui import ui, app
from frontend import state
import io
from fastapi.responses import StreamingResponse, PlainTextResponse
from datetime import date

# Routes for file downloads (for all export types)
@app.get("/download-frames-zip")
def download_frames_zip():
    if state.latest_frames_output is None:
        return PlainTextResponse("Error: Frame processing not started yet.", status_code=400)

    content = state.latest_frames_output.frames_zip

    if isinstance(content, dict):
        return StreamingResponse(io.BytesIO(b"Error building ZIP"), media_type='text/plain')

    buffer = io.BytesIO(content)
    buffer.seek(0)
    filename = f'Frames_Export_{date.today().strftime("%d%m%Y")}.zip'
    return StreamingResponse(
        buffer,
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@app.get("/download-drawings-zip")
def download_drawings_zip():
    if state.latest_drawings_output is None:
        return PlainTextResponse("Error: Drawing processing not started yet.", status_code=400)

    content = state.latest_drawings_output.generated_zip_buffer

    if isinstance(content, dict):
        return StreamingResponse(io.BytesIO(b"Error building ZIP"), media_type='text/plain')

    buffer = io.BytesIO(content)
    buffer.seek(0)
    filename = f'Drawings_Export_{date.today().strftime("%d%m%Y")}.zip'
    return StreamingResponse(
        buffer,
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )