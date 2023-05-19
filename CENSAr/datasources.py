import streamlit as st
import geopandas as gpd
import pandas as pd

data_dir = 'https://storage.googleapis.com/python_mdg/censar_data/'
carto_dir = 'https://storage.googleapis.com/python_mdg/censar_carto/'

@st.cache_data
def caba_neighborhood_limits(root=carto_dir):
    path = f"{root}caba_barrios.zip"
    gdf = gpd.read_file(path)
    return gdf

@st.cache_data
def caba_comunas_limits(root=carto_dir):
    path = f"{root}caba_comunas.zip"
    gdf = gpd.read_file(path)
    return gdf

@st.cache_data
def radios_gba24_2010(root=carto_dir):
    path = f"{root}radios_2010_gba24.zip"
    radios = gpd.read_file(path)
    return radios

@st.cache_data
def radios_caba_2010(root=carto_dir):
    path = f"{root}radios_2010_caba.zip"
    radios = gpd.read_file(path)
    return radios

@st.cache_data
def radios_prov(year, prov, root=carto_dir, mask=None):
    path = f"{root}radios_{year}_{prov}.zip"
    radios = gpd.read_file(path)

    if mask is not None:
        if mask.crs != radios.crs:
            mask = mask.to_crs(radios.crs)
        radios = radios.clip(mask)
        
    return radios

@st.cache_data
def radios_precenso_2020(root, geo_filter=None, mask=None):
    """
    geo_filter (dict): nomprov + nomdepto (e.g. {'prov':'18', 'depto':'021'})
    mask (Polygon): shapely's polygon geometry
    """
    path = f"{root}radios_precenso_2020.zip"
    radios = gpd.read_file(path)
    
    #1. Filtra radios dentro del departamento
    if geo_filter is not None:
      radios = radios.loc[(radios['prov']==geo_filter['prov']) &
                           (radios['depto']==geo_filter['depto'])].copy()

    #2. Selección de radios por envolvente o mancha
    if mask is not None:
        if mask.crs != radios.crs:
            mask = mask.to_crs(radios.crs)
        radios = radios.clip(mask)
    
    #3. Columnas legibles
    radios.rename(columns={'ind01':'total_viviendas', 
                           'ind05':'viviendas_tipo_casa', 
                           'ind06':'viviendas_tipo_depto', 
                           'ind07':'depto_alt_monob'}, inplace=True)
    
    radios['total_viviendas'] = radios['total_viviendas'].astype(int)
    radios['viviendas_tipo_casa'] = radios['viviendas_tipo_casa'].astype(float)
    radios['viviendas_tipo_depto'] = radios['viviendas_tipo_depto'].astype(float)
    radios['depto_alt_monob'] = radios['depto_alt_monob'].astype(float)
    return radios

@st.cache_data
def tipoviv_radios_prov(year, prov, var_types, root=data_dir):
    path = f"{root}tipo_vivienda_radios_{prov}_{year}.csv"
    tipoviv_radio = pd.read_csv(path, dtype=var_types)
    tipoviv_radio.columns= tipoviv_radio.columns.str.lower()
    return tipoviv_radio

@st.cache_data
def regtenviv_radios_prov(year, prov, var_types, root=data_dir):
    path = f"{root}reg_tenencia_viv_radios_{prov}_{year}.csv"
    regtenviv_radio = pd.read_csv(path, dtype=var_types)
    regtenviv_radio.columns= regtenviv_radio.columns.str.lower()
    return regtenviv_radio

@st.cache_data
def desagueinod_radios_prov(year, prov, var_types, root=data_dir):
    path = f"{root}desagueinod_radios_{prov}_{year}.csv"
    desagueinod_radio = pd.read_csv(path, dtype=var_types)
    desagueinod_radio.columns= desagueinod_radio.columns.str.lower()
    return desagueinod_radio

@st.cache_data
def personas_radios_prov(year, prov, var_types, root=data_dir):
    path = f"{root}personas_radios_{prov}_{year}.csv"
    personas_radio = pd.read_csv(path, dtype=var_types)
    personas_radio.columns= personas_radio.columns.str.lower()
    return personas_radio

@st.cache_data
def inmat_radios_gba24_2010(root=data_dir):
    path = f"{root}inmat_gba24.csv"
    inmat_por_radio = pd.read_csv(path)
    return inmat_por_radio

@st.cache_data
def inmat_radios_caba_2010(root=data_dir):
    path = f"{root}inmat_caba.csv"
    inmat_por_radio = pd.read_csv(path)
    return inmat_por_radio

@st.cache_data
def tracts_matching_0110(prov, var_types,root=data_dir):
    path = f"{root}{prov}_conversion_010.csv"
    conversion_radios = pd.read_csv(path, dtype=var_types)
    return conversion_radios

@st.cache_data
def persproy_depto_2025(prov, root=data_dir):
    path = f"{root}persproyect_depto_{prov}.csv"
    proyecciones_pobl = pd.read_csv(path, index_col='Departamento')
    return proyecciones_pobl