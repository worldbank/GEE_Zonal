# Monthly Zonal statistics - Urban Indices

GEE Javascript script to export statistics of monthly settlement and urbanization indices by feature in a featureCollection. Outputs to panel dataset. 

Timeframe: 04/2013 to present

Stats returned: mean, min, median, max, count

Prerequisite
Reference polygon layer (e.g. administrative divisions or vector grid). To add as an import named table.

# Script

This analysis seeks to identify landcover change of urban areas over time. It uses Nighttime Lights, Landsat 8, 
and Sentinel 1 SAR (Radar) data. Data are sampled to a tessellation of polygons over the AOI, and zonal statistics
are extracted for each based on month and year. These data are exported to csv files in Drive where they can be 
downloaded and brought into STATA for further analysis. 
 
Note: If using Landsat 7, Sentinel 2 or other data, some available functions (ex: compositing) may be different.
  
```
// create feature collection to calculate zonal stats 
Map.setOptions('SATELLITE'); 
var shown = true;
var opacity = 0.5;
var table = ee.FeatureCollection(table);
Map.addLayer(table, {color:'c2a324'}, "Fishnet", shown, opacity);
Map.centerObject(table, 9);

// get bbox from table bounds
var bbox = table.geometry().bounds();

// set map viz parameters
var red = {color: 'red', fillColor: '00000000'};
var blue = {color: 'blue', fillColor: '0000FF'};

// import datasets
var l8sr = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR"),
    ghsl = ee.Image("JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1"),
    ntl = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"),
    worldpop = ee.ImageCollection("WorldPop/GP/100m/pop"),
    s1 = ee.ImageCollection("COPERNICUS/S1_GRD"),
    table = ee.FeatureCollection("users/jbelanger/kandahar_tess_sq_500m_sum_builtbuff");


//-----------------[ NIGHTTIME LIGHTS ]-----------------------//
print('//-----------------[ NIGHTTIME LIGHTS ]-----------------------//');


//----------------- NTL: filter image collection -----------------------//
print('//----------------- NTL: filter image collection -----------------------//');

// filter the image collection by fishnet bbox and date.
var ntl_filter = ntl.filterBounds(bbox)
    .filterDate('2013-04-01','2019-04-30')
    .filter(ee.Filter.calendarRange(1,12,'month'));
print("filtered NTL collection: ", ntl_filter);
Map.addLayer(ntl_filter, {}, "ntl");
print("ntl collection size:", ntl_filter.size());

//----------------- NTL: add MOY band -----------------------//
print('//----------------- NTL: add MOY band -----------------------//');

// create date band (month of year) for each image in collection
var addDate = function(image){
  var moy = image.date().getRelative('month', 'year');
  var moyBand = ee.Image.constant(moy).uint16().rename('month');
  var doy = image.date().getRelative('day', 'year');
  var doyBand = ee.Image.constant(doy).uint16().rename('day');
  return image.addBands(doyBand).addBands(moyBand);
};

// create temporally grouped reduction (monthly, only for April)
var years = ee.List.sequence(2014, 2019);
var months = ee.List.sequence(1,12);

var monthlyImages = years.map(function(year) {
  return months.map(function(month) {
    var filtered = ntl_filter
        .filterBounds(bbox)
        .filter(ee.Filter.calendarRange(year, year, 'year'))
        .filter(ee.Filter.calendarRange(month, month, 'month'))
        .map(addDate);
    var monthly = filtered.max(); // get the max pixel value of each 
    return monthly.set({'month': month, 'year': year});
});
}).flatten();

// we now have one image per month for the entire period of interest
var ntl_monthly = ee.ImageCollection.fromImages(monthlyImages);
print("filtered monthly ntl: ", ntl_monthly);
Map.addLayer(ntl_monthly.first(), {}, "ntl monthly composite example");

//----------------- NTL: reduce region -----------------------//
print('//----------------- NTL: reduce region -----------------------//');

// combine reducers
var reducers = ee.Reducer.mean()
  .combine({reducer2: ee.Reducer.min(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.max(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.median(), sharedInputs: true});
  
// reduceRegion() on feature collecion
var ntl_data = table.map(function(feature) {
  return ntl_monthly.map(function(image) {
    return ee.Feature(feature.geometry().centroid(100),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        bestEffort: true,
        scale: 450
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print("ntl_data.first: ", ntl_data.first());

//----------------- NTL: export data -----------------------//
print('//----------------- NTL: export data -----------------------//');

// export results to csv
Export.table.toDrive({
  collection:ntl_data,
  folder: "AF_Urban",
  description:"URB_Kandahar_500m_builtup_tess_2014_2019_NTL",
  fileFormat:"CSV",
});

//---------------{ add worldpop & GHSL just for kicks }-----------------------//
print("//---------------{ add worldpop & GHSL just for kicks }-----------------------//");

// add worldpop
var pop14 = worldpop.filterDate('2014');
var pop19 = worldpop.filterDate('2019');
var viz_params = {
  min: 1.0,
  max: 50.0,
  palette: ['#ffffff', '#0000ff'],
};

//--------------------[ LANDSAT 8 ]-----------------------//
print('//--------------------[ LANDSAT 8 ]-----------------------//');
 
// create monthly composite with max values (greenest pixel) where  cloudy pixels are masked. 
//first, check out how many images there are per month in l8sr:
// is it a 16 day return period (~ 2 images per month)?
var l8filtered = l8sr.filterBounds(bbox)
    .filterDate('2013-04-01','2019-04-30')
    .filter(ee.Filter.calendarRange(1,12,'month'));
print("landsat collection: ", l8filtered);
print("landsat collection size:", l8filtered.size());

//----------------- L8: mask cloudy pixels -----------------------//
print('//----------------- L8: mask cloudy pixels -----------------------//');
 
// mask cloudy pixels, such that cloud and shadow = 0. does this affect reduce regions mean?
// mask will be applied in the next step when MOY band is added.
function maskL8sr(image) {
 var cloudShadowBitMask = (1 << 3);   // bit 3 is cloud shadow
 var cloudsBitMask = (1 << 5);        // bit 5 is clouds
 var qa = image.select('pixel_qa');   // Get the pixel QA band.
 
 // set both flags to zero to indicate clear conditions.
 var mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)
 .and(qa.bitwiseAnd(cloudsBitMask).eq(0));
 return image.updateMask(mask);
}

// the other version of cloud masking (listed in docs for L4,5,7)
var maskL8sr_min = function(image) {
  var qa = image.select('pixel_qa');
  // If the cloud bit (5) is set and the cloud confidence (7) is high
  // or the cloud shadow bit is set (3), then it's a bad pixel.
  var cloud = qa.bitwiseAnd(1 << 5)           // 5 = cloud bit 
                  .and(qa.bitwiseAnd(1 << 7)) // 7 = high cloud confidence
                  .or(qa.bitwiseAnd(1 << 3)); // 3 = bad pixel
  // Remove edge pixels that don't occur in all bands
  var mask2 = image.mask().reduce(ee.Reducer.min()); // this just uses the min value of the pixel, rather than = 0
  //var mask3 = qa.bitwiseAnd(cloud).eq(0); // alternative to the above, set the values = 0
  return image.updateMask(cloud.not()).updateMask(mask2);
};    


//----------------- L8: add MOY band -----------------------//
print('//----------------- L8: add MOY band -----------------------//');

// create date band (month of year) for each image in collection
var addDate = function(image){
  var moy = image.date().getRelative('month', 'year');
  var moyBand = ee.Image.constant(moy).uint16().rename('month');
  var doy = image.date().getRelative('day', 'year');
  var doyBand = ee.Image.constant(doy).uint16().rename('day');
  return image.addBands(doyBand).addBands(moyBand);
};

// create temporally grouped reduction (monthly, only for April)
var years = ee.List.sequence(2014, 2019);
var months = ee.List.sequence(1,12);
var bands = ['B4','B5','B6','B7'];

var monthlyImages = years.map(function(year) {
  return months.map(function(month) {
    var filtered = l8sr
        .filterBounds(bbox)
        .filter(ee.Filter.calendarRange(year, year, 'year'))
        .filter(ee.Filter.calendarRange(month, month, 'month'))
        .map(maskL8sr) // this is the one that takes the min of the pixel (doesn't make it zero)
        .map(addDate)
        .select(bands);
    var monthly = filtered.max(); // get the max pixel value of each 
    return monthly.set({'month': month, 'year': year});
});
}).flatten();

// we now have one image per month for the entire period of interest
var monthlycol = ee.ImageCollection.fromImages(monthlyImages);
print("filtered monthly images: ", monthlycol);
Map.addLayer(monthlycol.first(), {}, "monthly composite example");


//----------------- L8: calculate NDVI; NDBI; UI -----------------------//
print('//----------------- L8: calculate NDVI; NDBI; UI -----------------------//');
 
// set band variables for multi indicator calculation
var red = monthlycol.select('B4');
var nir = monthlycol.select('B5');
var swir1 = monthlycol.select('B6');
var swir2 = monthlycol.select('B7');

// create function to add indices to images as bands 
function addBands(image){
  var ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI'); // ndvi = (nir - red) / (nir + red)
  var ndbi = image.normalizedDifference(['B6', 'B5']).rename('NDBI'); // ndbi = (red - nir) / (red + nir)
  var urb = image.normalizedDifference(['B7', 'B5']).rename('UI'); // urban index = (swir2 - nir)/(swir2 + nir)
  return image.addBands(ndvi).addBands(ndbi).addBands(urb);
}

// run addBands on image collection.
var indices = ['NDVI','NDBI','UI'];
var l8sr_bands = monthlycol.map(addBands).select(indices);
print("filtered w/ indices (first): ", l8sr_bands.first());


//----------------- L8: reduce region -----------------------//
print('//----------------- L8: reduce region -----------------------//');
 
// combine reducers
var reducers = ee.Reducer.mean()
  .combine({reducer2: ee.Reducer.min(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.max(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.median(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.count(), sharedInputs: true});

var l8_data = table.map(function(feature) {
  return l8sr_bands.map(function(image) {
    var reduction = image.reduceRegion({
      reducer: reducers,
      geometry: feature.geometry(),
      scale: 30,
    });
    return feature             // Use the feature as base
      .setMulti(reduction)     // like your second try
      .copyProperties(image);  // also include image properties
  });
}).flatten();
print("first reduceRegions result: ", l8_data.first());

// filter the table to print one chart
//var table_filter = ee.FeatureCollection([table.first()]);
//Map.addLayer(table_filter.style(red), {}, "fishnet_first");


//----------------- L8: export data -----------------------//
print('//----------------- L8: export data -----------------------//');

// export l8_data results to csv
Export.table.toDrive({
  collection:l8_data,
  folder: "AF_Urban",
  description:"URB_Kandahar_500m_builtup_tess_2014_2019_L8",
  fileFormat:"CSV"
});

//--------------------[ SENTINEL 1 SAR ]-----------------------//
print('//--------------------[ SENTINEL 1 SAR ]-----------------------//');


//----------------- S1: filter image collection -----------------------//
print("//----------------- S1: filter image collection -----------------------//");
var start = ee.Date('2014-01-01'); // we only have data 2015 onward for our AOI
var finish = ee.Date('2019-12-31');

// pull FLOAT ("natural") if you want to do any kind of pixel math/raster calc - otherwise your results will be wrong! 
// pull GRD if you don't want to filter, as it has already been converted to dB. 
// see https://groups.google.com/u/1/g/google-earth-engine-developers/c/gl6cwbW-7ww/m/T0SBA_OaAAAJ
var s1collection = ee.ImageCollection('COPERNICUS/S1_GRD') 
.filterDate(start, finish)
.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
.filter(ee.Filter.eq('instrumentMode', 'IW'))
.filterBounds(bbox)
.select(['VV']);

print('original s1 collection', s1collection.first());
print('original s1 collection size', s1collection.size());
Map.addLayer(s1collection.first(), {min:-25, max:-5}, 's1 collection first', 0);



//----------------- S1: add DOY band -----------------------//
print("//----------------- S1: add DOY band -----------------------//");

// we do not want monthly composites. we just want one image per month
// we DO want MOY info added to the images. 

//create date band (day of year) for each image in collection
var addDate = function(image){
  var doy = image.date().getRelative('day', 'year');
  var doyBand = ee.Image.constant(doy).uint16().rename('date');
  
  return image.addBands(doyBand);
};

var s1_withDate = s1collection.map(addDate);
print(s1_withDate);

// apply frequency histogram reducers and print in the console
function ymdList(imgcol){
    var iter_func = function(image, newlist){
        var date = ee.Number.parse(image.date().format("YYYYMM"));
        newlist = ee.List(newlist);
        return ee.List(newlist.add(date).sort());
    };
    return imgcol.iterate(iter_func, ee.List([]));
}
var ymd = ymdList(s1_withDate);
// print count of date frequency to the console. 
print(ee.List(ymd).reduce(ee.Reducer.frequencyHistogram()));


//----------------- S1: data visualization/differencing -----------------------//
print("//----------------- S1: data visualization/differencing -----------------------//");

// let's play around with visualization parameters to view the difference between two specific dates
var vizparam = {bands: 'VV', min:-30, max:0, palette:['#00ffff', '#ff0000']};

var start15 = ee.Date('2015-05-01'); 
var finish15 = ee.Date('2015-05-15');
var start19 = ee.Date('2019-05-01'); 
var finish19 = ee.Date('2019-05-15');

var s1_may15 = s1_withDate.filterDate(start15, finish15).select(0).max();
Map.addLayer(s1_may15, vizparam, 's1 early may 2015');
var s1_may19 = s1_withDate.filterDate(start19, finish19).select(0).max();
Map.addLayer(s1_may19, vizparam, 's1 early may 2019');

//----------------- S1: reduce regions -----------------------//
print("//----------------- S1: reduce regions -----------------------//");

// combine reducers
var reducers = ee.Reducer.mean()
  .combine({reducer2: ee.Reducer.min(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.max(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.median(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.count(), sharedInputs: true});

// use reduce regioN because reduce regionS produces max error
var s1_data = table.map(function(feature) {
  return s1_withDate.map(function(image) {
    var reduction = image.reduceRegion({
      reducer: reducers,
      geometry: feature.geometry(),
      scale: 10, // use a 100 meter scale, can try smaller (smoothing is at 50m resolution)
    });
    return feature             // Use the feature as base
      .setMulti(reduction)     // like your second try
      .copyProperties(image);  // also include image properties
  });
}).flatten();

//----------------- S1: export data -----------------------//
print("//----------------- S1: export data -----------------------//");

// export results to csv
// is there a geopandas-type way to combine results from three imagery sources into one table?
Export.table.toDrive({
  collection:s1_data,
  folder: "AF_Urban",
  description:"URB_Kandahar_500m_builtup_2014_2019_S1",
  fileFormat:"CSV"
});
```
