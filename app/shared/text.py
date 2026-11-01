def initials_of(name: str) -> str:
    parts = [p for p in name.replace(".", " ").split() if p.lower() != "dr"]
    return "".join(p[0] for p in parts[:2]).upper() or "U"
