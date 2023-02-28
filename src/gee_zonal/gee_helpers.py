import ee
import pandas as pd
import geopandas as gpd
import geojson
from shapely.geometry import Polygon, MultiPolygon
import warnings

def gpd_to_gee(inD):
    '''Convert a geopandas GeoDataFrame to EE Feature Collection
    :param inD: Input features
    :type inD: geopandas.GeoDataFrame or path of shapefile/geojson
    :return ee.FeatureCollection
    '''
    if type(inD)==str:
        gdf = gpd.read_file(inD)
    elif type(inD)==gpd.GeoDataFrame:
        gdf = inD.copy()
    else:
        raise Exception("Input features must be either GeoDataFrame or readable by Geopandas")
    if gdf.crs.to_string() != 'EPSG:4326':
        warnings.warn(f"Geometries were converted using native crs: {gdf.crs.to_string()}")
    all_polys = []
    for idx, row in gdf.iterrows():
        try:
            shpJSON = geojson.Feature(
                geometry = row['geometry'], 
                properties= {key:value for key, value in row.items() if key != 'geometry'}
            )
            ee_feat = ee.Feature(shpJSON)
            all_polys.append(ee_feat)
        except:
            print(f"feature {idx} is invalid")            
    cur_ee = ee.FeatureCollection(all_polys)
    return(cur_ee)

def authenticateGoogleDrive():
    try:
        from pydrive.drive import GoogleDrive
        from pydrive.auth import GoogleAuth
        gauth = GoogleAuth()
        drive = GoogleDrive(gauth)
        return drive
    except:
        print("Google Drive tools are not available")

