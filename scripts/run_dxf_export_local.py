import json
from pathlib import Path

from app.services.dxf_export_service import export_supplier_grouped_dxf_zip

# ---- CONFIG ----
DOC_URL = "https://cad.onshape.com/documents/XXXXX/w/XXXXX/e/XXXXX"
JSON_PATH = Path("/mnt/data/current.json")  # your uploaded file

# ----------------

def main():
    with open(JSON_PATH, "r") as f:
        payload = json.load(f)

    files = export_supplier_grouped_dxf_zip(DOC_URL, payload)

    print(f"Exported {len(files)} DXF files:")

    for name in files.keys():
        print(" -", name)


if __name__ == "__main__":
    main()
