import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def choropleth(
    gdf: gpd.GeoDataFrame,
    column: str,
    cmap: str = "viridis",
) -> go.Figure:
    fig = px.choropleth(
        gdf,
        geojson=gdf.geometry,
        locations=gdf.index,
        color=column,
        color_continuous_scale=cmap,
    )
    fig.update_geos(fitbounds="geojson", visible=True)
    # fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


def compare_chropleths(
    *gdfs: gpd.GeoDataFrame,
    column: str,
    nrows: int = 1,
    ncols: int = 1,
    titles: list[str] = [],
    cmap: str = "viridis",
) -> go.Figure:
    if nrows * ncols == 1:
        ncols = len(gdfs)
    elif nrows * ncols < len(gdfs):
        raise ValueError("Not enough subplots for all the gdfs")

    titles = titles or [f"Map {i}" for i in range(len(gdfs))]

    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        specs=[[{"type": "choropleth"} for c in range(ncols)] for r in range(nrows)],
        subplot_titles=titles,
    )
    for i, gdf in enumerate(gdfs):
        fig.add_trace(
            choropleth(gdf, column, cmap).data[0],
            row=i // ncols + 1,
            col=i % ncols + 1,
        )

    fig.update_geos(fitbounds="geojson", visible=True)
    return fig


def compare_columns_chropleths(
    gdf: gpd.GeoDataFrame,
    columns: list[str],
    nrows: int = 1,
    ncols: int = 1,
    cmap: str = "viridis",
) -> go.Figure:
    if nrows * ncols == 1:
        ncols = len(columns)
    elif nrows * ncols < len(columns):
        raise ValueError("Not enough subplots for all columns")

    titles = columns

    fig = make_subplots(
        rows=nrows,
        cols=ncols,
        specs=[[{"type": "choropleth"} for c in range(ncols)] for r in range(nrows)],
        subplot_titles=titles,
    )
    for i, column in enumerate(columns):
        fig.add_trace(
            choropleth(gdf, column, cmap).data[0],
            row=i // ncols + 1,
            col=i % ncols + 1,
        )
    # for i, data in enumerate(fig["data"]):
    #     fig.update_traces(marker_color=data["marker"]["line"]["color"])

    fig.update_geos(fitbounds="geojson", visible=True)
    return fig
