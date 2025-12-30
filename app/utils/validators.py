# app/utils/validators.py

def ensure_url(url: str):
    """Validate that a URL is provided."""
    if not url or not url.strip():
        raise ValueError("Onshape URL is required.")
    return url


def ensure_dict(value, name="payload"):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a dictionary.")
    return value
