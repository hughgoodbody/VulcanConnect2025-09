# app/services/part_list_service.py

import logging
import os
import json
from typing import Any, Dict, List, Tuple

from app.services.bom_service import get_quantity_header_id
from app.config.settings import (
    LOCAL_DATA_PATH,
    DEVELOPMENT_MODE,
    API_VERSION,
)
from app.onshape.api_switch import api_or_mock

logger = logging.getLogger(__name__)


class PartListService:
    """
    Build a Master Part List from:
      - BOM (filtered rows)
      - Parts metadata
      - Per-part bodydetails calls

    In DEV mode:
      - Parts metadata loaded from local JSON (e.g. via manifest or other mocks)
      - BodyDetails loaded from LOCAL_DATA_PATH/bodydetails/{partId}.json

    In PROD mode:
      - Parts metadata should come from real Onshape /parts endpoint (TODO)
      - BodyDetails fetched per part from:
          /api/{API_VERSION}/parts/d/{did}/{wvm}/{wvmid}/e/{eid}/partid/{partId}/bodydetails
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
        dedup_bom_by_source: List[Dict[str, Any]],  # currently unused, kept for future optimisation
    ) -> List[Dict[str, Any]]:
        """
        Build the master part list for a given BOM and configuration.

        master key = (documentId, elementId, configuration, partId)
        """

        logger.info("Building Master Part List...")

        # ---------------------------------------------------------------------
        # 1) LOAD PART METADATA
        # ---------------------------------------------------------------------
        parts_meta = PartListService._fetch_parts_metadata()
        meta_lookup: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for p in parts_meta:
            eid = p.get("elementId")
            pid = p.get("partId")
            if eid and pid:
                meta_lookup[(eid, pid)] = p

        # ---------------------------------------------------------------------
        # 2) PRECOMPUTE SHEET-METAL RELATIONS (UNFLATTENED <-> FLATTENED)
        # ---------------------------------------------------------------------
        unflattened_to_flattened: Dict[Tuple[str, str], Tuple[str, str]] = {}
        flattened_flags: Dict[Tuple[str, str], bool] = {}

        for p in parts_meta:
            eid = p.get("elementId")
            pid = p.get("partId")
            if not eid or not pid:
                continue

            key = (eid, pid)
            is_flat = bool(p.get("isFlattenedBody"))
            flattened_flags[key] = is_flat

            unflat_id = p.get("unflattenedPartId")
            if unflat_id:
                # p is flattened; unflat_id is the folded/real partId
                unflattened_to_flattened[(eid, unflat_id)] = (eid, pid)

        # ---------------------------------------------------------------------
        # 3) BUILD QUANTITIES + CONTEXT (INCL. WVM INFO FOR BODYDETAILS CALLS)
        # ---------------------------------------------------------------------
        # master key: (documentId, elementId, configuration, partId)
        quantity_by_key: Dict[Tuple[str, str, str, str], float] = {}
        context_by_key: Dict[
            Tuple[str, str, str, str], Tuple[str, str, str]
        ] = {}  # key -> (wvmType, wvmId, did)

        quantity_header_id = get_quantity_header_id(bom_dict)
        if not quantity_header_id:
            quantity_header_id = PartListService._infer_quantity_header_from_rows(
                filtered_bom_rows
            )

        if not quantity_header_id:
            logger.warning(
                "Quantity header not found; defaulting to 1 per distinct part row."
            )

        for row in filtered_bom_rows:
            src = row.get("itemSource", {})
            did = src.get("documentId")
            eid = src.get("elementId")
            wvm_type = src.get("wvmType")
            wvm_id = src.get("wvmId")
            cfg = src.get("configuration")
            pid = src.get("partId")

            if not (did and eid and cfg and pid and wvm_type and wvm_id):
                logger.warning("Skipping BOM row missing identity fields: %s", row)
                continue

            key = (did, eid, cfg, pid)

            # Quantity
            if quantity_header_id:
                hv = row.get("headerIdToValue", {})
                val = hv.get(quantity_header_id, 0)
                qty = PartListService._safe_numeric(val)
                if qty <= 0:
                    qty = 1
            else:
                qty = 1

            quantity_by_key[key] = quantity_by_key.get(key, 0) + qty

            # Context (used for per-part bodydetails)
            if key not in context_by_key:
                context_by_key[key] = (wvm_type, wvm_id, did)

        # ---------------------------------------------------------------------
        # 4) PREPARE BODYDETAILS CACHE (PER PART)
        # ---------------------------------------------------------------------
        bodydetails_cache: Dict[
            Tuple[str, str, str, str, str, str], Dict[str, Any]
        ] = {}
        # key = (did, eid, wvmType, wvmId, configuration, partId_for_bodydetails)

        # ---------------------------------------------------------------------
        # 5) BUILD MASTER LIST ENTRIES
        # ---------------------------------------------------------------------
        master_list: List[Dict[str, Any]] = []

        for (did, eid, cfg, pid), qty in quantity_by_key.items():
            ctx = context_by_key.get((did, eid, cfg, pid))
            if not ctx:
                logger.warning(
                    "Missing context (wvmType/wvmId) for key %s; skipping.", (did, eid, cfg, pid)
                )
                continue

            wvm_type, wvm_id, _ = ctx

            meta = meta_lookup.get((eid, pid), {})
            body_type = meta.get("bodyType")
            is_mesh = meta.get("isMesh")

            # --- Skip composites (per your spec) ---
            if body_type == "composite":
                logger.warning(
                    "Skipping composite part %s / %s / %s – bodyType=composite",
                    eid, pid, cfg,
                )
                continue

            # --- Skip mesh/non-solid ---
            if is_mesh is True or (body_type and body_type != "solid"):
                logger.warning(
                    "Skipping non-solid/mesh part %s / %s / %s – bodyType=%s, isMesh=%s",
                    eid, pid, cfg, body_type, is_mesh
                )
                continue

            # ---------------- SHEET METAL DETECTION + FLATTENED MAPPING ----------------
            sheet_metal = False
            sheet_role = None
            sheet_id = None  # flattenedPartId if applicable

            # Unflattened → flattened mapping from metadata
            if (eid, pid) in unflattened_to_flattened:
                sheet_metal = True
                sheet_role = "unflattened"
                sheet_id = unflattened_to_flattened[(eid, pid)][1]

            elif flattened_flags.get((eid, pid), False) or meta.get("unflattenedPartId"):
                # This is a flattened part
                sheet_metal = True
                sheet_role = "flattened"
                sheet_id = pid

            # ---------------- BODYDETAILS PER PART (KEY CHANGE) ----------------
            # For sheet metal unflattened parts, we want the bodydetails for the
            # FLATTENED part (sheet_id). Otherwise, use its own partId.
            if sheet_metal and sheet_role == "unflattened" and sheet_id:
                partid_for_bodydetails = sheet_id
            else:
                partid_for_bodydetails = pid

            bd_key = (did, eid, wvm_type, wvm_id, cfg, partid_for_bodydetails)
            bodydetails: Dict[str, Any] = {}

            if bd_key in bodydetails_cache:
                bodydetails = bodydetails_cache[bd_key]
            else:
                bodydetails = PartListService._fetch_bodydetails_for_part(
                    did=did,
                    wvm_type=wvm_type,
                    wvm_id=wvm_id,
                    eid=eid,
                    configuration=cfg,
                    part_id=partid_for_bodydetails,
                )
                bodydetails_cache[bd_key] = bodydetails

            if not bodydetails:
                logger.warning(
                    "No bodydetails for %s / %s / %s / %s – continuing without geometry.",
                    did, eid, cfg, partid_for_bodydetails
                )

            # ---------------- MASTER ENTRY ASSEMBLY ----------------
            entry: Dict[str, Any] = {
                "documentId": did,
                "elementId": eid,
                "configuration": cfg,
                "partId": pid,
                "quantity": qty,

                # Metadata
                "name": meta.get("name"),
                "partNumber": meta.get("partNumber"),
                "bodyType": body_type,
                "isMesh": is_mesh,

                # Sheet metal flags
                "sheetMetal": sheet_metal,
                "sheetMetalRole": sheet_role,    # 'unflattened' or 'flattened' or None
                "sheetMetalId": sheet_id,        # flattened partId (if any)

                # Per-part bodydetails (for geometry checks)
                # If sheet metal & unflattened, this is the FLATTENED part's bodydetails.
                "bodyDetails": bodydetails,
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

        best = max(sums.items(), key=lambda kv: kv[1])[0]
        return best

    # -------------------------------------------------------------------------
    # PARTS METADATA LOADING
    # -------------------------------------------------------------------------
    @staticmethod
    def _fetch_parts_metadata() -> List[Dict[str, Any]]:
        """
        DEV MODE:
          - Load parts metadata from local mocks.
            (You can keep your existing manifest logic or adapt this.)

        PROD MODE:
          - TODO: Call Onshape /parts API for each deduped PartStudio.
        """
        if not DEVELOPMENT_MODE:
            # TODO: Real Onshape /parts calls should go here.
            logger.info("PRODUCTION mode: _fetch_parts_metadata not yet implemented.")
            return []

        # For now, expect a manifest listing part metadata files, as discussed earlier.
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
                            "Parts file %s did not contain a JSON list; skipping.",
                            filename,
                        )
            except Exception as e:
                logger.error("Failed to load parts file %s: %s", filename, e)

        logger.info("Loaded %d part metadata entries from local files.", len(all_parts))
        return all_parts

    # -------------------------------------------------------------------------
    # BODYDETAILS PER PART
    # -------------------------------------------------------------------------
    @staticmethod
    def _fetch_bodydetails_for_part(
        did: str,
        wvm_type: str,
        wvm_id: str,
        eid: str,
        configuration: str,
        part_id: str,
    ) -> Dict[str, Any]:
        """
        Fetch bodydetails for a single part.

        DEV MODE:
          - Load from LOCAL_DATA_PATH/bodydetails/{partId}.json

        PROD MODE:
          - GET /api/{API_VERSION}/parts/d/{did}/{wvm_type}/{wvm_id}/e/{eid}/partid/{partId}/bodydetails
            with ?configuration={configuration}
        """
        if DEVELOPMENT_MODE:
            # Local JSON mocks
            bodydetails_dir = os.path.join(LOCAL_DATA_PATH, "bodydetails")
            filename = f"{part_id}.json"
            full_path = os.path.join(bodydetails_dir, filename)

            if not os.path.exists(full_path):
                logger.warning(
                    "Dev bodydetails file not found for partId=%s at %s",
                    part_id,
                    full_path,
                )
                return {}

            try:
                with open(full_path, "r") as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                logger.error(
                    "Failed to load dev bodydetails file %s: %s", full_path, e
                )
                return {}

        # --- PRODUCTION MODE: Call Onshape API ---
        path = (
            f"/api/{API_VERSION}/parts/d/"
            f"{did}/{wvm_type}/{wvm_id}/e/{eid}/partid/{part_id}/bodydetails"
        )

        query = {}
        if configuration:
            query["configuration"] = configuration

        try:
            bodydetails = api_or_mock(
                mock_filename=None,
                method="GET",
                path=path,
                query=query,
            )
            return bodydetails or {}
        except Exception as e:
            logger.error(
                "Error fetching bodydetails from Onshape for partId=%s: %s",
                part_id,
                e,
            )
            return {}
