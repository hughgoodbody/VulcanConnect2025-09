# app/onshape/parser.py

from urllib.parse import urlparse, parse_qs
from typing import Tuple


def parse_url(doc_url: str) -> Tuple[str, str, str, str]:
    """
    Parse a standard Onshape URL into (documentId, wvmType, wvmId, elementId).

    Expected formats:
      - /documents/{did}/w/{wid}/e/{eid}
      - /documents/{did}/v/{vid}/e/{eid}
      - /documents/{did}/m/{mid}/e/{eid}

    Returns:
        did, wvm_type, wvm_id, eid
    """
    parsed = urlparse(doc_url)
    segments = [seg for seg in parsed.path.split("/") if seg]

    try:
        doc_index = segments.index("documents")
    except ValueError:
        raise ValueError(f"Invalid Onshape URL (no 'documents' segment): {doc_url}")

    try:
        did = segments[doc_index + 1]
        wvm_type = segments[doc_index + 2]  # w / v / m
        wvm_id = segments[doc_index + 3]
        if segments[doc_index + 4] != "e":
            raise ValueError("Expected 'e' segment before elementId")
        eid = segments[doc_index + 5]
    except (IndexError, ValueError) as exc:
        raise ValueError(f"Invalid Onshape URL structure: {doc_url}") from exc

    return did, wvm_type, wvm_id, eid
