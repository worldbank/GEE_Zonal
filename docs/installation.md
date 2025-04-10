# Installation

The required dependencies are *earthengine-api*, *geopandas*, *geojson*, and *notebook*. The package (and dependencies) can be installed via pip:

```sh
pip install gee_zonal
```

This is the preferred method to install geodev, as it will always install the most recent stable release.

If you don't have [pip](https://pip.pypa.io) installed, this [Python installation guide](http://docs.python-guide.org/en/latest/starting/installation/) can guide you through the process.

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

If the pip installation is not working, you can install the package from source:

```sh
pip install git+https://github.com/worldbank/GEE_Zonal.git
```