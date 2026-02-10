def search_in_dict(data: dict, keys: list) -> str | None:
    """Helper para buscar en un dict haciendo BFS."""
    if not isinstance(data, dict):
        return None

    queue = []
    queue.extend(data.items())
    while queue:
        key, value = queue.pop(0)
        if isinstance(value, dict):
            queue.extend(value.items())
        elif key in keys and value is not None:
            return str(value)
    return None
