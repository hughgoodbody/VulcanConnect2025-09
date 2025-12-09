from flask import Blueprint, jsonify
import json
import os

supplier_bp = Blueprint("suppliers", __name__)

SUPPLIER_FILE = "user_data/hugh/SupplierDetails.json"

@supplier_bp.get("/")
def get_suppliers():
    try:
        with open(SUPPLIER_FILE, "r") as f:
            data = json.load(f)
        return jsonify(data.get("suppliers", []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
