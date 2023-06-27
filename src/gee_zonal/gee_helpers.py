import ee
import pandas as pd
import geopandas as gpd
import geojson
from shapely.geometry import Polygon, MultiPolygon
import warnings
from os.path import join, expanduser, exists

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

def authenticateGoogleDrive(creds_dir=join(expanduser('~'), '.config', 'creds')):
    try:
        from pydrive.drive import GoogleDrive
        from pydrive.auth import GoogleAuth
        gauth = GoogleAuth()
        gauth.LoadClientConfigFile(join(creds_dir, 'client_secrets.json'))
        gauth.LoadCredentialsFile(join(creds_dir, "gdrive_creds.txt"))
        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()
        # Save the current credentials to a file
        gauth.SaveCredentialsFile(join(creds_dir, "gdrive_creds.txt"))
        drive = GoogleDrive(gauth)
        return drive
    except ImportError:
        print("pydrive is not installed. Install pydrive if you want to use Google Drive functionality")
    except Exception as e:
        print(e)