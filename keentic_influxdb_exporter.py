import json
import time
import requests

from jsonpath_ng.ext import parse

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

    def __init__(self, endpoint, command, root, tags, values):
        self._endpoint = endpoint
        self._command = command
        self._root = parse(root)
        self._tags = json_path_init(tags)
        self._values = json_path_init(values)

    def collect(self):

        url = '{}/show/{}'.format(self._endpoint, self._command.replace(' ', '/'))
        response = json.loads(requests.get(url).content.decode('UTF-8'))

        roots = self._root.find(response)

        for root in roots:
            tags = {}
            values = {}

            for tagName, tagPath in self._tags.items():
                if tagPath == '~':
                    tags[tagName] = root.path.fields[0]
                else:
                    tags[tagName] = self.get_first_value(tagPath.find(root.value))

            for valueName, valuePath in self._values.items():
                values[valueName] = normalize_value(self.get_first_value(valuePath.find(root.value)))

            metric = self.create_metric(self._command, tags, values)
            print(json.dumps(metric))

    @staticmethod
    def create_metric(measurement, tags, values):
        return {
            "measurement": measurement,
            "tags": tags,
            "time": int(time.time() * 1000.0),
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

    for metric in metrics:
        collectors.append(KeeneticCollector(endpoint, metric['command'], metric['root'], metric['tags'], metric['values']))

    while True:
        for collector in collectors: collector.collect()
        time.sleep(configuration['interval_sec'])
