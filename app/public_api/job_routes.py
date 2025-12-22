from flask import Blueprint, request, jsonify
from app.handlers.config_handler import ConfigHandler
from app.handlers.bom_handler import BomHandler
from app.services.part_list_service import PartListService
from app.db import get_db_connection
from threading import Thread
from app.services.job_service import create_job, update_job
import traceback
import json

job_bp = Blueprint("job", __name__)

def run_job_async(job_id, onshape_url, config_values, user_options):
    try:
        update_job(job_id, status="processing", progress=5,
                   message="Encoding configuration")
        
        # 1. Convert UI values → Onshape parameters
        parameter_list = build_parameter_list(config_values)
        
        # 2. Encode configuration (returns dict)
        encoding = ConfigHandler.encode_configuration(onshape_url, parameter_list)
        configuration_string = encoding["encodedId"]  # YES — use this
        #encoded_id = encoding["encodedId"]
        query_param = encoding["queryParam"]
        print("CONFIGURATION STRING:", configuration_string)
        print("QUERY PARAM:", query_param)

        update_job(job_id, progress=25,
                   message="Fetching BOM")
        print("ENCODED ID BEING SENT TO BOM:", encoded_id)
        bom = BomHandler.fetch_bom_for_configuration(onshape_url, parameter_list)



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
        tb = traceback.format_exc()
        print("JOB FAILED:", tb)
    
        update_job(
            job_id,
            status="error",
            message=str(e),
            error=tb
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
@job_bp.route("/updateParts", methods=["POST", "GET"])
def update_parts():

    if request.method == "POST":
        payload = request.json

        if not payload:
            return jsonify({"error": "Missing JSON body"}), 400

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Always overwrite row id = 1
            cur.execute(
                """
                INSERT INTO job_current (id, payload, updated_at)
                VALUES (1, %s, NOW())
                ON CONFLICT (id)
                DO UPDATE SET
                    payload = EXCLUDED.payload,
                    updated_at = NOW();
                """,
                (json.dumps(payload),)
            )

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({
                "status": "ok",
                "message": "Current job updated"
            }), 200

        except Exception as e:
            print("DB ERROR:", e)
            return jsonify({"error": str(e)}), 500

    # ------------------------
    # GET: view current job
    # ------------------------
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT payload, updated_at FROM job_current WHERE id = 1;"
        )
        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return jsonify({"message": "No job stored yet"}), 200

        return jsonify({
            "updated_at": row[1],
            "payload": row[0]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500






    
# ----------------------------------------------------------
# Create jobs table - run once
# ----------------------------------------------------------
@job_bp.route("/dev/init-db", methods=["GET"])
def init_db():

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE job_current (
            id INTEGER PRIMARY KEY,
            updated_at TIMESTAMP DEFAULT NOW(),
            payload JSONB
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

@job_bp.route("/result/<job_id>", methods=["GET"])
def job_result(job_id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT result FROM jobs WHERE id=%s",
        (job_id,)
    )

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[0]:
        return jsonify({"error": "Result not ready"}), 404

    return jsonify(row[0])

@job_bp.route("/status/<job_id>", methods=["GET"])
def job_status(job_id):

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT status, progress, message, error
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
        "message": row[2],
        "error": row[3]
    })

