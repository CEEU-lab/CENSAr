#from copy import deepcopy
#from typing import Callable

import matplotlib
import matplotlib.pyplot as plt
from branca.element import Template, MacroElement
import re
import geopandas as gpd
import folium
import mapclassify

def get_choroplet_colors(
    map: folium.folium.Map, 
    drop_continuos_bar: bool = True
    ):
    """
    Gets the colormap in a choropleth map of a folium object type. 
    If indicated, it also drops the default continuous bar legend.

    Parameters
    ----------
    map : folium.Map
        Folium canvas containing choropletic maps.
    drop_continuos_bar: Bool
        Whether to drop folium continuous scale or not 

    Returns
    -------
    colors:list[float]
        Color codes
    """
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
                            # if there is more than one choroplet, drop the legend from the last one only
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

def legend_rgba_to_hex(
    rgba_color : int|str
    ):
    """
    Transforms a rgba color code into hex.

    Parameters
    ----------
    rgba_color : int | str
        Color code to be trsnaformed. 

    Returns
    -------
    hex_code:str
        Hexadecimal color code
    """
    hex_code = matplotlib.colors.to_hex(rgba_color, keep_alpha=True)
    return hex_code

def build_template(
        indicator_name : str, 
        legend_classes : list[str], 
        colors : list[tuple[float,float,float,float]]):
    """
    Creates the str template of the new choroplet legend.

    Parameters
    ----------
    indicator_name : str
        Name of the variable to use as legend title.
    legend_classes : list
        Range of the variable continuous values 
        e.g. ['[0.55, 0.55]', '(0.55, 0.56]', '(0.56, 0.58]', '(0.58, 0.62]']
    colors : list
        Color codes used for each range of values
        e.g. [(0.8, 0.8, 0.8, 1.0), ...]

    Returns
    -------
    template:str
        str input for Template() class instantiation. This object will be 
        added to the folium.map where the choroplet exists.
    """
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

def legend_intervals_to_int(
    legend_classes : list[str]
    ):
    """
    Transforms the str representation of floats into integer.

    Parameters
    ----------
    legend_classes : list
        Range of the variable continuous values 
        e.g. ['[0.55, 0.55]', '(0.55, 0.56]', '(0.56, 0.58]', '(0.58, 0.62]']. 

    Returns
    -------
    list:int
        Color codes
    """

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

def plot_matplotlib_dual_choroplet(
        thiner_area: gpd.GeoDataFrame, 
        cat_name: str, 
        coarser_area: gpd.GeoDataFrame, 
        figsize: tuple[int, int] =(16,7)
    ):
    """
    Draws a two overlay choropleth map indicating spatial dissimilarity 
    for the coarser geometries and population group totals for the thinner ones.

    Parameters
    ----------
    thiner_area : gpd.GeoDataFrame
        administrative subdivisions at a thiner area level (e.g. census tracts)
    cat_name : str
        Name of the column with population group totals (e.g."Slums")
    coarser_area : gpd.GeoDataFrame
        administrative subdivisions at a coarser area level (e.g. department)
    figsize: tuple[int, int]
        Figure size
    
    Returns
    -------
    fig:matplotlib.figure.Figure
        Visual representation of the dissimilarity estimations
    """

    fig = plt.figure(figsize=figsize)
    ax1 = fig.add_subplot(1,1,1)

    thiner_area.plot(column = cat_name,cmap='YlOrRd',ax=ax1, alpha = 0.9, legend=False)
    dissim_colname = f"dissim_idx_{cat_name}"
    coarser_area.plot(ax=ax1, column=dissim_colname, cmap = 'gist_yarg',edgecolor='grey', 
                linewidth=0.6, alpha = 0.6, legend=True)

    props = dict(boxstyle='round', facecolor='linen', alpha=0.8)
    for point in coarser_area.iterrows():
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

