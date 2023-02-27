# GEE Zonal

![pypi](https://img.shields.io/pypi/v/gee-zonal)
![GitHub issues](https://img.shields.io/github/issues/worldbank/GEE_Zonal?style=plastic)
![GitHub starts](https://img.shields.io/github/stars/worldbank/GEE_Zonal?style=social)

This python package provides a wrapper function to request temporal and zonal statistics from Google Earth Engine (GEE) datasets.

## Summary

A zonal statistics function was created to ease the process of working with the GEE API. The function can work with any raster data loaded to EE (`ee.ImageCollections` or `ee.Image`) and vector features (`geopandas.GeoDataFrame` or `ee.FeatureCollection`), and returns tabular data.

Statistics can be requested at various temporal resolutions (`original` frequency, `monthly`, or `annual`). The workflow conducts pixel-by-pixel temporal aggregations, before summarizing statistics over target features.

Additionaly, the package provides functionality to quickly search the GEE Catalog.

#### [Documentation Pages](https://worldbank.github.io/GEE_Zonal/)

## Installation

The required dependencies are *earthengine-api*, *geopandas*, and *notebook*. The package (and dependencies) can be installed via pip:

```sh
pip install gee_zonal
```

## Setup

The Earth Engine Python API needs to be authenticated with a Google account. First, sign up to Google Earth Engine [here](https://earthengine.google.com/signup/).

Launch a jupyter notebook, and authenticate your account with the ee library.

```python
import ee
ee.Authenticate()
```

You can check that this worked by running `ee.Initialize()`, then import and run the library:

```python
from gee_zonal import ZonalStats, Catalog
```

If the pip installation is not working, you can recreate the environment before and install the package from source:

```sh
conda create -n ee
conda activate ee
conda install -c conda-forge earthengine-api geopandas notebook ipykernel​
git clone https://github.com/worldbank/GEE_Zonal.git
python setup.py build
python setup.py install
python -m ipykernel install --user --name ee --display-name "Earth Engine"
```

## Usage

### ZonalStats()

Main class to calculate temporal and zonal statistics using the GEE backend. The object can be initialized with parameters specifying data inputs and the type of aggregation.

```python
import ee
from gee_zonal import ZonalStats
AOIs = ee.FeatureCollection('<id of ee.FeatureCollection>')
AOIs = '<path to shapefile>'
zs = ZonalStats(
  collection_id = 'LANDSAT/LC08/C01/T1_8DAY_NDVI',
  target_features = AOIs,
  statistic_type = "all", # all includes min, max, mean, and stddev
  frequency = "annual",
  temporal_stat = "mean"
)
```

See docstring for more details on the input parameters for `ZonalStats()` and the [example notebook](./notebooks/Test%20Zonal%20Statistics.ipynb).

The output statistics can be retrieved directly in the notebook (as a `DataFrame`):

```python
res = zs.runZonalStats()
```

Or retrieved from Google Drive as a csv table if an `output_name` and `output_dir` were specified.

### Catalog()

Inventory of Earth Engine datasets with some functions to search catalog by tags, title, and year / time period

```python
from gee_zonal import Catalog
cat = Catalog()
```

The catalog object contains a `datasets` variable, a `DataFrame` containing a copy of the Earth Engine data catalog, retrieved from [Earth-Engine-Datasets-List](https://github.com/samapriya/Earth-Engine-Datasets-List).

```python
cat.datasets
```

#### Search functions

```python
results = cat.search_tags("ndvi")
results = results.search_by_period(1985, 2021)
results = results.search_title("landsat")
print(results)
```

## Additional Resources

- [geemap](https://geemap.org/): Python libary with more functionality to work with GEE.
- [awesome-gee-community-catalog](https://gee-community-catalog.org/): Extended catalog of EE datasets.

## License

[**World Bank Master Community License Agreement**](LICENSE.md).
