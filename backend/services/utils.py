import re


def sanitise_collection_name(name: str) -> str:
    """Convert any user-facing subject name to a valid ChromaDB collection name."""
    sanitised = re.sub(r'[^a-zA-Z0-9._-]', '-', name.strip())
    sanitised = re.sub(r'-+', '-', sanitised)
    sanitised = sanitised.strip('-')
    if len(sanitised) < 3:
        sanitised = sanitised + '-01'
    return sanitised[:512]
