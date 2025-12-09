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

        # Load metadata + body details once
        parts_meta = PartListService._fetch_parts_metadata()
        body_details = PartListService._fetch_body_details()

        # Map each Part Studio to its identifying keys
        studio_groups = PartListService._group_by_part_studio(dedup_bom_by_source)

        # Build final list
        master_list = []

        for row in filtered_bom:
            src = row.get("itemSource", {})
            document_id = src.get("documentId")
            element_id = src.get("elementId")
            wvm_type = src.get("wvmType")
            wvm_id = src.get("wvmId")
            part_id = src.get("partId")
            configuration = src.get("configuration")

            if not part_id:
                logger.warning("Skipping BOM row missing partId: %s", row)
                continue

            # Identify sheet-metal, composite, etc.
            meta = PartListService._lookup_part_meta(parts_meta, part_id)

            # Attach body geometry
            bodies = PartListService._lookup_body_details(body_details, part_id)

            # Compute quantity for this exact part
            qty = PartListService._lookup_quantity(
                filtered_bom,
                document_id,
                element_id,
                wvm_type,
                wvm_id,
                part_id,
                configuration
            )

            master_list.append({
                "partId": part_id,
                "quantity": qty,
                "documentId": document_id,
                "elementId": element_id,
                "wvmType": wvm_type,
                "wvmId": wvm_id,
                "configuration": configuration,
                "isSheetMetal": meta.get("isSheetMetal", False),
                "flattenedBodyId": meta.get("flattenedBodyId"),
                "unflattenedPartId": meta.get("unflattenedPartId"),
                "compositePartId": meta.get("compositePartId"),
                "hasCutList": meta.get("hasCutList", False),
                "bodyDetails": bodies
            })

        logger.info("Master Part List built. Total parts: %d", len(master_list))
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
