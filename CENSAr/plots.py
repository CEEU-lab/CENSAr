from typing import Any

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.figure import Figure
import esda
from splot import esda as esdaplot

from CENSAr.clustering.geo_utils import compute_weights


def compare_chropleths(
    *gdfs: gpd.GeoDataFrame,
    column: str | list[str] = [],
    titles: list[str | None] | None = None,
    urban_boundaries: None | list[gpd.GeoDataFrame],
    figsize: tuple[int, int] = (12, 8),
    SRID: int | str = 4326, 
    legend_kwds: dict[str, Any] = {"shrink": 0.3},
    **kwargs,
) -> Figure:
    """
    Plots a choropletic maps comparison between geodataframes columns.

    Parameters
    ----------
    gdfs : gpd.GeoDataFrame
        Geodataframes used in columns comparison .
    columns : str | list of str
        Name/s of the column/s of each geodataframe.
    titles : list of str or None
        Choropletic maps titles
    urban_boundaries : None | list of gdf
        List of overlaying Polygon bounadries. The list
        must match with the number of dataframes in *gdfs
    figsize : tuple
        Figure size.
    SRID : int | str, default EPSG 4326
        Coordinates reference system.
    legend_kwds : dict, default {"shrink": 0.3}
        Legend settings.
    **kwargs: Aditional plotting config.
        e.g. scheme (str): "Quantiles"

    Returns
    -------
    fig:matplotlib.figure.Figure
        Choropletic maps
    """
    nplots = len(gdfs)
    fig, axes = plt.subplots(nrows=1, ncols=nplots, figsize=figsize)

    # convert to list when only one column is needed
    if isinstance(column, str):
        column = [column for _ in range(nplots)]
    assert len(column) == nplots, "one column for every dataset must be definided."

    titles = titles or [None for _ in range(nplots)]
    assert len(titles) == nplots, "one title for every dataset must be definided."

    kwargs["legend"] = kwargs.get("legend", True)
    kwargs["legend_kwds"] = legend_kwds
    
    print(kwargs)

    for gdf, ax, column in zip(gdfs, axes, column):
        gdf.to_crs(SRID).plot(ax=ax, column=column, **kwargs)

    if urban_boundaries:
        idx = 0
        for gdf in urban_boundaries:
            gdf.to_crs(SRID).geometry.boundary.plot(ax=axes[idx], linewidth=0.1, color='black')
            idx += 1

    for ax in axes:
        ax.set_axis_off()

    for ax, title in zip(axes, titles):
        ax.set_title(title)

    plt.tight_layout()
    plt.close()
    return fig

def plot_grouped_bars(
    df: pd.DataFrame, 
    figsize: tuple[int, int], 
    chart_title: str | None, 
    len_groups: int, 
    bar_width: float, 
    colors: dict, 
    fcolor: str, 
    tcolor:str, 
    yaxis_name:str, 
    yaxis_formatter: str | None, 
    ylim: int | None,
    xaxis_formatter: str | None, 
    xticks_rotation: int):
    """
    Plots grouped bar charts.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with bar values by group.
    figsize : tuple
        Figure size.
    chart_title : str | None
        Choropletic maps titles
    len_groups : int
        Number of bar groups.
    bar_width : float
        Bar width.
    colors : dict
        Name of the dataframe columns and color codes (e.g. {colname:color})
    fcolor : str
        Bar annotations background color
    tcolor : str
        Bar annotations text color
    yaxis_name : str
        yaxis title
    yaxis_formatter : str | None
        y axis values style formatting (e.g. '{}%')
    ylim : int
        y axis limit
    xaxis_formatter : str | None
        x axis values style formatting (e.g. '{}$')
    xtick_rotation : int
        xticks text rotation
    
    Returns
    -------
    fig:matplotlib.figure.Figure
        Grouped bars chart
    """
    labels = [c for c in df.columns.values]
    cat_groups = [i for i in df.index.values]
    val_arrays = {}

    for g in cat_groups:
        val_arrays[g] = df.loc[g].values[:len(labels)]

    first_group = list(val_arrays.keys())[0]
    dis = np.arange(len(val_arrays[first_group]))

    fig, ax = plt.subplots(figsize=figsize)

    for k,v in val_arrays.items():
        if k!= first_group:
            dis = [x + bar_width for x in dis]
        
        ax.bar(dis,height=val_arrays[k], width=bar_width, label=k, 
                align='center', color=colors[k])

        annot_props = dict(boxstyle='round', facecolor=fcolor, alpha=1)
        for horizontal, vertical in zip(dis, val_arrays[k]):
            ax.text(horizontal,
                    vertical/2, 
                    str(vertical), 
                    fontsize=10,
                    color=tcolor, 
                    bbox=annot_props, ha='center')
            
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel(yaxis_name)

    plt.suptitle(chart_title, fontsize=15)
    ax.set_ylim(ylim)
    ax.legend()

    if len(cat_groups)%2 == 0:
        xpos = [pos + (bar_width/2) for pos in range(len_groups)]
    else:
        xpos = [pos + bar_width for pos in range(len_groups)]
      
    plt.xticks(xpos, labels, rotation=xticks_rotation)
    plt.grid(color='lightgrey',  linewidth=0.5, alpha=0.3)

    if yaxis_formatter:
        plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda y, _: yaxis_formatter.format(int(y))))

    if xaxis_formatter:
        plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, _: xaxis_formatter.format(int(x))))

    plt.tight_layout()
    plt.close()

    return fig

