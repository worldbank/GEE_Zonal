var table = ee.FeatureCollection("users/jbelanger/IELFS_HH_buff");

// based on Leo Martine's code

// create feature collection to calculate zonal stats
Map.setOptions('SATELLITE');
var shown = true;
var opacity = 0.5;
var table = ee.FeatureCollection(table);
Map.addLayer(table, {color:'c2a324'}, "aoi", shown, opacity);
Map.centerObject(table, 9);

// set map viz parameters
var red = {color: 'red', fillColor: '00000000'};
var blue = {color: 'blue', fillColor: '0000FF'};

//bounds of the reference layer
var bounds = ee.FeatureCollection(table).geometry().bounds()

//========================================================================================================================

// import modis and filter by bounds
// terra 250m
var modis = ee.ImageCollection("MODIS/006/MOD11A1").filterBounds(bounds);
var bandname = 'LST_Day_1km'


//-----------------[ Get Monthly Statistics ]-----------------------//
print('//-----------------[ Get Monthly Statistics ]-----------------------//');


// import modis LST data (1km)
var LandSurfaceTemp = modis

// set analysis start time (enter first day of start month and last day of end month)
var startDate = ee.Date('2006-09-01');
// set analysis end time
var endDate = ee.Date('2020-09-30');

// calculate the number of months to process
var nMonths = ee.Number(endDate.difference(startDate,'month')).round();
print(nMonths)

//create the list of months
var monList = ee.List.sequence(0,nMonths.subtract(1)).map(function (n){
  return startDate.advance(n,'month').format('YYYY-MM');
});
print(monList)

var monthlyLandSurfaceTemp =  ee.FeatureCollection(
  ee.List.sequence(0,nMonths.subtract(1)).map(function (n) {
          var ini = startDate.advance(n,'month');
          // advance just one month
          var end = ini.advance(1,'month');
          return ee.FeatureCollection(table.map(function(feature){
          var filteredImage = LandSurfaceTemp.filterDate(ini,end).mean().select(bandname)
          // mean
          var mean = filteredImage.reduceRegion({
                  reducer: ee.Reducer.mean(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          // var valMean = ee.Number(mean.get(bandname));
          var valMean = ee.List([ee.Number(mean.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          valMean = ee.Number(valMean).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000) //keep only 3 decimals and convert to Celcius

          //min
          var min = filteredImage.reduceRegion({
                  reducer: ee.Reducer.min(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          // var valMin = ee.Number(min.get(bandname));
          var valMin = ee.List([ee.Number(min.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          valMin = ee.Number(valMin).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000) //keep only 3 decimals and convert to Celcius

          //max
          var max = filteredImage.reduceRegion({
                  reducer: ee.Reducer.max(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          // var valMax = ee.Number(max.get(bandname));
          var valMax = ee.List([ee.Number(max.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          valMax = ee.Number(valMax).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000) //keep only 3 decimals and convert to Celcius

          //stdDev
          var stdDev = filteredImage.reduceRegion({
                  reducer: ee.Reducer.stdDev(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          // var valstdDev = ee.Number(stdDev.get(bandname));
          var valstdDev = ee.List([ee.Number(stdDev.get(bandname)), -99999]).reduce(ee.Reducer.firstNonNull());
          valstdDev = ee.Number(valstdDev).multiply(0.02).subtract(273.15).multiply(1000).round().divide(1000) //keep only 3 decimals and convert to Celcius

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
              'lst_mean': valMean,
              'lst_min': valMin,
              'lst_max': valMax,
              'lst_stdDev': valstdDev,
              'date': monList.get(n),
          });
      }))

  })
).flatten();

print(monthlyLandSurfaceTemp.first())

//Export the data to a CSV
Export.table.toDrive({
  collection:monthlyLandSurfaceTemp,
  folder: 'AF_Drought',
  description:"survey_HH_2019_modis_lst_2kmbuff",
  fileFormat:"CSV"
})
