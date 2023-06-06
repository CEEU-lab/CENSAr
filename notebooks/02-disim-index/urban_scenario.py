import pandas as pd
import geopandas as gpd

from CENSAr.datasources import (
    personas_radios_prov,
    tipoviv_radios_prov,
    radios_prov,
    persproy_depto_2025,
)

from CENSAr.modeling_tools import (
    simulate_total_var, 
    simulate_cat_var
)

from CENSAr.vector_data_analysis.geoprocessing import (from_wkt, build_thiner_pct_in_coarser_geom)
from CENSAr.aggregation import named_aggregation

def resistencia_stquo_scenario():
    envolvente_resistencia_00 = gpd.read_file('../../CENSAr/data/ManchaUrbana_Resistencia_1999.geojson')
    envolvente_resistencia_10 = gpd.read_file('../../CENSAr/data/ManchaUrbana_Resistencia_2010.geojson')
    envolvente_resistencia_20 = gpd.read_file('../../CENSAr/data/ManchaUrbana_Resistencia_2022.geojson')

    # se cargan las geometrías de las tres fotos censales
    chaco_2001 = radios_prov(year=2001, prov="chaco", mask=envolvente_resistencia_00)
    chaco_2010 = radios_prov(year=2010, prov="chaco", mask=envolvente_resistencia_10)
    chaco_2020 = radios_prov(year=2010, prov="chaco", mask=envolvente_resistencia_20)

    # se cargan las tablas de personas para estimar el total de viviendas 2020
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

    # Tablas REDATAM - Total personas en 2001 y 2010
    pers_2001 = personas_radios_prov(year=2001, prov="chaco", var_types={"link": "object"})
    pers_2001_geo = chaco_2001.set_index("link").join(pers_2001.set_index("link"))
    pers_2010 = personas_radios_prov(year=2010, prov="chaco", var_types={"link": "object"})
    pers_2010_geo = chaco_2010.set_index("link").join(pers_2010.set_index("link"))

    # Tabla de proyecciones de poblacion por departamento
    proy = persproy_depto_2025(prov="chaco")

    # Total viviendas 2020
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

    # Indicadores agregados
    tipo_vivienda_agg_2001 = named_aggregation(
        tipo_2001_geo, name="tipo vivienda particular"
    )
    tipo_vivienda_agg_2010 = named_aggregation(
        tipo_2010_geo, name="tipo vivienda particular"
    )
    tipo_vivienda_agg_2020 = named_aggregation(
        tipo_2020_geo, name="tipo vivienda particular"
    )

    # Vector de calibracion (superficie informal)
    url = "https://storage.googleapis.com/python_mdg/censar_data/informal_settlements_072022.csv"
    asentamientos = pd.read_csv(url)
    asentamientos_gdf = from_wkt(df=asentamientos, wkt_column='geometry')

    tipo_2020_reset = tipo_2020_geo.reset_index()
    calibration_weights = build_thiner_pct_in_coarser_geom(coarser_geom=tipo_2020_reset, thiner_geom=asentamientos_gdf,
                                                        coarser_idx='link', thiner_idx='id_renabap', crs=5347, coarser_tot=False)

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
                'agg':True,
                'calibration':True,
                'pct_val':3.5}
    return scenario