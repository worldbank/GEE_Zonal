import ee, os, re
from datetime import datetime
import pandas as pd
import io

class ZonalStats_Modis(object):
    '''
    Object to calculate zonal and temporal statistics from Earth Engine datasets (ee.ImageCollections) over vector shapes (ee.FeatureCollections)
    :param index: Which index to calculate (NDVI, EVI, NDSI, NDWI)
    :type index: str
    :param target_features: vector features
    :type target_features: ee.FeatureCollection (for now)
    :param statistic_type: statistic to calculate by zone
    :type statistic_type: str (one of mean, max, median, min, sum, stddev, var)
    :param output_name: file name for output statistics
    :type output_name: str
    :param scale: scale for calculation
    :type scale: int
    :param min_threshold: filter out values lower than min_threshold
    :type min_threshold: int
    :param water_mask: filter out water
    :type water_mask: boolean
    :param frequency: Optional, temporal frequency for aggregation
    :type frequency: str (monthly, annual, or original) defaults to original (raw temporal frequency of the dataset).
    :param temporal_stat: Optional, statistic for temporal aggregation
    :type temporal_stat: str (mean, max, median, min, or sum, defaults to None)
    :param output_dir: Optional, google drive directory to save outputs
    :type output_dir: str (defaults to gdrive_folder)
    '''
    def __init__(self, target_features, output_name,
                scale = 250, tile_scale = 4, output_dir = "gdrive_folder",
                start_year = 2001, end_year = 2020):
        cat = Catalog()
        self.target_features = target_features
        self.output_dir = output_dir
        self.output_name = output_name
        self.task = None
        self.scale = scale
        self.tile_scale = tile_scale
        self.start_year = start_year
        self.end_year = end_year
        
    def runZonalStats(self):
        dataset = ee.ImageCollection("MODIS/006/MCD12Q1").select('LC_Type1')
        
        years = list(range(self.start_year, self.end_year, 1))
        
        allowed_statistics = {
            "mean": ee.Reducer.mean(),
            "max": ee.Reducer.max(),
            "median": ee.Reducer.median(),
            "min": ee.Reducer.min(),
            "sum": ee.Reducer.sum(),
            "stddev": ee.Reducer.stdDev(),
            "var": ee.Reducer.variance(),
            "all" : ee.Reducer.mean() \
                .combine(ee.Reducer.minMax(), sharedInputs=True) \
                .combine(ee.Reducer.stdDev(), sharedInputs=True)
        }
                            
        def getStats(feature):
            
            for year in years:
                
                modis_year = dataset.filter(ee.Filter.calendarRange(year, year, 'year')).first()
                cropland = modis_year.eq(12).Or(modis_year.eq(14)).eq(1).multiply(ee.Image.pixelArea())
                
                zs_stat = ee.Image(cropland).reduceRegion(
                    geometry = feature.geometry(),
                    reducer = allowed_statistics['sum'],
                    scale = self.scale,
                    tileScale = self.tile_scale,
                    bestEffort = True,
                    maxPixels = 10e15
                ).get('LC_Type1')
                
                col_name = ee.String("cropland_").cat(ee.String(str(year)))
                feature = feature.set(col_name, zs_stat)
            
            return feature
            
        res = self.target_features.map(getStats)
        
        self.task = ee.batch.Export.table.toDrive(
            collection = res,
            description = f'Zonal statistics sum of Cropland',
            fileFormat = 'CSV',    
            folder = self.output_dir,
            fileNamePrefix = self.output_name,
        )
        self.task.start()

    def reportRunTime(self):
        start_time = self.task.status()['start_timestamp_ms']
        update_time = self.task.status()['update_timestamp_ms']
        if self.task.status()['state'] == "RUNNING":
            delta = datetime.now() - datetime.fromtimestamp(start_time/1000)
            print("Still running")
            print(f"Runtime: {delta.seconds//60} minutes and {delta.seconds % 60} seconds")
        if self.task.status()['state'] == "COMPLETED":
            delta = datetime.fromtimestamp(update_time/1000) - datetime.fromtimestamp(start_time/1000)
            print("Completed")
            print(f"Runtime: {delta.seconds//60} minutes and {delta.seconds % 60} seconds")
        if self.task.status()['state'] == "FAILED":
            print("Failed!")
            print(self.task.status()['error_message'])
        if self.task.status()['state'] == "READY":
            print("Status is Ready, hasn't started")