def plot_dist_continvar(
    serie: pd.Series, 
    tit: str | None, 
    figsize: tuple[int, int], 
    bval: int, 
    lim: int, 
    xlabel: str, 
    ylabel: str, 
    fill_hist: bool):
    """
    Plots distributions for continuous variables.

    Parameters
    ----------
    serie : pd.Series
        Continuous values serie.
    tit : str | None
        Chart title.
    figsize : tuple
        Figure size.
    bval : int
        Bins size.
    lim : int
        xaxis limit
    xlabel : str
        xaxis title
    ylabel : str
        yaxis title
    fill_hist : bool
        Wether to fill histogram or not

    Returns
    -------
    fig:matplotlib.figure.Figure
        Distribution charts
    """
    fig, (ax1, ax2, ax3) = plt.subplots(ncols=3, nrows=1, figsize=figsize)

    boxprops = dict(color="#000000",linewidth=1.25)
    medianprops = dict(color="#fed547",linewidth=1.5)
    ax1.boxplot(serie, showfliers=False, boxprops=boxprops, medianprops=medianprops)
    ax2.hist(serie, bins=bval, density=False, histtype='step', color='#07cdd8',fill=fill_hist)
    serie.plot(kind='kde', ax=ax3, color='#07cdd8', legend=None)

    plt.suptitle(tit, fontsize=20)
    ax1.set_title('')
    ax2.set_title('')
    ax3.set_title('')

    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel)

    ax2.set_xlabel(ylabel)
    ax2.set_ylabel(xlabel) 
    ax2.xaxis.set_label_coords(1.05, -.12)

    ax1.set_xticks([])
    ax3.set_yticks([]) 
    ax3.set_ylabel('')

    for ax in [ax1,ax2,ax3]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

    ax3.spines['left'].set_visible(False)

    # medidas de tendencia central 
    for ax in [ax2, ax3]:
        ax.grid(axis='x')
        ax.axvline(serie.describe()['mean'], color='#4e2c76', linewidth=1)
        ax.axvline(serie.describe()['50%'], color='#fed547', linewidth=1)
        ax.set_xlim(0,lim)
    
    plt.tight_layout()
    plt.close()

    return fig

def plot_local_autocorrelation(
    gdf: gpd.GeoDataFrame,
    indicators: list[str],
    p_value: float = 0.05,
    weights: str = "queen",
    knn_k: int = 5,
    figsize: tuple[int, int] = (20, 7),
    cmap: str = "viridis",
    **kwargs,
):
    """
    Plot local autocorrelation for each indicator in the list.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        GeoDataFrame with the data.
    indicators : list[str]
        List of indicators to plot.
    p_value : float, optional
        P-value for the local autocorrelation, by default 0.05.
    weights : str, optional
        Weights to use, by default "queen".
    knn_k : int, optional
        Number of neighbors to use when weights is "knn", by default 5.
    figsize : tuple[int, int], optional
        Figure size, by default (20, 7).
    cmap : str, optional
        Colormap to use, by default "viridis".

    Returns
    -------
    Figure
        Figure with the plots.
    """
    for indicator in indicators:
        w = compute_weights(gdf, weights=weights, knn_k=knn_k)
        lisa = esda.Moran_Local(gdf[indicator], w)
        fig, subplots = esdaplot.plot_local_autocorrelation(
            lisa,
            gdf,
            indicator,
            p=p_value,
            figsize=figsize,
            cmap=cmap,
            **kwargs,
        )
        fig.suptitle(f"{indicator.capitalize()} - Local Autocorrelation")


def plot_local_autocorrelation_bv(
    gdf: gpd.GeoDataFrame,
    target_attr: str,
    reference_attr: str,
    p_value: float = 0.05,
    weights: str = "queen",
    knn_k: int = 5,
    figsize: tuple[int, int] = (20, 7),
    cmap: str = "viridis",
    **kwargs,
):
    w = compute_weights(gdf, weights=weights, knn_k=knn_k)
    lisa_bv = esda.Moran_Local_BV(gdf[target_attr], gdf[reference_attr], w)
    fig, subplots = esdaplot.plot_local_autocorrelation(
        lisa_bv,
        gdf,
        target_attr,
        p=p_value,
        figsize=figsize,
        cmap=cmap,
        **kwargs,
    )
    fig.suptitle(
        f"{target_attr.capitalize()} - {reference_attr.capitalize()}\nBivariate Local Autocorrelation"  # noqa
    )
