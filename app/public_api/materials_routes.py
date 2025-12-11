from flask import Blueprint, jsonify
import json
import os

material_bp = Blueprint("materials", __name__)

MATERIAL_FILE = os.path.join("user_data", "hugh", "CommonSFXMaterials.json")

@material_bp.get("/")
def get_materials():
    try:
        with open(MATERIAL_FILE, "r") as f:
            data = json.load(f)

        # data is already a list
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
