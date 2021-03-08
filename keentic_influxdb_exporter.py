import configparser
import json
import os
import time

from jsonpath_rw import parse
from typing import Dict, List

from influxdb_writter import InfuxWriter
from keenetic_api import KeeneticClient
from value_normalizer import normalize_value


def json_path_init(paths: Dict[str, str]):
    queries = {}

    for pathName, path in paths.items():
        if path == "~":
            queries[pathName] = path
        else:
            queries[pathName] = parse(path)

    return queries


class KeeneticCollector(object):

    def __init__(self, keenetic_client: KeeneticClient, metric_configuration: Dict[str, object]):
        self._keenetic_client = keenetic_client
        self._command: str = metric_configuration['command']
        self._params = metric_configuration.get('param', {})
        self._root = parse(metric_configuration['root'])
        self._tags = json_path_init(metric_configuration['tags'])
        self._values = json_path_init(metric_configuration['values'])

    def collect(self) -> List[dict]:
        response = self._keenetic_client.metric(self._command, self._params)

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
                if value is not None:
                    values[valueName] = normalize_value(value)

            if values.__len__() == 0:
                continue

            metric = self.create_metric(self._command, tags, values)
            # print(json.dumps(metric))
            metrics.append(metric)

        metrics.append(
            self.create_metric("collector", {"command": self._command}, {"duration": (time.time_ns() - start_time)}))

        return metrics

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
    pwd = os.path.dirname(os.path.realpath(__file__))
    metrics_configuration = json.load(open(pwd + "/config/metrics.json", "r"))

    metrics = metrics_configuration['metrics']

    config = configparser.ConfigParser(interpolation=None)
    config.read(pwd + "/config/config.ini")
    infuxdb_writer = InfuxWriter(config['influxdb'])

    keenetic_config = config['keenetic']
    print("Connecting to router: " + keenetic_config['admin_endpoint'])

    collectors = []
    with KeeneticClient(keenetic_config['admin_endpoint'], keenetic_config.getboolean('skip_auth'),
                        keenetic_config['login'], keenetic_config['password']) as kc:
        for metric_configuration in metrics:
            print("Configuring metric: " + metric_configuration['command'])
            collectors.append(KeeneticCollector(kc, metric_configuration))

        wait_interval = config['collector'].getint('interval_sec')
        print(f"Configuration done. Start collecting with interval: {wait_interval} sec")
        while True:
            for collector in collectors:
                metrics = collector.collect()
                infuxdb_writer.write_metrics(metrics)
            time.sleep(wait_interval)
