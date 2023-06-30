import geopandas as gpd
from esda.moran import (
    Moran, 
    Moran_Local, 
    Moran_BV, 
    Moran_Local_BV
    )

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
    This function takes a geopandas GeoDataFrame and estimates the 
    spatial autocorrelation between the observations of the same group and their sorroundings.
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
    list : esda.Moran or esda.Moran_Local objects
    """
    w = compute_weights(gdf, weights=weights, knn_k=knn_k)
    
    if local:
        return [Moran_Local(gdf[indicator], w) for indicator in indicators]
    else:
        # global
        return [Moran(gdf[indicator].values, w) for indicator in indicators]

def lisa_bv(
    gdf: gpd.GeoDataFrame,
    target_attr: str,
    reference_attr: str,
    weights: str = "queen",
    knn_k: int = 5,
    local: bool = True,
):
    """
    This function takes a geopandas GeoDataFrame and estimates the 
    spatial autocorrelation between a group of observations and neighboors of a different group.
    Parameters:
    gdf (geopandas.GeoDataFrame):
        GeoDataFrame with geometries
    target_attr (str):
        Name of the column with observations
    reference_attr (str):
        Name of the column representing neighboors reference
    weights (str):
        Spatial weights type. Default: "queen"
    knn_k (int):
        Number of neighbors for KNN weights. Default: 5
    local (bool). Default: True:
        Wether to return local or global statistic
    

    Returns:
    esda.Moran_BV | esda.Moran_Local: bivariate spatial autocorrelation objects
    """
    w = compute_weights(gdf, weights=weights, knn_k=knn_k)
    
    if local:
        return Moran_Local_BV(gdf[target_attr], gdf[reference_attr], w)
    
    else:
        # global
        return Moran_BV(gdf[target_attr], gdf[reference_attr], w)
    