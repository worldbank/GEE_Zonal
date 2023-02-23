Catalog
=====

Searching EE Catalog
----------------

**Catalog()**

Inventory of Earth Engine datasets with some functions to search catalog by 
tags, title, and year / time period.

.. autoclass:: gee_tools.Catalog

**Usage**

.. code-block:: python

   from gee_tools import Catalog
   cat = Catalog()

The catalog contains a ``datasets`` variable - a pandas Data Frame of the 
Earth Engine data catalog - retrieved from Earth-Engine-Datasets-List and 
also saved in the src folder.

**Search functions**

.. code-block:: python

   cat.datasets
   results = cat.search_tags("ndvi")
   results = results.search_by_period(1985, 2021)
   results = results.search_title("landsat")