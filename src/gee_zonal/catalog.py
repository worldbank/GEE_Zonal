"""
Catalog - Search archive of EE Datasets.
"""

import os
import re
import pandas as pd

repo_dir = os.path.dirname(
    os.path.realpath(__file__)
)  # if Notebooks could also access through ..


class Catalog(object):
    """
    Inventory of Earth Engine public, saved as a DataFrame under datasets variable
    """

    def __init__(self, datasets=None, redownload=False):
        def load_datasets():
            if redownload:
                datasets = pd.read_csv(
                    "https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.csv"
                )
                datasets = datasets[
                    [
                        "id",
                        "provider",
                        "title",
                        "start_date",
                        "end_date",
                        "startyear",
                        "endyear",
                        "type",
                        "tags",
                        "asset_url",
                        "thumbnail_url",
                    ]
                ]
                datasets.to_csv(
                    os.path.join(repo_dir, "Earth-Engine-Datasets-List/eed_latest.csv"),
                    index=False,
                )
            else:
                try:
                    datasets = pd.read_csv(
                        "https://raw.githubusercontent.com/samapriya/Earth-Engine-Datasets-List/master/gee_catalog.csv"
                    )
                except Exception:
                    datasets = pd.read_csv(
                        os.path.join(
                            repo_dir, "Earth-Engine-Datasets-List/eed_latest.csv"
                        )
                    )
            datasets["tags"] = datasets.tags.apply(lambda x: x.lower())
            datasets["tags"] = datasets.tags.apply(lambda x: x.split(", "))
            datasets["start_date"] = pd.to_datetime(datasets.start_date)
            datasets["end_date"] = pd.to_datetime(datasets.end_date)
            return datasets

        self.datasets = load_datasets() if datasets is None else datasets

    def __str__(self):
        return self.datasets.title.to_string()

    def __len__(self):
        return len(self.datasets)

    def search_tags(self, keyword):
        """
        search for keyword in tags
        """
        keyword = keyword.lower()
        search_results = self.datasets.loc[
            self.datasets.tags.apply(lambda x: keyword in x)
        ]
        if len(search_results) > 0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")

    def search_title(self, keyword):
        """
        search for keyword in title
        """

        def search_function(title, keyword):
            match = re.search(keyword, title, flags=re.IGNORECASE)
            return True if match else False

        search_results = self.datasets.loc[
            self.datasets.title.apply(search_function, args=[keyword])
        ]
        if len(search_results) > 0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")

    def search_by_year(self, year):
        """
        get all datasets from a particular year:
            dataset start <= year <= dataset end
        """
        search_results = self.datasets.loc[
            (self.datasets.startyear <= year) & (self.datasets.endyear >= year)
        ]
        if len(search_results) > 0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")

    def search_by_period(self, start, end):
        """
        get all datasets that intersect a time period:
            start of dataset <= end year
            end of dataset >= start year
        """
        search_results = self.datasets.loc[
            (self.datasets.startyear <= end) & (self.datasets.endyear >= start)
        ]
        if len(search_results) > 0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
