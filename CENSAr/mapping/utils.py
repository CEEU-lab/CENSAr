from pathlib import Path

import srsly
from pydantic import BaseModel


# validate the mapping format
class Mapping(BaseModel):
    """Mapping categories for CENSAr data"""

    type: str
    mapping: dict[str, str | list[str]]
    source_column: str | None = None


def load_mapping(path: str | Path) -> dict[str, Mapping]:
    """
    Load a mapping from a yaml file.
    """
    with open(path, "r") as f:
        mapping = srsly.yaml_loads(f.read())

    return {key: Mapping(**value).dict() for key, value in mapping.items()}  # type: ignore
