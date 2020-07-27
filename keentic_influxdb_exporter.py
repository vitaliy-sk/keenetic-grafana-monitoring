import json
import time
import requests

from typing import Dict
from value_normalizer import normalize_data, isvalidmetric


class KeeneticCollector(object):

    def __init__(self, endpoint, request, tags_levels):
        self._endpoint = endpoint
        self._request = request
        self._tags_levels = tags_levels

    def collect(self):

        response = json.loads(requests.get(self._endpoint).content.decode('UTF-8'))
        prefix = self._request.split(' ')
        metrics = self.recursive_iterate(response, prefix, [], {}, 0)

        for metric in metrics:
            print(json.dumps(metric))

    def recursive_iterate(self, data, path, metrics, tags, level):

        if isinstance(data, dict):

            data = normalize_data(data)
            tags = tags.copy()
            tags.update(self.tags(data))
            values = self.values(data)

            if values.__len__() > 0:
                metrics.append(self.create_metric(path, tags, values))

            for key in data:
                value = data.get(key)
                if isinstance(value, list) or isinstance(value, dict):
                    key_path = path.copy()

                    if level in self._tags_levels:  # Need for some API, like show processes
                        tags['_'.join(path)] = key
                    else:
                        key_path.append(key)

                    self.recursive_iterate(value, key_path, metrics, tags, level + 1)

        if isinstance(data, list):
            for idx, value in enumerate(data):
                self.recursive_iterate(value, path, metrics, tags, level + 1)

        return metrics

    def create_metric(self, path, tags, values):
        return {
            "measurement": '_'.join(path),
            "tags": tags,
            "time": int(time.time() * 1000.0),
            "fields": values
        }

    def tags(self, data):
        labels: Dict[str, str] = {}

        for key in data:
            value = data.get(key)
            if isinstance(value, str): labels[key] = value

        return labels

    def values(self, data):
        values = {}

        for key in data:
            value = data.get(key)

            if isvalidmetric(value): values[key] = value

        return values


if __name__ == '__main__':
    (KeeneticCollector('http://192.168.1.1:79/rci/show/processes', 'processes', [1])).collect()
   # (KeeneticCollector('http://192.168.1.1:79/rci/show/processes', 'processes', [1])).collect()

    # while True: time.sleep(1)
