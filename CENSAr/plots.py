from typing import Any

import esda
import geopandas as gpd
import matplotlib.pyplot as plt
from splot import esda as esdaplot
from matplotlib.figure import Figure

from CENSAr.clustering.geo_utils import compute_weights


def compare_chropleths(
    *gdfs: gpd.GeoDataFrame,
    column: str | list[str] = [],
    titles: list[str | None] | None = None,
    figsize: tuple[int, int] = (12, 8),
    legend_kwds: dict[str, Any] = {"shrink": 0.3},
    **kwargs,
) -> Figure:
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
        gdf.plot(ax=ax, column=column, **kwargs)

    for ax in axes:
        ax.set_axis_off()

    for ax, title in zip(axes, titles):
        ax.set_title(title)

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
