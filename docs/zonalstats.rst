ZonalStats
=====

Creating a ZonalStats object
----------------

**ZonalStats()** is the main object to request zonal statistics 
using the Google Earth Engine Python API. The object can be initialized 
with the following parameters.

.. autoclass:: gee_tools.ZonalStats

A shapefile can be called directly from GEE assets, or easily converted 
using ``gee_helpers.gpd_to_gee`` or the geemap package.

Retrieving output table
----------------

**1. Retrieve output table directly**

Statistics can be accessed as the result of ``ZonalStats.runZonalStats()``
This will be computed within the python earth engine environment.

.. code-block:: python

    from gee_tools import ZonalStats
    AOIs = ee.FeatureCollection('users/afche18/Ethiopia_AOI') # ID of ee.FeatureCollection
    zs = ZonalStats(
      collection_id = 'LANDSAT/LC08/C01/T1_8DAY_NDVI',
      target_features = AOIs, 
      statistic_type = "mean", 
      frequency = "annual",
      temporal_stat = "mean"
    )
    df = zs.runZonalStats()
    df

.. csv-table::
   :file: sample_output.csv
   :header-rows: 1

**2. Submit an EE Task**

Alternatively, a task can be submitted to the Earth Engine servers 
by specifying an *output_name* and *outuput_dir*.

This option is recommended to run statistics for big areas or for a high
number of collections. The output table will be saved on the specified 
directory in Google Drive.

.. code-block:: python

    import ee
    from gee_tools import ZonalStats
    ee.Initialize()
    zs = ZonalStats(
      collection_id = 'LANDSAT/LC08/C01/T1_8DAY_NDVI',
      target_features = AOIs, 
      statistic_type = "mean", 
      frequency = "annual",
      temporal_stat = "mean,
      output_dir="pretty_folder",
      output_name="pretty_file"
    )
    zs.runZonalStats()
    
The status of the task can be monitored with ``ZonalStats.reportRunTime()``

>>> zs.reportRunTime()
Completed
Runtime: 0 minutes and 2 seconds