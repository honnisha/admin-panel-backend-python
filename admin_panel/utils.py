import re
from pydantic import TypeAdapter


class DeserializeAction:
    CREATE = 0
    UPDATE = 1
    TABLE_ACTION = 2


class DataclassBase:
    def model_dump(self, *args, **kwargs) -> dict:
        adapter = TypeAdapter(type(self))
        return adapter.dump_python(self, *args, **kwargs)


def humanize_field_name(name: str) -> str:
    # Convert snake_case / kebab-case / mixed tokens to Title Case with acronyms preserved
    s = name.replace("-", "_")
    parts = [p for p in s.split("_") if p]

    def cap(token: str) -> str:
        # Keep common acronyms uppercase
        if token.lower() in {"id", "ip", "url", "api", "http", "https", "h2h"}:
            return token.upper()
        # If token contains digits, capitalize first letter only (e.g. "h2h" -> "H2h")
        if re.search(r"\d", token):
            return token[:1].upper() + token[1:].lower()
        return token[:1].upper() + token[1:].lower()

    return " ".join(cap(p) for p in parts)
