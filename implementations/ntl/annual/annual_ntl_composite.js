
var ntl = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"),
    table = ee.FeatureCollection("users/jbelanger/badghis_prov_2020");
 
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
    .filterDate('2020-01-01','2020-12-31')
    .filter(ee.Filter.calendarRange(1,12,'month'))
    .select(['avg_rad']);

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

// create annual composite
var annual2020 = ntl_filter.reduce(ee.Reducer.mean());
print("annual 2020", annual2020);
Map.addLayer(annual2020, {}, "annual 2020");


//----------------- NTL: export data -----------------------//
print('//----------------- NTL: export data -----------------------//');

Export.image.toDrive({
  image: annual2020,
  folder: 'AFG_Displacement',
  description: 'BDG_NTL_2020',
  scale: 450,
  region: bbox
});