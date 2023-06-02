from typing import Any

import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def compare_chropleths(
    *gdfs: gpd.GeoDataFrame,
    column: str | list[str] = [],
    titles: list[str | None] | None = None,
    figsize: tuple[int, int] = (12, 8),
    legend_kwds: dict[str, Any] = {"shrink": 0.3},
    **kwargs):
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
    figsize : tuple
        Figure size.
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
        gdf.plot(ax=ax, column=column, **kwargs)

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
    chart_title: str, 
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
                vertical/len_groups, 
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

  xpos = [pos + bar_width for pos in range(len_groups)]  
  plt.xticks(xpos, labels, rotation=xticks_rotation)
  plt.grid(color='lightgrey',  linewidth=0.5, alpha=0.3)

  if yaxis_formatter:
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda y, _: yaxis_formatter.format(int(y))))

  if xaxis_formatter:
    plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, _: xaxis_formatter.format(int(x))))


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
    ax.set_xlim(0,lim);