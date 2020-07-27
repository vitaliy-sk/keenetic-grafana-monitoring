import json
import time
import re

from typing import Dict

import requests

def isfloat(value): return (isinstance(value, str) and re.match(r'^-?\d+(?:\.\d+)?$', value) is not None)

class KeeneticCollector(object):

    def __init__(self, endpoint, request):
        self._endpoint = endpoint
        self._request = request

    def collect(self):

        response = json.loads(requests.get(self._endpoint).content.decode('UTF-8'))
        prefix = self._request.split(' ')
        metrics = self.iterate(response, prefix, [], {})

        for metric in metrics:
            print(json.dumps(metric))

    def iterate(self, data, path, metrics, tags):

        if isinstance(data, dict):

            tags = tags.copy()
            tags.update(self.tags(data))
            values = self.values(data)

            if values.__len__() > 0:
                metrics.append(self.create_metric(path, tags, values))

            for key in data:
                value = data.get(key)
                if isinstance(value, list) or isinstance(value, dict):
                    key_path = path.copy()
                    key_path.append(key)
                    self.iterate(value, key_path, metrics, tags)

        if isinstance(data, list):
            for idx, value in enumerate(data):
                self.iterate(value, path, metrics, tags)

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
            if isinstance(value, str) and not isfloat(value): labels[key] = value

        return labels

    def values(self, data):
        values = {}

        for key in data:
            value = data.get(key)

            if isinstance(value, int): values[key] = value
            if isinstance(value, bool): values[key] = value
            if isfloat(value): values[key] = float(value)

        return values


if __name__ == '__main__':
    # Usage: json_exporter.py port endpoint
    (KeeneticCollector('http://192.168.1.1:79/rci/show/interface', 'interface')).collect()

    # while True: time.sleep(1)
