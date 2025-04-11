# PyDrive Support

As demonstrated in the [example notebook](zonal_statistics_example), zonal statistics can be submitted as tasks using Earth Engine's `ee.batch.Export.table.toDrive` feature. This is generally preferred when running large computations, or trying to batch several tasks in parallel.

The `ZonalStats` object contains a function `getZonalStats()` to retrieve the resulting table directly from Google Drive using [pydrive](https://pythonhosted.org/PyDrive/).

This requires additional configuration to provide access to Google Drive. First, the *pydrive* package needs to be installed.

``` sh
pip install pydrive
```

## Setup

Follow the [instructions](https://pythonhosted.org/PyDrive/quickstart.html) to obtain a client configuration file `client_secrets.json`.

One additional step required is **go to Audience and add your email as a test user.** Otherwise, you will have to publish the application.

Place the `client_secrets.json` file in a folder such that the `authenticateGoogleDrive()` function can find it. By default the function looks for the file in `~/.config/creds/client_secrets.json`. You can change this by passing the `creds_dir` argument to the function.

## Usage

``` python
from gee_zonal import authenticateGoogleDrive
from os.path.import join

# Authorize Google Drive
drive = authenticateGoogleDrive(creds_dir = join(expanduser('~'), '.config', 'creds')) # Change to path where you stored client_secrets file

# Run ZonalStats
zs = ZonalStats(
    collection_id='UCSB-CHG/CHIRPS/PENTAD',
    target_features=AOIs,
    statistic_type="mean",
    temporal_stat="sum",
    frequency="annual",
    scale=5000,
    output_dir = "gdrive_folder",
    output_name="pretty_output"
)

# Submit task to Earth Engine
zs.runZonalStats()

# Check if task is completed
zs.reportRunTime()

# Retrieve result
df = zs.getZonalStats(drive)
```
