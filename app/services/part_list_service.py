# app/services/part_list_service.py

from typing import Dict, List, Tuple
from app.onshape.onshape import Onshape
from app.onshape.parser import parse_url
from app.config.settings import API_BASE, API_VERSION, CREDS_PATH
from app.onshape.api_switch import api_or_mock


class PartListService:

    # ------------------------------------------------------------
    # MASTER ENTRY POINT
    # ------------------------------------------------------------
    @staticmethod
    def build_master_part_list(doc_url: str, encoded_id: str,
                               filtered_bom: List[Dict], dedup_bom_by_source: List[Dict]):
        """
        Returns a unified list of part records including:
        - quantity
        - sheet metal flags
        - unflattenedPartId
        - compositePartId
        - body details
        - document + element IDs
        - assembly configuration
        """

        # 1. Group BOM rows by part studio so we minimize API calls
        studio_groups = PartListService._group_by_part_studio(dedup_bom_by_source)

        # Will hold metadata for each Part Studio
        studio_metadata = {}

        # 2. Fetch /parts + /bodydetails for each part studio
        for key, _ in studio_groups.items():
            did, wvm_type, wvm_id, eid = key

            parts_meta = PartListService._fetch_parts_metadata(did, wvm_type, wvm_id, eid)
            body_details = PartListService._fetch_body_details(did, wvm_type, wvm_id, eid)

            studio_metadata[key] = {
                "parts_meta": parts_meta,
                "body_details": body_details,
            }

        # 3. Build final master list by iterating the filtered BOM
        master_list = []

        for row in filtered_bom:
            did = row["documentId"]
            wvm_type = row["wvmType"]
            wvm_id = row["wvmId"]
            eid = row["elementId"]
            part_id = row["partId"]

            studio_key = (did, wvm_type, wvm_id, eid)
            meta = studio_metadata.get(studio_key, {})

            parts_meta = meta.get("parts_meta", [])
            body_details = meta.get("body_details", {})

            # Merge metadata for this part
            part_record = PartListService._build_part_record(
                row,                     # BOM details including quantity
                parts_meta,              # full part metadata from /parts
                body_details,            # geometry from /bodydetails
                encoded_id               # assembly config
            )

            master_list.append(part_record)

        return master_list



    # ------------------------------------------------------------
    # GROUP BOM BY PART STUDIO
    # ------------------------------------------------------------
    @staticmethod
    def _group_by_part_studio(dedup_bom) -> Dict[Tuple, List[Dict]]:
        groups = {}
        for row in dedup_bom:
            key = (
                row["documentId"],
                row["wvmType"],
                row["wvmId"],
                row["elementId"]
            )
            groups[key] = True
        return groups



    # ------------------------------------------------------------
    # FETCH PART META
    # ------------------------------------------------------------
    @staticmethod
    def _fetch_parts_metadata(did, wvm_type, wvm_id, eid):
        """
        /parts/d/{did}/{wvmType}/{wvmId}/e/{eid}
        Returns all part metadata in the Part Studio.
        """

        path = f"/api/{API_VERSION}/parts/d/{did}/{wvm_type}/{wvm_id}/e/{eid}"

        return api_or_mock(
            mock_filename="parts_meta.json",  # create this later if needed
            method="GET",
            path=path
        )



    # ------------------------------------------------------------
    # FETCH BODY DETAILS
    # ------------------------------------------------------------
    @staticmethod
    def _fetch_body_details(did, wvm_type, wvm_id, eid):
        """
        /partstudios/.../bodydetails
        Returns all bodies + mapping to partIds
        """

        path = (
            f"/api/{API_VERSION}/partstudios/d/"
            f"{did}/{wvm_type}/{wvm_id}/e/{eid}/bodydetails"
        )

        return api_or_mock(
            mock_filename="bodydetails.json",
            method="GET",
            path=path
        )



    # ------------------------------------------------------------
    # COMBINE DATA INTO FINAL PART RECORD
    # ------------------------------------------------------------
    @staticmethod
    def _build_part_record(bom_row: Dict, parts_meta: List[Dict],
                           body_details: Dict, encoded_id: str) -> Dict:

        part_id = bom_row["partId"]

        # Extract metadata for this part
        part_meta = next((p for p in parts_meta if p["partId"] == part_id), {})

        # Extract body details for this part
        body_info = PartListService._extract_body_details_for_part(part_id, body_details)

        return {
            "partId": part_id,
            "quantity": bom_row["quantity"],
            "assemblyConfig": encoded_id,

            # IDs
            "documentId": bom_row["documentId"],
            "elementId": bom_row["elementId"],
            "wvmType": bom_row["wvmType"],
            "wvmId": bom_row["wvmId"],

            # Part metadata
            "isSheetMetal": part_meta.get("isSheetMetal", False),
            "flattenedBodyId": part_meta.get("flattenedBodyId"),
            "unflattenedPartId": part_meta.get("unflattenedPartId"),
            "compositePartId": part_meta.get("compositePartId"),
            "hasCutList": part_meta.get("hasCutList", False),

            # Geometry
            "bodyDetails": body_info
        }



    # ------------------------------------------------------------
    # FIND GEOMETRY FOR A PARTICULAR PART ID
    # ------------------------------------------------------------
    @staticmethod
    def _extract_body_details_for_part(part_id: str, body_details: Dict):
        bodies = body_details.get("bodies", [])
        matching = [b for b in bodies if b.get("partId") == part_id]
        return matching
