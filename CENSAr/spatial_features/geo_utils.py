import geopandas as gpd

def label_thiner_area_with_coarser_idx(thiner_geom, coarser_geom, perfect_match=False):
    """
    doctring
    """

    if perfect_match:
        print("Write section")
        # TODO: write code to map coarser area label to thiner geometries
        # when thiner polygons have all their area inside a coarser Polygon
        # thiner_area[coarser_idx] = thiner_area[thiner_idx].map(coarser_area[coarser_idx])

    else:
        # thiner area polygons doesn't match perfectly with coarser area boundaries
        thiner_geom.reset_index(inplace=True)
        thiner_geom['area_tot'] = thiner_geom.area
        geom_inter = gpd.overlay(coarser_geom, thiner_geom, how='intersection')

        geom_inter['ovl_area'] = geom_inter.area
        geom_inter['area_pct'] = round(geom_inter['ovl_area'] / geom_inter['area_tot'], 3)
        geom_inter = geom_inter.sort_values(by='area_pct', ascending=False).reset_index(drop=True)
        geom_inter.drop_duplicates(subset='link', keep='first', inplace=True)

        geom_inter.drop(columns=['ovl_area', 'area_tot', 'area_pct'], inplace=True)

        # TODO: Generalize
        thiner_area = thiner_geom.merge(geom_inter[['link', 'barrio', 'grupo']], on='link')

        # TODO: Avoid the generation of 'level_0' column so there is no need to drop it 
        if 'level_0' in thiner_area.columns:
            thiner_area.drop(columns='level_0', inplace=True)
    return thiner_area