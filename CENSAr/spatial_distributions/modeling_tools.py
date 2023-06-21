import os

import numpy as np
import geopandas as gpd
from numpy.random import choice

from CENSAr.datasources import tracts_matching_0110

DATA_DIR = os.getenv(
    "CENSAR_DATA_DIR",
    "https://storage.googleapis.com/python_mdg/censar_data",
)
CARTO_DIR = os.getenv(
    "CENSAR_CARTO_DIR",
    "https://storage.googleapis.com/python_mdg/censar_carto",
)


def totals_forecast(
    gdf_pers_01,
    gdf_var_01,
    gdf_pers_10,
    gdf_var_10,
    proyections_df,
    namedept,
    base_year,
    forecast_year):
    """
    Returns the projected number of households or residential units
    based on Statistics National Institute (INDEC) total persons
    forecasts by department and previous census ratios between
    persons and households/residential units.

    Parameters
    ----------
    gdf_pers_01 : gpd.GeoDataFrame
        Geodataframe of 2001 Census with total number of persons by tract.
    gdf_var_01 : gpd.GeoDataFrame
        Geodataframe of 2001 Census 2001 with  household or residential units by tract.
    gdf_pers_10 : gpd.GeoDataFrame
        Geodataframe of 2010 Census with total number of persons by tract.
    gdf_var_10 : gpd.GeoDataFrame
        Geodataframe of 2010 Census 2001 with  household or residential units by tract.
    proyections_df : pd.DataFrame
        Dataframe with total persons forecasts by department and year.
    namedept : str
        Name of the department in the preyections dataframe.
    base_year : str
        Reference year to define persons to households/residential units ratio. If
        none of 2001 or 2010 are selected, the average between them is used.
    forecast_year : str
        Target year to the forecasted number of persons by department.

    Returns
    -------
    tot_var:int
        Projected number of households or residential units.
    """

    if base_year == "2001":
        ratio = round(gdf_pers_01["total"].sum() / gdf_var_01["total"].sum(), 2)
    elif base_year == "2010":
        ratio = round(gdf_pers_10["total"].sum() / gdf_var_10["total"].sum(), 2)
    else:
        # Moderate growth
        ratio_01 = round(gdf_pers_01["total"].sum() / gdf_var_01["total"].sum(), 2)
        ratio_10 = round(gdf_pers_10["total"].sum() / gdf_var_10["total"].sum(), 2)
        ratio = round((ratio_01 + ratio_10) / 2, 2)

    proy_totpers = proyections_df.loc[namedept, forecast_year]
    tot_var = int(proy_totpers / ratio)
    return tot_var


def distribute_totals_tract(tot_var, weights, catname, forecast_year, gdf):
    """
    Returns the projected number of households or residential units
    distributed by census tract based on .

    Parameters
    ----------
    tot_var : int
        Total number of households or residential units to be distributed by tract.
    weights : dict
        Tracts probabilites defined based on observed distributions.
    catname : str
        Name of the column to be used as reference distribution.
    forecast_year : str
        Year of projected total.
    gdf : gpd.GeoDataFrame
        Geodataframe where the new variable by tract will be created (e.g. 2010 or 2020)

    Returns
    -------
    totals_by_tract:pd.Series
        Total number or target category of households/residential units by tract.
    """
    gdf_reset = gdf.reset_index().copy()

    if weights is None:
        # Gets observed distribution
        gdf_reset[f"{catname}_dist"] = (
            gdf_reset[f"{catname}"] / gdf_reset[f"{catname}"].sum()
        )
        weights = (
            gdf_reset[f"{catname}_dist"].fillna(0) / gdf_reset[f"{catname}_dist"].sum()
        )

    np.random.seed(1)
    drawn_tracts = choice(gdf_reset["link"], tot_var, p=weights)

    totals_tract = np.unique(drawn_tracts, return_counts=True)
    proj_totals = dict(zip(totals_tract[0], totals_tract[1]))

    gdf_reset[f"{catname}_{forecast_year}"] = (
        gdf_reset["link"].map(proj_totals).fillna(0)
    )
    totals_by_tract = dict(
        zip(gdf_reset["link"], gdf_reset[f"{catname}_{forecast_year}"])
    )
    return totals_by_tract


