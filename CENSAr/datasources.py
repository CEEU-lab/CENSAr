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
def radios_corrientes(year, root=carto_dir, mask=None):
    path = f"{root}radios_{year}_corrientes.zip"
    radios = gpd.read_file(path)

    if mask is not None:
        if mask.crs != radios.crs:
            mask = mask.to_crs(radios.crs)
        radios = radios.clip(mask)
        
    return radios

@st.cache_data
def tipoviv_radios_corrientes(year, var_types, root=data_dir):
    path = f"{root}tipo_vivienda_radios_corrientes_{year}.csv"
    tipoviv_radio = pd.read_csv(path, var_types)
    return tipoviv_radio

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

