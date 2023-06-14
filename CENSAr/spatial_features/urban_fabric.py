import numpy as np
import pandas as pd
import seaborn as sns
import geopandas as gpd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from CENSAr.spatial_features.utils import *
from CENSAr.datasources import *

#################################################
### Spatial distribution of census attributes ### 
#################################################
class UrbanFeatures:
    """
    Recipe to represent cities based on spatial characteristics.
    
    ...

    Attributes
    ----------
    thiner_area : gpd.GeoDataFrame
        administrative subdivisions at a thiner area level (e.g. census tracts)
    coarser_area : gpd.GeoDataFrame
        administrative subdivisions at a coarser area level (e.g. department)
    

    Methods
    -------
    spatial_dissimilarity(idx_coarser_area, var_name, cat_name):
        Calculates spatial dissimilarity between population groups.
    noninteractive_dissimilarity_index(idx_coarser_area, var_name, cat_name, chart):
        Draws non interactive representations of the spatial dissimilaritly index
    interactive_dissimilarity_index(idx_coarser_area, idx_thiner_area, var_name, cat_name, chart):
        Draws interactive representations of the spatial dissimilaritly index
    """

    def __init__(
            self, 
            thiner_area: gpd.GeoDataFrame, 
            coarser_area: gpd.GeoDataFrame
        ):
        """
        Constructs attributes for the city object

        Parameters
        ----------
            thiner_area : gpd.GeoDataFrame
                administrative subdivisions at a thiner area level
            coarser_area : gpd.GeoDataFrame : gpd.GeoDataFrame
                administrative subdivisions at a coarser area level
        """
        self.thiner_area = thiner_area
        self.coarser_area = coarser_area

    def spatial_dissimilarity(
            self, 
            idx_coarser_area: str, 
            var_name: str, 
            cat_name: str
        ):
        """
        Calculates spatial dissimilarity between population groups.

        Parameters
        ----------
            idx_coarser_area : str
                Name of the column with geometries identifiers
            var_name : str
                Name of the column with population totales (e.g."Households")
            cat_name : str
                Name of the column with population group totals (e.g."Slums")
        
        Returns
        -------
        dissim_areas:dict[gpd.GeodataFrame,gpd.GeoDataFrame]
            Coarser and thiner area datasets with dissimilarity estimations
        """
        # copies
        thiner_area = self.thiner_area.copy()
        coarser_area = self.coarser_area.copy()

        # coarser area totals
        coarser_area_tot_var = thiner_area.groupby(idx_coarser_area)[[var_name]].sum()
        coarser_area_tot_cat = thiner_area.groupby(idx_coarser_area)[[cat_name]].sum()
        coarser_area_totals = coarser_area_tot_var.join(coarser_area_tot_cat)
        coarser_area_totals.columns = [var_name, cat_name]

        # thiner area totals
        total_var_col, total_cat_col = f"tot_{var_name}_coarser_area", f"tot_{cat_name}_coarser_area" 

        thiner_area[total_var_col] = thiner_area[idx_coarser_area].map(
            coarser_area_totals[var_name]
        )
        thiner_area[total_cat_col] = thiner_area[idx_coarser_area].map(
            coarser_area_totals[cat_name]
        )

        # Dissimilarity Index at thiner area level
        dissim_colname = f"dissim_idx_{cat_name}"
        dissim_areas = {}
        thiner_area[dissim_colname] = np.abs(
            (thiner_area[cat_name] / thiner_area[total_cat_col]) - 
            (
            (thiner_area[var_name] - thiner_area[cat_name])/
            (thiner_area[total_var_col] - thiner_area[total_cat_col])
            )                                                                                                                                                               
        )
        thiner_area_cols = [c for c in thiner_area.columns if c != 'geometry'] + ['geometry']
        dissim_thiner_area = thiner_area[thiner_area_cols].copy()
        dissim_areas['thiner_dissim'] = dissim_thiner_area


        # Dissimilarity Index at coarser area level
        dissim_df = ((thiner_area.groupby([idx_coarser_area])[[dissim_colname]].sum() * 0.5).round(3)).reset_index()
        coarser_area = pd.merge(coarser_area, coarser_area_totals, on=idx_coarser_area)
        coarser_area[dissim_colname] = dissim_df[dissim_colname]
        coarser_area_cols = [c for c in coarser_area.columns if c != 'geometry'] + ['geometry']
        dissim_coarser_area = coarser_area[coarser_area_cols].copy()
        dissim_areas['coarser_dissim'] = dissim_coarser_area

        return dissim_areas
                                                                                                                                                                                                                            
         

    # Methods to represent the spatial dissimilarity within urban areas
    def noninteractive_dissimilarity_index(
        self, 
        idx_coarser_area: str, 
        var_name: str, 
        cat_name: str, 
        chart: str
        ):
        """
        Draws non interactive representations of the spatial dissimilaritly index.

        Parameters
        ----------
        idx_coarser_area : str
            Name of the column with geometries identifiers
        var_name : str
            Name of the column with population totales (e.g."Households")
        cat_name : str
            Name of the column with population group totals (e.g."Slums")
        chart : str
            Name of the chart type to represent dissimilarity index results 
            ("bar", "scatter" or "choroplet")
        
        Returns
        -------
        fig:matplotlib.figure.Figure
            Visual representation of the dissimilarity estimations
        """
        dissim_colname = f"dissim_idx_{cat_name}"
        dissim_colname_100 = dissim_colname + "_100"
        dfs = self.spatial_dissimilarity(idx_coarser_area, var_name, cat_name)
        coarser_dissim = dfs['coarser_dissim']
        coarser_dissim[dissim_colname_100] = round(coarser_dissim[dissim_colname] * 100, 2)
        
        if chart == "bar":
            fig, ax = plt.subplots()
            coarser_dissim_sorted = coarser_dissim.sort_values(by=dissim_colname, ascending=True)
            coarser_dissim_sorted.plot(
                x=idx_coarser_area,
                y=dissim_colname_100,
                kind="bar",
                figsize=(18, 6),
                legend=False,
                ax=ax,
                title="Disimilitud espacial de la categoría: %s" % (cat_name),
                color="#F5564E",
                edgecolor="#FAB95B",
                alpha=1,
            )

            for p in ax.patches:
                ax.annotate(
                    str(p.get_height()) + "%",
                    (p.get_x() * 1.005, p.get_height() * 1.02),
                    rotation=75,
                )

            plt.xticks(rotation=80)
            plt.grid(axis="y", c="grey", alpha=0.1)
            plt.grid(axis="x", c="grey", alpha=0.1)
            plt.gca().set_yticklabels(
                ["{:.0f}%".format(x) for x in plt.gca().get_yticks()]
            )
            plt.tight_layout()
            plt.close()
            return fig

        if chart == "scatter":
            pct_colname = f"pct_{cat_name}"
            coarser_dissim[pct_colname] = round(
                (coarser_dissim[cat_name] / coarser_dissim[var_name] * 100), 2
            )

            ax = sns.lmplot(
                x=pct_colname,
                y=dissim_colname_100,
                data=coarser_dissim,
                aspect=2,
                height=7.5,
                line_kws={"color": "lightblue"},
                scatter_kws={"color": "Red", "alpha": 0.4, "s": 200},
                fit_reg=True,
            )

            ax.fig.suptitle(
                "Disimilitud espacial VS Porcentaje de la categoria por area superior",
                fontsize=15,
                x=0.54,
                y=1.02,
            )
            plt.xlabel(
                "Porcentaje de %s por area inferior" % (cat_name), labelpad=20
            )
            plt.ylabel(
                "Disimilitud espacial de la categoría: %s" % (cat_name), labelpad=20
            )
            plt.grid(axis="y", c="grey", alpha=0.1)
            plt.grid(axis="x", c="grey", alpha=0.1)

            plt.gca().set_yticklabels(
                ["{:.0f}%".format(x) for x in plt.gca().get_yticks()]
            )
            plt.gca().set_xticklabels(
                ["{:.0f}%".format(x) for x in plt.gca().get_xticks()]
            )

            def label_point(x, y, val, ax):
                a = pd.concat({"x": x, "y": y, "val": val}, axis=1)
                for i, point in a.iterrows():
                    ax.text(point["x"] + 0.02, point["y"], str(point["val"]))

            label_point(
                coarser_dissim[pct_colname],
                coarser_dissim[dissim_colname_100],
                coarser_dissim.iloc[:, 0],
                plt.gca(),
            )

            plt.tight_layout()
            plt.close()
            return ax.fig
        
        if chart == 'choroplet':
            thiner_dissim = dfs['thiner_dissim']
            fig = plot_matplotlib_dual_choroplet(thiner_area=thiner_dissim, 
                                                 cat_name=cat_name, 
                                                 coarser_area=coarser_dissim)
            return fig

    def interactive_dissimilarity_index(
            self, 
            idx_coarser_area: str, 
            idx_thiner_area: str, 
            var_name: str, 
            cat_name: str, 
            chart: str
        ):
        """
        Draws interactive representations of the spatial dissimilaritly index.

        Parameters
        ----------
        idx_coarser_area : str
            Name of the column with geometries identifiers
        var_name : str
            Name of the column with population totales (e.g."Households")
        cat_name : str
            Name of the column with population group totals (e.g."Slums")
        chart : str
            Name of the chart type to represent dissimilarity index results 
            ("bar", "scatter" or "choroplet")
        
        Returns
        -------
        fig:go.Figure | folium.Map
            Visual representation of the dissimilarity estimations
        """
        dissim_colname = f"dissim_idx_{cat_name}"
        dissim_colname_100 = dissim_colname + "_100"
        dfs = self.spatial_dissimilarity(idx_coarser_area, var_name, cat_name)
        coarser_dissim = dfs['coarser_dissim']
        coarser_dissim[dissim_colname_100] = round(coarser_dissim[dissim_colname] * 100, 2)
        
        if chart == "bar":
            coarser_dissim_sorted = coarser_dissim.sort_values(by=dissim_colname, ascending=True)

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=coarser_dissim_sorted[idx_coarser_area],
                        y=coarser_dissim_sorted[dissim_colname_100],
                        hovertemplate="Indice de disimilitud espacial: %{y:.2f}% <extra></extra>",
                        marker={
                            "color": "rgba(240, 240, 240, 1.0)",
                            "line": {
                                "width": 0
                                     },
                        },
                    ),
                ]
            )

            fig.update_traces(
                marker_color="#ADD8E6",
                marker_line_color="#1E3F66",
                marker_line_width=1.5,
                opacity=0.6,
            )

            fig.update_layout(
                autosize=True,
                width=1000,
                height=500,
                title="Disimilitud espacial de la categoría '{}' por área superior".format(
                    cat_name
                ),
                plot_bgcolor="white",
                hoverlabel=dict(bgcolor="white"),
                yaxis=None,
                xaxis=None,
            )

            fig.update_yaxes(showline=True, linecolor="black", ticksuffix="%")
            fig.update_xaxes(showline=True, linecolor="black")

            return fig

        if chart == "scatter":
            pct_colname = f"pct_{cat_name}"
            coarser_dissim[pct_colname] = round(
                (coarser_dissim[cat_name] / coarser_dissim[var_name] * 100), 2
            )
            
            coarser_dissim["hover_names"] = coarser_dissim[idx_coarser_area] + ": "
            coarser_dissim["hover_values"] = (
                coarser_dissim[pct_colname].astype(str)
                + "%"
                + ", "
                + coarser_dissim[dissim_colname_100].astype(str)
                + "%"
            )
            coarser_dissim["hover_label"] = coarser_dissim["hover_names"] + coarser_dissim["hover_values"]

            dataPoints = go.Scatter(
                x=coarser_dissim[pct_colname],
                y=coarser_dissim[dissim_colname_100],
                mode="markers",
                marker=dict(opacity=0.5),
                text=coarser_dissim["hover_label"],
                hoverinfo="text",
                showlegend=False,
            )

            x = sm.add_constant(coarser_dissim[pct_colname])
            model = sm.OLS(coarser_dissim[dissim_colname_100], x).fit()
            coarser_dissim["bestfit"] = model.fittedvalues

            lineOfBestFit = go.Scatter(
                x=coarser_dissim[pct_colname],
                y=coarser_dissim["bestfit"],
                # name='Línea de ajuste',
                mode="lines",
                line=dict(color="firebrick", width=2),
                showlegend=False,
            )

            data = [dataPoints, lineOfBestFit]

            layout = go.Layout(
                title="Disimilitud vs. Porcentaje de la categoría '{}' por area superior".format(
                    cat_name
                ),
                xaxis=dict(title="Porcentaje de %s por %s" % (cat_name, idx_coarser_area)),
                yaxis=dict(
                    title="Disimilitud espacial de la categoría: %s" % (cat_name)
                ),
                hovermode="closest",
            )

            fig = go.Figure(data=data, layout=layout)
            fig.update_traces(
                marker_color="#ADD8E6",
                marker_line_color="#1E3F66",
                marker_line_width=1.5,
                opacity=0.6,
            )

            fig.update_layout(
                autosize=True,
                width=1000,
                height=500,
                plot_bgcolor="white",
                hoverlabel=dict(bgcolor="white"),
            )

            fig.update_yaxes(showline=True, linecolor="black", ticksuffix="%")
            fig.update_xaxes(showline=True, linecolor="black", ticksuffix="%")

            return fig
        
        if chart == 'choroplet':
            thiner_dissim = dfs['thiner_dissim']
            fig = plot_folium_dual_choroplet(
                cat_name=cat_name,
                thiner_area=thiner_dissim,
                thiner_area_name=idx_thiner_area,
                coarser_area=coarser_dissim,
                coarser_area_name=idx_coarser_area,
                nombre_region='Borrar parametro',
                map_height=1000,
                bins_classificator = 'NaturalBreaks',
                legend_builder={'thiner_area':False, 'coarser_area':True}
                )
            return fig

    def __call__(self, idx_coarser_area, var_name, cat_name):
        return self.spatial_dissimilarity(idx_coarser_area, var_name, cat_name)

    def __call__(self, idx_coarser_area, var_name, cat_name, chart):
        return self.noninteractive_dissimilarity_index(
            idx_coarser_area, var_name, cat_name, chart)

    def __call__(self, idx_coarser_area, idx_thiner_area, var_name, cat_name, chart):
        return self.interactive_dissimilarity_index(
            idx_coarser_area, idx_thiner_area, var_name, cat_name, chart)