def observed_dist(catname, idx_col, base_year, gdf_base, gdf_forecast):
    """
    Returns observed percentages by tract for a given variable distribution.

    Parameters
    ----------
    catname : str | dict
        Name of the column to be used as reference distribution. Or dictionary
        following the year of the distribution and the category name
        (e.g. {'2001':'casilla', '2010':rancho})
    idx_col : str
        Name of the tracts index column in the geodataframe where the category
        is being simulated.
    base_year : str
        Year to be used for the new simulated column naming. For example,
        'casilla_2010'. This number identifies in the simulated geodataframe the
        year used as based distribution.
    gdf_base : gpd.GeoDataFrame
        Geodataframe housing the category by tract used as observed distribution
    gdf_forecast : gdp.GeoDataFrame
        Geodataframe where the new category by tract is being simulated.

    Returns
    -------
    var_tract:dict
        Probabilities distribution by tract (e.g. {'22007213': 0.4}).
    """
    if type(catname) is dict:
        # overwrites category name based on the observed year
        catname = catname[base_year]
    tract_pct = gdf_base[catname] / gdf_base[catname].sum()
    cat_dist = dict(zip(tract_pct.index, tract_pct.values))
    gdf_reset = gdf_forecast.reset_index()
    var_pct = round(gdf_reset[idx_col].map(cat_dist).astype(float), 4)
    gdf_reset[f"{catname}_{base_year}"] = var_pct
    var_tract = dict(zip(gdf_reset[idx_col], gdf_reset[f"{catname}_{base_year}"]))

    return var_tract


def var_forecast(
    gdf_2001, gdf_2010, catname, gdf_2020, pct_target, base_year, 
    tot_colname, calibration_vector={'weights':None, 'mix_dist':False}):
    """
    Returns the total number of households or residential units for a given
    category with his distribution by census tract.

    Parameters
    ----------
    gdf_2001 : gpd.GeoDataFrame
        Geodataframe of 2001 Census 2001 with household or residential units by tract.
    gdf_2010 : gpd.GeoDataFrame
        Geodataframe of 2010 Census 2001 with household or residential units by tract.
    catname : str | dict
        Name of the column to be used as reference distribution. Or dictionary
        following the year of the distribution and the category name
        (e.g. {'2001':'casilla', '2010':rancho})
    gdf_2020 : gpd.GeoDataFrame
        Census geodataframe where the category is being simulated.
    pct_target : float
        Percentage representing the weight of the simulated category over the total
        households or residential units (e.g. 2.5 for informal settelments).
    base_year : str
        Reference year to define the observed households/residential units
        distribution. If none of 2001 or 2010 are selected, the average between them is used.
    tot_colname : str
        name of the total variables column in the census geodataframe where
        the category is being simulated.
    calibration_vector : dict, default "{'weights':None, 'mix_dist':False}"
        Percentage of tract geometries intersected by other polygons.

    Returns
    -------
    totcat:int
        Total number of residential units or households for a given category.
    weights: pd.Series
    """
    if gdf_2010.equals(gdf_2020):
        # 2020 geometries are not available
        idx_col = "link"
        gdf_2020 = gdf_2020.reset_index().copy()
    else:
        # 2020 geometries are available
        if base_year not in ["2001", "2010"]:
            idx_col = "link"
        else:
            idx_col = f"link_{base_year}"

    if base_year == "2001":
        dist_dict = observed_dist(
            catname=catname,
            idx_col=idx_col,
            base_year="2001",
            gdf_base=gdf_2001,
            gdf_forecast=gdf_2020,
        )  # 2001 distribution
        gdf_2020[f"{catname}_2001"] = gdf_2020[idx_col].map(dist_dict)
        dist_var = gdf_2020[f"{catname}_2001"]

    elif base_year == "2010":
        dist_dict = observed_dist(
            catname=catname,
            idx_col=idx_col,
            base_year="2010",
            gdf_base=gdf_2010,
            gdf_forecast=gdf_2020,
        )  # 2010 distribution
        gdf_2020[f"{catname}_2010"] = gdf_2020[idx_col].map(dist_dict)
        dist_var = gdf_2020[f"{catname}_2010"]

    else:
        data = {"2001": gdf_2001, "2010": gdf_2010}
        for year in ["2001", "2010"]:
            if idx_col == "link":
                idx_col_year = f"link_{year}"
            dist_dict = observed_dist(
                catname=catname,
                idx_col=idx_col_year,
                base_year=year,
                gdf_base=data[year],
                gdf_forecast=gdf_2020,
            )
            gdf_2020[f"var_{year}"] = gdf_2020[idx_col_year].map(dist_dict)

        gdf_2020["var_0110"] = round(
            (gdf_2020["var_2001"] + gdf_2020["var_2010"]) / 2, 4
        )  # middle beetwen 01 and 10 
        dist_var = gdf_2020[f"var_0110"]

    if calibration_vector['weights']: 
        gdf_2020['calibration_weights'] = gdf_2020[idx_col].map(calibration_vector['weights'])

        # distribution based on the spatial relation with calibration 
        calibration_dist_var =  gdf_2020['calibration_weights'].fillna(1)/gdf_2020['calibration_weights'].sum() 
        
        # mix observed 2001 & 2010 distributions with intersected calibration polygons
        if calibration_vector['mix_dist']:
            dist_var_ = round((dist_var + calibration_dist_var)/2, 4)
            dist_var = dist_var_.copy() 
        else:
            # use calibration vector only
            dist_var = calibration_dist_var.copy()

    totcat = int(
        gdf_2020[tot_colname].sum() * pct_target / 100
    )  # total number to be distributed by tract
    weights = dist_var.fillna(0) / dist_var.sum()
    
    return totcat, weights


