from glob import glob
from pathlib import Path
from copy import deepcopy

import pandas as pd

from CENSAr.logging import get_logger

from .utils import load_mapping

logger = get_logger(__name__)

PARENT_DIR = Path(__file__).parent


HOGARES = load_mapping(PARENT_DIR / "hogares.yaml")
VIVIENDAS = load_mapping(PARENT_DIR / "viviendas.yaml")

ALL = {}
for path in glob(str(PARENT_DIR / "*.yaml")):
    mapping = load_mapping(path)
    if set(mapping.keys()) & set(ALL.keys()):
        logger.warning(
            f"Overwriting mapping keys: {set(mapping.keys()) & set(ALL.keys())}"
        )
    ALL.update(mapping)


def category_mapping(series: pd.Series, mapping: dict) -> pd.Series:
    """
    Apply a mapping to a categorical pandas series.
    """
    series = deepcopy(series)

    mapping_ = {
        value: key for key, values in mapping["mapping"].items() for value in values
    }
    return series.apply(lambda x: mapping_.get(x))  # type: ignore


def numeric_mapping(series: pd.Series, mapping: dict) -> pd.Series:
    """
    Apply a numeric mapping to a category pandas series.
    """
    series = deepcopy(series)
    df = pd.DataFrame({"x": series})

    for key, query in mapping["mapping"].items():
        idx = df.query(query).index
        series.loc[idx] = key

    return series


def apply_mapping(series: pd.Series, mapping_key: str):
    """
    Apply a mapping to a dataframe.
    """
    series = deepcopy(series)

    if mapping_key not in ALL:
        logger.error(f"Mapping {mapping_key} not found. in {ALL.keys()}")
        raise ValueError(f"Mapping {mapping_key} not found. in {ALL.keys()}")

    match mapping_type := ALL[mapping_key]["type"]:
        case "category":
            return category_mapping(series, ALL[mapping_key])
        case "numeric":
            return numeric_mapping(series, ALL[mapping_key])
        case _:
            raise ValueError(f"Mapping type {mapping_type} not supported")
