import ee, os, re
try:
    import geemap
except:
    print("geemap not available")
from datetime import datetime
import pandas as pd

pd.set_option('display.max_colwidth', None)
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
                datasets = pd.read_json("https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.json")
                datasets = datasets[['id', 'provider', 'title', 'start_date', 'end_date', 'startyear', 'endyear', 'type', 'tags', 'asset_url', 'thumbnail_url']]
                datasets.to_csv(os.path.join(repo_dir, "Earth-Engine-Datasets-List/eed_latest.csv"), index=False)
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
    :type collection_id: str
    :param target_features: vector features
    :type target_features: ee.FeatureCollection (for now)
    :param statistic_type: statistic to calculate by zone
    :type statistic_type: str (one of mean, max, median, min, sum, std, var)
    :param output_name: file name for output statistics
    :type output_name: str
    :param freq: Optional, temporal frequency for aggregation
    :type freq: str (monthly, annual, or original) defaults to monthly. original uses the raw temporal frequency of the dataset.
    :param temporal_stat: Optional, statistic for temporal aggregation
    :type temporal_stat: str (mean, max, median, min, or sum, defaults to mean)
    :param band: Optional, specify name of image band to use
    :type band: str
    :param output_dir: Optional, google drive directory to save outputs
    :type output_dir: str (defaults to gdrive_folder)
    '''
    def __init__(self, collection_id, target_features, statistic_type, output_name,
                freq = "monthly", temporal_stat = "mean", band = None, output_dir = "gdrive_folder"):
        self.collection_id = collection_id
        self.collection_suffix = collection_id[collection_id.rfind("/")+1:]
        self.ee_dataset = ee.ImageCollection(collection_id) if band is None else ee.ImageCollection(collection_id).select(band)
        cat = Catalog()
        self.metadata = cat.datasets.loc[cat.datasets.id==collection_id].iloc[0]
        self.target_features = target_features
        self.statistic_type = statistic_type
        self.freq = freq
        self.temporal_stat = temporal_stat
        self.output_dir = output_dir
        self.output_name = output_name
        self.task = None

    def yList(self):
        '''
        Create list of years from a given dataset
        '''
        years = list(range(self.metadata.startyear, self.metadata.endyear, 1))
        return ee.List(years)

    def ymList(self):
        '''
        Create list of year/month pairs from a given dataset
        '''
        start = self.metadata.start_date
        end = self.metadata.end_date
        ym_range = pd.date_range(datetime(start.year, start.month, 1), datetime(end.year, end.month, 1), freq="MS")
        ym_range = list(date.strftime("%Y%m") for date in ym_range)
        return ee.List(ym_range)
    
    def ymList_ee(self):
        '''
        Create list of year/month pairs from a given dataset using EE
        '''
        def iter_func(image, newlist):
            date = ee.Number.parse(image.date().format("YYYYMM")).format();
            newlist = ee.List(newlist);
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
        }
        if freq not in ['monthly', 'annual']:
            raise Exception("frequency must be one of annual, monthly, or original")
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
        if freq=="original":
            byTime = self.ee_dataset
        return byTime.toBands()
        
    def runZonalStats(self):
        if self.freq == "monthly":
            timesteps = self.ymList()
        elif self.freq =="annual":
            timesteps = self.yList()
        byTimesteps = self.temporalStack(timesteps, self.freq, self.temporal_stat)
        allowed_statistics = {
            "mean": ee.Reducer.mean(),
            "max": ee.Reducer.max(),
            "median": ee.Reducer.median(),
            "min": ee.Reducer.min(),
            "sum": ee.Reducer.sum(),
            "std": ee.Reducer.stdDev(),
            "var": ee.Reducer.variance(),
        }
        if self.statistic_type not in allowed_statistics.keys():
            raise Exception(
                "satistic must be one of be one of {}".format(", ".join(list(allowed_statistics.keys())))
                )
        zs = ee.Image(byTimesteps).reduceRegions(
            collection = self.target_features, 
            reducer = allowed_statistics[self.statistic_type],
            scale = 30
        )
        self.task = ee.batch.Export.table.toDrive(
            collection = zs,
            description = f'Zonal statistics {self.statistic_type} of {self.collection_suffix}',
            fileFormat = 'CSV',    
            folder = self.output_dir,
            fileNamePrefix = self.output_name,
        )
        self.task.start()