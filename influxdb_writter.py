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
        logging.info("Connecting to InfluxDB: " + self._configuration['url'])

    def write_metrics(self, metrics):
        self._write_api.write(bucket=self._configuration['bucket'], org=self._configuration['org'], record=metrics)
