# GEE Zonal

This package contains two classes to ease the process of getting statistics from Google Earth Engine datasets.

The GOST team will use this to build a dataset for the Poverty GP, and we will also use this space to discuss Earth Engine issues and use cases.

## Usage

**Catalog()**

Inventory of Earth Engine datasets with some functions to search catalog by tags, title, and year / time period

```python
from gee_tools import Catalog
cat = Catalog()
```

The catalog contains a *datasets* variable - a pandas Data Frame of the Earth Engine data catalog - retrieved from [Earth-Engine-Datasets-List](https://github.com/samapriya/Earth-Engine-Datasets-List) and also saved in the src folder.

```python
cat.datasets
```

*Search functions*

```python
results = cat.search_tags("ndvi")
results = results.search_by_period(1985, 2021)
results = results.search_title("landsat")
```

**ZonalStats()**

Object to calculate zonal and temporal statistics from Earth Engine datasets (ee.ImageCollections) over vector shapes (ee.FeatureCollections)
See [Test Zonal Statistics notebook](./notebooks/Test%20Zonal%20Statistics.ipynb)

```python
import ee
from gee_tools import ZonalStats
ee.Initialize()
AOIs = ee.FeatureCollection('<id of ee.FeatureCollection>')
zs = ZonalStats(
  collection_id = 'LANDSAT/LC08/C01/T1_8DAY_NDVI',
  target_features = AOIs,
  statistic_type = "mean",
  freq = "annual",
  output_name = "pretty_output",
  temporal_stat = "mean
)

```

See docstrings for more details on the input parameters for ZonalStats(). The output statistics can be retrieved directly in the notebook (as a ee.featureCollection / dictionary), or retrieved from Google Drive as a csv table.

## Environment Setup

Currently only depends on *earthengine-api* and *pandas*. In the future we will probably include *geopandas* and *geemap*.

```sh
conda create -n ee
conda activate ee
conda install -c conda-forge earthengine-api
earthengine authenticate
conda install -c conda-forge pandas
pip install ipykernel​
python -m ipykernel install --user --name ee --display-name "Earth Engine"
conda install -c conda-forge notebook
```

Or, using the environment.yml file (hasn't been tested)

```sh
conda env create -f environment.yml
conda activate ee
earthengine authenticate
```

## Project Checklist

- [ ] Go through variables for Poverty GP dataset
- [ ] Test downloading files directly from Google Drive to local drive
- [ ] Add capability to interact with shapefiles/geopandas like geemap
- [ ] Improve documentation / environment setup

## License

[**World Bank Master Community License Agreement**](LICENSE.md).
