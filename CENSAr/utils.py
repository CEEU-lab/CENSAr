#from copy import deepcopy
#from typing import Callable

import matplotlib
import matplotlib.pyplot as plt
from branca.element import Template, MacroElement
import re
import folium
import mapclassify
#import pandas as pd
#import geopandas as gpd

def get_choroplet_colors(map, drop_continuos_bar=True):
    for map_key in map._children:
        if map_key.startswith('choropleth'):
            choro = map._children[map_key]
            for choro_key in choro._children:
                if choro_key.startswith('color_map'):
                    choro_color_map = map._children[map_key]._children[choro_key]
                    
                    if drop_continuos_bar:
                        choro_keys = [k.startswith('choropleth') for k in map._children.keys()]
                        choro_count = choro_keys.count(True)
                        
                        if choro_count > 1:
                            # if more than one choroplet, drop the legend from the last one only
                            choro_key = [k for k in map._children.keys()][-1]

                            # filters the colormap of that choroplet (the last index)
                            choro_items = [k for k in map._children[choro_key]._children.keys()]
                            cmap_key = ['color_map_' in i for i in choro_items]
                            # there is only one cmap in the list
                            branca_ref = [i for (i, v) in zip(choro_items, cmap_key) if v][0]
                            # gets colors and drop branca object
                            choro_color_map = map._children[choro_key]._children[branca_ref] 
                            colors = choro_color_map.__dict__['colors']
                            del(map._children[choro_key]._children[branca_ref])
                            

                        else:
                            del(map._children[map_key]._children[choro_key])
                        
        
    colors = choro_color_map.__dict__['colors']
    return colors

def legend_rgba_to_hex(rgba_color):
    return matplotlib.colors.to_hex(rgba_color, keep_alpha=True)

def build_template(indicator_name, legend_classes, colors):
    section1 = '''
                {% macro html(this, kwargs) %}
                <!doctype html>
                <html lang="en">
                <head>
                  <meta charset="utf-8">
                  <meta name="viewport" content="width=device-width, initial-scale=1">
                  <title>jQuery UI Draggable - Default functionality</title>
                  <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
                  <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
                  <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
                  <script>
                  $( function() {
                    $( "#maplegend" ).draggable({
                                    start: function (event, ui) {
                                        $(this).css({
                                            right: "auto",
                                            top: "auto",
                                            bottom: "auto"
                                        });
                                    }
                                });
                });
                  </script>
                </head>
                <body>
                <div id='maplegend' class='maplegend'
                    style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
                     border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
                '''
    hex_colors = [legend_rgba_to_hex(rgba_color=c) for c in colors]
    section2 = '''<div class='legend-title'> {} </div>
                    <div class='legend-scale'>
                      <ul class='legend-labels'>
                        <li><span style='background:{};opacity:0.7;'></span>{}</li>
                        <li><span style='background:{};opacity:0.7;'></span>{}</li>
                        <li><span style='background:{};opacity:0.7;'></span>{}</li>
                        <li><span style='background:{};opacity:0.7;'></span>{}</li>
                '''.format(indicator_name, hex_colors[0], legend_classes[0],
                                           hex_colors[1],legend_classes[1],
                                           hex_colors[2],legend_classes[2],
                                           hex_colors[3],legend_classes[3])

    section3 = '''</ul>
                    </div>
                    </div>
                    </body>
                    </html>
                    <style type='text/css'>
                      .maplegend .legend-title {
                        text-align: left;
                        margin-bottom: 5px;
                        font-weight: bold;
                        font-size: 90%;
                        }
                      .maplegend .legend-scale ul {
                        margin: 0;
                        margin-bottom: 5px;
                        padding: 0;
                        float: left;
                        list-style: none;
                        }
                      .maplegend .legend-scale ul li {
                        font-size: 80%;
                        list-style: none;
                        margin-left: 0;
                        line-height: 18px;
                        margin-bottom: 2px;
                        }
                      .maplegend ul.legend-labels li span {
                        display: block;
                        float: left;
                        height: 16px;
                        width: 30px;
                        margin-right: 5px;
                        margin-left: 0;
                        border: 1px solid #999;
                        }
                      .maplegend .legend-source {
                        font-size: 80%;
                        color: #777;
                        clear: both;
                        }
                      .maplegend a {
                        color: #777;
                        }
                    </style>
                    {% endmacro %}'''
    template = section1 + section2 + section3
    return template

def legend_intervals_to_int(legend_classes):

    intervals=[]
    for n in range(len(legend_classes)):
        new_interval = re.findall(r"[-+]?\d*\.\d+|\d+", legend_classes[n])
        int_interval = [round(float(i),1) for i in new_interval]
        intervals.append(int_interval)

    int_legend = []

    for idx in range(len(intervals)):
        if idx == 0:
            string_interval = '[ ' + str(intervals[idx][0]) + ', ' + str(intervals[idx][1]) + ']'

        else:
            string_interval = '[ ' + str(intervals[idx][0]) + ', ' + str(intervals[idx][1]) + ')'
        int_legend.append(string_interval)

    return int_legend


