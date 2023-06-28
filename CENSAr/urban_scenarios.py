import pandas as pd
import geopandas as gpd
from copy import deepcopy

from CENSAr.datasources import (
    personas_radios_prov,
    tipoviv_radios_prov,
    radios_prov,
    persproy_depto_2025,
    radios_precenso_2020
)

from CENSAr.spatial_distributions.modeling_tools import (
    simulate_total_var, 
    simulate_cat_var,
    tracts_2020_to_2010,
    tracts_2010_to_2001
)

from CENSAr.spatial_distributions.geo_utils import (
    from_wkt, 
    build_thiner_pct_in_coarser_geom
)
from CENSAr.aggregation import named_aggregation

def resistencia_stquo_2020(
        path00: str, 
        path10: str, 
        path_20: str,
        control_flow: dict = {'allocation_method':'avoid_relocations'}):
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
    control_flow : dict
        Wether to allow or avoid negative values by census tract
        after simulation.

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

    # Simulation canvas
    chaco_2020.set_index('link', inplace=True)
    chaco_2020['link_2010'] = chaco_2020.index
    tipo_2020_geo = tracts_2010_to_2001(tracts_2020_gdf=chaco_2020, prov_name='chaco')

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

    # status quo: avoid dwelling units relocation
    total_2010 = dict(zip(tipo_2010_geo.index, tipo_2010_geo.total))
    tipo_2020_geo['total_2010'] = tipo_2020_geo['link_2010'].map(total_2010)
    tipo_2020_geo["diff"] = tipo_2020_geo["total"] - tipo_2020_geo["total_2010"] 
    neg_diff = tipo_2020_geo.loc[tipo_2020_geo['diff']< 0,['diff','total_2010']].copy()
    neg_diff['diff'] = neg_diff['diff'] * -1
    tipo_2020_geo.loc[tipo_2020_geo['diff']< 0,'total'] = neg_diff.sum(axis=1)

    print('Adjusted_total: {}'.format(tipo_2020_geo['total'].sum()))
    tipo_2020_geo.drop(columns=['total_2010','diff'], inplace=True)

    # Aggregations
    tipo_vivienda_agg_2001 = named_aggregation(
        tipo_2001_geo, name="tipo vivienda particular"
    )
    tipo_vivienda_agg_2010 = named_aggregation(
        tipo_2010_geo, name="tipo vivienda particular"
    )

    # Simulation canvas
    tipo_vivienda_agg_2020 = deepcopy(tipo_2020_geo[['total','link_2001','link_2010','geometry']])

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
    # 3. Porcentaje of housing informality in the city (7.3%) # avg between 2001 and 2010 
    informal_simulated_distribution = simulate_cat_var(
        gdf_var_01=tipo_vivienda_agg_2001,
        gdf_var_10=tipo_vivienda_agg_2010,
        base_year="0110",
        forecast_year="2020",
        forecast_gdf=tipo_vivienda_agg_2020.reset_index(), #BUG FIX: better handling for idx_col
        pct_val=4.55,
        catname={"2001": "informal", "2010": "informal"},
        tot_colname="total",
        calibration_vector={'weights':calibration_weights, 'mix_dist':True}
    )

    if control_flow['allocation_method'] == 'avoid_relocations':
        # It avoids looses by census tract
        tipo_vivienda_agg_2020["cat_sim"] = tipo_vivienda_agg_2020.index.map(informal_simulated_distribution)

        # TODO: Feature design
        # Avoid dwelling units relocation
        var_2010 = dict(zip(tipo_vivienda_agg_2010.index, tipo_vivienda_agg_2010.informal))
        tipo_vivienda_agg_2020['informal_2010'] = tipo_vivienda_agg_2020['link_2010'].map(var_2010)
        tipo_vivienda_agg_2020["diff"] = tipo_vivienda_agg_2020["cat_sim"] - tipo_vivienda_agg_2020["informal_2010"]
        neg_diff = tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['diff']< 0,['diff','informal_2010']].copy()
        neg_diff['diff'] = neg_diff['diff'] * -1
        tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['diff']< 0,'cat_sim'] = neg_diff.sum(axis=1)

        tipo_vivienda_agg_2020.rename(columns={'cat_sim':'informal'}, inplace=True)
        tipo_vivienda_agg_2020.drop(columns=['diff','informal_2010'], inplace=True)
    else:
        # It does not control losses by census tract
        tipo_vivienda_agg_2020["informal"] = tipo_vivienda_agg_2020.index.map(informal_simulated_distribution)
    
    # TODO: Feature design
    # Use upper limits to avoid exceding total when reproducing observed distributions
    fix_total = tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['informal']>tipo_vivienda_agg_2020['total'], 'total']
    tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['informal']>tipo_vivienda_agg_2020['total'], 'informal'] = fix_total
    
    # TODO: Feature design
    # Simulate more than one category controlling total number of units in the area
    tipo_vivienda_agg_2020['formal'] = tipo_vivienda_agg_2020['total'] - tipo_vivienda_agg_2020['informal'] 

    scenario = {2001:tipo_vivienda_agg_2001, 
                2010:tipo_vivienda_agg_2010, 
                2020:tipo_vivienda_agg_2020,
                'footpr01':footprint_resistencia_00,
                'footpr10':footprint_resistencia_10,
                'footpr20':footprint_resistencia_20,
                'agg':True,
                'calibration':True,
                'pct_val':4.55}
    return scenario