def CityGenerator(
    thiner_geom: gpd.GeoDataFrame,
    coarser_geom: gpd.GeoDataFrame,
    coarser_geom_idx: str,
    thiner_geom_idx: str,
    total_population: str,
    group_population: str,
    operation: dict[str, bool] = {'stat':'spatial_dissimilarity', 'VisObjRep':'scatter', 'dynamic_mode':True}
    ):
    """
    Wrapper for the UrbanFeatures class.

    Parameters
    ----------
    idx_coarser_area : str
        Name of the column with geometries identifiers
    var_name : str
        Name of the column with population totales (e.g."Households")
    cat_name : str
        Name of the column with population group totals (e.g."Slums")
    chart : str
        Name of the chart type to represent dissimilarity index results 
        ("bar", "scatter" or "choroplet")

    Returns
    -------
    dissim_areas:dict[gpd.GeodataFrame,gpd.GeoDataFrame]
            Coarser and thiner area datasets with dissimilarity estimations
    fig:matplotlib.figure | go.Figure | folium.Map
        Visual representation of the dissimilarity estimations
    
    """

    city = UrbanFeatures(
        thiner_area=thiner_geom, 
        coarser_area=coarser_geom
    )

    if operation['stat'] == "spatial dissimilarity":
        if operation['VisObjRep'] == None:
            dissim_areas = city.spatial_dissimilarity( 
                            idx_coarser_area=coarser_geom_idx, 
                            var_name=total_population, 
                            cat_name=group_population
                            )
            return dissim_areas
        
        else: 
            if operation['dynamic_mode']:
                fig = city.interactive_dissimilarity_index(
                    idx_coarser_area=coarser_geom_idx,
                    idx_thiner_area=thiner_geom_idx,
                    var_name=total_population,
                    cat_name=group_population,
                    chart=operation['VisObjRep']
                )
                return fig
            else:
                fig = city.noninteractive_dissimilarity_index(
                    idx_coarser_area=coarser_geom_idx,
                    var_name=total_population,
                    cat_name=group_population,
                    chart=operation['VisObjRep']
                )
                return fig       

def radios_inmat_2010(region_name, geog, vals):
    geog["str_link"] = geog["int_link"].apply(lambda x: "0" + str(x))
    vals["str_link"] = vals["Codigo"].apply(lambda x: "0" + str(x))
    vals["cod_depto"] = vals["str_link"].apply(lambda x: x[:5])
    gdf = pd.merge(geog, vals, on="str_link")

    if region_name != "Capital Federal":
        inmat_gba24 = reformat_inmat_2010(gdf)
        inmat_region = inmat_gba24.loc[inmat_gba24["region"] == region_name].copy()
    else:
        inmat_caba = reformat_inmat_2010(gdf)
        inmat_region = inmat_caba.copy()

    return inmat_region



