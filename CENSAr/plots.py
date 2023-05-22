from typing import Any

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def compare_chropleths(
    *gdfs: gpd.GeoDataFrame,
    column: str | list[str] = [],
    titles: list[str | None] | None = None,
    figsize: tuple[int, int] = (12, 8),
    legend_kwds: dict[str, Any] = {"shrink": 0.3},
    **kwargs,
):
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