def plot_folium_dual_choroplet(
    gdf_inferior,
    gdf_superior,
    categoria,
    indicador_superior,
    nombre_superior,
    nombre_region,
    map_height=500,
    idx_col_inferior='str_link',
    intervalo = 'NaturalBreaks',
    leyenda_alternativa={'gdf_inferior':False, 'gdf_superior':False}
):
    centroide = gdf_inferior.geometry.centroid
    coordenadas = [centroide.y.mean(), centroide.x.mean()]

    if nombre_region == "Capital Federal":
        zoom_value = 11
    elif nombre_region == "Bs.As. G.B.A. Zona Norte":
        zoom_value = 9
        coordenadas = [centroide.y.mean() + 0.25, centroide.x.mean()]
    else:
        # Center base map
        zoom_value = 11

    layer = folium.Map(
        location=coordenadas,
        zoom_start=zoom_value,
        height=map_height,
        control_scale=True,
        tiles="cartodbpositron",
    )

    tiles = ["openstreetmap", "stamenterrain"]
    for tile in tiles:
        folium.TileLayer(tile).add_to(layer)

    if intervalo == 'NaturalBreaks':
        qcut = mapclassify.NaturalBreaks(gdf_inferior[categoria].values, k=4) 
    elif intervalo == 'Percentiles':
        qcut = mapclassify.Percentiles(gdf_inferior[categoria].values, pct=[25, 50, 75, 100])
    else:
        # EqualInterval
        qcut = mapclassify.EqualInterval(gdf_inferior[categoria].values, k=4)
        
    
    bins_inf = [b for b in qcut.bins]
    bins_inf.insert(0, 0.00)
    legend_classes_inf = qcut.get_legend_classes()

    area_inf = folium.Choropleth(
        name="Radios censales",
        geo_data=gdf_inferior,
        data=gdf_inferior[[c for c in gdf_inferior.columns if c != "geometry"]],
        columns=[idx_col_inferior, categoria],
        key_on="properties.{}".format(idx_col_inferior),
        fill_color="YlOrRd",
        bins=bins_inf,  
        fill_opacity=0.9,
        line_opacity=0.1, 
        highlight=True,
        legend_name="Viviendas {} a nivel inferior".format(
            categoria
        ),
        smooth_factor=1,
    ).add_to(layer)

    if leyenda_alternativa['gdf_inferior']:
        target_col = "Viviendas {} a nivel inferior".format(
            categoria
        )
        colors = get_choroplet_colors(map=layer, drop_continuos_bar=True)
        int_legend_classes = legend_intervals_to_int(legend_classes_inf)
        template = build_template(target_col, int_legend_classes, colors)
        macro_inf = MacroElement()
        macro_inf._template = Template(template)
        layer.add_child(macro_inf)

    area_inf.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=[idx_col_inferior, categoria],
            aliases=["Radio_id:", categoria.capitalize() + ":"],
        )
    )
    
    if intervalo == 'NaturalBreaks':
        qcut = mapclassify.NaturalBreaks(gdf_superior[indicador_superior].values, k=4)
    elif intervalo == 'Percentiles':
        qcut = mapclassify.Percentiles(gdf_superior[indicador_superior].values, pct=[25, 50, 75, 100])
    else:
        # EqualInterval
        qcut = mapclassify.EqualInterval(gdf_superior[indicador_superior].values, k=4)
    
    bins_sup = [b for b in qcut.bins]
    bins_sup.insert(0, 0.00)
    sup_legend_classes = qcut.get_legend_classes()

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
        bins=bins_sup,  # type: ignore
        fill_opacity=0.6,
        line_opacity=0.1,  # type: ignore
        highlight=True,
        legend_name="Disimilitud espacial: {}".format(
            categoria
        ),
        smooth_factor=1,
    ).add_to(layer)

    if leyenda_alternativa['gdf_superior']:
        target_col = "Disimilitud espacial"
        colors = get_choroplet_colors(map=layer, drop_continuos_bar=True)
        template = build_template(target_col, sup_legend_classes, colors)
        macro_sup = MacroElement()
        macro_sup._template = Template(template)
        layer.add_child(macro_sup)

    area_sup.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=[nombre_superior, indicador_superior],
            aliases=[nombre_superior + ":", "Disimilitud espacial:"],
        )
    )

    folium.LayerControl().add_to(layer)

    return layer

def plot_matplotlib_dual_choroplet(gdf_inferior, categoria, gdf_superior, figsize=(16,7)):

    fig = plt.figure(figsize=figsize)
    ax1 = fig.add_subplot(1,1,1)

    gdf_inferior.plot(column = categoria,cmap='YlOrRd',ax=ax1, alpha = 0.9, legend=False)
    gdf_superior.plot(ax=ax1, column='CEC', cmap = 'gist_yarg',edgecolor='grey', 
                linewidth=0.6, alpha = 0.6, legend=True)

    props = dict(boxstyle='round', facecolor='linen', alpha=0.8)
    for point in gdf_superior.iterrows():
        ax1.text(point[1]['geometry'].centroid.x,
                point[1]['geometry'].centroid.y,
                point[1]['grupo'],
                horizontalalignment='center',
                fontsize=10,
                bbox=props) 

    ax1.set_axis_off()
    
    plt.tight_layout()
    plt.close()
    return fig