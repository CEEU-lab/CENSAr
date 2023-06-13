import numpy as np
import pandas as pd
import seaborn as sns
import geopandas as gpd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from CENSAr.utils import *
from CENSAr.datasources import *

#################################################
### Spatial distribution of census attributes ### 
#################################################


class UrbanFeatures:
    """
    """

    def __init__(self, thiner_area, coarser_area):
        self.thiner_area = thiner_area
        self.coarser_area = coarser_area

    def spatial_dissimilarity(self, idx_coarser_area, var_name, cat_name):

        # coarser area totals
        coarser_area_tot_var = self.thiner_area.groupby(idx_coarser_area)[[var_name]].sum()
        coarser_area_tot_cat = self.thiner_area.groupby(idx_coarser_area)[[cat_name]].sum()
        coarser_area_totals = coarser_area_tot_var.join(coarser_area_tot_cat)
        coarser_area_totals.columns = [var_name, cat_name]

        # thiner area totals
        total_var_col, total_cat_col = f"tot_{var_name}_coarser_area", f"tot_{cat_name}_coarser_area" 

        self.thiner_area[total_var_col] = self.thiner_area[idx_coarser_area].map(
            coarser_area_totals[var_name]
        )
        self.thiner_area[total_cat_col] = self.thiner_area[idx_coarser_area].map(
            coarser_area_totals[cat_name]
        )

        # Dissimilarity Index at thiner area level
        dissim_col_name = f"DI_{cat_name}"
        dissim_areas = {}
        self.thiner_area[dissim_col_name] = np.abs(
            (self.thiner_area[cat_name] / self.thiner_area[total_cat_col]) - 
            (
            (self.thiner_area[var_name] - self.thiner_area[cat_name])/
            (self.thiner_area[total_var_col] - self.thiner_area[total_cat_col])
            )
        )
        thiner_area_cols = [c for c in self.thiner_area.columns if c != 'geometry'] + ['geometry']
        dissim_thiner_area = self.thiner_area[thiner_area_cols].copy()
        dissim_areas['thiner_dissim'] = dissim_thiner_area


        # Dissimilarity Index at coarser area level
        dissim_df = ((self.thiner_area.groupby([idx_coarser_area])[[dissim_col_name]].sum() * 0.5).round(3)).reset_index()
        self.coarser_area[dissim_col_name] = dissim_df[dissim_col_name]
        coarser_area_cols = [c for c in self.coarser_area.columns if c != 'geometry'] + ['geometry']
        dissim_coarser_area = self.coarser_area[coarser_area_cols].copy()
        dissim_areas['coarser_dissim'] = dissim_coarser_area

        return dissim_areas
        
         

    # Methods to represent the spatial dissimilarity within urban areas
    def noninteractive_dissimilarity_index(
        self, x, idx_thiner_area, idx_coarser_area, cat_group, chart
        ):
        if chart == "bar":
            df = self.spatial_dissimilarity(x, idx_thiner_area, idx_coarser_area)
            df["DI_100"] = round(df["DI"] * 100, 2)

            fig, ax = plt.subplots()
            df.sort_values(by="DI", ascending=True).plot(
                x=idx_coarser_area,
                y="DI_100",
                kind="bar",
                figsize=(18, 6),
                legend=False,
                ax=ax,
                title="Disimilitud espacial de la categoría: %s" % (cat_group),
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
            df = self.spatial_dissimilarity(x, idx_thiner_area, idx_coarser_area)
            df["DI_100"] = round(df["DI"] * 100, 2)
            df["tot_var"] = df[idx_thiner_area].map(
                self.coarser_area["tot_var_coarser_area"]
            )
            df["tot_cat"] = df[idx_coarser_area].map(
                self.coarser_area["tot_cat_coarser_area"]
            )
            df["pct_cat"] = round(
                (df["tot_cat"] / df["tot_var"] * 100), 2
            )

            ax = sns.lmplot(
                x="pct_cat",
                y="DI_100",
                data=df,
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
                "Porcentaje de %s por %s" % (cat_group, idx_thiner_area), labelpad=20
            )
            plt.ylabel(
                "Disimilitud espacial de la categoría: %s" % (cat_group), labelpad=20
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
                df["pct_cat"],
                df["DI_100"],
                df.iloc[:, 0],
                plt.gca(),
            )

            plt.tight_layout()
            plt.close()
            return ax.fig

    def interactive_dissimilarity_index(
        self, x, idx_thiner_area, idx_coarser_area, cat_group, chart
    ):
        if chart == "bar":
            df = self.spatial_dissimilarity(x, idx_thiner_area, idx_coarser_area)
            df["DI_100"] = round(df["DI"] * 100, 2)
            df = df.sort_values(by="DI", ascending=True)

            fig, ax = plt.subplots()
            df.sort_values(by="DI", ascending=True).plot(
                x=idx_coarser_area,
                y="DI_100",
                kind="bar",
                figsize=(18, 6),
                legend=False,
                ax=ax,
                title="Disimilitud espacial de la categoría: %s" % (cat_group),
                color="#F5564E",
                edgecolor="#FAB95B",
                alpha=1,
            )

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=df[idx_coarser_area],
                        y=df["DI_100"],
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
                    cat_group
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
            df = self.spatial_dissimilarity(x, idx_thiner_area, idx_coarser_area)
            df["DI_100"] = round(df["DI"] * 100, 2)
            df["tot_var"] = df[idx_coarser_area].map(
                self.area_superior["tot_var_coarser_area"]
            )
            df["tot_cat"] = df[idx_coarser_area].map(
                self.df["tot_cat_coarser_area"]
            )
            df["pct_cat"] = round(
                (df["tot_cat"] / df["tot_var"] * 100), 2
            )
            df["hover_names"] = df[idx_coarser_area] + ": "
            df["hover_values"] = (
                df["%_categoria"].astype(str)
                + "%"
                + ", "
                + df["DI_100"].astype(str)
                + "%"
            )
            df["hover_label"] = df["hover_names"] + df["hover_values"]

            #customdata = np.stack((df[id_superior]), axis=-1)

            dataPoints = go.Scatter(
                x=df["pct_cat"],
                y=df["DI_100"],
                mode="markers",
                marker=dict(opacity=0.5),
                text=df["hover_label"],
                hoverinfo="text",
                showlegend=False,
            )

            x = sm.add_constant(df["pct_cat"])
            model = sm.OLS(df["DI_100"], x).fit()
            df["bestfit"] = model.fittedvalues

            lineOfBestFit = go.Scatter(
                x=df["pct_cat"],
                y=df["bestfit"],
                # name='Línea de ajuste',
                mode="lines",
                line=dict(color="firebrick", width=2),
                showlegend=False,
            )

            data = [dataPoints, lineOfBestFit]

            layout = go.Layout(
                title="Disimilitud vs. Porcentaje de la categoría '{}' por area superior".format(
                    cat_group
                ),
                xaxis=dict(title="Porcentaje de %s por %s" % (cat_group, idx_coarser_area)),
                yaxis=dict(
                    title="Disimilitud espacial de la categoría: %s" % (cat_group)
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

    def __call__(self, idx_coarser_area, var_name, cat_name):
        return self.spatial_dissimilarity(idx_coarser_area, var_name, cat_name)

    def __call__(self, x, idx_thiner_area, idx_coarser_area, cat_group, chart):
        return self.noninteractive_dissimilarity_index(
            x, idx_thiner_area, idx_coarser_area, cat_group, chart)

    def __call__(self, x, idx_thiner_area, idx_coarser_area, cat_group, chart):
        return self.interactive_dissimilarity_index(
            x, idx_thiner_area, idx_coarser_area, cat_group, chart)


def CityGenerator(thiner_geom,
    coarser_geom,
    coarser_geom_idx,
    total_population,
    group_population,
    operation):
    """
    
    ...
    Parametros:
    -----------
    gdf(gdf): area de análisis de nivel administrativo inferior
    nombre_unidad_s (str): nombre del area administrativa superior
    nombre_unidad_i(str): nombre del area administrativa inferior
    nombre_variable (str): nombre de la variable que contiene el universo
                           total de nuestra categoría (e.g.: "hogares","viviendas","personas")
    nombre_categoría (str): nombre de la categoría contenida dentro de un universo o población
                            mayor (e.g.: "hogares con nbi", "viviendas recuperables", "mujeres", etc.)
    estadístico (str): nombre del indicador con el que se describe el recorte territorial.
                       Cada uno corresponde a un método de la clase "UrbanFeatures"
                       (e.g.: "CEC", etc.)
    VisObjRep (str): Visual object representation of the UrbanFeatures instantiated class 
    
    dinamico (bool): grafico dinamico (Plotly) o estatico (sns+matplotlib)
    Devuelve:
    -------
    matplotlib.figure: chart representando los valores del estadístico deleccionado
    pandas.dataframe:  totales de un índice para cada nivel administrativo
    """

    city = UrbanFeatures(
        thiner_area=thiner_geom, 
        coarser_area=coarser_geom
    )

    #operation = {'stat':'spatial_dissimilarity', 'VisObjRep':'scatter', 'dynamic_mode':_True}

    if operation['stat'] == "spatial dissimilarity":
        if operation['VisObjRep'] == None:
            DI = city.spatial_dissimilarity( 
                            idx_coarser_area=coarser_geom_idx, 
                            var_name=total_population, 
                            cat_name=group_population
                            )
            return DI
        '''
        else:
            # Returns the visual representation of spatial dissimilarity
            if operation['dynamic_mode']:
                # Using dynamic charts
                fig = city.interactive_dissimilarity_index(
                        x=gdf,
                        idx_thiner_area=nombre_unidad_i,
                        idx_coarser_area=nombre_unidad_s,
                        categoria=cat_group,
                        chart=operation['VisObjRep']
                        )
                return fig

            else:
                # Using static charts
                fig = city.noninteractive_dissimilarity_index(
                        x=gdf,
                        idx_thiner_area=nombre_unidad_i,
                        idx_coarser_area=nombre_unidad_s,
                        categoria=cat_group,
                        chart=operation['VisObjRep']
                        )
                return fig
    '''
        
        


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


def indice_geografia_superior(territorio_df, nombre_area, nombre_region, area_superior_gdf=None):
    """
    Construye un indice complejo (e.g.: calidad de los materiales de la vivienda)
    desde una geografia inferior a otra superior
    """
    if nombre_region == "Capital Federal":
        if nombre_area == "barrio":
            area_superior_gdf = caba_neighborhood_limits()
        elif nombre_area == "comuna":
            area_superior_gdf = caba_comunas_limits()
        else:
            pass

        gdf = pd.merge(
            area_superior_gdf,
            territorio_df,
            left_on=nombre_area.upper(),
            right_on=nombre_area,
        )

    elif nombre_region == "Bs.As. G.B.A. Zona Norte":
        area_superior_gdf = gba_norte_dept_limits().to_crs(4326)
        gdf = pd.merge(area_superior_gdf, territorio_df, on=nombre_area)

    elif nombre_region == "Bs.As. G.B.A. Zona Oeste":
        area_superior_gdf = gba_oeste_dept_limits().to_crs(4326)
        gdf = pd.merge(area_superior_gdf, territorio_df, on=nombre_area)

    elif nombre_region == "Bs.As. G.B.A. Zona Sur":
        area_superior_gdf = gba_sur_dept_limits().to_crs(4326)
        gdf = pd.merge(area_superior_gdf, territorio_df, on=nombre_area)
    else:
        gdf = pd.merge(area_superior_gdf, territorio_df, on=nombre_area)

    return gdf
