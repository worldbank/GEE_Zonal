# Daily Temperature

Javascript script to export daily air temperature at 2m statistics by feature in a featureCollection.

Dataset used: [https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_DAILY](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_DAILY)  
Timeframe: **1979 - ~Now**  
Precision: **0.25 arc degrees**  
Unit: **Celsius Degrees**, *can easily be set to Kelvin*  
Stats returned: **mean**, **min**, **max**, **stdDev**

## Prerequisite

- Reference polygon layer (e.g. administrative divisions or vector grid). To add as an import named **table**. Should contain only one field called **pcode**, used as a unique identifier.

## Script

```javascript
//bounds of the reference layer
var bounds = ee.FeatureCollection(table).geometry().bounds()

//get the ECMWF/ERA5/DAILY and filtered with bounds
var ERA5_Daily = ee.ImageCollection("ECMWF/ERA5/DAILY").filterBounds(bounds);

//get the Temp band
var bandName = 'mean_2m_air_temperature'

// set analysis start time
var startDate = ee.Date('1980-01-01'); 
// set analysis end time (not inclusive so set 1 day after expected enddate)
var endDate = ee.Date('2020-06-30'); 

// calculate the number of days to process
var nDays = ee.Number(endDate.difference(startDate,'day')).round();
print(nDays)

//create the list of days
var dayList = ee.List.sequence(0,nDays.subtract(1)).map(function (n){
  return startDate.advance(n,'day').format('YYYY-MM-dd');
});
print(dayList)

var dailyTemp =  ee.FeatureCollection(
  ee.List.sequence(0,nDays.subtract(1)).map(function (n) {
          var ini = startDate.advance(n,'day');
          // advance one day
          var end = ini.advance(1,'day');
          return  ee.FeatureCollection(table.map(function(feature){
            var filteredImage = ERA5_Daily.filterDate(ini,end).mean().select(bandName)
            // mean
            var mean = filteredImage.reduceRegion({
                    reducer: ee.Reducer.mean(),
                    geometry: feature.geometry(),
                    scale: 1000,
                    bestEffort:true
                });
            var valMean = ee.Number(mean.get(bandName));
            valMean = ee.Number(ee.Algorithms.If(valMean,valMean,-999));
            valMean = ee.Number(valMean).subtract(273.15).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits
            
            //min
            var min = filteredImage.reduceRegion({
                    reducer: ee.Reducer.min(),
                    geometry: feature.geometry(),
                    scale: 1000,
                    bestEffort:true
                });
            var valMin = ee.Number(min.get(bandName));
            valMin = ee.Number(ee.Algorithms.If(valMin,valMin,-999));
            valMin = ee.Number(valMin).subtract(273.15).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits
            
            //max
            var max = filteredImage.reduceRegion({
                    reducer: ee.Reducer.max(),
                    geometry: feature.geometry(),
                    scale: 1000,
                    bestEffort:true
                });
            var valMax = ee.Number(max.get(bandName));
            valMax = ee.Number(ee.Algorithms.If(valMax,valMax,-999));
            valMax = ee.Number(valMax).subtract(273.15).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits
            
            //stdDev
            var stdDev = filteredImage.reduceRegion({
                    reducer: ee.Reducer.stdDev(),
                    geometry: feature.geometry(),
                    scale: 1000,
                    bestEffort:true
                });
            var valstdDev = ee.Number(stdDev.get(bandName));
            valstdDev = ee.Number(ee.Algorithms.If(valstdDev,valstdDev,-999));
            valstdDev = ee.Number(valstdDev).multiply(1000).round().divide(1000) //scale : 0.0001 and 3 digits
            
            return ee.Feature(null, {
                'uid' : ee.String(feature.get('pcode')).cat('-').cat(ee.String(dayList.get(n))),
                'pcode' : feature.get('pcode'),
                'temp_mean': valMean,
                'temp_min': valMin,
                'temp_max': valMax,
                'temp_stdDev': valstdDev,
                'date': dayList.get(n),
            });
        }))
  })
).flatten();

//print(dailyTemp)

//Export the data to a CSV
Export.table.toDrive({
  collection:dailyTemp,
  description:"daily_temp",
  fileFormat:"CSV",
  selectors:'uid,pcode,temp_mean,temp_min,temp_max,temp_stdDev,date'
})
```
## Output

The scripts generates a CSV file with the following fields:

- **uid**: Concatenation of **pcode**+**date**
- **pcode**: **pcode** field of the polygon
- **temp_mean**: Mean temperature. Rounded to 3 decimals.
- **temp_min**: Minimum temperature. Rounded to 3 decimals.
- **temp_max**: Maximum temperature. Rounded to 3 decimals.
- **temp_stdDev**: Standard Deviation temperature. Rounded to 3 decimals.
- **date**: day in the format YYYY-MM-dd.

*No values are returned as -999.*
*/!\ Daily = large outputs.*

Example:

|uid           |pcode |temp_mean|temp_min|temp_max|temp_stdDev|date   |
|--------------|------|---------|--------|--------|-----------|-------|
|NE0613-1980-01-01|NE0613|22.749    |21.944   |23.571   |0.379      |1980-01-01|