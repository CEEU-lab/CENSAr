import re
from glob import glob
from pathlib import Path

import pandas as pd
import geopandas as gpd

from CENSAr.logging import get_logger

from .utils import Mapping, NamedAggregator, load_aggregation

logger = get_logger(__name__)

PARENT_DIR = Path(__file__).parent


HOGARES = load_aggregation(PARENT_DIR / "hogares.yaml")
VIVIENDAS = load_aggregation(PARENT_DIR / "viviendas.yaml")

ALL = {}
for path in glob(str(PARENT_DIR / "*.yaml")):
    aggregations = load_aggregation(path)
    if set(aggregations.keys()) & set(ALL.keys()):
        logger.warning(
            f"Overwriting aggregations keys: {set(aggregations.keys()) & set(ALL.keys())}"
        )
    ALL.update(aggregations)


def list_named_aggregations() -> list[str]:
    """
    List all available named aggregations.
    """
    return list(ALL.keys())


def named_aggregation(
    data: pd.DataFrame | gpd.GeoDataFrame,
    name: str,
) -> pd.DataFrame | gpd.GeoDataFrame:
    """
    Apply a named aggregation to a dataset.

    Parameters
    ----------
    data : pd.DataFrame | gpd.GeoDataFrame
        Data to be aggregated.
    name : str
        Name of the aggregation to be applied.

    Returns
    -------
    pd.DataFrame | gpd.GeoDataFrame
        Aggregated data.

    Raises
    ------
    ValueError
        If the named aggregation is not found.
    """
    data = data.copy()
    aggregation = ALL.get(name)
    if not aggregation:
        logger.error(f"Named aggregation `{name}` not found in {ALL.keys()}")
        raise ValueError(f"Named aggregation `{name}` not found in {ALL.keys()}")

    logger.info(f"Applying named aggregation `{name}`")
    data = aggregate(data, aggregation.mapping)
    return data


def aggregate(
    data: gpd.GeoDataFrame | pd.DataFrame,
    schema: list[Mapping],
    errors: str = "skip",
) -> gpd.GeoDataFrame | pd.DataFrame:
    """
    Aggregate data according to a schema.

    Parameters
    ----------
    data : gpd.GeoDataFrame | pd.DataFrame
        Data to be aggregated.
    schema : list[Mapping]
        Schema to be used for aggregation.
    aggregator : str | Callable[..., pd.Series | gpd.GeoSeries], optional
        Aggregation function to be used, by default "sum".
    errors : str, optional
        How to handle errors, by default "skip".
        could be:
            - "raise": raise an error
            - "skip": skip the column

    Returns
    -------
    gpd.GeoDataFrame | pd.DataFrame
        Aggregated data.

    Raises
    ------
    ValueError
        If no columns are found for a mapping.
    """

    data = data.copy()

    original_columns = data.columns
    for mapping in schema:
        mapping = Mapping(**mapping) if isinstance(mapping, dict) else mapping
        columns = mapping.columns
        if mapping.regex:
            for pattern in mapping.regex:
                columns += list(filter(re.compile(pattern).match, data.columns))

        if not columns:
            raise ValueError(f"No columns found for mapping {mapping.name}")

        if extra_columns := set(columns) - set(original_columns):
            msg = f"Extra columns found for mapping {mapping.name}: {extra_columns}"
            if errors == "raise":
                raise ValueError(msg)
            elif errors == "skip":
                logger.warning(f"{msg}. Extra columns will be ignored.")
                columns = list(set(columns) - extra_columns)

        data[mapping.name] = data[columns].aggregate(mapping.aggregator, axis=1)
        data.drop(columns, axis=1, inplace=True)

    return data


def stats(
    data: gpd.GeoDataFrame | pd.DataFrame,
    columns: list[str],
) -> dict[str, gpd.GeoDataFrame | pd.DataFrame]:
    """
    Calculate descriptive statistics for a dataset.

    Parameters
    ----------
    data : gpd.GeoDataFrame | pd.DataFrame
        Data to be used for statistics.
    columns : list[str]
        Columns to be used for statistics.

    Returns
    -------
    dict[str, gpd.GeoDataFrame | pd.DataFrame]
        dict with the following keys:
            - df_tot: original data
            - df_pct: percentage over total
    """
    data = data.copy()
    total = data[columns].sum(axis=1)
    data["total"] = total

    return {
        "df_tot": data,
        "df_pct": data[columns] / total * 100,
    }
