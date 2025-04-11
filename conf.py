# Configuration file for the Sphinx documentation builder.
import sys
import os

sys.path.append(os.path.abspath("../src"))

# mock import these packages because readthedocs doesn't have them installed
autodoc_mock_imports = ["ee", "pandas", "geopandas", "geojson", "shapely"]

# -- Project information

project = "GEE Zonal"
copyright = "2021, World Bank"
author = "Andres Chamorro"

release = "1.0"
version = "0.2.0"
html_title = f"GEE Zonal {release}"

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "myst_nb",
]

nb_execution_mode = "off"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_book_theme"  #'sphinx_rtd_theme' sphinx_book_theme

html_theme_options = {
    "repository_url": "https://github.com/worldbank/GEE_Zonal",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
}

# -- Options for EPUB output
epub_show_urls = "footnote"
