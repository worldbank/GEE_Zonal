"""
ZonalStats - Calcualte temporal/zonal statistics.
"""
import ee
from datetime import datetime
import pandas as pd
import io
import sys, os
from .catalog import Catalog
from .gee_helpers import gpd_to_gee
ee.Initialize()

class ZonalStats(object):
    """
    Python class to calculate zonal and temporal statistics from Earth Engine datasets (ee.ImageCollection or ee.Image) over vector shapes (ee.FeatureCollections).
    
    :param target_features: vector features
    :type target_features: ee.FeatureCollection, gpd.GeoDataFrame, or str path to a shapefile/GeoJSON
    :param statistic_type: method to aggregate image pixels by zone
    :type statistic_type: str - mean, max, median, min, sum, stddev, var, count, minmax, p75, p25, p95, all
    :param collection_id: ID for Earth Engine dataset
    :type collection_id: str, default: None
    :param ee_dataset: input dataset if no collection ID is provided
    :type ee_dataset: ee.Image or ee.ImageCollection, default: None
    :param band: name of image band to use
    :type band: str, default: None
    :param output_name: file name for output statistics if saved to Google Drive
    :type output_name: str, default: None
    :param output_dir: directory name for output statistics if saved to Google Drive
    :type output_dir: str, default: None
    :param frequency: temporal frequency for aggregation
    :type frequency: str (monthly, annual, or original), default: original
    :param temporal_stat: statistic for temporal aggregation
    :type temporal_stat: str (mean, max, median, min, sum), default: None
    :param scale: scale for calculation in mts
    :type scale: int, default: 250
    :param min_threshold: filter out values lower than treshold
    :type min_threshold: int, default: None
    :param mask: filter out observations where mask is zero
    :type mask: ee.Image, default: None
    :param tile_scale: tile scale factor for parallel processing
    :type tile_scale: int, default: 1
    :param start_year: specify start year for statistics
    :type start_year: int, default: None
    :param end_year: specify end year for statistics
    :type end_year: int, default: None
    :param scale_factor: scale factor to multiply ee.Image to get correct units
    :type scale_factor: int, default: None
    :param mapped: Boolean to indicate whether to use mapped or non-mapped version of zonal stats
    :type mapped: bool, default: False
    """
    def __init__(self, target_features, statistic_type, collection_id=None, ee_dataset = None, 
                band = None, output_name = None, output_dir = None, frequency = "original", 
                temporal_stat = None, scale = 250, min_threshold = None, mask = None, tile_scale = 1,
                start_year = None, end_year = None, scale_factor = None, mapped = False, return_image = False):
        self.collection_id = collection_id
        if collection_id is None and ee_dataset is None:
            raise Exception('One of collection_id or ee_dataset must be supplied')
        self.collection_suffix = collection_id[collection_id.rfind("/")+1:] if collection_id else None
        if ee_dataset is None:
            try:
                ee.ImageCollection(collection_id).getInfo()
                self.ee_dataset = ee.ImageCollection(collection_id) if band is None else ee.ImageCollection(collection_id).select(band)
            except:
                try:
                    ee.Image(collection_id).getInfo()
                    self.ee_dataset = ee.Image(collection_id) if band is None else ee.Image(collection_id).select(band)
                except:
                    raise Exception('Collection ID does not exist')
        else:
            self.ee_dataset = ee_dataset if band is None else ee_dataset.select(band)
        cat = Catalog()
        self.metadata = cat.datasets.loc[cat.datasets.id==collection_id].iloc[0] if collection_id else None
        self.target_features = target_features if type(target_features)==ee.FeatureCollection else gpd_to_gee(target_features)
        self.statistic_type = statistic_type
        self.frequency = frequency
        self.temporal_stat = temporal_stat
        self.output_dir = output_dir
        self.output_name = output_name
        self.task = None
        self.scale = scale
        self.min_threshold = min_threshold
        self.mask = mask
        self.scale_factor = scale_factor
        self.tile_scale = tile_scale
        self.start_year = start_year
        self.end_year = end_year
        self.mapped = mapped
        self.return_image = return_image

    def yList(self, start=None, end=None):
        '''
        Create list of years from a given dataset
        '''
        if start is None:
            years = list(range(self.metadata.startyear, self.metadata.endyear+1, 1))
        else:
            years = list(range(start, end+1, 1))
        return ee.List(years)

    def ymList(self, start=None, end=None):
        '''
        Create list of year/month pairs from a given dataset
        '''
        if start is None and end is None:
            start = self.metadata.start_date
            end = self.metadata.end_date
            ym_range = pd.date_range(datetime(start.year, start.month, 1), datetime(end.year, end.month, 1), freq="MS")
            ym_range = list(date.strftime("%Y%m") for date in ym_range)
        else:
            ym_range = pd.date_range(datetime(start, 1, 1), datetime(end, 12, 31), freq="MS")
            ym_range = list(date.strftime("%Y%m") for date in ym_range)
        return ee.List(ym_range)
    
    def ymList_ee(self):
        '''
        Create list of year/month pairs from a given dataset using EE
        '''
        def iter_func(image, newlist):
            date = ee.Number.parse(image.date().format("YYYYMM")).format()
            newlist = ee.List(newlist)
            return ee.List(newlist.add(date).sort())
        ymd = self.ee_dataset.iterate(iter_func, ee.List([]))
        return ee.List(ymd).distinct()
    
    def temporalStack(self, date_list, freq, stat):
        allowed_statistics_ts = {
            "mean": ee.Reducer.mean(),
            "max": ee.Reducer.max(),
            "median": ee.Reducer.median(),
            "min": ee.Reducer.min(),
            "sum": ee.Reducer.sum(),
            "stddev": ee.Reducer.stdDev(),
        }
        if stat not in allowed_statistics_ts.keys():
            raise Exception(
                "temporal satistic must be one of be one of {}".format(", ".join(list(allowed_statistics_ts.keys())))
                )
        def aggregate_monthly(ym):
            date = ee.Date.parse("YYYYMM", ym)
            y = date.get('year')
            m = date.get('month')
            monthly = self.ee_dataset.filter(ee.Filter.calendarRange(y, y, 'year')) \
                .filter(ee.Filter.calendarRange(m, m, 'month')) \
                .reduce(allowed_statistics_ts[stat]) \
                .set('month', m) \
                .set('year', y) \
                .set('system:index', ee.String(y.format().cat('_').cat(m.format())))
            return monthly
        def aggregate_annual(y):
            y = ee.Number(y)
            annual = self.ee_dataset.filter(ee.Filter.calendarRange(y, y, 'year')) \
                .reduce(allowed_statistics_ts[stat]) \
                .set('year', y) \
                .set('system:index', ee.String(y.format()))            
            return annual
        if freq=="monthly":
            byTime = ee.ImageCollection.fromImages(date_list.map(aggregate_monthly))
        if freq=="annual":
            byTime = ee.ImageCollection.fromImages(date_list.map(aggregate_annual))
        return byTime #.toBands()
        
    def applyWaterMask(self, image, year=None):
        land_mask = ee.Image("MODIS/MOD44W/MOD44W_005_2000_02_24").select('water_mask').eq(0)
        return image.updateMask(land_mask)
        
    def applyMinThreshold(self, image, min_threshold):
        bool_mask = image.gte(min_threshold)
        return image.updateMask(bool_mask)
        
    def applyMask(self, image, mask):
        return image.updateMask(mask)

    def applyScaleFactor(self, image):
        return image.multiply(self.scale_factor)

    def applyScaleFactorIC(self, image_collection, scale_factor):
        return image_collection.map(self.applyScaleFactor)
    
    def runZonalStats(self):
        """
        Run zonal statistics aggregation
        
        :return: tabular statistics
        :rtype: DataFrame or dict with EE task status if output_name/dir is specified
        """
        if self.frequency not in ['monthly', 'annual', 'original']:
            raise Exception("frequency must be one of annual, monthly, or original")
        if self.frequency == "monthly":
            timesteps = self.ymList(self.start_year, self.end_year)
        elif self.frequency == "annual":
            timesteps = self.yList(self.start_year, self.end_year)
        elif self.frequency == "original":
            if self.start_year is not None and self.end_year is not None:
                start_year_format = datetime(self.start_year, 1, 1).strftime("%Y-%m-%d")
                end_year_format = datetime(self.end_year, 12, 31).strftime("%Y-%m-%d")
                self.ee_dataset = self.ee_dataset.filterDate(start_year_format, end_year_format)
        # byTimesteps = self.ee_dataset.toBands() if self.frequency=="original" else self.temporalStack(timesteps, self.frequency, self.temporal_stat)
        if self.frequency=="original":
            if type(self.ee_dataset) == ee.image.Image:
                byTimesteps = self.ee_dataset
            elif type(self.ee_dataset) == ee.imagecollection.ImageCollection:
                byTimesteps = self.ee_dataset.toBands()
        else:
            byTimesteps = self.temporalStack(timesteps, self.frequency, self.temporal_stat)
            # byTimesteps = byTimesteps.toBands()
        
        # pre-processing
        if self.mask is not None:
            if self.mask == "water":
                byTimesteps = self.applyWaterMask(byTimesteps)
            elif type(self.mask) == ee.image.Image:
                byTimesteps = self.applyMask(byTimesteps, self.mask)
        if self.min_threshold is not None:
            byTimesteps = self.applyMinThreshold(byTimesteps, self.min_threshold)
        if self.scale_factor is not None:
            byTimesteps = self.applyScaleFactorIC(byTimesteps, self.scale_factor)
        
        allowed_statistics = {
            "count": ee.Reducer.frequencyHistogram().unweighted(),
            "mean": ee.Reducer.mean(),
            "max": ee.Reducer.max(),
            "median": ee.Reducer.median(),
            "min": ee.Reducer.min(),
            "sum": ee.Reducer.sum(),
            "stddev": ee.Reducer.stdDev(),
            "var": ee.Reducer.variance(),
            "minmax" : ee.Reducer.minMax(),
            "p75" : ee.Reducer.percentile([75]), # maxBuckets=10 , minBucketWidth=1, maxRaw=1000
            "p25" : ee.Reducer.percentile([25]), # maxBuckets=10 , minBucketWidth=1, maxRaw=1000
            "p95" : ee.Reducer.percentile([95]), # maxBuckets=10 , minBucketWidth=1, maxRaw=1000
            "all" : ee.Reducer.mean() \
                .combine(ee.Reducer.minMax(), sharedInputs=True) \
                .combine(ee.Reducer.stdDev(), sharedInputs=True)
        }
        
        def combine_reducers(reducer_list):
            for i, r in enumerate(reducer_list):
                if i==0:
                    reducer = r
                if i>0:
                    reducer = reducer.combine(r, sharedInputs=True)
            return reducer
        
        if type(self.statistic_type) == str:            
            if self.statistic_type not in allowed_statistics.keys():
                raise Exception(
                    "satistic must be one of be one of {}".format(", ".join(list(allowed_statistics.keys())))
                    )
            else:
                reducer = allowed_statistics[self.statistic_type]                
        elif type(self.statistic_type) == list:
            for stat_type in self.statistic_type:
                if stat_type not in allowed_statistics.keys():
                    raise Exception(
                        "satistic must be one of be one of {}".format(", ".join(list(allowed_statistics.keys())))
                        )
            reducer_list = [allowed_statistics[stat_type] for stat_type in self.statistic_type]
            reducer = combine_reducers(reducer_list)
        
        if self.mapped == True:
            def zs_func(feature):
                zs_result = byTimesteps.reduceRegion(
                    reducer = reducer,
                    geometry = feature.geometry(),
                    scale = self.scale,
                    maxPixels = 10e15, #1e13
                    tileScale = self.tile_scale
                    )
                feature = feature.set(zs_result)
                return feature
            zs = self.target_features.map(zs_func) #.getInfo()
        else:
            zs = ee.Image(byTimesteps).reduceRegions(
                collection = self.target_features, 
                reducer = reducer,
                scale = self.scale,
                tileScale = self.tile_scale
            )
        if self.output_dir is not None and self.output_name is not None:
            self.task = ee.batch.Export.table.toDrive(
                collection = zs,
                description = f'Zonal statistics for {self.collection_suffix}',
                fileFormat = 'CSV',    
                folder = self.output_dir,
                fileNamePrefix = self.output_name,
            )
            self.task.start()
            # return(self)
        elif self.return_image:
            return(byTimesteps)
        else:
            res = zs.getInfo()
            return(self.get_zonal_res(res))
    
    def get_zonal_res(self, res, rename=None):
        ''' 
        Create a data frame from the results of GEE zonal
        :param res: response from RunZonalStats method retrieved via featureCollection.getInfo()
        :type res: dictionary from ee.FeatureCollection
        '''
        feats = res['features']
        ids = [f['id'] for f in feats]
        series = [pd.Series(f['properties']) for f in feats]
        df = pd.DataFrame(data=series, index=ids)
        if rename:
            df.rename(columns=rename, inplace=True)
        return df

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
    
    def getZonalStats(self, drive):
        folder = drive.ListFile({'q': f"title = '{self.output_dir}' and trashed=false and mimeType = 'application/vnd.google-apps.folder'"}).GetList()[0]
        folder_id = folder['id']
        export_file = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false and title contains '{self.output_name}'"}).GetList()[0]
        s = export_file.GetContentString()
        c = pd.read_csv(io.StringIO(s))
        c.drop(['.geo', 'system:index'], axis=1, inplace=True)
        return c