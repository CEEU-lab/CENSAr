from copy import deepcopy

import libpysal
import geopandas as gpd
import h3pandas  # noqa


def geopandas_to_h3(
    gdf: gpd.GeoDataFrame,
    resolution: int = 8,
    resample: bool = True,
) -> gpd.GeoDataFrame:
    """
    This function takes a geopandas GeoDataFrame and returns a geopandas GeoDataFrame
    with the h3 index for the given resolution
    Parameters:
    gdf (geopandas.GeoDataFrame):
        GeoDataFrame with geometries
    resolution (int):
        h3 resolution level
    resample (bool):
        If True, resample the geometries to the h3 resolution

    Returns:
    geopandas.GeoDataFrame : GeoDataFrame with the hexgrid as geometries
    """
    gdf = deepcopy(gdf)
    if resample:
        return gdf.h3.polyfill_resample(resolution=resolution)
    else:
        return gdf.h3.polyfill(resolution=resolution)


def compute_weights(gdf: gpd.GeoDataFrame, weights: str = "queen", knn_k: int = 5):
    """
    This function takes a geopandas GeoDataFrame and returns a libpysal weights object
    Parameters:
    gdf (geopandas.GeoDataFrame):
        GeoDataFrame with geometries
    weights (str):
        Spatial weights type. Default: "queen"
    knn_k (int):
        Number of neighbors for KNN weights. Default: 5

    Returns:
    libpysal.weights : libpysal weights object
    """
    match weights:
        case "queen":
            w = libpysal.weights.Queen.from_dataframe(gdf)
        case "knn":
            w = libpysal.weights.KNN.from_dataframe(gdf, k=knn_k)
        case _:
            raise ValueError(f"Invalid weights type: {weights}")
    return w
