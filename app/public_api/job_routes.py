from flask import Blueprint, request, jsonify
from app.handlers.config_handler import ConfigHandler
from app.handlers.bom_handler import BomHandler
from app.services.part_list_service import PartListService
from app.db import get_db_connection
from threading import Thread
from app.services.job_service import create_job, update_job
import traceback

job_bp = Blueprint("job", __name__)

def run_job_async(job_id, onshape_url, config_values, user_options):
    try:
        update_job(job_id, status="processing", progress=5,
                   message="Encoding configuration")

        parameter_list = build_parameter_list(config_values)
        encoded_id = ConfigHandler.encode_configuration(onshape_url, parameter_list)

        update_job(job_id, progress=25,
                   message="Fetching BOM")

        bom = BomHandler.fetch_bom_for_configuration(onshape_url, encoded_id)

        update_job(job_id, progress=50,
                   message="Building master part list")

        master_list = PartListService.build_master_part_list(
            onshape_url,
            encoded_id,
            bom["raw"],
            bom["filtered"],
            bom["dedupBySource"]
        )

        update_job(
            job_id,
            status="done",
            progress=100,
            message="Completed",
            result={
                "encodedId": encoded_id,
                "filteredBom": bom["filtered"],
                "dedupBomBySource": bom["dedupBySource"],
                "masterPartList": master_list,
                "userOptions": user_options
            }
        )

    except Exception as e:
        update_job(
            job_id,
            status="error",
            message="Job failed",
            error=str(e)
        )


# ----------------------------------------------------------
# Utility: convert frontend configValues → Onshape param list
# ----------------------------------------------------------
def build_parameter_list(config_values):
    param_list = []

    for param_id, value in config_values.items():

        # Quantity values → { "value": 10, "units": "mm" }
        if isinstance(value, dict) and "value" in value and "units" in value:
            param_list.append({
                "parameterId": param_id,
                "parameterValue": {
                    "type": "BTMParameterQuantity",
                    "value": value["value"],
                    "units": value["units"]
                }
            })

        # Boolean
        elif isinstance(value, bool):
            param_list.append({
                "parameterId": param_id,
                "parameterValue": value
            })

        # Numeric
        elif isinstance(value, (int, float)):
            param_list.append({
                "parameterId": param_id,
                "parameterValue": value
            })

        # Enum / String
        else:
            param_list.append({
                "parameterId": param_id,
                "parameterValue": str(value)
            })

    return param_list


# ----------------------------------------------------------
# POST /api/job/create
# ----------------------------------------------------------
@job_bp.post("/create")
def create_job_endpoint():
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"error": "Missing JSON body"}), 400

    onshape_url = payload.get("onshapeUrl")
    config_values = payload.get("configValues", {})
    user_options = payload.get("userOptions", {})

    if not onshape_url:
        return jsonify({"error": "Missing onshapeUrl"}), 400

    # 1. Create DB job
    job_id = create_job()

    # 2. Start background thread
    t = Thread(
        target=run_job_async,
        args=(job_id, onshape_url, config_values, user_options),
        daemon=True
    )
    t.start()

    # 3. Return immediately
    return jsonify({
        "jobId": job_id
    }), 202


# ----------------------------------------------------------
# POST /api/job/updateParts
# ----------------------------------------------------------
@job_bp.route("/updateParts", methods=["POST"])
def update_parts():    
    payload = request.json    
    #print("Received updated parts:", payload)
    return jsonify({"status": "ok", "updated": True})




@job_bp.route("/status/<job_id>", methods=["GET"])
def job_status(job_id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT status, progress, message
        FROM jobs
        WHERE id=%s
        """,
        (job_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "status": row[0],
        "progress": row[1],
        "message": row[2]
    })

    
# ----------------------------------------------------------
# Create jobs table - run once
# ----------------------------------------------------------
@job_bp.route("/dev/init-db", methods=["GET"])
def init_db():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id UUID PRIMARY KEY,
            status TEXT NOT NULL,
            progress INT DEFAULT 0,
            message TEXT,
            result JSONB,
            error TEXT,
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

    return {"ok": True, "message": "jobs table ready"}

@job_bp.route("/dev/test-db", methods=["GET"])
def test_db():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM jobs;")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {"jobs": count}
