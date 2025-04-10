//bounds of the reference layer
var bounds = ee.FeatureCollection(table).geometry().bounds()
var dekadsFC = ee.FeatureCollection(dekads)
//get the CHIRPS and filtered with bounds
var CHIRPS = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(bounds);

//get the precipitation band
var bandName = 'precipitation'

var dekadalCHIRPS =  ee.FeatureCollection(
  dekadsFC.map(function (d) {
          var ini = d.get('sd');
          var end = d.get('ed');
          var id = d.get('id')
          return ee.FeatureCollection(table.map(function(feature){
            var filteredImage = CHIRPS.filterDate(ini,end).sum().select(bandName)
            var mean = filteredImage.reduceRegion({
                  reducer: ee.Reducer.mean(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
            var valMean = ee.Number(mean.get(bandName));
            valMean = ee.Number(valMean).multiply(100).round().divide(100) //keep only 2 decimals

          return ee.Feature(null, {
              'uid' : ee.String(feature.get('pcode')).cat('-').cat(ee.String(id)),
              'pcode' : feature.get('pcode'),
              'rainfall_mm': valMean,
              'dekad': id,
          });
      }))

  })
).flatten();

//print(dekadalCHIRPS)

//Export the data to a CSV
Export.table.toDrive({
  collection:dekadalCHIRPS,
  description:"dekadal_rainfall",
  fileFormat:"CSV",
  selectors:'uid,pcode,rainfall_mm,dekad'
})
