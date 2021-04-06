# Cumulative Dekadal Rainfall 

Javascript script to export cumulative dekadal rainfall by feature in a featureCollection.

*Every month has three dekads, such that the first two dekads have 10 days (i.e., 1-10, 11-20), and the third is comprised of the remaining days of the month.*

Dataset used: [https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY](https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY)  
Timeframe: **1981 - Now**  
Precision: **0.05 arc degrees**  
Units: **millimeters**

## Prerequisite

- Reference polygon layer (e.g. administrative divisions). To add as an import named **table**. Should contain only one field called **pcode**, used as a unique identifier.
- List of dekads to compute. To add as an import named **dekads**. See *dekads_generator.js* to generate your list, or filter *dekads_1981-2020.csv*.


## Script

```javascript
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
```
## Output

The scripts generates a CSV file with the following fields:

- **uid**: Concatenation of **date**+**pcode**
- **pcode**: **pcode** field of the polygon
- **chirps_sum**: cumulative precipitation in millimeters. Rounded to 3 decimals.
- **date**: year + dekad number *(from 1 to 36 by year)*

Example:

| uid  |pcode   |chirps_sum   |date   | 
|---|---|---|---|
| TD2201-1981-1|TD2201   |35.604   |1981-1   |
| TD2202-1981-1|TD2202   |55.979   |1981-1   |