import pandas as pd
import geopandas as gpd
from shapely import wkt

def from_wkt(df, wkt_column, crs=4326):
    '''
    Crea un geodataframe a partir de una columna de geometria de tipo object/string
    '''
    
    df["geometry"]= df[wkt_column].apply(wkt.loads) 
    gdf = gpd.GeoDataFrame(df, geometry='geometry',crs=crs) 
    
    return gdf

def from_coarser_to_thiner_area(coarser_geom, thiner_geom,coarser_idx, thiner_idx):

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