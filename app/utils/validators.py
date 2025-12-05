# app/utils/validators.py

def validate_url_not_empty(url: str) -> None:
    if not url or not url.strip():
        raise ValueError("URL must not be empty.")
