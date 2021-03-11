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

The catalog contains a *dataset* variable - a pandas Data Frame of the Earth Engine data catalog - retrieved from [Earth-Engine-Datasets-List](https://github.com/samapriya/Earth-Engine-Datasets-List) and also saved in the src folder.

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

```python
import ee
from gee_tools import ZonalStats
ee.Initialize()
AOIs = ee.FeatureCollection('<id of ee.FeatureCollection>')
# Image Collection id, ee. Feature Collection, statistic type
zs = ZonalStats(collection_id = 'LANDSAT/LC08/C01/T1_8DAY_NDVI', target_features = AOIs, statistic_type = "mean", output_name = "pretty_output")

```

See notebooks and docstrings for more details on the input parameters for ZonalStats().

## Environment Setup

Currently only depends on *earthengine-api* and *pandas*. In the future we will probably include *geopandas* and *geemap*.

```{important}
conda create -n ee
conda activate ee
conda install -c conda-forge earthengine-api
earthengine authenticate
conda install -c conda-forge pandas
pip install ipykernel​
python -m ipykernel install --user --name ee --display-name "Earth Engine"
```

Or, using the environment.yml file (hasn't been tested)

```{important}
conda env create -f environment.yml
conda activate ee
earthengine authenticate
```

## Project Checklist

- [ ] Go through variables for Poverty GP dataset
- [ ] Test downloading files directly from Google Drive to local drive
- [ ] Add capability to interact with shapefiles/geopandas like geemap
- [ ] Improve documentation / environment setup

## Resources

- [Development Data Partnership](https://docs.datapartnership.org)
    > A partnership between international organizations and companies, created to facilitate the use of third-party data in research and international development.

- [Awesome Data Partnership](https://datapartnership.github.io/awesome-datapartnership/)
    > A curated list of projects, data goods and derivative works associated with the Development Data Partnership

- [The DIME Wiki](https://dimewiki.worldbank.org/wiki/Main_Page)
    > The DIME Wiki is a public good developed and maintained by DIME Analytics, a team which creates tools that improve the quality of impact evaluation research at DIME. The DIME Wiki is targeted to all researchers and M&E specialists at the World Bank, clients who are managing data collection efforts in the field, donor institutions, universities, NGOs, and governments. While there are many existing impact evaluation resources, none meet the specific gap the DIME Wiki aims to fulfill: a resource focused on practical implementation guidelines rather than theory, open to the public, easily searchable, suitable for users of varying levels of expertise, up-to-date with the latest technological advances in electronic data collection, with a vibrant network of editors who are experts in this field.

- [The DIME Analytics Data Handbook](https://worldbank.github.io/dime-data-handbook/)
    > This book is intended to serve as an introduction to the primary tasks required in development research, from experimental design to data collection to data analysis to publication. It serves as a companion to the DIME Wiki and is produced by DIME Analytics.

- [GitHub Pages](https://guides.github.com/features/pages/)
    > GitHub Pages are public webpages hosted and easily published through GitHub. 

- [Jupyter Book](https://jupyterbook.org/intro.html)
    > Jupyter Book is an open source project for building beautiful, publication-quality books and documents from computational material.

## Project Organization

```markdown
    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   ├── gee_tools.py   <- Code for Python classes
    │
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io
```

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
