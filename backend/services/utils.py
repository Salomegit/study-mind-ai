import re
from hashlib import sha256


def sanitise_collection_name(name: str) -> str:
    """Convert any user-facing subject name to a valid ChromaDB collection name."""
    sanitised = re.sub(r'[^a-zA-Z0-9._-]', '-', name.strip())
    sanitised = re.sub(r'-+', '-', sanitised)
    sanitised = sanitised.strip('-')
    if len(sanitised) < 3:
        sanitised = sanitised + '-01'
    return sanitised[:512]


def user_collection_prefix(user_id: str) -> str:
    """Return a stable, opaque ChromaDB prefix for one authenticated user."""
    return f"u{sha256(user_id.encode('utf-8')).hexdigest()[:24]}_"


def user_collection_name(user_id: str, name: str) -> str:
    """Map a logical collection name into the caller's isolated namespace."""
    clean_name = sanitise_collection_name(name).strip("._-") or "collection"
    clean_name = clean_name[:37].rstrip("._-") or "collection"
    return f"{user_collection_prefix(user_id)}{clean_name}"
