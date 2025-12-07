# app/handlers/bom_handler.py

from typing import Any, Dict, List

from app.onshape.onshape import Onshape
from app.onshape.parser import parse_url
from app.config.settings import CREDS_PATH, API_VERSION, API_BASE
from app.services.bom_service import filter_bom_rows, dedupe_bom_by_source


class BomHandler:

    @staticmethod
    def fetch_filtered_bom(doc_url: str) -> Dict[str, Any]:
        did, wvm_type, wvm_id, eid = parse_url(doc_url)

        onshape = Onshape(API_BASE, logging=False, creds=CREDS_PATH)
        path = (
            f"/api/{API_VERSION}/assemblies/d/"
            f"{did}/{wvm_type}/{wvm_id}/e/{eid}/bom"
        )
        query = {"indented": False, "multiLevel": False, "generateIfAbsent": True}

        raw = onshape.request("GET", path, query=query).json()
        return filter_bom_rows(raw)

    @staticmethod
    def fetch_deduped_bom(doc_url: str) -> List[Dict[str, Any]]:
        bom = BomHandler.fetch_filtered_bom(doc_url)
        return dedupe_bom_by_source(bom)