def simulate_total_var(
    gdf_pers_01,
    gdf_var_01,
    gdf_pers_10,
    gdf_var_10,
    proy_df,
    namedept,
    base_year,
    forecast_year,
    catname="total",
):
    """
    Distributes the projected number of households or residential units by tract
    following the same distribution in the most recent census information.
    Today 2010 census is the latest data with total persons available by tract.

    Parameters
    ----------
    gdf_pers_01 : gpd.GeoDataFrame
        Geodataframe of 2001 Census with total number of persons by tract.
    gdf_var_01 : gpd.GeoDataFrame
        Geodataframe of 2001 Census 2001 with  household or residential units by tract.
    gdf_pers_10 : gpd.GeoDataFrame
        Geodataframe of 2010 Census with total number of persons by tract.
    gdf_var_10 : gpd.GeoDataFrame
        Geodataframe of 2010 Census 2001 with  household or residential units by tract.
    proyections_df : pd.DataFrame
        Dataframe with total persons forecasts by department and year.
    namedept : str
        Name of the department in the preyections dataframe.
    base_year : str
        Reference year to define persons to households/residential units ratio. If
        none of 2001 or 2010 are selected, the average between them is used.
    forecast_year : str
        Year of projected total.
    catname : str, default 'total'
        Name of the output column by tract.

    Returns
    -------
    sim_dist:pd.Series
          Total number of households/residential units by tract.
    """
    # Get number of households or residential units based on persons projection
    proj_total = totals_forecast(
        gdf_pers_01,
        gdf_var_01,
        gdf_pers_10,
        gdf_var_10,
        proy_df,
        namedept,
        base_year,
        forecast_year,
    )
    print(f"The total number of projected households/residential units is {proj_total}")

    # And follows the observed total households or residential units distribution in the 2010 tracts
    sim_dist = distribute_totals_tract(
        tot_var=proj_total,
        weights=None,
        catname=catname,
        forecast_year=forecast_year,
        gdf=gdf_var_10,
    )
    return sim_dist