def corrientes_stquo_2020(
        path00: str, 
        path10: str, 
        path_20: str,
        control_flow: dict = {'allocation_method':'avoid_relocations'}):
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
    control_flow : dict
        Wether to allow or avoid negative values by census tract
        after simulation.

    Returns
    -------
    scenario:dict
        Aggregated indicators with 2020 simulated distributions,
        2010 and 2001 observed distributions, urban footprint vector data
        and scenario metadata.
    """
    # rasterdata_analysis outputs
    footprint_corrientes_00 = gpd.read_file(path00)
    footprint_corrientes_10 = gpd.read_file(path10)
    footprint_corrientes_20 = gpd.read_file(path_20)

    # Loads census tracts within footprint limit
    corrientes_2001 = radios_prov(year=2001, prov="corrientes", mask=footprint_corrientes_00)
    corrientes_2010 = radios_prov(year=2010, prov="corrientes", mask=footprint_corrientes_10)
    corrientes_2020 = radios_precenso_2020(geo_filter=None, mask=footprint_corrientes_20)

    tipo_2001 = tipoviv_radios_prov(
        year=2001, prov="corrientes", var_types={"LINK": "object"}
    )
    tipo_2001_geo = corrientes_2001.set_index("link").join(tipo_2001.set_index("link"))

    tipo_2010 = tipoviv_radios_prov(year=2010, prov="corrientes", var_types={"link": "object"})
    tipo_2010_geo = corrientes_2010.set_index("link").join(tipo_2010.set_index("link"))

    corrientes_2020_ = tracts_2020_to_2010(
        tracts_2020_gdf=corrientes_2020, tracts_2010_gdf=corrientes_2010
    )
    # Informative print
    print(corrientes_2020_["link_2010"].isna().unique())

    # Simulation canvas
    tipo_2020_geo = tracts_2010_to_2001(tracts_2020_gdf=corrientes_2020_, prov_name='corrientes')


    # Aggregations
    tipo_vivienda_agg_2001 = named_aggregation(
        tipo_2001_geo, name="tipo vivienda particular"
    )
    tipo_vivienda_agg_2010 = named_aggregation(
        tipo_2010_geo, name="tipo vivienda particular"
    )

    # Simulation canvas
    tipo_vivienda_agg_2020 = deepcopy(tipo_2020_geo[['link','total_viviendas','link_2001','link_2010','geometry']])

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
    # 3. Porcentaje of housing informality in the city (5.95%) - this is the avg between 2001 and 2010 
    informal_simulated_distribution = simulate_cat_var(
        gdf_var_01=tipo_vivienda_agg_2001,
        gdf_var_10=tipo_vivienda_agg_2010,
        base_year="0110",
        forecast_year="2020",
        forecast_gdf=tipo_vivienda_agg_2020, 
        pct_val=3.65,
        catname={"2001": "informal", "2010": "informal"},
        tot_colname="total_viviendas",
        calibration_vector={'weights':calibration_weights, 'mix_dist':True}
    )

    if control_flow['allocation_method'] == 'avoid_relocations':
        # It avoids looses by census tract
        tipo_vivienda_agg_2020["cat_sim"] = tipo_vivienda_agg_2020['link'].map(informal_simulated_distribution)

        # TODO: Feature design
        # Avoid dwelling units relocation
        var_2010 = dict(zip(tipo_vivienda_agg_2010.index, tipo_vivienda_agg_2010.informal))
        tipo_vivienda_agg_2020['informal_2010'] = tipo_vivienda_agg_2020['link_2010'].map(var_2010)
        tipo_vivienda_agg_2020["diff"] = tipo_vivienda_agg_2020["cat_sim"] - tipo_vivienda_agg_2020["informal_2010"]
        neg_diff = tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['diff']< 0,['diff','informal_2010']].copy()
        neg_diff['diff'] = neg_diff['diff'] * -1
        tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['diff']< 0,'cat_sim'] = neg_diff.sum(axis=1)

        tipo_vivienda_agg_2020.rename(columns={'cat_sim':'informal'}, inplace=True)
        tipo_vivienda_agg_2020.drop(columns=['diff','informal_2010'], inplace=True)
    else:
        # It does not control losses by census tract
        tipo_vivienda_agg_2020["informal"] = tipo_vivienda_agg_2020.index.map(informal_simulated_distribution)
    
    # TODO: Feature design
    # Use upper limits to avoid exceding total when reproducing observed distributions
    fix_total = tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['informal']>tipo_vivienda_agg_2020['total_viviendas'], 'total_viviendas']
    tipo_vivienda_agg_2020.loc[tipo_vivienda_agg_2020['informal']>tipo_vivienda_agg_2020['total_viviendas'], 'informal'] = fix_total
    
    # TODO: Feature design
    # Simulate more than one category controlling total number of units in the area
    tipo_vivienda_agg_2020['formal'] = tipo_vivienda_agg_2020['total_viviendas'] - tipo_vivienda_agg_2020['informal'] 
    filter_cols = ['link', 'link_2001', 'link_2010', 'formal', 'informal', 'total_viviendas','geometry']
    tipo_vivienda_agg_2020=tipo_vivienda_agg_2020[filter_cols].copy()

    scenario = {2001:tipo_vivienda_agg_2001, 
                2010:tipo_vivienda_agg_2010, 
                2020:tipo_vivienda_agg_2020,
                'footpr01':footprint_corrientes_00,
                'footpr10':footprint_corrientes_10,
                'footpr20':footprint_corrientes_20,
                'agg':True,
                'calibration':True,
                'pct_val':3.65}
    return scenario