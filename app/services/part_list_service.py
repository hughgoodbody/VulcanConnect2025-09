# app/services/part_list_service.py

import logging
from typing import Any, Dict, List, Optional, Tuple

from app.services.bom_service import get_quantity_header_id

logger = logging.getLogger(__name__)


class PartListService:

    # -------------------------------------------------------------------------
    # PUBLIC: BUILD MASTER PART LIST
    # -------------------------------------------------------------------------
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

        # Create lookup: partId → metadata
        part_meta_lookup = {
            p.get("partId"): p for p in parts_meta
        }

        # Create lookup: partId → list of body detail dicts
        body_lookup = {}
        for b in body_details.get("bodies", []):
            pid = b.get("partId")
            if pid:
                body_lookup.setdefault(pid, []).append(b)

        # Create BOM partId → BOM row lookup
        bom_part_lookup = {
            row.get("itemSource", {}).get("partId"): row
            for row in filtered_bom
        }

        master_list = []

        # ---------------------------------------------------------------------
        # PROCESS EACH BOM ROW
        # ---------------------------------------------------------------------
        for row in filtered_bom:
            src = row.get("itemSource", {})
            part_id = src.get("partId")

            if not part_id:
                logger.warning("Skipping BOM row without partId: %s", row)
                continue

            # Metadata & geometry lookup
            meta = part_meta_lookup.get(part_id, {})
            bodies = body_lookup.get(part_id, [])

            # Detect sheet-metal correctly
            is_sheet_metal = PartListService._is_sheet_metal(meta, bodies)

            # Compute quantity for this exact part configuration
            qty = PartListService._lookup_quantity(
                filtered_bom,
                part_id,
                src.get("documentId"),
                src.get("elementId"),
                src.get("wvmType"),
                src.get("wvmId"),
                src.get("configuration")
            )

            # Base part entry
            entry = {
                "partId": part_id,
                "quantity": qty,

                "documentId": src.get("documentId"),
                "elementId": src.get("elementId"),
                "wvmType": src.get("wvmType"),
                "wvmId": src.get("wvmId"),
                "configuration": src.get("configuration"),

                # geometry
                "bodyDetails": bodies,

                # sheet-metal fields (to be filled below)
                "isSheetMetal": is_sheet_metal,
                "unflattenedPartId": None,
                "flattenedBodyId": None,
                "flatPatternBodies": [],
                "foldedPartId": None,

                # composite/cutlist
                "compositePartId": meta.get("compositePartId"),
                "hasCutList": meta.get("hasCutList", False)
            }

            # -----------------------------------------------------------------
            # SHEET METAL HANDLING
            # -----------------------------------------------------------------
            if is_sheet_metal:
                unflat_id = meta.get("unflattenedPartId")
                flat_body_id = meta.get("flattenedBodyId")

                entry["unflattenedPartId"] = unflat_id
                entry["flattenedBodyId"] = flat_body_id

                # Attach flat pattern bodies
                if flat_body_id:
                    entry["flatPatternBodies"] = [
                        b for b in body_details.get("bodies", [])
                        if b.get("bodyId") == flat_body_id
                    ]

                # Find folded version in BOM
                if unflat_id and unflat_id in bom_part_lookup:
                    entry["foldedPartId"] = unflat_id
                else:
                    entry["foldedPartId"] = None

            master_list.append(entry)

        logger.info("Master Part List complete. %d parts", len(master_list))
        return master_list

    # -------------------------------------------------------------------------
    # SHEET METAL DETECTION
    # -------------------------------------------------------------------------
    @staticmethod
    def _is_sheet_metal(meta: Dict[str, Any], bodies: List[Dict[str, Any]]) -> bool:
        """Identify sheet-metal parts using robust multi-rule logic."""

        # Rule A: metadata explicitly says so
        if meta.get("isSheetMetal") is True:
            return True

        # Rule B: sheet-metal ALWAYS has unflattenedPartId
        if meta.get("unflattenedPartId"):
            return True

        # Rule C: any body flagged as flattened
        for b in bodies:
            if b.get("isFlattenedBody"):
                return True

        return False

    # -------------------------------------------------------------------------
    # QUANTITY LOOKUP
    # -------------------------------------------------------------------------
    @staticmethod
    def _lookup_quantity(
        filtered_bom: List[Dict[str, Any]],
        part_id: str,
        document_id: str,
        element_id: str,
        wvm_type: str,
        wvm_id: str,
        configuration: str
    ) -> int:

        # Try to detect quantity column
        # NOTE: filtered BOM rows may not contain the BOM dict with headers,
        # so we fall back to dynamic detection below.
        quantity_id = None

        # Heuristic: find a headerId where values are numeric
        for row in filtered_bom:
            for key, val in row.get("headerIdToValue", {}).items():
                if isinstance(val, (int, float)) or str(val).isdigit():
                    quantity_id = key
                    break
            if quantity_id:
                break

        if not quantity_id:
            logger.warning("Quantity header not found—defaulting to 1 per row.")
            return 1

        qty = 0
        for row in filtered_bom:
            src = row.get("itemSource", {})
            if (
                src.get("partId") == part_id
                and src.get("documentId") == document_id
                and src.get("elementId") == element_id
                and src.get("wvmType") == wvm_type
                and src.get("wvmId") == wvm_id
                and src.get("configuration") == configuration
            ):
                hv = row.get("headerIdToValue", {})
                val = hv.get(quantity_id)
                try:
                    qty += int(val)
                except:
                    pass

        return qty if qty > 0 else 1

    # -------------------------------------------------------------------------
    # LOAD MOCK PARTS METADATA
    # -------------------------------------------------------------------------
    @staticmethod
    def _fetch_parts_metadata() -> List[Dict[str, Any]]:
        path = "local_json_responses/parts_meta.json"
        try:
            import json
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load parts metadata: %s", e)
            return []

    # -------------------------------------------------------------------------
    # LOAD MOCK BODY DETAILS
    # -------------------------------------------------------------------------
    @staticmethod
    def _fetch_body_details() -> Dict[str, Any]:
        path = "local_json_responses/bodydetails.json"
        try:
            import json
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load body details: %s", e)
            return {"bodies": []}