def simulate_cat_var(
    gdf_var_01,
    gdf_var_10,
    base_year,
    forecast_year,
    forecast_gdf,
    pct_val,
    catname,
    tot_colname,
    calibration_vector={'weights':None, 'mix_dist':False}):
    """
    Distributes the estimated number of households or residential units by tract
    following the same distribution in the most recent census information.

    Parameters
    ----------
    gdf_var_01 : gpd.GeoDataFrame
        Geodataframe of 2001 Census 2001 with household or residential units by tract.
    gdf_var_10 : gpd.GeoDataFrame
        Geodataframe of 2010 Census 2001 with household or residential units by tract.
    base_year : str
        Reference year to define the observed households/residential units
        distribution. If none of 2001 or 2010 are selected, the average between them is used.
    forecast_year : str
        Year of the census geodataframe where the category is being simulated.
    forecast_gdf : gpd.GeoDataFrame
        Census geodataframe where the category is being simulated.
    pct_val : float
        Percentage representing the weight of the simulated category over the total
        households or residential units (e.g. 2.5 for informal settelments).
    catname : str | dict
        Name of the column to be used as reference distribution. Or dictionary
        following the year of the distribution and the category name
        (e.g. {'2001':'casilla', '2010':rancho})
    tot_colname : str
        name of the total variables column in the census geodataframe where
        the category is being simulated.
    calibration_vector : dict, default "{'weights':None, 'mix_dist':False}"
        Percentage of tract geometries intersected by other polygons.

    Returns
    -------
    sim_dist:pd.Series
          Total number of target category household/units by tract.
    """
    # Calculate tract distribution based on coarser area total
    cat_var, probs = var_forecast(
        gdf_2001=gdf_var_01,
        gdf_2010=gdf_var_10,
        catname=catname,
        gdf_2020=forecast_gdf,
        pct_target=pct_val,
        base_year=base_year,
        tot_colname=tot_colname,
        calibration_vector = calibration_vector
    )
    
    sim_dist = distribute_totals_tract(
        tot_var=cat_var,
        weights=probs,
        catname=None,
        forecast_year=forecast_year,
        gdf=forecast_gdf,
    )
    return sim_dist


def tracts_2020_to_2010(tracts_2020_gdf, tracts_2010_gdf):
    """
    Matches 2020 with 2010 census tract geometries.

    Parameters
    ----------
    tracts_2020_gdf : gpd.GeoDataFrame
        Geodataframe with 2020 census tract geometries.
    tracts_2010_gdf : gdp.GeoDataFrame
        Geodataframe with 2010 census tract geometries.

    Returns
    -------
    tracts_2020_gdf:gpd.GeoDataFrame
        Geodataframe with 2020 census tract geometries and 2010 link column.
    """
    tracts_2020_gdf_ = tracts_2020_gdf[["link", "geometry"]].copy()
    tracts_2020_gdf_rep = tracts_2020_gdf_.to_crs(tracts_2010_gdf.crs)
    tracts_2020_gdf_rep["geometry"] = tracts_2020_gdf_rep.geometry.centroid
    tracts_20_to_10 = gpd.sjoin(
        tracts_2020_gdf_rep, tracts_2010_gdf, predicate="within"
    )
    tracts_20_to_10.rename(
        columns={"link_left": "link_2020", "link_right": "link_2010"}, inplace=True
    )

    tracts_2010 = dict(zip(tracts_20_to_10.link_2020, tracts_20_to_10.link_2010))
    tracts_2020_gdf["link_2010"] = tracts_2020_gdf.link.map(tracts_2010)

    # Assign the idx of the nearest tract
    NaN2020 = tracts_2020_gdf[tracts_2020_gdf["link_2010"].isna()].copy()
    NaN2020["geometry"] = NaN2020.geometry.centroid

    tracts_missing = NaN2020.to_crs(tracts_2010_gdf.crs).sjoin_nearest(tracts_2010_gdf)
    tracts_missing.rename(
        columns={"link_left": "link_2020", "link_right": "link_2010_"}, inplace=True
    )
    tracts_nearest = dict(zip(tracts_missing.link_2020, tracts_missing.link_2010_))

    tracts_2020_gdf["link_2010"].fillna(
        tracts_2020_gdf["link"].map(tracts_nearest), inplace=True
    )
    return tracts_2020_gdf


def tracts_2010_to_2001(tracts_2020_gdf):
    """
    Creates 2001 census link column for the 2020 census geodataframe.

    Parameters
    ----------
    tracts_2020_gdf : gpd.GeoDataFrame
        Geodataframe with 2020 census tract geometries.

    Returns
    -------
    tracts_2020_gdf:gpd.GeoDataFrame
        Geodataframe with 2020 census tract geometries and 2001 link column.
    """

    if "link_2010" not in tracts_2020_gdf.columns:
        raise TypeError("GeoDataFrame must contain 2010 census link reference")

    df = tracts_matching_0110(
        prov="corrientes",
        var_types={"Link01": "object", "Link10": "object"},
        root=DATA_DIR,
    )
    link2001 = dict(zip(df.Link10, df.Link01))
    tracts_2020_gdf["link_2001"] = tracts_2020_gdf["link_2010"].map(link2001)
    return tracts_2020_gdf
