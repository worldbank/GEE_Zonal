var imageCollection = ee.ImageCollection("MODIS/006/MOD13Q1"),
    table = ee.FeatureCollection("users/jbelanger/IELFS_HH_buff");

// based on Leo Martine's code

// create feature collection to calculate zonal stats 
Map.setOptions('SATELLITE'); 
var shown = true;
var opacity = 0.5;
Map.addLayer(table, {color:'C20707'}, "aoi", shown, opacity);
Map.centerObject(table, 9);

// set map viz parameters
var red = {color: 'red', fillColor: '00000000'};
var blue = {color: 'blue', fillColor: '0000FF'};

//bounds of the reference layer
var bounds = table.geometry().bounds();

//========================================================================================================================

//get the Land Surface Temp and filtered with bounds
var NDVI = ee.ImageCollection("MODIS/006/MOD13Q1").filterBounds(bounds);

//get the Temp band
var bandname = 'NDVI';

// set analysis start time (enter first day of start month and last day of end month)
var startDate = ee.Date('2006-09-01'); 
// set analysis end time
var endDate = ee.Date('2020-09-30'); 

// calculate the number of months to process
var nMonths = ee.Number(endDate.difference(startDate,'month')).round();
print(nMonths);

//create the list of months
var monList = ee.List.sequence(0,nMonths.subtract(1)).map(function (n){
  return startDate.advance(n,'month').format('YYYY-MM');
});
print(monList);

var monthlyNDVI =  ee.FeatureCollection(
  ee.List.sequence(0,nMonths.subtract(1)).map(function (n) {
          var ini = startDate.advance(n,'month');
          // advance just one month
          var end = ini.advance(1,'month');
          return ee.FeatureCollection(table.map(function(feature){
          var filteredImage = NDVI.filterDate(ini,end).mean().select('NDVI');
          // mean
          var mean = filteredImage.reduceRegion({
                  reducer: ee.Reducer.mean(),
                  geometry: feature.geometry(),
                  scale: 250,
                  bestEffort:true
              });
          var valMean = ee.List([ee.Number(mean.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          //valMean = ee.Number(valMean).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000); //keep only 3 decimals and convert to Celcius
          
          //min
          var min = filteredImage.reduceRegion({
                  reducer: ee.Reducer.min(),
                  geometry: feature.geometry(),
                  scale: 250,
                  bestEffort:true
              });
          var valMin = ee.List([ee.Number(min.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          ///valMin = ee.Number(valMin).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000); //keep only 3 decimals and convert to Celcius
          
          //max
          var max = filteredImage.reduceRegion({
                  reducer: ee.Reducer.max(),
                  geometry: feature.geometry(),
                  scale: 250,
                  bestEffort:true
              });
          var valMax = ee.List([ee.Number(max.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          //valMax = ee.Number(valMax).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000); //keep only 3 decimals and convert to Celcius
          
          //stdDev
          var stdDev = filteredImage.reduceRegion({
                  reducer: ee.Reducer.stdDev(),
                  geometry: feature.geometry(),
                  scale: 250,
                  bestEffort:true
              });
          var valstdDev = ee.List([ee.Number(stdDev.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
         //valstdDev = ee.Number(valstdDev).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000); //keep only 3 decimals and convert to Celcius
          
          return ee.Feature(null, {
              'uid' : ee.String(feature.get('HH_ID')).cat('-').cat(ee.String(monList.get(n))),
              'BAD' : feature.get('BAD'),
              'HH_dist_nm' : feature.get('HH_dist_nm'),
              'HH_dist_cd' : feature.get('HH_dist_cd'),
              'HH_prov_nm' : feature.get('HH_prov_nm'),
              'HH_prov_cd' : feature.get('HH_prov_cd'),
              'urru' : feature.get('urru'),
              'gps_latitu' : feature.get('gps_latitu'),
              'gps_longit' : feature.get('gps_longit'),
              'survey_typ' : feature.get('survey_typ'),
              'ndvi_mean': valMean,
              'ndvi_min': valMin,
              'ndvi_max': valMax,
              'ndvi_stdDev': valstdDev,
              'date': monList.get(n),
          });
      }));
    
  })
).flatten();

//print(monthlyNDVI);

//Export the data to a CSV
Export.table.toDrive({
  collection:monthlyNDVI,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_ndvi_2kmbuff",
  fileFormat:"CSV",
  //selectors:'uid,pcode,ndvi_mean,ndvi_min,ndvi_max,ndvi_stdDev,date'
});