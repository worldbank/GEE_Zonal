# Daily Temperature

Series of GEE Javascript scripts to extract zonal statistics of environmental variables that may indicate drought conditions. Indices include LST (MODIS; NDVI (MODIS); Precipitation (CHIRPS).
 
Each index has two different scripts, one that collects 15-year single-month averages and one that collects monthly data from the same time period (2006-2020). For the purposes of the analysis this was applied to, data were collected starting and ending in September, but this can be modified by the user at their discretion. 

Timeframe: **2006 - 2020**   
Stats returned: **mean**, **min**, **max**, **stdDev**

- Reference polygon layer (e.g. administrative divisions or vector grid). To add as an import named **table**. 
