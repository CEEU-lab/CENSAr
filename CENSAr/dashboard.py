from PIL import Image
#import orca
import streamlit as st
#from streamlit_folium import st_folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd

from datasources import *
from contexto_urbano import *
from utils import *

st.set_page_config(
    page_title="CENSAr",
    page_icon="./sl//favicon.ico",
    layout='wide',
    initial_sidebar_state='collapsed')

st.write(
        """
<iframe src="resources/sidebar-closer.html" height=0 width=0>
</iframe>""",
        unsafe_allow_html=True,
    )

# CSS
with open('./sl/style.css') as f:
    st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)

menu_list = st.sidebar.radio('Secciones', ["Inicio",  "Segregación espacial"])

if menu_list == "Inicio":

    col1, _ ,col3 = st.columns((2,0.5,2))
    col1.header("CENSAr")
    col1.markdown("""
                  ```
                  > Herramientas de análisis territorial
                  ```
                  """)

    landing = Image.open('img/tejido_urbano.png')
    col3.image(landing, width=250)
    
    st.subheader('**Componentes de análisis**')
    st.markdown("""
    * **Poblacion**:
        ```
        - esta seccion permite estudiar la distribución territorial de un conjunto de variables censales. Todas ellas, vinculadas
        a las características de la población y su distribucion en el espacio urbano.
        ```
        """)

elif menu_list == "Segregación espacial":

    st.subheader('Visor de patrones de asentamiento')
    st.markdown('Seleccione una variable censal para analizar su distribución en la región deseada')
    st.markdown(' ')

    col1, col2, col3, col4 = st.columns((1,1,1,1))
    regions = ['Capital Federal', 'Bs.As. G.B.A. Zona Oeste', 'Bs.As. G.B.A. Zona Norte', 'Bs.As. G.B.A. Zona Sur']
    region = col1.selectbox('Region', regions)

    indicators = ['Calidad constructiva de la vivienda', 'Calidad de conexiones a servicios básicos',
                  'Viviendas en construcción', 'Viviendas en altura', 'Viviendas en áreas de difícil acceso']
    indicator = col2.selectbox('Indicador', indicators)

    if indicator == 'Calidad constructiva de la vivienda':
        with st.expander("Inspeccionar indicador"):
            st.write("""
                Según el Censo 2010, la calidad de la vivienda se encuentra determinada por dos tipos de materiales: los predominantes
                en los pisos y cubierta exterior de sus techos. Así, el indicador se estructura en cuatro calidades (para una lectura más
                detallada sobre las mismas se puede consultar la [siguiente documentación](https://www.indec.gob.ar/ftp/cuadros/poblacion/informe_calmat_2001_2010.pdf).
                El indicador propuesto agrupa las calidades III y IV como irrecuperables y mantiene las I y II como aceptables y recuperables respectivamente.
                Para el análisis de distribución territorial, se utiliza el [índice de Duncan](https://www.scielo.cl/scielo.php?script=sci_arttext&pid=S0250-71612006000300004)
                (comunmente utilizado en el estudio de segregación territorial).
                Este describe la manera en la que se distribuye un grupo en el espacio a partir de la relación entre distintos niveles administrativos
                (uno de mayor y otro de menor agregación). El mismo varía entre cero y uno indicando distribuciones igualitarias o de máxima concentración.
                El valor cero sólo se alcanza cuando en todas las unidades hay la misma proporción entre el grupo estudiado y el resto de población.
            """)

    if (indicator == 'Calidad constructiva de la vivienda') and (region == 'Capital Federal'):

        area_superior = col3.selectbox('Area superior', ['barrio','comuna'])
        categoria_inmat = col4.selectbox('Categoría', ['recuperables', 'irrecuperables', 'aceptables'])
    
        radios_geom = radios_caba_2010()
        radios_vals = inmat_radios_caba_2010()

    elif (indicator == 'Calidad constructiva de la vivienda') and (region != 'Capital Federal'):

        area_superior = col3.selectbox('Area superior', ['departamento'])
        categoria_inmat = col4.selectbox('Categoría', ['aceptables', 'recuperables', 'irrecuperables'])
        radios_geom = radios_gba24_2010().to_crs(4326)
        radios_vals = inmat_radios_gba24_2010()

    else:
        pass

    inmat_inf = radios_inmat_2010(region_name=region, geog=radios_geom, vals=radios_vals)

    col5, col6 = st.columns((1,1))
    fig1 = construye_territorio(gdf=inmat_inf, nombre_unidad_s=area_superior, nombre_unidad_i='str_link',
                                nombre_variable='total_inmat', nombre_categoria=categoria_inmat, estadistico='CEC', tipo='bar', dinamico=True)

    fig2 = construye_territorio(gdf=inmat_inf, nombre_unidad_s=area_superior, nombre_unidad_i='str_link',
                                nombre_variable='total_inmat', nombre_categoria=categoria_inmat, estadistico='CEC', tipo='scatter', dinamico=True)

    col5.plotly_chart(fig1, use_container_width=True)
    col6.plotly_chart(fig2, use_container_width=True)

    territorio_superior = construye_territorio(gdf=inmat_inf, nombre_unidad_s=area_superior, nombre_unidad_i='str_link',
                                            nombre_variable='total_inmat', nombre_categoria=categoria_inmat, estadistico=None, tipo=None)

    inmat_sup = indice_geografia_superior(territorio_df=territorio_superior, nombre_area=area_superior, nombre_region=region)
    fig3 = plot_folium_dual_choroplet(gdf_inferior=inmat_inf, gdf_superior=inmat_sup, categoria=categoria_inmat,
                                    indicador_superior='CEC', nombre_superior=area_superior, nombre_region=region)
    folium_static(fig3, width=1350, height=500)
