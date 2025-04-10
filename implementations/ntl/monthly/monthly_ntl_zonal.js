var ntl = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"),
    table = ee.FeatureCollection("users/jbelanger/IOM_round11_BDG_1kmbuff");

// create feature collection to calculate zonal stats
Map.setOptions('SATELLITE');
var shown = true;
var opacity = 0.5;
var table = ee.FeatureCollection(table);
Map.addLayer(table, {color:'0000FF'}, "buffers", shown, opacity);
Map.centerObject(table, 9);

// get bbox from table bounds
var bbox = table.geometry().bounds();

// set map viz parameters
var red = {color: 'red', fillColor: '00000000'};
var blue = {color: 'blue', fillColor: '0000FF'};


//-----------------[ NIGHTTIME LIGHTS ]-----------------------//
print('//-----------------[ NIGHTTIME LIGHTS ]-----------------------//');


//----------------- NTL: filter image collection -----------------------//
print('//----------------- NTL: filter image collection -----------------------//');

// filter the image collection by fishnet bbox and date.
var ntl_filter = ntl.filterBounds(bbox)
    .filterDate('2016-01-01','2020-12-31')
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
var years = ee.List.sequence(2016, 2020);
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
  .combine({reducer2: ee.Reducer.median(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.stdDev(), sharedInputs: true});

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

Map.addLayer(table, {color:'0000FF'}, "Fishnet", shown, opacity);

//----------------- NTL: export data -----------------------//
print('//----------------- NTL: export data -----------------------//');

// export results to csv
Export.table.toDrive({
  collection:ntl_data,
  folder: "AF_Displacement",
  description:'BDG_NTL_2020_r11_1km_allvar',
  fileFormat:"CSV",
  selectors:["SettNameEn","Settlement",'Latitude','Longitude','RoundNumbe','avg_rad_min','avg_rad_max','avg_rad_mean','avg_rad_median','avg_rad_stdDev',
  'month','year']
});
