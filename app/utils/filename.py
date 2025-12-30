# app/utils/filename.py

import re

_ALLOWED = set("().-%")  # explicitly *not* including "_"

def sanitize_token(value: str) -> str:
    """
    Make a token safe for filenames AND safe for underscore-delimited parsing.
    - Replaces whitespace and invalid chars with '-'
    - Removes underscores entirely (since '_' is your delimiter)
    - Collapses repeated '-'
    """
    if value is None:
        return ""

    s = str(value).strip()

    out = []
    for ch in s:
        if ch == "_":
            # underscore is reserved delimiter, remove it entirely
            continue
        if ch.isalnum() or ch in _ALLOWED:
            out.append(ch)
        elif ch.isspace():
            out.append("-")
        else:
            out.append("-")

    cleaned = "".join(out)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned
