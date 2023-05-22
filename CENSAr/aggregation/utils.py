from enum import Enum
from pathlib import Path

import srsly
from pydantic import BaseModel


class Mapping(BaseModel):
    name: str
    aggregator: str = "sum"
    regex: list[str] = []
    columns: list[str] = []


class NamedAggregator(BaseModel):
    mapping: list[Mapping]


def load_aggregation(path: str | Path) -> dict[str, Mapping]:
    """
    Load aggregations from a yaml file.
    """
    with open(path, "r") as f:
        aggregations = srsly.yaml_loads(f.read())

    return {key: NamedAggregator(**value) for key, value in aggregations.items()}  # type: ignore
