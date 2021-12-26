"""
Manages pipeline metrics

"""

import json
import pandas as pd

from FileNames import FileNames


class Metrics:

    def __init__(self, metrics_folder, metrics_sets):
        self.__metrics_ds = dict()
        self.__folder = metrics_folder
        self.__metrics = None
        self.__metrics_sets = metrics_sets

    def metric_set_to_df(self, metrics_set):
        """
        Collects a set of individual metrics in json format into a pandas
        DataFrame

        :param metrics_set: metrics file name pattern

        :return:
            The dataset where the metrics were collected in, is added as a new
            entry to the metrics dataset dictionary self.__metrics_ds

        """
        _metrics_files = FileNames.collect_file_names(self.__folder, metrics_set)
        _metric_list = list()
        if len(_metrics_files) == 0:
            return
        for f in _metrics_files:
            # print(f)
            with open(f"{self.__folder}{f}") as fp:
                _metric = json.load(fp)
                # print(_metric)
                _metric_list.append(_metric)

        self.__metrics_ds[metrics_set] = pd.DataFrame(_metric_list)

    def collect_metrics(self):
        """
        Merges as one dataset all the datasets collected in the dictionary of metrics datasets
        self.__metrics_ds

        :return:

            The merged dataset the property self.__metrics
        """

        for m in self.__metrics_sets:
            self.metric_set_to_df(m)

        for k in self.__metrics_ds.keys():
            if self.__metrics is None:
                self.__metrics = self.__metrics_ds[k]
            else:
                self.__metrics = self.__metrics.merge(self.__metrics_ds[k], on="data_set", how="inner")

    def get_metrics(self, data_set_name):
        return self.metrics[(self.metrics["data_set"] == data_set_name)].to_dict("records")[0]

    @property
    def metrics(self):
        return self.__metrics

    def save_metrics(self):
        self.__metrics.to_csv(f"{self.__folder}full_metrics.csv")

    def open_metrics(self):
        self.__metrics = pd.read_csv(f"{self.__folder}full_metrics.csv")