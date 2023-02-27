import ee, os, re
try:
    import eemont
except:
    print("eemont not available")
from datetime import datetime
import pandas as pd
import io

class ZonalStats_Landsat(object):
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
    def __init__(self, index, target_features, statistic_type, output_name,
                scale = 250, min_threshold = None, water_mask = False, tile_scale = 4,
                frequency = "original", temporal_stat = None, output_dir = "gdrive_folder",
                start_year = 1984, end_year = 2021):
        self.index = index
        cat = Catalog()
        self.target_features = target_features
        self.statistic_type = statistic_type
        self.frequency = frequency
        self.temporal_stat = temporal_stat
        self.output_dir = output_dir
        self.output_name = output_name
        self.task = None
        self.scale = scale
        self.min_threshold = min_threshold
        self.water_mask = water_mask
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
        if start is None:
            start = self.metadata.start_date
            end = self.metadata.end_date
        else:
            start = datetime(start, 1, 1)
            end = datetime(end, 1, 1)
        ym_range = pd.date_range(datetime(start.year, start.month, 1), datetime(end.year, end.month, 1), freq="MS")
        ym_range = list(date.strftime("%Y%m") for date in ym_range)
        return ee.List(ym_range)
        
    def temporalStack(self, ee_dataset, date_list, freq, stat):
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
            monthly = ee_dataset.filter(ee.Filter.calendarRange(y, y, 'year')) \
                .filter(ee.Filter.calendarRange(m, m, 'month')) \
                .reduce(allowed_statistics_ts[stat]) \
                .set('month', m) \
                .set('year', y) \
                .set('system:index', ee.String(y.format().cat('_').cat(m.format())))
            return monthly
        def aggregate_annual(y):
            y = ee.Number(y)
            annual = ee_dataset.filter(ee.Filter.calendarRange(y, y, 'year')) \
                .reduce(allowed_statistics_ts[stat]) \
                .set('year', y) \
                .set('system:index', ee.String(y.format()))            
            return annual
        if freq=="monthly":
            byTime = ee.ImageCollection.fromImages(date_list.map(aggregate_monthly))
        if freq=="annual":
            byTime = ee.ImageCollection.fromImages(date_list.map(aggregate_annual))
        return byTime.toBands()
    
    def applyWaterMask(self, image, year=None):
        land_mask = ee.Image("MODIS/MOD44W/MOD44W_005_2000_02_24").select('water_mask').eq(0)
        return image.updateMask(land_mask)
    
    def applyMinThreshold(self, image, min_threshold):
        bool_mask = image.gte(min_threshold)
        return image.updateMask(bool_mask)
    
    def runZonalStats(self):
        
        spectralIndices = eemont.indices()
        
        # Define function to get and rename bands of interest from OLI.
        def renameOLI(img):
            return img.select(
                ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'pixel_qa']
          )
        # Define function to get and rename bands of interest from ETM+.
        def renameETM(img):
            return img.select(
                ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'pixel_qa'],
                ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'pixel_qa']
          )
         # Define function to apply harmonization transformation.
        def etm2oli(img):
            coefficients = {
              'itcps': ee.Image.constant([0.0003, 0.0088, 0.0061, 0.0412, 0.0254, 0.0172]).multiply(10000),
              'slopes': ee.Image.constant([0.8474, 0.8483, 0.9047, 0.8462, 0.8937, 0.9071])
            }
            return img.select(['B2', 'B3', 'B4', 'B5', 'B6', 'B7']) \
                .multiply(coefficients['slopes']) \
                .add(coefficients['itcps']) \
                .round() \
                .toShort() \
                .addBands(img.select('pixel_qa'))
        # Define function to mask out clouds and cloud shadows.
        def fmask(img):
            cloudShadowBitMask = 1 << 3
            cloudsBitMask = 1 << 5
            qa = img.select('pixel_qa')
            mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0) \
                .And(qa.bitwiseAnd(cloudsBitMask).eq(0))
            return img.updateMask(mask)
        def fmask_457(args):
            qa = args.select('pixel_qa')
            cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7))
            cloud = cloud.Or(qa.bitwiseAnd(1 << 3))
            mask2 = args.mask().reduce(ee.Reducer.min());
            return args.updateMask(cloud.Not()).updateMask(mask2)
        # Define function to prepare OLI images.
        def prepOLI(img):
            orig = img
            img = renameOLI(img)
            img = fmask(img)
            img = scale_landsat(img)
            return ee.Image(img.copyProperties(orig, orig.propertyNames()))
        # Define function to prepare ETM+ images.
        def prepETM(img):
            orig = img
            img = renameETM(img)
            img = fmask_457(img)
            img = etm2oli(img)
            img = scale_landsat(img)
            return ee.Image(img.copyProperties(orig, orig.propertyNames()))
        def scale_landsat(img):
            scaled = img.select(['B[2-7]']).divide(1e4)
            scaled = scaled.addBands(img.select(['pixel_qa']))
            return ee.Image(scaled.copyProperties(img,img.propertyNames()))
        def lookupL8(img):
            return {
                'A': img.select('B1'),
                'B': img.select('B2'),
                'G': img.select('B3'),
                'R': img.select('B4'),
                'N': img.select('B5'),
                'S1': img.select('B6'),
                'S2': img.select('B7'),                
                'T1' : img.select('B10'),
                'T2': img.select('B11')
            }
        additionalParameters = {
            'g': float(2.5),
            'C1': float(6.0),
            'C2': float(7.5),
            'L': float(1.0),
            'p': float(2.0),
            'c': float(1.0)
        }
        def _index(self,index):
            for idx in index:
                def temporalIndex(img):
                    lookupDic = lookupL8(img)
                    lookupDic = {**lookupDic, **additionalParameters}
                    return img.addBands(img.expression(spectralIndices[idx]['formula'],lookupDic).rename(idx))
                self = self.map(temporalIndex)
            return self
        
        def getStats(feature):
            
            oliCol = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR').filterBounds(feature.geometry()).map(prepOLI)
            etmCol = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR').filterBounds(feature.geometry()).map(prepETM)
            tmCol = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR').filterBounds(feature.geometry()).map(prepETM)
            col = oliCol \
                .merge(etmCol) \
                .merge(tmCol)
                # .index(self.index) \
                # .select(self.index)
            col_index = _index(col, self.index).select(self.index)
            
            if self.frequency not in ['monthly', 'annual', 'original']:
                raise Exception("frequency must be one of annual, monthly, or original")
            if self.frequency == "monthly":
                timesteps = self.ymList(self.start_year, self.end_year)
            elif self.frequency =="annual":
                timesteps = self.yList(self.start_year, self.end_year)
            byTimesteps = col_index.toBands() if self.frequency=="original" else self.temporalStack(col_index, timesteps, self.frequency, self.temporal_stat)
            
            # pre-processing
            if self.water_mask == True:
                byTimesteps = self.applyWaterMask(byTimesteps)
            if self.min_threshold is not None:
                byTimesteps = self.applyMinThreshold(byTimesteps, self.min_threshold)
                
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
            if self.statistic_type not in allowed_statistics.keys():
                raise Exception(
                    "satistic must be one of be one of {}".format(", ".join(list(allowed_statistics.keys())))
                    )
            zs = ee.Image(byTimesteps).reduceRegion(
                geometry = feature.geometry(),
                reducer = allowed_statistics['all'],
                scale = self.scale,
                tileScale = self.tile_scale,
                bestEffort = True,
                maxPixels = 10e15
            )
            return feature.setMulti(zs)
        
        # res = self.target_features.map(getStats)
        # countries = pd.read_csv(os.path.join(repo_dir, "countries.csv"))
        # features = []
        # for country_code in countries.wb_adm0_co.to_list():
        #     features.append(getStats(self.target_features.filterMetadata('WB_ADM0_CO', 'equals', country_code)))
        # res = ee.FeatureCollection(features)
        res = ee.FeatureCollection(ee.Feature(getStats(self.target_features)))
        # res2 = ee.Feature(res)
        # res3 = ee.FeatureCollection(res2)
        # res = ee.FeatureCollection(res)
        
        self.task = ee.batch.Export.table.toDrive(
            collection = res,
            description = f'Zonal statistics {self.statistic_type} of {self.temporal_stat} Landsat Harmonized',
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