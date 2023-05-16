from copy import deepcopy
from typing import Callable

import folium
import mapclassify
import pandas as pd
import geopandas as gpd


def reformat_inmat_2010(gdf):
    gdf["aceptables"] = gdf["Cal1"]
    gdf["recuperables"] = gdf["Cal2"]
    gdf["irrecuperables"] = gdf["Cal3"] + gdf["Cal4"]
    gdf["total_inmat"] = gdf["aceptables"] + gdf["recuperables"] + gdf["irrecuperables"]
    columns = [c for c in gdf.columns if c != "geometry"]
    gdf_ = gdf[columns + ["geometry"]]
    return gdf_


def aggregate(
    data: gpd.GeoDataFrame | pd.DataFrame,
    mapping: dict[str, list[str]],
    aggregator: str | Callable[..., pd.Series] = "sum",
    groupby: str | list[str] = "LINK",
) -> dict[str, gpd.GeoDataFrame | pd.DataFrame]:
    """
    Group a dataframe by a column and aggregate the values of the columns
    specified in the mapping.

    Parameters
    ----------
    data : gpd.GeoDataFrame | pd.DataFrame
        Dataframe to group.
    mapping : dict[str, list[str]]
        Mapping of the columns to aggregate.
    aggregator : str | Callable[..., pd.Series], optional
        Aggregation method, by default "sum".
    groupby : str | list[str], optional
        Column to group by, by default "LINK".

    Returns
    -------
    dict[str, gpd.GeoDataFrame | pd.DataFrame]
        Dictionary with the grouped dataframes.
    """

    data = deepcopy(data)
    data.set_index(groupby, inplace=True)
    for new_key, old_keys in mapping.items():
        data[new_key] = data[old_keys].aggregate(aggregator, axis=1)  # type: ignore
        data.drop(columns=old_keys, inplace=True)

    total = data.sum(axis=1)

    df_pct = data.div(total, axis=0) * 100

    data["total"] = total
    df_pct["total"] = total

    return {"df_tot": data.reset_index(), "df_pct": df_pct.reset_index()}


def plot_folium_dual_choroplet(
    gdf_inferior,
    gdf_superior,
    categoria,
    indicador_superior,
    nombre_superior,
    nombre_region,
):
    centroide = gdf_inferior.geometry.centroid
    coordenadas = [centroide.y.mean(), centroide.x.mean()]

    if nombre_region == "Capital Federal":
        zoom_value = 11
    elif nombre_region == "Bs.As. G.B.A. Zona Norte":
        zoom_value = 9
        coordenadas = [centroide.y.mean() + 0.25, centroide.x.mean()]
    else:
        zoom_value = 10

    layer = folium.Map(
        location=coordenadas,
        zoom_start=zoom_value,
        height=500,  # type: ignore
        control_scale=True,
        tiles="cartodbpositron",
    )

    tiles = ["openstreetmap", "stamenterrain"]
    for tile in tiles:
        folium.TileLayer(tile).add_to(layer)

    cut = mapclassify.NaturalBreaks(gdf_inferior[categoria], k=4)
    bins = [b for b in cut.bins]
    bins.insert(0, 0.00)

    area_inf = folium.Choropleth(
        name="Radios censales",
        geo_data=gdf_inferior,
        data=gdf_inferior[[c for c in gdf_inferior.columns if c != "geometry"]],
        columns=["str_link", categoria],
        key_on="properties.str_link",
        fill_color="YlOrRd",
        bins=bins,  # type: ignore
        fill_opacity=0.9,
        line_opacity=0.1,  # type: ignore
        highlight=True,
        legend_name="Casos totales de la categoría {} a nivel inferior".format(
            categoria
        ),
        smooth_factor=1,
    ).add_to(layer)

    area_inf.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["str_link", categoria],
            aliases=["Radio_id:", categoria.capitalize() + ":"],
        )
    )

    cut = mapclassify.NaturalBreaks(gdf_superior[indicador_superior], k=4)
    bins = [b for b in cut.bins]
    bins.insert(0, 0.00)

    if nombre_region == "Capital Federal":
        nombre_superior = nombre_superior.upper()
    else:
        pass

    area_sup = folium.Choropleth(
        name=nombre_superior.capitalize(),
        geo_data=gdf_superior,
        data=gdf_superior[[c for c in gdf_superior.columns if c != "geometry"]],
        columns=[nombre_superior, indicador_superior],
        key_on="properties." + nombre_superior,
        fill_color="Greys",
        bins=bins,  # type: ignore
        fill_opacity=0.6,
        line_opacity=0.1,  # type: ignore
        highlight=True,
        legend_name="Indice de concentración espacial para la categoría {}".format(
            categoria
        ),
        smooth_factor=1,
    ).add_to(layer)

    area_sup.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=[nombre_superior, indicador_superior],
            aliases=[nombre_superior + ":", "Concentración espacial:"],
        )
    )

    folium.LayerControl().add_to(layer)
    return layer
