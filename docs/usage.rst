Usage
*****

Creating a ZonalStats object
============================

**ZonalStats()** is the main class to request temporal and zonal statistics 
using the GEE backend. The object can be initialized with parameters 
specifying data inputs and the type of aggregation.

.. autoclass:: gee_zonal.zonalstats.ZonalStats

Input target features can be referenced directly as a GEE asset, or can be supplied
as a ``geopandas.GeoDataFrame``, or a path to a shapefile/GeoJSON (will be automatically
converted to ``ee.FeatureCollection``).

.. automethod:: gee_zonal.zonalstats.ZonalStats.runZonalStats

Retrieving output table
=======================

1. Retrieve output table directly
-----------------------------------

Statistics can be accessed as the result of ``ZonalStats.runZonalStats()``
This will be computed within the python earth engine environment.

.. code-block:: python

    from gee_zonal import ZonalStats
    AOIs = ee.FeatureCollection('users/afche18/Ethiopia_AOI') # ID of ee.FeatureCollection
    zs = ZonalStats(
      collection_id = 'LANDSAT/LC08/C01/T1_8DAY_NDVI',
      target_features = AOIs, 
      statistic_type = "all", # all includes min, max, mean, and stddev
      frequency = "annual",
      temporal_stat = "mean"
    )
    df = zs.runZonalStats()
    df

2. Submit an EE Task
--------------------

Alternatively, a task can be submitted to the Earth Engine servers 
by specifying an *output_name* and *outuput_dir*.

This option is recommended to run statistics for big areas or for a high
number of collections. The output table will be saved on the specified 
directory in Google Drive.

.. code-block:: python

    import ee
    from gee_tools import ZonalStats
    zs = ZonalStats(
      collection_id = 'LANDSAT/LC08/C01/T1_8DAY_NDVI',
      target_features = AOIs, 
      statistic_type = "all", # all includes min, max, mean, and stddev
      frequency = "annual",
      temporal_stat = "mean",
      output_dir = "pretty_folder",
      output_name= "pretty_file"
    )
    zs.runZonalStats()
    
The status of the task can be monitored with ``ZonalStats.reportRunTime()``

>>> zs.reportRunTime()
Completed
Runtime: 0 minutes and 2 seconds

Searching the EE catalog
========================

The `Earth Engine Data Catalog <https://developers.google.com/earth-engine/datasets>`_
is an archive of public datasets available via Google Earth Engine. The **Catalog()** 
class provides a quick way to search for datasets by tags, title, and year / time period.

Initialize Catalog Object
-------------------------

The catalog object contains a ``datasets`` variable, a ``DataFrame``
containing a copy of the Earth Engine data catalog.

.. code-block:: python

   from gee_zonal import Catalog
   cat = Catalog()
   cat.datasets

Search functions
----------------

.. code-block:: python

   results = cat.search_tags("ndvi")
   results = results.search_by_period(1985, 2021)
   results = results.search_title("landsat")
   print(results)

.. autoclass:: gee_zonal.catalog.Catalog
   :members: