import os
import unicodedata

import pandas as pd
import geopandas as gpd

from CENSAr.logging import get_logger

logger = get_logger(__name__)


DATA_DIR = os.getenv(
    "CENSAR_DATA_DIR",
    "https://storage.googleapis.com/python_mdg/censar_data",
)
CARTO_DIR = os.getenv(
    "CENSAR_CARTO_DIR",
    "https://storage.googleapis.com/python_mdg/censar_carto",
)


def text_normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    return text


def caba_neighborhood_limits(root=CARTO_DIR):
    logger.info("retriving CABA neighborhood")
    path = f"{root}/caba_barrios.zip"
    return gpd.read_file(path)


def caba_comunas_limits(root=CARTO_DIR):
    path = f"{root}/caba_comunas.zip"
    return gpd.read_file(path)


def radios_gba24_2010(root=CARTO_DIR):
    path = f"{root}/radios_2010_gba24.zip"
    return gpd.read_file(path)


def radios_caba_2010(root=CARTO_DIR):
    path = f"{root}/radios_2010_caba.zip"
    return gpd.read_file(path)


def radios_prov(year, prov, root=CARTO_DIR, mask=None):
    path = f"{root}/radios_{year}_{prov}.zip"
    radios = gpd.read_file(path)

    if mask is not None:
        if mask.crs != radios.crs:
            mask = mask.to_crs(radios.crs)
        radios = radios.clip(mask)

    return radios


def radios_precenso_2020(root=CARTO_DIR, geo_filter=None, mask=None):
    """
    geo_filter (dict): nomprov + nomdepto (e.g. {'prov':'18', 'depto':'021'})
    mask (Polygon): shapely's polygon geometry
    """
    path = f"{root}/radios_precenso_2020.zip"
    radios = gpd.read_file(path)

    # 1. Filtra radios dentro del departamento
    if geo_filter is not None:
        radios = radios.loc[
            (radios["prov"] == geo_filter["prov"])
            & (radios["depto"] == geo_filter["depto"])
        ].copy()

    # 2. Selección de radios por envolvente o mancha
    if mask is not None:
        if mask.crs != radios.crs:
            mask = mask.to_crs(radios.crs)
        radios = radios.clip(mask)

    # 3. Columnas legibles
    radios.rename(
        columns={
            "ind01": "total_viviendas",
            "ind05": "viviendas_tipo_casa",
            "ind06": "viviendas_tipo_depto",
            "ind07": "depto_alt_monob",
        },
        inplace=True,
    )

    radios["total_viviendas"] = radios["total_viviendas"].astype(int)
    radios["viviendas_tipo_casa"] = radios["viviendas_tipo_casa"].astype(float)
    radios["viviendas_tipo_depto"] = radios["viviendas_tipo_depto"].astype(float)
    radios["depto_alt_monob"] = radios["depto_alt_monob"].astype(float)
    return radios


def radios_eph_censo_2010(aglo_idx, root=CARTO_DIR):
    path = f"{root}/radios_eph_json.zip"
    logger.info(path)
    mask = gpd.read_file(path)
    mask_wgs = mask[mask["eph_codagl"].isin([aglo_idx])].copy().to_crs(4326)
    mask_wgs["cons"] = 0
    return mask_wgs.dissolve(by="cons")


def tipoviv_radios_prov(year, prov, var_types, root=DATA_DIR):
    path = f"{root}/tipo_vivienda_radios_{prov}_{year}.csv"
    logger.info(f"loading `{path}`")
    tipoviv_radio = pd.read_csv(path, dtype=var_types)
    tipoviv_radio.columns = [text_normalize(c) for c in tipoviv_radio.columns]
    return tipoviv_radio


def regtenviv_radios_prov(year, prov, var_types, root=DATA_DIR):
    path = f"{root}/reg_tenencia_viv_radios_{prov}_{year}.csv"
    regtenviv_radio = pd.read_csv(path, dtype=var_types)
    regtenviv_radio.columns = [text_normalize(c) for c in regtenviv_radio.columns]
    return regtenviv_radio


def desagueinod_radios_prov(year, prov, var_types, root=DATA_DIR):
    path = f"{root}/desagueinod_radios_{prov}_{year}.csv"
    desagueinod_radio = pd.read_csv(path, dtype=var_types)
    desagueinod_radio.columns = [text_normalize(c) for c in desagueinod_radio.columns]
    return desagueinod_radio


def personas_radios_prov(year, prov, var_types, root=DATA_DIR):
    path = f"{root}/personas_radios_{prov}_{year}.csv"
    logger.info(f"loading `{path}`")
    personas_radio = pd.read_csv(path, dtype=var_types)
    personas_radio.columns = [text_normalize(c) for c in personas_radio.columns]
    return personas_radio


def servurban_radios_prov(prov, var_types, root=DATA_DIR):
    path = f"{root}/servurbanos_radios_{prov}_2001.csv"
    servurban_radio = pd.read_csv(path, dtype=var_types)
    servurban_radio.columns = [text_normalize(c) for c in servurban_radio.columns]
    return servurban_radio


def inmat_radios_gba24_2010(root=DATA_DIR):
    path = f"{root}/inmat_gba24.csv"
    return pd.read_csv(path)


def inmat_radios_caba_2010(root=DATA_DIR):
    path = f"{root}/inmat_caba.csv"
    return pd.read_csv(path)


def tracts_matching_0110(prov, var_types, root=DATA_DIR):
    filename = f"{prov}_tracts_pairing_0110.csv"
    path = os.path.join(root, filename)
    logger.info(f"loadding `{path}`")

    return pd.read_csv(path, dtype=var_types)


def persproy_depto_2025(prov, root=DATA_DIR):
    filename = f"persproyect_depto_{prov}.csv"
    path = os.path.join(root, filename)
    logger.info(f"loading, `{path}`")
    return pd.read_csv(path, index_col="Departamento")
