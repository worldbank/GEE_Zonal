//bounds of the reference layer
var bounds = ee.FeatureCollection(table).geometry().bounds()
//dekads
var dekadsFC = ee.FeatureCollection(dekads)
//get the CHIRPS and filtered with bounds
var CHIRPS = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY").filterBounds(bounds);
//precipitation band
var bandName = 'precipitation'

var dekadalCHIRPS =  ee.FeatureCollection(
  dekadsFC.map(function (d) {
          var ini = d.get('sd');
          var end = d.get('ed');
          var id = d.get('id')
          return ee.FeatureCollection(table.map(function(feature){
            // sum
            var filteredImage = CHIRPS.filterDate(ini,end).sum().select(bandName)
            var sum = filteredImage.reduceRegion({
                  reducer: ee.Reducer.sum(),
                  geometry: feature.geometry(),
                  scale: 1000,
                  bestEffort:true
              });
            var valSum = ee.Number(sum.get(bandName));
            valSum = ee.Number(valSum).multiply(1000).round().divide(1000) //keep only 3 decimals
          //returns a feature with null gemoetry
          return ee.Feature(null, {
              'uid' : ee.String(feature.get('pcode')).cat('-').cat(ee.String(id)),
              'pcode' : feature.get('pcode'),
              'chirps_sum': valSum,
              'dekad': id,
          });
      }))
    
  })
).flatten();

//Export the data to a CSV
Export.table.toDrive({
  collection:dekadalCHIRPS,
  description:"iso3_dekadal_chirps",
  fileFormat:"CSV",
  selectors:'uid,pcode,chirps_sum,dekad'
})