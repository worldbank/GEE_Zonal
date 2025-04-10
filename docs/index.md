# GEE Zonal

[![PyPI version](https://img.shields.io/pypi/v/gee-zonal.svg)](https://pypi.python.org/pypi/gee-zonal)

This python package provides a wrapper function to request temporal and zonal statistics from Google Earth Engine (GEE) datasets.

## Summary

A zonal statistics function was created to ease the process of working with the GEE API. The function can work with any raster data loaded to EE (`ee.ImageCollections` or `ee.Image`) and vector features (`geopandas.GeoDataFrame` or `ee.FeatureCollection`), and returns tabular data.

Statistics can be requested at various temporal resolutions (`original` frequency, `monthly`, or `annual`). The workflow conducts pixel-by-pixel temporal aggregations, before summarizing statistics over target features.

Additionally, the package provides functionality to quickly search the GEE Catalog.

!!! note

    This project is under active development. Feel free to open a new issue or a discussion if you have any questions or suggestions.
