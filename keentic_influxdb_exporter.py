import json
import time
import urllib

import requests

from jsonpath_ng.ext import parse

from influxdb_writter import InfuxWritter
from value_normalizer import normalize_value


def json_path_init(paths):
    queries = {}

    for pathName, path in paths.items():
        if path == "~":
            queries[pathName] = path
        else:
            queries[pathName] = parse(path)

    return queries


class KeeneticCollector(object):

    def __init__(self, infuxdb_writter, endpoint, metric_configration):
        self._influx = infuxdb_writter
        self._endpoint = endpoint
        self._command = metric_configration['command']
        self._params = metric_configration.get('param', {})
        self._root = parse(metric_configration['root'])
        self._tags = json_path_init(metric_configration['tags'])
        self._values = json_path_init(metric_configration['values'])

    def collect(self):

        url = '{}/show/{}'.format(self._endpoint, self._command.replace(' ', '/')) + "?" + urllib.parse.urlencode(
            self._params)
        response = json.loads(requests.get(url).content.decode('UTF-8'))

        roots = self._root.find(response)
        metrics = []
        start_time = time.time_ns()

        for root in roots:
            tags = self._params.copy()
            values = {}

            for tagName, tagPath in self._tags.items():
                if tagPath == '~':
                    tags[tagName] = root.path.fields[0]
                else:
                    tags[tagName] = self.get_first_value(tagPath.find(root.value))

            for valueName, valuePath in self._values.items():
                value = self.get_first_value(valuePath.find(root.value))
                if value is not None: values[valueName] = normalize_value(value)

            if values.__len__() == 0: continue

            metric = self.create_metric(self._command, tags, values)
            # print(json.dumps(metric))
            metrics.append(metric)

        metrics.append(
            self.create_metric("collector", {"command": self._command}, {"duration": (time.time_ns() - start_time)}))

        infuxdb_writter.write_metrics(metrics)

    @staticmethod
    def create_metric(measurement, tags, values):
        return {
            "measurement": measurement,
            "tags": tags,
            "time": time.time_ns(),
            "fields": values
        }

    @staticmethod
    def get_first_value(array):
        if array and len(array) > 0:
            return array[0].value
        else:
            return None


if __name__ == '__main__':

    print(
        "  _  __                    _   _         _____      _ _           _             \n | |/ /                   | | (_)       / ____|    | | |         | |            \n | ' / ___  ___ _ __   ___| |_ _  ___  | |     ___ | | | ___  ___| |_ ___  _ __ \n |  < / _ \/ _ \ '_ \ / _ \ __| |/ __| | |    / _ \| | |/ _ \/ __| __/ _ \| '__|\n | . \  __/  __/ | | |  __/ |_| | (__  | |___| (_) | | |  __/ (__| || (_) | |   \n |_|\_\___|\___|_| |_|\___|\__|_|\___|  \_____\___/|_|_|\___|\___|\__\___/|_|   \n                                                                                \n                                                                                ")

    configuration = json.load(open("config.json", "r"))
    endpoint = configuration['endpoint']
    metrics = configuration['metrics']

    collectors = []

    infuxdb_writter = InfuxWritter(configuration)

    print("Connecting to router: " + endpoint)

    for metric_configuration in metrics:
        print("Configuring metric: " + metric_configuration['command'])
        collectors.append(KeeneticCollector(infuxdb_writter, endpoint, metric_configuration))

    while True:
        for collector in collectors: collector.collect()
        time.sleep(configuration['interval_sec'])
