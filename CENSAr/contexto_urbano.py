import numpy as np
import pandas as pd
import seaborn as sns
import geopandas as gpd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from CENSAr.utils import *
from CENSAr.datasources import *

##################################################
# Distribución territorial de atributos censales #
##################################################


class ContextoUrbano:
    """
    Describe un territorio a partir de la relación de atributos
    entre áreas administrativas superiores e inferiores.
    Parametros
    ----------
    area_superior (pandas dataframe): totales de la variable y la categoria a describir por unidad administrativa
    area_inferior (pandas dataframe): totales de la variable y la categoria a describir por unidad administrativa
    """

    def __init__(self, area_inferior, area_superior):
        self.area_inferior = area_inferior
        self.area_superior = area_superior

    def concentracion_espacial(self, x, id_inferior, id_superior):
        x["categoria_area_superior"] = x[id_superior].map(
            self.area_superior["categoria"]
        )
        x["variable_area_superior"] = x[id_superior].map(self.area_superior["variable"])

        x["categoria_area_inferior"] = x[id_inferior].map(
            self.area_inferior["categoria"]
        )
        x["variable_area_inferior"] = x[id_inferior].map(self.area_inferior["variable"])

        x["CEC"] = np.abs(
            (x["categoria_area_inferior"] / x["categoria_area_superior"])
            - (
                (x["variable_area_inferior"] - x["categoria_area_inferior"])
                / (x["variable_area_superior"] - x["categoria_area_superior"])
            )
        )
        
        # Concentración espacial de la categoría
        CEC = ((x.groupby([id_superior])[["CEC"]].sum() * 0.5).round(3)).reset_index()

        return CEC

    # metodos para graficar resultados (estaticos)
    def concentracion_espacial_plot(
        self, x, id_inferior, id_superior, estadistico, categoria, chart
    ):
        if chart == "bar":
            area_cec = self.concentracion_espacial(x, id_inferior, id_superior)
            area_cec["CEC_100"] = round(area_cec["CEC"] * 100, 2)

            fig, ax = plt.subplots()
            area_cec.sort_values(by=estadistico, ascending=True).plot(
                x=id_superior,
                y="CEC_100",
                kind="bar",
                figsize=(18, 6),
                legend=False,
                ax=ax,
                title="Disimilitud espacial de la categoría: %s" % (categoria),
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
            return fig

        if chart == "scatter":
            area_cec = self.concentracion_espacial(x, id_inferior, id_superior)
            area_cec["CEC_100"] = round(area_cec["CEC"] * 100, 2)
            area_cec["variable"] = area_cec[id_superior].map(
                self.area_superior["variable"]
            )
            area_cec["categoria"] = area_cec[id_superior].map(
                self.area_superior["categoria"]
            )
            area_cec["%_categoria"] = round(
                (area_cec["categoria"] / area_cec["variable"] * 100), 2
            )

            cec_cat = sns.lmplot(
                x="%_categoria",
                y="CEC_100",
                data=area_cec,
                aspect=2,
                height=7.5,
                line_kws={"color": "lightblue"},
                scatter_kws={"color": "Red", "alpha": 0.4, "s": 200},
                fit_reg=True,
            )

            cec_cat.fig.suptitle(
                "Disimilitud espacial del atributo VS Porcentaje por area superior",
                fontsize=15,
                x=0.54,
                y=1.02,
            )
            plt.xlabel(
                "Porcentaje de %s por %s" % (categoria, id_superior), labelpad=20
            )
            plt.ylabel(
                "Disimilitud espacial de la categoría: %s" % (categoria), labelpad=20
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
                area_cec["%_categoria"],
                area_cec["CEC_100"],
                area_cec.iloc[:, 0],
                plt.gca(),
            )

            plt.tight_layout()
            return cec_cat.fig

    def concentracion_espacial_plotly(
        self, x, id_inferior, id_superior, estadistico, categoria, chart
    ):
        if chart == "bar":
            area_cec = self.concentracion_espacial(x, id_inferior, id_superior)
            area_cec["CEC_100"] = round(area_cec["CEC"] * 100, 2)
            area_cec = area_cec.sort_values(by=estadistico, ascending=True)

            fig, ax = plt.subplots()
            area_cec.sort_values(by=estadistico, ascending=True).plot(
                x=id_superior,
                y="CEC_100",
                kind="bar",
                figsize=(18, 6),
                legend=False,
                ax=ax,
                title="Disimilitud espacial de la categoría: %s" % (categoria),
                color="#F5564E",
                edgecolor="#FAB95B",
                alpha=1,
            )

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=area_cec[id_superior],
                        y=area_cec["CEC_100"],
                        hovertemplate="Indice de disimilitud espacial: %{y:.2f}% <extra></extra>",
                        marker={
                            "color": "rgba(240, 240, 240, 1.0)",
                            "line": {"width": 0},
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
                    categoria
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
            area_cec = self.concentracion_espacial(x, id_inferior, id_superior)
            area_cec["CEC_100"] = round(area_cec["CEC"] * 100, 2)
            area_cec["variable"] = area_cec[id_superior].map(
                self.area_superior["variable"]
            )
            area_cec["categoria"] = area_cec[id_superior].map(
                self.area_superior["categoria"]
            )
            area_cec["%_categoria"] = round(
                (area_cec["categoria"] / area_cec["variable"] * 100), 2
            )
            area_cec["hover_names"] = area_cec[id_superior] + ": "
            area_cec["hover_values"] = (
                area_cec["%_categoria"].astype(str)
                + "%"
                + ", "
                + area_cec["CEC_100"].astype(str)
                + "%"
            )
            area_cec["hover_label"] = area_cec["hover_names"] + area_cec["hover_values"]

            customdata = np.stack((area_cec[id_superior]), axis=-1)

            dataPoints = go.Scatter(
                x=area_cec["%_categoria"],
                y=area_cec["CEC_100"],
                mode="markers",
                marker=dict(opacity=0.5),
                text=area_cec["hover_label"],
                hoverinfo="text",
                showlegend=False,
            )

            x = sm.add_constant(area_cec["%_categoria"])
            model = sm.OLS(area_cec["CEC_100"], x).fit()
            area_cec["bestfit"] = model.fittedvalues

            lineOfBestFit = go.Scatter(
                x=area_cec["%_categoria"],
                y=area_cec["bestfit"],
                # name='Línea de ajuste',
                mode="lines",
                line=dict(color="firebrick", width=2),
                showlegend=False,
            )

            data = [dataPoints, lineOfBestFit]

            layout = go.Layout(
                title="Disimilitud vs. Porcentaje de la categoría '{}' por area superior".format(
                    categoria
                ),
                xaxis=dict(title="Porcentaje de %s por %s" % (categoria, id_superior)),
                yaxis=dict(
                    title="Concentración espacial de la categoría: %s" % (categoria)
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

    def __call__(self, x, id_inferior, id_superior):
        return self.concentracion_espacial(x, id_inferior, id_superior)

    def __call__(self, x, id_inferior, id_superior, estadistico, categoria, chart):
        return self.concentracion_espacial_plot(
            x, id_inferior, id_superior, estadistico, categoria, chart
        )

    def __call__(self, x, id_inferior, id_superior, estadistico, categoria, chart):
        return self.concentracion_espacial_plotly(
            x, id_inferior, id_superior, estadistico, categoria, chart
        )


def atributos_urbanos(inferior_gdf, idas, idai, universo, categoria):
    """
    Agrupa los totales de la variable y categoría deseada a un nivel administrativo
    superior y los mapea en el gdf de nivel administrativo inferior
     ...
    Parametros:
    -----------
    inferior_gdf(gdf): area de análisis de nivel administrativo inferior
    idas(str): id del area administrativa superior
    idai(str): id del area administrativa inferior
    universo(str): nombre de la variable que contiene el universo
                   total de nuestra categoría (e.g.: "hogares","viviendas","personas")
    categria(str): nombre de la categoría en la que se clasifica
                   nuestra variable de análisis (e.g.: "hogares con NBI","viviendas recuperables")
    Devuelve:
    -------
    dict: dataframes con totales para cada nivel administrativo
    """

    # area administrativa superior
    # total_universo_as = inferior_gdf.groupby(idas)[['VIVIEND']].sum()
    # total_categoria_as = inferior_gdf.groupby(idas)[['recuperables']].sum()
    total_universo_as = inferior_gdf.groupby(idas)[[universo]].sum()
    total_categoria_as = inferior_gdf.groupby(idas)[[categoria]].sum()
    area_superior = total_universo_as.join(total_categoria_as)
    area_superior.columns = ["variable", "categoria"]

    # thiner area
    area_inferior = inferior_gdf.set_index(idai).loc[:, [universo, categoria]]
    area_inferior.columns = ["variable", "categoria"]

    return {"superior": area_superior, "inferior": area_inferior}


def construye_territorio(
    gdf,
    nombre_unidad_s,
    nombre_unidad_i,
    nombre_variable,
    nombre_categoria,
    estadistico,
    tipo,
    dinamico=False,
):
    """
    Realza una selección total o parcial dentro de un área metropolitana
    y la caracteriza a partir de su contexto urbano.
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
                       Cada uno corresponde a un método de la clase "ContextoUrbano"
                       (e.g.: "CEC", etc.)
    tipo (str): tipo de gráfico de salida para el método concentracion_espacial_plot()
    dinamico (bool): grafico dinamico (Plotly) o estatico (sns+matplotlib)
    Devuelve:
    -------
    matplotlib.figure: chart representando los valores del estadístico deleccionado
    pandas.dataframe:  totales de un índice para cada nivel administrativo
    """

    unidad_administrativa = atributos_urbanos(
        inferior_gdf=gdf,
        idas=nombre_unidad_s,
        idai=nombre_unidad_i,
        universo=nombre_variable,
        categoria=nombre_categoria,
    )

    territorio = ContextoUrbano(
        unidad_administrativa["inferior"], unidad_administrativa["superior"]
    )

    if estadistico:
        if dinamico:
            return territorio.concentracion_espacial_plotly(
                x=gdf,
                id_inferior=nombre_unidad_i,
                id_superior=nombre_unidad_s,
                estadistico=estadistico,
                categoria=nombre_categoria,
                chart=tipo,
            )

        else:
            return territorio.concentracion_espacial_plot(
                x=gdf,
                id_inferior=nombre_unidad_i,
                id_superior=nombre_unidad_s,
                estadistico=estadistico,
                categoria=nombre_categoria,
                chart=tipo,
            )
    else:
        return territorio.concentracion_espacial(
            x=gdf, id_inferior=nombre_unidad_i, id_superior=nombre_unidad_s
        )


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
