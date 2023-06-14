import pandas as pd
import geopandas as gpd

from CENSAr.datasources import (
    personas_radios_prov,
    tipoviv_radios_prov,
    radios_prov,
    persproy_depto_2025,
)

from CENSAr.spatial_distributions.modeling_tools import (
    simulate_total_var, 
    simulate_cat_var
)

from CENSAr.spatial_distributions.geo_utils import (
    from_wkt, 
    build_thiner_pct_in_coarser_geom
)
from CENSAr.aggregation import named_aggregation

def resistencia_stquo_2020(
        path00: str, 
        path10: str, 
        path_20: str):
    """
    Loads an urban growth scenario defined for a projection year

    Parameters
    ----------
    path00 : str
        Directory route to the urban footprint vector data 
        generated with rasterdata module for 2000.
    path10 : str
        Directory route to the urban footprint vector data 
        generated with rasterdata module for 2010.
    path20 : str
        Directory route to the urban footprint vector data 
        generated with rasterdata module for 2020.

    Returns
    -------
    scenario:dict
        Aggregated indicators with 2020 simulated distributions,
        2010 and 2001 observed distributions, urban footprint vector data
        and scenario metadata.
    """
    # rasterdata_analysis outputs
    footprint_resistencia_00 = gpd.read_file(path00)
    footprint_resistencia_10 = gpd.read_file(path10)
    footprint_resistencia_20 = gpd.read_file(path_20)

    # Loads census tracts within footprint limit
    chaco_2001 = radios_prov(year=2001, prov="chaco", mask=footprint_resistencia_00)
    chaco_2010 = radios_prov(year=2010, prov="chaco", mask=footprint_resistencia_10)
    chaco_2020 = radios_prov(year=2010, prov="chaco", mask=footprint_resistencia_20)

    # Estimates total dwelling units in 2020 based on persons tables (2001 & 2010)
    tipo_2001 = tipoviv_radios_prov(
        year=2001,
        prov="chaco",
        var_types={"link": "object"},
    )
    tipo_2001_geo = chaco_2001.set_index("link").join(tipo_2001.set_index("link"))

    tipo_2010 = tipoviv_radios_prov(
        year=2010,
        prov="chaco",
        var_types={"link": "object"},
    )
    tipo_2010_geo = chaco_2010.set_index("link").join(tipo_2010.set_index("link"))

    tipo_2020 = tipoviv_radios_prov(
        year=2010,
        prov="chaco",
        var_types={"link": "object"},
    )
    tipo_2020_geo = chaco_2020.set_index("link").join(tipo_2020.set_index("link"))

    # REDATAM - Total persons 2001 & 2010
    pers_2001 = personas_radios_prov(year=2001, prov="chaco", var_types={"link": "object"})
    pers_2001_geo = chaco_2001.set_index("link").join(pers_2001.set_index("link"))
    pers_2010 = personas_radios_prov(year=2010, prov="chaco", var_types={"link": "object"})
    pers_2010_geo = chaco_2010.set_index("link").join(pers_2010.set_index("link"))

    # Projected population by department
    proy = persproy_depto_2025(prov="chaco")

    # Total dwelling units 2020
    tipo_2020_geo["total"] = simulate_total_var(
        gdf_pers_01=pers_2001_geo,
        gdf_var_01=tipo_2001_geo,
        gdf_pers_10=pers_2010_geo,
        gdf_var_10=tipo_2010_geo,
        proy_df=proy,
        namedept="San Fernando",
        base_year="2010",
        forecast_year="2020",
        catname="total",
    )

    # Aggregations
    tipo_vivienda_agg_2001 = named_aggregation(
        tipo_2001_geo, name="tipo vivienda particular"
    )
    tipo_vivienda_agg_2010 = named_aggregation(
        tipo_2010_geo, name="tipo vivienda particular"
    )
    tipo_vivienda_agg_2020 = named_aggregation(
        tipo_2020_geo, name="tipo vivienda particular"
    )

    # Calibration vector (informal settlements surface)
    url = "https://storage.googleapis.com/python_mdg/censar_data/informal_settlements_072022.csv"
    inf_settl = pd.read_csv(url)
    inf_settl_gdf = from_wkt(df=inf_settl, wkt_column='geometry')

    tipo_2020_reset = tipo_2020_geo.reset_index()
    calibration_weights = build_thiner_pct_in_coarser_geom(
        coarser_geom=tipo_2020_reset, 
        thiner_geom=inf_settl_gdf,
        coarser_idx='link', 
        thiner_idx='id_renabap', 
        crs=5347, 
        coarser_tot=False
    )

    # Scenario main definition
    # 1. Combines aggregated indicators distributions observed by tract in 2001-2010 
    # 2. Percentage of informal settlement land within the tract (respecting the total informal area)
    # 3. Porcentaje of housing informality in the city (3.5%) 
    informal_simulated_distribution = simulate_cat_var(
        gdf_var_01=tipo_vivienda_agg_2001,
        gdf_var_10=tipo_vivienda_agg_2020,
        base_year="0110",
        forecast_year="2020",
        forecast_gdf=tipo_vivienda_agg_2020,
        pct_val=3.5,
        catname={"2001": "informal", "2010": "informal"},
        tot_colname="total",
        calibration_vector={'weights':calibration_weights, 'mix_dist':True}
    )

    tipo_vivienda_agg_2020["cat_sim"] = tipo_vivienda_agg_2020.index.map(informal_simulated_distribution)
    tipo_vivienda_agg_2020["informal_2020"] = tipo_vivienda_agg_2020["informal"] + tipo_vivienda_agg_2020["cat_sim"]

    tipo_vivienda_agg_2020.drop(columns=['formal','informal','cat_sim'], inplace=True)
    tipo_vivienda_agg_2020.rename(columns={'informal_2020':'informal'}, inplace=True)
    tipo_vivienda_agg_2020['formal'] = tipo_vivienda_agg_2020['total'] - tipo_vivienda_agg_2020['informal'] - tipo_vivienda_agg_2020['situacion de calle']

    scenario = {2001:tipo_vivienda_agg_2001, 
                2010:tipo_vivienda_agg_2010, 
                2020:tipo_vivienda_agg_2020,
                'footpr01':footprint_resistencia_00,
                'footpr10':footprint_resistencia_10,
                'footpr20':footprint_resistencia_20,
                'agg':True,
                'calibration':True,
                'pct_val':3.5}
    return scenario