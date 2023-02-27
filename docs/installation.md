# Installation

The required dependencies are *earthengine-api*, *geopandas*, *geojson*, and *notebook*. The package (and dependencies) can be installed via pip:

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

```{note} Authenticating from within a terminal can lead to issues with gcloud.
```

You can check that this worked by running `ee.Initialize()`, then import and run the library:

```python
from gee_zonal import ZonalStats, Catalog
```

If the pip installation is not working, you can recreate the environment before and install the package from source:

```sh
conda create -n ee
conda activate ee
conda install -c conda-forge earthengine-api geopandas geojson notebook ipykernel​
git clone https://github.com/worldbank/GEE_Zonal.git
python setup.py build
python setup.py install
python -m ipykernel install --user --name ee --display-name "Earth Engine"
```