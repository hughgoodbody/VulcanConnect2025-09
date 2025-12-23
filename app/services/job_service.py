import uuid
from app.db import get_db_connection
from psycopg2.extras import Json
import json



def create_job(ui_schema=None):
    job_id = str(uuid.uuid4())

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO jobs (id, status, progress, message, ui_schema)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (job_id, "queued", 0, "Job queued", json.dumps(ui_schema) if ui_schema else None)
    )

    conn.commit()
    cur.close()
    conn.close()

    return job_id


def update_job(job_id, status=None, progress=None, message=None, result=None, error=None):
    fields = []
    values = []

    if status is not None:
        fields.append("status=%s")
        values.append(status)

    if progress is not None:
        fields.append("progress=%s")
        values.append(progress)

    if message is not None:
        fields.append("message=%s")
        values.append(message)

    if result is not None:
        fields.append("result=%s")
        values.append(Json(result))

    if error is not None:
        fields.append("error=%s")
        values.append(error)

    if not fields:
        return

    values.append(job_id)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        f"""
        UPDATE jobs
        SET {", ".join(fields)}, updated_at=now()
        WHERE id=%s
        """,
        values
    )

    conn.commit()
    cur.close()
    conn.close()
