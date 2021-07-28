var modis = ee.ImageCollection("MODIS/006/MOD13Q1"),
    table = ee.FeatureCollection("users/jbelanger/IELFS_HH_buff_clean");
    
// export takes 22 min to 6 hours 

// create feature collection to calculate zonal stats 
Map.setOptions('SATELLITE'); 
var shown = true;
var opacity = 0.5;
Map.addLayer(table, {color:'C20707'}, "aoi", shown, opacity);
Map.centerObject(table, 9);

function getCols(tableMetadata) {
  print(tableMetadata.columns);
}
print(table.limit(0).evaluate(getCols)); 

//var points = ee.FeatureCollection.randomPoints(region, points, seed, maxError)

// set map viz parameters
var red = {color: 'red', fillColor: '00000000'};
var blue = {color: 'blue', fillColor: '0000FF'};

//bounds of the reference layer
var bounds = ee.FeatureCollection(table).geometry().bounds()

var CHIRPSvis = {
  min: 1.0,
  max: 17.0,
  palette: ['001137', '0aab1e', 'e7eb05', 'ff4a2d', 'e90000'],
};
    
//========================================================================================================================

// import modis and filter by bounds 
//get the CHIRPS and filtered with bounds
var CHIRPS = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(bounds);
//Map.addLayer(CHIRPS.first(), CHIRPSvis, '');
//get the precipitation band
var bandname = 'precipitation';

//-----------------[ Get 15-year Statistics ]-----------------------//
print('//-----------------[ Get 15-year Statistics ]-----------------------//');

var modis_i = CHIRPS.filterBounds(bounds).filterDate('2006-09-01','2020-09-30').select(bandname)

// list starts in january but image collection starts in september
var months = ee.List.sequence(1, 12)

var reducers = ee.Reducer.mean()
  .combine({reducer2: ee.Reducer.min(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.max(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.median(), sharedInputs: true})
  .combine({reducer2: ee.Reducer.stdDev(), sharedInputs: true});

// desired result == one set of stats for each month
var monthly_stats = months.map(function(month){
  var modis_m = modis_i.filter(ee.Filter.calendarRange(ee.Number(month).subtract(1),month,'month'))
  // get monthly mean and set month property
  var img = modis_m.reduce(ee.Reducer.mean()).set('Month', ee.Number(month).toInt())
  return(img)
});

var monthlycol = ee.ImageCollection.fromImages(monthly_stats);
print(monthlycol)
Map.addLayer(monthlycol.first(),CHIRPSvis, 'chirps monthly');

// jan
//var jan = monthlycol.filter(ee.Filter.calendarRange(1,1,'month'));

var jan = monthlycol.filterMetadata('Month', 'equals', 1);
print(jan);
Map.addLayer(jan.first(),CHIRPSvis, 'chirps jan 15 yr avg');

var janstat = table.map(function(feature) {
  return jan.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000, 
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(janstat.first());


// feb
var feb = monthlycol.filterMetadata('Month', 'equals', 2);

var febstat = table.map(function(feature) {
  return feb.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(febstat.first());


// mar
var mar = monthlycol.filterMetadata('Month', 'equals', 3);

var marstat = table.map(function(feature) {
  return mar.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(marstat.first());

// apr
var apr = monthlycol.filterMetadata('Month', 'equals', 4);

var aprstat = table.map(function(feature) {
  return apr.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(aprstat.first());

// may
var may = monthlycol.filterMetadata('Month', 'equals', 5);

var maystat = table.map(function(feature) {
  return may.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(maystat.first());

// jun
var jun = monthlycol.filterMetadata('Month', 'equals', 6);
Map.addLayer(jun.first(),CHIRPSvis, 'jun 15 yr avg');

var junstat = table.map(function(feature) {
  return jun.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(junstat.first());

// jul
var jul = monthlycol.filterMetadata('Month', 'equals', 7);

var julstat = table.map(function(feature) {
  return jul.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(julstat.first());

// aug
var aug = monthlycol.filterMetadata('Month', 'equals', 8);

var augstat = table.map(function(feature) {
  return aug.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(augstat.first());

// sep
var sep = monthlycol.filterMetadata('Month', 'equals', 9);

var sepstat = table.map(function(feature) {
  return sep.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(sepstat.first());

// oct
var oct = monthlycol.filterMetadata('Month', 'equals', 10);

var octstat = table.map(function(feature) {
  return oct.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(octstat.first());

// nov
var nov = monthlycol.filterMetadata('Month', 'equals', 11);

var novstat = table.map(function(feature) {
  return nov.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(novstat.first());

// dec
var dec = monthlycol.filterMetadata('Month', 'equals', 12);

var decstat = table.map(function(feature) {
  return dec.map(function(image) {
    return ee.Feature(feature.geometry(),
      image.reduceRegion({
        reducer: reducers,
        geometry: feature.geometry(),
        scale: 1000,
        bestEffort: true
      })).copyProperties(feature).copyProperties(image);
  });
}).flatten();
print(decstat.first());


/// export all data 

//Export the data to a CSV
Export.table.toDrive({
  collection:janstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_jan",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:febstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_feb",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:marstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_mar",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:aprstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_apr",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:maystat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_may",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:junstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_jun",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:julstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_jul",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:augstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_aug",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV 
Export.table.toDrive({
  collection:sepstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_sep",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:octstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_oct",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:novstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_nov",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})

//Export the data to a CSV
Export.table.toDrive({
  collection:decstat,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_chirps_15yr_poly_dec",
  fileFormat:"CSV",
  selectors: ['BAD','HH_ID','survey_typ','Month','urru','HH_dist_nm','HH_dist_cd','HH_prov_nm',
  'HH_prov_cd','urru','precipitation_mean_max', 'precipitation_mean_mean',
  'precipitation_mean_median','precipitation_mean_min','precipitation_mean_stdDev']
})