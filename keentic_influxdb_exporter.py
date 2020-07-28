import json
import time
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

    def __init__(self, infuxdb_writter, endpoint, command, root, tags, values):
        self._influx = infuxdb_writter
        self._endpoint = endpoint
        self._command = command
        self._root = parse(root)
        self._tags = json_path_init(tags)
        self._values = json_path_init(values)

    def collect(self):

        url = '{}/show/{}'.format(self._endpoint, self._command.replace(' ', '/'))
        response = json.loads(requests.get(url).content.decode('UTF-8'))

        roots = self._root.find(response)
        metrics = []
        start_time = time.time_ns()

        for root in roots:
            tags = {}
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
            metrics.append(metric)

        metrics.append( self.create_metric( "collector", { "command" : self._command }, { "duration" : (time.time_ns() - start_time) } ) )
        # print(json.dumps(metrics))

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
    configuration = json.load(open("config.json", "r"))
    endpoint = configuration['endpoint']
    metrics = configuration['metrics']

    collectors = []

    infuxdb_writter = InfuxWritter(configuration)

    for metric in metrics:
        collectors.append(KeeneticCollector(infuxdb_writter, endpoint, metric['command'], metric['root'], metric['tags'], metric['values']))

    while True:
        for collector in collectors: collector.collect()
        time.sleep(configuration['interval_sec'])
