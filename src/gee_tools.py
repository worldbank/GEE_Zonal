import ee, geemap, os, datetime, re
import pandas as pd

pd.set_option('display.max_colwidth', None)
repo_dir = os.path.dirname(os.path.realpath(__file__)) # if Notebooks could also access thorugh ..

class Catalog(object):
    def __init__(self, datasets = None):
        
        def load_datasets():
            datasets = pd.read_csv(os.path.join(repo_dir, "Earth-Engine-Datasets-List/eed_latest.csv"))
            datasets['tags'] = datasets.tags.apply(lambda x: x.split(', '))
            datasets['start_date'] = pd.to_datetime(datasets.start_date)
            datasets['end_date'] = pd.to_datetime(datasets.end_date)
            return datasets
        self.datasets = load_datasets() if datasets is None else datasets
    
    def __str__(self):
        return self.datasets.title.to_string()

    def search_tags(self, search):
        search = search.lower()
        search_results = self.datasets.loc[self.datasets.tags.apply(lambda x: search in x)]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
        
    def search_title(self, search):
        def search_function(title, search):
            match = re.search(search, title, flags=re.IGNORECASE)
            return True if match else False
        search_results = self.datasets.loc[self.datasets.title.apply(search_function, args = [search])]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
        
    def search_by_year(self, year):
        search_results = self.datasets.loc[(self.datasets.startyear <= year) & (year <= self.datasets.endyear)]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")
    
    def search_by_date(self, year, month, day):
        date = datetime.datetime(year, month, day)
        search_results = self.datasets.loc[(self.datasets.start_date < date) & (date < self.datasets.end_date)]
        if len(search_results)>0:
            return Catalog(search_results)
        else:
            raise Exception("No hits!")