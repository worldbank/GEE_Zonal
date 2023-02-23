Installation
=====

To use GEE Zonal, first create an environment with the 
following packages: **earthengine-api** and **pandas**

.. code-block:: console

    conda create -n ee
    conda activate ee
    conda install -c conda-forge earthengine-api pandas
    earthengine authenticate
    pip install ipykernel​ jupyter
    python -m ipykernel install --user --name ee --display-name "Earth Engine"

Make sure your earth engine environment is authenticated. This can also be 
done within python:

.. code-block:: python

    import ee
    ee.Authenticate()

Test that this worked by initializing the earth engine API 
and importing the ZonalStats class.

>>> import ee
>>> ee.Initialize()
>>> from gee_tools import ZonalStats