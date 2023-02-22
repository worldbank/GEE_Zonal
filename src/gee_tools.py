import ee, os, re
from datetime import datetime
import pandas as pd
import io

repo_dir = os.path.dirname(os.path.realpath(__file__)) # if Notebooks could also access thorugh ..

class Catalog(object):
    '''
    Inventory of Earth Engine datasets, saved as a pandas DataFrame
    This is retrieved from https://github.com/samapriya/Earth-Engine-Datasets-List
    All credit goes to Samapriya Roy!
    '''
    def __init__(self, datasets = None, redownload = False):
        def load_datasets():
            if redownload == True:
                datasets = pd.read_csv("https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.csv")
                datasets = datasets[['id', 'provider', 'title', 'start_date', 'end_date', 'startyear', 'endyear', 'type', 'tags', 'asset_url', 'thumbnail_url']]
                datasets.to_csv(os.path.join(repo_dir, "Earth-Engine-Datasets-List/eed_latest.csv"), index=False)
            else:
                try:
                    datasets = pd.read_csv("https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.csv")
                except:
                    datasets = pd.read_csv(os.path.join(repo_dir, "Earth-Engine-Datasets-List/eed_latest.csv"))
            datasets['tags'] = datasets.tags.apply(lambda x: x.lower())
            datasets['tags'] = datasets.tags.apply(lambda x: x.split(', '))
            datasets['start_date'] = pd.to_datetime(datasets.start_date)
            datasets['end_date'] = pd.to_datetime(datasets.end_date)
            return datasets
        self.datasets = load_datasets() if datasets is None else datasets
        
    def __str__(self):
        return self.datasets.title.to_string()
    
    def __len__(self):
        return len(self.datasets)
        
    def search_tags(self, keyword):
        '''
        search for keyword in tags
        '''
        keyword = keyword.lower()
        search_results = self.datasets.loc[self.datasets.tags.apply(lambda x: keyword in x)]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
        
    def search_title(self, keyword):
        '''
        search for keyword in title
        '''
        def search_function(title, keyword):
            match = re.search(keyword, title, flags=re.IGNORECASE)
            return True if match else False
        search_results = self.datasets.loc[self.datasets.title.apply(search_function, args = [keyword])]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
        
    def search_by_year(self, year):
        '''
        get all datasets from a particular year:
            dataset start <= year <= dataset end
        '''
        search_results = self.datasets.loc[(self.datasets.startyear <= year) & (self.datasets.endyear >= year)]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
    
    def search_by_period(self, start, end):
        '''
        get all datasets that intersect a time period:
            start of dataset <= end year
            end of dataset >= start year
        '''
        search_results = self.datasets.loc[(self.datasets.startyear <= end) & (self.datasets.endyear >= start)]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
        
class ZonalStats(object):
    '''
    Object to calculate zonal and temporal statistics from Earth Engine datasets (ee.ImageCollections) over vector shapes (ee.FeatureCollections)
    :param collection_id: ID for Earth Engine dataset
    :type collection_id: str or Image Collection
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
    :param band: Optional, specify name of image band to use
    :type band: str
    :param output_dir: Optional, google drive directory to save outputs
    :type output_dir: str (defaults to none)
    '''
    def __init__(self, target_features, statistic_type, collection_id = None, output_name="",
                scale = 250, min_threshold = None, mask = None, tile_scale = 1, collection_is_image = False,
                start_year = None, end_year = None, ee_dataset = None, scale_factor = None,
                frequency = "original", temporal_stat = None, band = None, output_dir = ""):
        self.collection_id = collection_id if collection_id else None
        self.collection_suffix = collection_id[collection_id.rfind("/")+1:] if collection_id else None
        if ee_dataset is None:
            if collection_is_image == True:
                self.ee_dataset = ee.Image(collection_id) if band is None else ee.Image(collection_id).select(band)
            else:
                self.ee_dataset = ee.ImageCollection(collection_id) if band is None else ee.ImageCollection(collection_id).select(band)
        else:
            self.ee_dataset = ee_dataset
        cat = Catalog()
        self.metadata = cat.datasets.loc[cat.datasets.id==collection_id].iloc[0] if collection_id else None
        self.target_features = target_features
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

    def yList(self, start=None, end=None):
        '''
        Create list of years from a given dataset
        '''
        if start is None:
            years = list(range(self.metadata.startyear, self.metadata.endyear+1, 1))
        else:
            years = list(range(start, end, 1))
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
                "satistic must be one of be one of {}".format(", ".join(list(allowed_statistics_ts.keys())))
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

    def applyScaleFactor(self, image, scale_factor):
        return image.multiply(scale_factor)
    
    def runZonalStats(self):
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
            byTimesteps = byTimesteps.toBands()
        
        # pre-processing
        if self.mask is not None:
            if self.mask == "water":
                byTimesteps = self.applyWaterMask(byTimesteps)
            elif type(self.mask) == ee.image.Image:
                byTimesteps = self.applyMask(byTimesteps, self.mask)
        if self.min_threshold is not None:
            byTimesteps = self.applyMinThreshold(byTimesteps, self.min_threshold)
        if self.scale_factor is not None:
            byTimesteps = self.applyScaleFactor(byTimesteps, self.scale_factor)
        
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
                
        zs = ee.Image(byTimesteps).reduceRegions(
            collection = self.target_features, 
            reducer = reducer,
            scale = self.scale,
            tileScale = self.tile_scale
        )
        if self.output_dir != '' and self.output_name != '':
            self.task = ee.batch.Export.table.toDrive(
                collection = zs,
                description = f'Zonal statistics for {self.collection_suffix}',
                fileFormat = 'CSV',    
                folder = self.output_dir,
                fileNamePrefix = self.output_name,
            )
            self.task.start()
        else:
            return(zs)
    
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
        c.drop('.geo', axis=1, inplace=True)
        return c