var table = ee.FeatureCollection("users/jbelanger/alcs_ielfs_areas/ALCS19_Filled");

// based on Leo Martine's code

// create feature collection to calculate zonal stats
Map.setOptions('SATELLITE');
var shown = true;
var opacity = 0.5;
Map.addLayer(table16, {color:'C20707'}, "aoi", shown, opacity);
Map.centerObject(table16, 9);

function getCols(tableMetadata) {
  print(tableMetadata.columns);
}
print(table16.limit(0).evaluate(getCols));

//var points = ee.FeatureCollection.randomPoints(region, points, seed, maxError)

// set map viz parameters
var red = {color: 'red', fillColor: '00000000'};
var blue = {color: 'blue', fillColor: '0000FF'};

//bounds of the reference layer
var bounds = ee.FeatureCollection(table16).geometry().bounds()

//========================================================================================================================



//get the CHIRPS and filtered with bounds
var CHIRPS = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(bounds);
Map.addLayer(CHIRPS.first());

//get the precipitation band
var bandname = 'precipitation';

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

var monthlyCHIRPS =  ee.FeatureCollection(
  ee.List.sequence(0,nMonths.subtract(1)).map(function (n) {
          var ini = startDate.advance(n,'month');
          // advance just one month
          var end = ini.advance(1,'month');
          return ee.FeatureCollection(table16.map(function(feature){
          var filteredImage = CHIRPS.filterDate(ini,end).mean().select('precipitation');
          // mean
          var mean = filteredImage.reduceRegion({
                  reducer: ee.Reducer.mean(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valMean = ee.List([ee.Number(mean.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          //valMean = ee.Number(ee.Algorithms.If(valMean,valMean,-999));
          valMean = ee.Number(valMean).multiply(1000).round().divide(1000); //keep only 3 decimals

          //min
          var min = filteredImage.reduceRegion({
                  reducer: ee.Reducer.min(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valMin = ee.List([ee.Number(min.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          //valMin = ee.Number(ee.Algorithms.If(valMin,valMin,-999));
          valMin = ee.Number(valMin).multiply(1000).round().divide(1000) //keep only 3 decimals

          //max
          var max = filteredImage.reduceRegion({
                  reducer: ee.Reducer.max(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valMax = ee.List([ee.Number(max.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
         // valMax = ee.Number(ee.Algorithms.If(valMax,valMax,-999));
         valMax = ee.Number(valMax).multiply(1000).round().divide(1000) //keep only 3 decimals

          //stdDev
          var stdDev = filteredImage.reduceRegion({
                  reducer: ee.Reducer.stdDev(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valstdDev = ee.List([ee.Number(stdDev.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          //valstdDev = ee.Number(ee.Algorithms.If(valstdDev,valstdDev,-999));
          valstdDev = ee.Number(valstdDev).multiply(1000).round().divide(1000) //keep only 3 decimals

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
              'chirps_mean': valMean,
              'chirps_min': valMin,
              'chirps_max': valMax,
              'chirps_stdDev': valstdDev,
              'date': monList.get(n),
          });
      }));

  })
).flatten();

//print(monthlyCHIRPS)
Map.addLayer(table16, {color:'C20707'}, "aoi");

//Export the data to a CSV
Export.table.toDrive({
  collection:monthlyCHIRPS,
  folder: 'AF_Drought',
  description:"survey_HH_2019_chirps_poly",
  fileFormat:"CSV",
  //selectors:['uid','BAD','chirps_mean','chirps_min','chirps_max','chirps_stdDev','date']
})
