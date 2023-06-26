# `CENSAr` 
## Urban growth analysis tools

Combines vector and raster data to study the physical and qualitatuve growth of urban areas. 

**1. Urban extent detection**

Use the [raster data analysis](https://github.com/CEEU-lab/CENSAr/tree/develop/CENSAr/raster_data_analysis) module to calculate Landsat or Sentinel imagery based indexes (e.g. `Urban Index (UI)`) for classification problems resolution (Urban Sprawl detection):

<p align="center">
  <img src="CENSAr/img/urban_extent_detection.png" alt="Urban Extent"/>
</p>


**2. Census Tract distributions**

Simulate tracts distributions based on observed census data (`2001`, `2010`, `2020`)

<p align="center">
  <img src="CENSAr/img/informal_tracts_forecasting.png" alt="Informal dwellings by census radius"/>
</p>

(...) modelling functions available on [spatial distributions](https://github.com/CEEU-lab/CENSAr/tree/develop/CENSAr/spatial_distributions)


**3. Spatial features**

Instatiate city objects and evaluate their spatial distribution of attributes

* **Spatial Dissimilitude**

<p align="center">
  <img src="CENSAr/img/spatial_dissimilitude.png" alt="informal dwellings dissimilitude"/>
</p>

(...) indexes calculation available on [spatial features](https://github.com/CEEU-lab/CENSAr/tree/develop/CENSAr/spatial_features)

**4. Spatial correlation**

Detect variable groups concentration

* **Clustering**

<p align="center">
  <img src="CENSAr/img/spatial_correlation.png" alt="informal dwellings spatial correlation"/>
</p>

(...) clustering functions available on [clustering](https://github.com/CEEU-lab/CENSAr/tree/develop/CENSAr/clustering) 
