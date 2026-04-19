import configparser
import logging

import requests

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class InfuxWriter(object):

    def __init__(self, configuration, configuration_file):
        requests.packages.urllib3.disable_warnings()
        self._configuration = configuration
        self._client = InfluxDBClient.from_config_file(configuration_file)
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        self._extra_tags = self._load_extra_tags(configuration_file)
        logging.info("Connecting to InfluxDB: " + self._configuration['url'])
        if self._extra_tags:
            logging.info("Applying extra tags to every point: " + str(self._extra_tags))

    @staticmethod
    def _load_extra_tags(configuration_file):
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(configuration_file)
        if not cp.has_section('tags'):
            return {}
        return {k: v for k, v in cp.items('tags')}

    def write_metrics(self, metrics):
        if self._extra_tags:
            for metric in metrics:
                metric.setdefault('tags', {}).update(self._extra_tags)
        self._write_api.write(bucket=self._configuration['bucket'], org=self._configuration['org'], record=metrics)
