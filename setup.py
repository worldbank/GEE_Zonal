from setuptools import find_packages, setup

setup(
    name='gee_zonal',
    packages=['gee_zonal'], #find_packages(),
    install_requires=[
        'geopandas',
        'earthengine-api',
        'notebook',
        'geojson',
    ],
    version='0.1.0',
    description='Wrapper function to request temporal and zonal statistics from Google Earth Engine',
    url="https://worldbank.github.io/GEE_Zonal/",
    keywords="gee zonal statistics earth engine",
    author='Devevelopment Data Group',
    maintainer='Andres Chamorro',
    project_urls={
    "Bug Tracker": "https://github.com/worldbank/GEE_Zonal/issues",
    "Documentation": "https://worldbank.github.io/GEE_Zonal/",
    "Source Code": "https://github.com/worldbank/GEE_Zonal/gee_zonal",
    },
    license='MIT',
)