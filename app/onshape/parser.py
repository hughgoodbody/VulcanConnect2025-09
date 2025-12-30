# app/onshape/parser.py

from urllib.parse import urlparse
from typing import Tuple


def parse_url(doc_url: str) -> Tuple[str, str, str, str]:
    """
    Parse an Onshape document URL into:
        did, wvm_type, wvm_id, eid

    Valid formats include:
    - https://cad.onshape.com/documents/{did}/w/{wid}/e/{eid}
    - https://cad.onshape.com/documents/{did}/v/{vid}/e/{eid}
    - https://cad.onshape.com/documents/{did}/m/{mid}/e/{eid}
    - ... with or without trailing slashes or query params.

    Raises ValueError on malformed URLs.
    """

    parsed = urlparse(doc_url)
    segments = [seg for seg in parsed.path.split("/") if seg]

    # Expecting: documents / did / (w|v|m) / wvmId / e / eid
    try:
        doc_index = segments.index("documents")
    except ValueError:
        raise ValueError(f"Invalid Onshape URL — missing 'documents': {doc_url}")

    try:
        did = segments[doc_index + 1]
        wvm_type = segments[doc_index + 2]     # "w" | "v" | "m"
        wvm_id = segments[doc_index + 3]

        if segments[doc_index + 4] != "e":
            raise ValueError(f"Invalid Onshape URL — expected /e/<eid>: {doc_url}")

        eid = segments[doc_index + 5]

    except IndexError:
        raise ValueError(f"Malformed Onshape URL — missing segments: {doc_url}")

    return did, wvm_type, wvm_id, eid
