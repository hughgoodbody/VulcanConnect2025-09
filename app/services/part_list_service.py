# app/services/part_list_service.py

import logging
from typing import Any, Dict, List, Tuple

from app.services.bom_service import get_quantity_header_id

logger = logging.getLogger(__name__)


class PartListService:

    # ---------------------------------------------------------------------
    # PUBLIC: Build Master Part List
    # ---------------------------------------------------------------------
    @staticmethod
    def build_master_part_list(
        doc_url: str,
        encoded_configuration: str,
        filtered_bom: List[Dict[str, Any]],
        dedup_bom_by_source: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
    
        logger.info("Building Master Part List...")
    
        parts_meta = PartListService._fetch_parts_metadata()
        body_details = PartListService._fetch_body_details()
    
        # Create BOM partId → row lookup
        bom_part_lookup = {
            row.get("itemSource", {}).get("partId"): row
            for row in filtered_bom
        }
    
        master_list = []
    
        for row in filtered_bom:
            src = row.get("itemSource", {})
            part_id = src.get("partId")
    
            if not part_id:
                continue
    
            # Metadata lookup
            meta = PartListService._lookup_part_meta(parts_meta, part_id)
    
            # Standard body details
            bodies = PartListService._lookup_body_details(body_details, part_id)
    
            # Compute quantity
            qty = PartListService._lookup_quantity(
                filtered_bom,
                src.get("documentId"),
                src.get("elementId"),
                src.get("wvmType"),
                src.get("wvmId"),
                part_id,
                src.get("configuration")
            )
    
            # Base entry
            entry = {
                "partId": part_id,
                "quantity": qty,
                "documentId": src.get("documentId"),
                "elementId": src.get("elementId"),
                "wvmType": src.get("wvmType"),
                "wvmId": src.get("wvmId"),
                "configuration": src.get("configuration"),
                "bodyDetails": bodies,
                "isSheetMetal": meta.get("isSheetMetal", False),
                "flattenedBodyId": None,
                "unflattenedPartId": None,
                "flatPatternBodies": []
            }
    
            # ---------------------------------------------------------
            # SHEET METAL LOGIC
            # ---------------------------------------------------------
            if meta.get("isSheetMetal"):
                unflat_id = meta.get("unflattenedPartId")  # folded part ID
                flat_body_id = meta.get("flattenedBodyId") # body of flat pattern
    
                entry["unflattenedPartId"] = unflat_id
                entry["flattenedBodyId"] = flat_body_id
    
                # Attach flat pattern geometry
                if flat_body_id:
                    entry["flatPatternBodies"] = [
                        bd for bd in body_details.get("bodies", [])
                        if bd.get("bodyId") == flat_body_id
                    ]
    
                # Try to match folded part using unflattenedPartId
                if unflat_id in bom_part_lookup:
                    entry["foldedPartId"] = unflat_id
                else:
                    entry["foldedPartId"] = None
    
            master_list.append(entry)
    
        return master_list


    # ---------------------------------------------------------------------
    # PART META LOOKUP
    # ---------------------------------------------------------------------
    @staticmethod
    def _lookup_part_meta(parts_meta: List[Dict[str, Any]], part_id: str) -> Dict[str, Any]:
        for meta in parts_meta:
            if meta.get("partId") == part_id:
                return meta
        logger.warning("Part metadata missing for partId: %s", part_id)
        return {}

    # ---------------------------------------------------------------------
    # BODY DETAILS LOOKUP
    # ---------------------------------------------------------------------
    @staticmethod
    def _lookup_body_details(body_details: Dict[str, Any], part_id: str) -> List[Dict[str, Any]]:
        bodies = body_details.get("bodies", [])
        return [b for b in bodies if b.get("partId") == part_id]

    # ---------------------------------------------------------------------
    # QUANTITY LOOKUP
    # ---------------------------------------------------------------------
    @staticmethod
    def _lookup_quantity(
        filtered_bom: List[Dict[str, Any]],
        document_id: str,
        element_id: str,
        wvm_type: str,
        wvm_id: str,
        part_id: str,
        configuration: str
    ) -> int:

        # Determine header ID of quantity column
        # We assume filtered BOM rows originate from raw BOM with headers included
        if not filtered_bom:
            return 1

        # Extract the BOM dict from the first row
        # If BOM rows were separated from headers earlier, quantity header must be provided separately.
        # For now we assume all filtered BOM rows share the same headerIdToValue structure.
        possible_bom_dict = filtered_bom[0].get("_bom_headers_source")
        quantity_id = None

        if possible_bom_dict:
            quantity_id = get_quantity_header_id(possible_bom_dict)

        # Fallback: search for a headerId that looks numeric
        if not quantity_id:
            # heuristic search across all rows:
            for row in filtered_bom:
                for key, val in row.get("headerIdToValue", {}).items():
                    if str(val).isdigit():
                        quantity_id = key
                        break
                if quantity_id:
                    break

        if not quantity_id:
            logger.warning("Quantity header ID not found; defaulting quantity=1.")
            return 1

        qty = 0

        for row in filtered_bom:
            src = row.get("itemSource", {})

            if (
                src.get("documentId") == document_id and
                src.get("elementId") == element_id and
                src.get("wvmType") == wvm_type and
                src.get("wvmId") == wvm_id and
                src.get("partId") == part_id and
                src.get("configuration") == configuration
            ):
                hv = row.get("headerIdToValue", {})
                val = hv.get(quantity_id)

                try:
                    qty += int(val)
                except:
                    pass

        return qty if qty > 0 else 1

    # ---------------------------------------------------------------------
    # PART STUDIO GROUPING
    # ---------------------------------------------------------------------
    @staticmethod
    def _group_by_part_studio(dedup_rows: List[Dict[str, Any]]) -> Dict[
        Tuple[str, str, str, str], bool
    ]:
        """
        Returns a dict keyed by: (documentId, wvmType, wvmId, elementId)
        """
        groups = {}

        for row in dedup_rows:
            src = row.get("itemSource", {})

            did = src.get("documentId")
            wvm_type = src.get("wvmType")
            wvm_id = src.get("wvmId")
            eid = src.get("elementId")

            if not (did and wvm_type and wvm_id and eid):
                logger.warning("Dedup row missing part studio identifiers: %s", row)
                continue

            key = (did, wvm_type, wvm_id, eid)
            groups[key] = True

        return groups

    # ---------------------------------------------------------------------
    # LOAD MOCK PART META
    # ---------------------------------------------------------------------
    @staticmethod
    def _fetch_parts_metadata() -> List[Dict[str, Any]]:
        """
        Loads mock parts metadata (in DEV mode).
        """
        path = "local_data/parts_meta.json"
        try:
            import json
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load parts metadata: %s", e)
            return []

    # ---------------------------------------------------------------------
    # LOAD MOCK BODY DETAILS
    # ---------------------------------------------------------------------
    @staticmethod
    def _fetch_body_details() -> Dict[str, Any]:
        """
        Loads mock body details (in DEV mode).
        """
        path = "local_data/bodydetails.json"
        try:
            import json
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load body details: %s", e)
            return {"bodies": []}
