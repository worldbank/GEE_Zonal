// https://developers.google.com/earth-engine/datasets/catalog/NOAA_CDR_AVHRR_NDVI_V5

//bounds of the reference layer
var bounds = ee.FeatureCollection(table).geometry().bounds()

//get the NOAA/CDR/AVHRR/NDVI/V5 and filtered with bounds
var NOAA_NDVI = ee.ImageCollection("NOAA/CDR/AVHRR/NDVI/V5").filterBounds(bounds);

//get the NDVI band
var bandName = 'NDVI'

// set analysis start time (enter first day of start month and last day of end month)
var startDate = ee.Date('1981-07-01');
// set analysis end time
var endDate = ee.Date('2020-10-31');

// calculate the number of months to process
var nMonths = ee.Number(endDate.difference(startDate,'month')).round();
print(nMonths)

//create the list of months
var monList = ee.List.sequence(0,nMonths.subtract(1)).map(function (n){
  return startDate.advance(n,'month').format('YYYY-MM');
});
print(monList)

var monthlyNDVI =  ee.FeatureCollection(
  ee.List.sequence(0,nMonths.subtract(1)).map(function (n) {
          var ini = startDate.advance(n,'month');
          // advance just one month
          var end = ini.advance(1,'month');
          return ee.FeatureCollection(table.map(function(feature){
          var filteredImage = NOAA_NDVI.filterDate(ini,end).mean().select(bandName)

          // mean
          var mean = filteredImage.reduceRegion({
                  reducer: ee.Reducer.mean(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valMean = ee.Number(mean.get(bandName));
          valMean = ee.Number(ee.Algorithms.If(valMean,valMean,-999999));
          valMean = ee.Number(valMean).divide(10000).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits

          //min
          var min = filteredImage.reduceRegion({
                  reducer: ee.Reducer.min(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valMin = ee.Number(min.get(bandName));
          valMin = ee.Number(ee.Algorithms.If(valMin,valMin,-999999));
          valMin = ee.Number(valMin).divide(10000).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits

          //max
          var max = filteredImage.reduceRegion({
                  reducer: ee.Reducer.max(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valMax = ee.Number(max.get(bandName));
          valMax = ee.Number(ee.Algorithms.If(valMax,valMax,-999999));
          valMax = ee.Number(valMax).divide(10000).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits

          //stdDev
          var stdDev = filteredImage.reduceRegion({
                  reducer: ee.Reducer.stdDev(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
          var valstdDev = ee.Number(stdDev.get(bandName));
          valstdDev = ee.Number(ee.Algorithms.If(valstdDev,valstdDev,-999999));
          valstdDev = ee.Number(valstdDev).divide(10000).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits

          return ee.Feature(null, {
              'uid' : ee.String(feature.get('pcode')).cat('-').cat(ee.String(monList.get(n))),
              'pcode' : feature.get('pcode'),
              'ndvi_mean': valMean,
              'ndvi_min': valMin,
              'ndvi_max': valMax,
              'ndvi_stdDev': valstdDev,
              'date': monList.get(n),
          });
      }))

  })
).flatten();

//print(monthlyNDVI)

//Export the data to a CSV
Export.table.toDrive({
  collection:monthlyNDVI,
  description:"monthly_ndvi",
  fileFormat:"CSV",
  selectors:'uid,pcode,ndvi_mean,ndvi_min,ndvi_max,ndvi_stdDev,date'
})
