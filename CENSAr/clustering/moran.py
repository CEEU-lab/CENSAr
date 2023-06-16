import geopandas as gpd
from esda.moran import Moran
from esda.moran import Moran_Local

from CENSAr.clustering.geo_utils import compute_weights

# Mapping from value to name (as a dict)
MORAN_LABELS = {
    0: "Non-Significant",
    1: "HH",
    2: "LH",
    3: "LL",
    4: "HL",
}


def lisa(
    gdf: gpd.GeoDataFrame,
    indicators: list[str],
    weights: str = "queen",
    knn_k: int = 5,
    local: bool = True
):
    """
    This function takes a geopandas GeoDataFrame with a LISA column and returns a
    geopandas GeoDataFrame with the LISA significant labels
    Parameters:
    gdf (geopandas.GeoDataFrame):
        GeoDataFrame with geometries
    indicators (list[str]):
        List of indicators to compute LISA for
    weights (str):
        Spatial weights type. Default: "queen"
    knn_k (int):
        Number of neighbors for KNN weights. Default: 5
    local (bool). Default: True
        Wether to return local or global Moran

    Returns:
    geopandas.GeoDataFrame : GeoDataFrame with the LISA significant labels
    """
    w = compute_weights(gdf, weights=weights, knn_k=knn_k)
    
    if local:
        return [Moran_Local(gdf[indicator], w) for indicator in indicators]
    else:
        # global
        return [Moran(gdf[indicator].values, w) for indicator in indicators]
