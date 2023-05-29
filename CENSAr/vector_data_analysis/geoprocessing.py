import geopandas as gpd
from shapely import wkt

def from_wkt(df, wkt_column, crs=4326):
    """
    Loads a shapely geometry from well known text column.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with wkt geometry representation.
    wkt_column : str
        Name of the wkt column.
    crs : str | int, default 4326
        Coordinate reference system.
    
    Returns
    -------
    gdf:gpd.GeoDataFrame
        Table with shapely geometry representation.
    """
    df["geometry"]= df[wkt_column].apply(wkt.loads) 
    gdf = gpd.GeoDataFrame(df, geometry='geometry',crs=crs) 
    
    return gdf

def from_coarser_to_thiner_area(coarser_geom, thiner_geom,coarser_idx, thiner_idx):
    """
    Returns the total number of households or residential units for a given
    category with his distribution by census tract.

    Parameters
    ----------
    coarser_geom : gpd.GeoDataFrame
        Geodataframe with coarser area Polygon geometries.
    thiner_geom : gpd.GeoDataFrame
        Geodataframe with thiner area Polygon geometries contained in coarser ones.
    coarser_idx : str 
        Name of the index column to identify each Polygon geometry (e.g.:"link"))
    thiner_idx : str 
        Name of the index column to identify each Polygon geometry (e.g.:"renabap_id"))

    Returns
    -------
    proportions:pd.DataFrame
        Table indicating the area overlay for thiner and coarser geometries and their respective shares.
    """

    thiner_geom['thiner_area'] = thiner_geom.geometry.area
    coarser_geom['coarser_area'] = coarser_geom.geometry.area

    ovl = gpd.overlay(coarser_geom, thiner_geom, how = "intersection", keep_geom_type=False)
    ovl['ovl_area'] = ovl.geometry.area

    proportions = ovl[[thiner_idx, coarser_idx,'thiner_area', 'coarser_area', 'ovl_area']].copy()
    proportions['thiner_share'] = proportions['ovl_area']/proportions['thiner_area']*100
    proportions['thiner_share'] = proportions['thiner_share'].round(1)
    proportions['coarser_share'] = proportions['ovl_area']/proportions['coarser_area']*100
    proportions['coarser_share'] = proportions['coarser_share'].round(1)
    
    return proportions