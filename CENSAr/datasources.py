import streamlit as st
import geopandas as gpd
import pandas as pd

@st.cache(allow_output_mutation=True)
def caba_neighborhood_limits():
    gdf = gpd.read_file('data/caba_barrios.zip')
    return gdf

@st.cache(allow_output_mutation=True)
def caba_comunas_limits():
    gdf = gpd.read_file('data/caba_comunas.zip')
    return gdf

@st.cache(allow_output_mutation=True)
def radios_gba24_2010():
    radios = gpd.read_file('data/radios_2010_gba24.zip')
    return radios

@st.cache(allow_output_mutation=True)
def radios_caba_2010():
    radios = gpd.read_file('data/radios_2010_caba.zip')
    return radios

@st.cache(allow_output_mutation=True)
def inmat_radios_gba24_2010():
    inmat_por_radio = pd.read_csv('data/inmat_gba24.csv')
    return inmat_por_radio

@st.cache(allow_output_mutation=True)
def inmat_radios_caba_2010():
    inmat_por_radio = pd.read_csv('data/inmat_caba.csv')
    return inmat_por_radio