def plot_folium_dual_choroplet(
    cat_name: str,
    thiner_area: gpd.GeoDataFrame,
    thiner_area_name: str,
    coarser_area: gpd.GeoDataFrame,
    coarser_area_name: str,
    map_height: int = 1000,
    bins_classificator: str = 'NaturalBreaks',
    legend_builder: dict[bool,bool] = {'thiner_area':False, 'coarser_area':False}
    ):
    """
    Draws a two overlay choropleth map indicating spatial dissimilarity 
    for the coarser geometries and population group totals for the thinner ones.

    Parameters
    ----------
    cat_name : str
        Name of the column with population group totals (e.g."Slums")
    thiner_area : gpd.GeoDataFrame
        administrative subdivisions at a thiner area level (e.g. census tracts)
    thiner_area_name : str
        Name of the column with geometries identifiers (e.g. "link")
    coarser_area : gpd.GeoDataFrame
        administrative subdivisions at a coarser area level (e.g. "department")
    coarser_area_name : str
        Name of the column with geometries identifiers (e.g. "zone")
    map_height: int, default 1000
        Figure height
    bins_classificator: str, default "NaturalBreaks"
        Classification schema to be used to get data intervals
    legend_builder: dict[bool, bool]
        Wether to drop the default legebd bar and draw a new one for both choroplets
    
    Returns
    -------
    layer:folium.Map
        Visual representation of the dissimilarity estimations
    """
    # layer config
    centroid_ref = thiner_area.geometry.centroid
    coords = [centroid_ref.y.mean(), centroid_ref.x.mean()]

    # Center base map
    zoom_value = 12

    layer = folium.Map(
        location=coords,
        zoom_start=zoom_value,
        height=map_height,
        control_scale=True,
        tiles="cartodbpositron"
    )

    tiles = ["openstreetmap", "stamenterrain"]
    for tile in tiles:
        folium.TileLayer(tile).add_to(layer)

    # thiner area choroplet
    if bins_classificator == 'NaturalBreaks':
        qcut = mapclassify.NaturalBreaks(thiner_area[cat_name].values, k=4) 
    elif bins_classificator == 'Percentiles':
        qcut = mapclassify.Percentiles(thiner_area[cat_name].values, pct=[25, 50, 75, 100])
    else:
        # EqualInterval
        qcut = mapclassify.EqualInterval(thiner_area[cat_name].values, k=4)
        
    thiner_bins = [b for b in qcut.bins]
    thiner_bins.insert(0, 0.00)
    thiner_legend_classes = qcut.get_legend_classes()
    
    thiner_choroplet = folium.Choropleth(
        name="Radios censales",
        geo_data=thiner_area,
        data=thiner_area[[c for c in thiner_area.columns if c != "geometry"]],
        columns=[thiner_area_name, cat_name],
        key_on="properties.{}".format(thiner_area_name),
        fill_color="YlOrRd",
        bins=thiner_bins,  
        fill_opacity=0.9,
        line_opacity=0.1, 
        highlight=True,
        legend_name="Viviendas {} a nivel inferior".format(
            cat_name
        ),
        smooth_factor=1,
    ).add_to(layer)

    if legend_builder['thiner_area']:
        target_col = "Viviendas {} a nivel inferior".format(
            cat_name
        )
        colors = get_choroplet_colors(map=layer, drop_continuos_bar=True)
        int_legend_classes = legend_intervals_to_int(thiner_legend_classes)
        template = build_template(target_col, int_legend_classes, colors)
        macro_inf = MacroElement()
        macro_inf._template = Template(template)
        layer.add_child(macro_inf)

    thiner_choroplet.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=[thiner_area_name, cat_name],
            aliases=["Radio_id:", cat_name.capitalize() + ":"],
        )
    )
    
    # coarser area choroplet
    dissim_colname = f"dissim_idx_{cat_name}"
    if bins_classificator == 'NaturalBreaks':
        qcut = mapclassify.NaturalBreaks(coarser_area[dissim_colname].values, k=4)
    elif bins_classificator == 'Percentiles':
        qcut = mapclassify.Percentiles(coarser_area[dissim_colname].values, pct=[25, 50, 75, 100])
    else:
        # EqualInterval
        qcut = mapclassify.EqualInterval(coarser_area[dissim_colname].values, k=4)
    
    coarser_bins = [b for b in qcut.bins]
    coarser_bins.insert(0, 0.00)
    coarser_legend_classes = qcut.get_legend_classes()

    coarser_choroplet = folium.Choropleth(
        name=coarser_area_name.capitalize(),
        geo_data=coarser_area,
        data=coarser_area[[c for c in coarser_area.columns if c != "geometry"]],
        columns=[coarser_area_name, dissim_colname],
        key_on="properties." + coarser_area_name,
        fill_color="Greys",
        bins=coarser_bins,  
        fill_opacity=0.6,
        line_opacity=0.1,  
        highlight=True,
        legend_name="Disimilitud espacial: {}".format(
            cat_name
        ),
        smooth_factor=1,
    ).add_to(layer)

    if legend_builder['coarser_area']:
        target_col = "Disimilitud espacial"
        colors = get_choroplet_colors(map=layer, drop_continuos_bar=True)
        template = build_template(target_col, coarser_legend_classes, colors)
        macro_sup = MacroElement()
        macro_sup._template = Template(template)
        layer.add_child(macro_sup)

    coarser_choroplet.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=[coarser_area_name, dissim_colname],
            aliases=[coarser_area_name + ":", "Disimilitud espacial:"],
        )
    )

    folium.LayerControl().add_to(layer)

    return layer

