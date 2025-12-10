# app/services/part_list_service.py

import logging
import os
import json
from typing import Any, Dict, List, Tuple

from app.services.bom_service import get_quantity_header_id
from app.config.settings import LOCAL_DATA_PATH, DEVELOPMENT_MODE

logger = logging.getLogger(__name__)


class PartListService:
    """
    Build a Master Part List from:
      - BOM (filtered rows)
      - Parts metadata
      - Body details
    In DEV mode, parts + bodies are loaded from local JSON via local_manifest.json.
    In PROD mode, the _fetch_* methods should be wired to the Onshape API.
    """

    # -------------------------------------------------------------------------
    # PUBLIC: BUILD MASTER PART LIST
    # -------------------------------------------------------------------------
    @staticmethod
    def build_master_part_list(
        doc_url: str,
        encoded_configuration: str,
        bom_dict: Dict[str, Any],
        filtered_bom_rows: List[Dict[str, Any]],
        dedup_bom_by_source: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Build the Master Part List for a given configuration.

        - doc_url / encoded_configuration are included for future use
        - bom_dict is the full BOM JSON from Onshape (or dev mock)
        - filtered_bom_rows is the BOM after filter_bom_rows()
        - dedup_bom_by_source is currently unused here, but kept for API parity
        """

        logger.info("Building Master Part List...")

        # ---------------------------------------------------------------------
        # 1) LOAD METADATA + GEOMETRY
        # ---------------------------------------------------------------------
        parts_meta = PartListService._fetch_parts_metadata()
        body_details = PartListService._fetch_body_details()

        # Lookup by (elementId, partId)
        meta_lookup: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for p in parts_meta:
            eid = p.get("elementId")
            pid = p.get("partId")
            if eid and pid:
                meta_lookup[(eid, pid)] = p

        # NOTE: For your current dev body JSON, bodies have no partId field.
        # We therefore only use bodyDetails for flat pattern body lookup by bodyId.
        all_bodies: List[Dict[str, Any]] = body_details.get("bodies", [])

        # ---------------------------------------------------------------------
        # 2) PRECOMPUTE SHEET-METAL MAPPING (unflattened -> flattened)
        # ---------------------------------------------------------------------
        # For each flattened part metadata: unflattenedPartId tells us which
        # folded/unflattened part it belongs to.
        unflattened_to_flattened: Dict[Tuple[str, str], Tuple[str, str]] = {}
        flattened_flags: Dict[Tuple[str, str], bool] = {}

        for p in parts_meta:
            eid = p.get("elementId")
            pid = p.get("partId")
            if not eid or not pid:
                continue

            key = (eid, pid)
            is_flattened = bool(p.get("isFlattenedBody"))
            flattened_flags[key] = is_flattened

            unflat_id = p.get("unflattenedPartId")
            if unflat_id:
                # p is flattened, unflat_id is the folded/real partId
                unflattened_to_flattened[(eid, unflat_id)] = (eid, pid)

        # ---------------------------------------------------------------------
        # 3) PRECOMPUTE QUANTITIES BY MASTER KEY
        # ---------------------------------------------------------------------
        # Master key: (documentId, elementId, configuration, partId)
        quantity_by_key: Dict[Tuple[str, str, str, str], float] = {}

        # Detect quantity header using BOM headers (preferred)
        quantity_header_id = get_quantity_header_id(bom_dict)

        # If not found, derive from row values (robust numeric heuristic)
        if not quantity_header_id:
            quantity_header_id = PartListService._infer_quantity_header_from_rows(
                filtered_bom_rows
            )

        if not quantity_header_id:
            logger.warning(
                "Quantity header not found—defaulting to 1 per distinct part row."
            )

        for row in filtered_bom_rows:
            src = row.get("itemSource", {})
            did = src.get("documentId")
            eid = src.get("elementId")
            cfg = src.get("configuration")
            pid = src.get("partId")

            if not (did and eid and cfg and pid):
                logger.warning("Skipping BOM row missing identity fields: %s", row)
                continue

            key = (did, eid, cfg, pid)

            if quantity_header_id:
                hv = row.get("headerIdToValue", {})
                val = hv.get(quantity_header_id, 0)
                qty = PartListService._safe_numeric(val)
                if qty <= 0:
                    qty = 1
            else:
                qty = 1

            quantity_by_key[key] = quantity_by_key.get(key, 0) + qty

        # ---------------------------------------------------------------------
        # 4) BUILD MASTER LIST ENTRIES PER UNIQUE MASTER KEY
        # ---------------------------------------------------------------------
        master_list: List[Dict[str, Any]] = []

        for (did, eid, cfg, pid), qty in quantity_by_key.items():
            meta = meta_lookup.get((eid, pid), {})

            body_type = meta.get("bodyType")
            is_mesh = meta.get("isMesh")

            # Skip composite parts (placeholder logic per your spec)
            if body_type == "composite":
                logger.warning(
                    "Skipping composite part %s / %s / %s – bodyType=composite",
                    eid, pid, cfg
                )
                continue

            # Skip mesh or non-solid
            if is_mesh is True or (body_type and body_type != "solid"):
                logger.warning(
                    "Skipping non-solid/mesh part %s / %s / %s – bodyType=%s, isMesh=%s",
                    eid, pid, cfg, body_type, is_mesh
                )
                continue

            # ---------------- SHEET METAL DETECTION + LINKING ----------------
            sheet_metal = False
            sheet_role = None
            sheet_id = None

            # If this (eid, pid) is an unflattened part that has a flattened twin
            if (eid, pid) in unflattened_to_flattened:
                sheet_metal = True
                sheet_role = "unflattened"
                sheet_id = unflattened_to_flattened[(eid, pid)][1]

            # If this part metadata itself is a flattened body
            elif flattened_flags.get((eid, pid), False) or meta.get("unflattenedPartId"):
                sheet_metal = True
                sheet_role = "flattened"
                sheet_id = pid

            # If there is a flattened sheet bodyId, collect flat pattern bodies
            flat_pattern_bodies: List[Dict[str, Any]] = []
            flat_body_id = None

            if sheet_metal and sheet_role == "unflattened":
                # Look up the flattened part meta
                flat_key = unflattened_to_flattened.get((eid, pid))
                if flat_key:
                    flat_meta = meta_lookup.get(flat_key)
                    if flat_meta:
                        flat_body_id = flat_meta.get("flattenedBodyId")

            elif sheet_metal and sheet_role == "flattened":
                flat_body_id = meta.get("flattenedBodyId")

            if flat_body_id:
                # Filter global bodies list for matching bodyId
                flat_pattern_bodies = [
                    b for b in all_bodies if b.get("id") == flat_body_id or b.get("bodyId") == flat_body_id
                ]

            entry: Dict[str, Any] = {
                "documentId": did,
                "elementId": eid,
                "configuration": cfg,
                "partId": pid,
                "quantity": qty,

                # metadata
                "name": meta.get("name"),
                "partNumber": meta.get("partNumber"),
                "bodyType": body_type,
                "isMesh": is_mesh,

                # sheet metal flags
                "sheetMetal": sheet_metal,
                "sheetMetalRole": sheet_role,  # 'unflattened' or 'flattened'
                "sheetMetalId": sheet_id,      # flattened partId
                "flattenedBodyId": flat_body_id,
                "flatPatternBodies": flat_pattern_bodies,

                # composite / cut list placeholders
                "compositePartId": meta.get("compositePartId"),
                "hasCutList": meta.get("hasCutList", False),
            }

            master_list.append(entry)

        logger.info("Master Part List complete. %d entries.", len(master_list))
        return master_list

    # -------------------------------------------------------------------------
    # QUANTITY SUPPORT
    # -------------------------------------------------------------------------
    @staticmethod
    def _safe_numeric(val: Any) -> float:
        """Convert a BOM cell value into a numeric, treating bools as non-quantity."""
        if isinstance(val, bool):
            # avoid treating True/False as 1/0
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        try:
            return float(str(val))
        except Exception:
            return 0.0

    @staticmethod
    def _infer_quantity_header_from_rows(
        rows: List[Dict[str, Any]]
    ) -> str:
        """
        Infer which headerId is the 'quantity' column by scanning numeric values.
        We pick the header whose total numeric sum across all rows is maximal.
        """
        sums: Dict[str, float] = {}

        for row in rows:
            hv = row.get("headerIdToValue", {})
            for hid, val in hv.items():
                num = PartListService._safe_numeric(val)
                if num > 0:
                    sums[hid] = sums.get(hid, 0.0) + num

        if not sums:
            return None

        # headerId with maximum sum is most likely quantity
        best = max(sums.items(), key=lambda kv: kv[1])[0]
        return best

    # -------------------------------------------------------------------------
    # LOAD MOCK PARTS METADATA (DEV) OR REAL DATA (PROD)
    # -------------------------------------------------------------------------
    @staticmethod
    def _fetch_parts_metadata() -> List[Dict[str, Any]]:
        """
        DEV MODE:
          - Reads local_manifest.json from LOCAL_DATA_PATH
          - Loads all 'parts' JSON files and concatenates them.

        PROD MODE:
          - TODO: call Onshape /parts API using deduped BOM
        """
        if not DEVELOPMENT_MODE:
            # TODO: implement real Onshape calls here
            logger.info("PRODUCTION mode: _fetch_parts_metadata not yet implemented.")
            return []

        manifest_path = os.path.join(LOCAL_DATA_PATH, "local_manifest.json")
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except Exception as e:
            logger.error("Could not load local manifest for parts: %s", e)
            return []

        all_parts: List[Dict[str, Any]] = []

        for filename in manifest.get("parts", []):
            full_path = os.path.join(LOCAL_DATA_PATH, filename)
            try:
                with open(full_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_parts.extend(data)
                    else:
                        logger.warning(
                            "Parts file %s did not contain a JSON list; skipping.", filename
                        )
            except Exception as e:
                logger.error("Failed to load parts file %s: %s", filename, e)

        logger.info("Loaded %d parts metadata entries from local files.", len(all_parts))
        return all_parts

    # -------------------------------------------------------------------------
    # LOAD MOCK BODY DETAILS (DEV) OR REAL DATA (PROD)
    # -------------------------------------------------------------------------
    @staticmethod
    def _fetch_body_details() -> Dict[str, Any]:
        """
        DEV MODE:
          - Reads local_manifest.json from LOCAL_DATA_PATH
          - Loads all 'bodies' JSON files and merges them into {"bodies": [...]}

        PROD MODE:
          - TODO: call Onshape /partstudios/.../bodydetails for each deduped PS
        """
        merged = {"bodies": []}

        if not DEVELOPMENT_MODE:
            # TODO: implement real Onshape calls here
            logger.info("PRODUCTION mode: _fetch_body_details not yet implemented.")
            return merged

        manifest_path = os.path.join(LOCAL_DATA_PATH, "local_manifest.json")
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except Exception as e:
            logger.error("Could not load local manifest for bodies: %s", e)
            return merged

        for filename in manifest.get("bodies", []):
            full_path = os.path.join(LOCAL_DATA_PATH, filename)
            try:
                with open(full_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        merged["bodies"].extend(data.get("bodies", []))
                    else:
                        logger.warning(
                            "Body file %s did not contain expected dict; skipping.", filename
                        )
            except Exception as e:
                logger.error("Failed to load body file %s: %s", filename, e)

        logger.info("Loaded %d bodies from local files.", len(merged["bodies"]))
        return merged
