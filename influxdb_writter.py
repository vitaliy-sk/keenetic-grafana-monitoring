import requests
from influxdb import InfluxDBClient
import influxdb_client
from influxdb_client.client.write_api import WriteOptions, WriteType


class InfuxWritter(object):

    def __init__(self, configuration):
        requests.packages.urllib3.disable_warnings()
        if configuration['influxdb']['enable']:
            self._configuration = configuration['influxdb']
            self._client = InfluxDBClient(self._configuration['host'], self._configuration['port'],
                                          self._configuration['username'], self._configuration['password'],
                                          self._configuration['db'])
            self.init_database()
            enable_influx_version = 1
        elif configuration['influxdb2']['enable']:
            self._configuration2 = configuration['influxdb2']
            self._client2 = influxdb_client.InfluxDBClient(
                url=self._configuration2['uri'],
                token=self._configuration2['token'],
                org=self._configuration2['org']
            )
            enable_influx_version = 2
        else:
            raise AssertionError('There is no enabled influxdb configurations')
        self._enable_influx_version = enable_influx_version

    def init_database(self):
        print("Connecting to InfluxDB: " + self._configuration['host'])
        db_name = self._configuration['db']
        # self._client.drop_database(db_name)

        if db_name not in self._client.get_list_database():
            print("Creating InfluxDB database: " + db_name)
            self._client.create_database(db_name)

    def write_metrics(self, metrics):
        if self._enable_influx_version == 1:
            self._client.write_points(metrics)
        elif self._enable_influx_version == 2:
            points = [self._convert_to_point(metric) for metric in metrics]
            self._client2.write_api(write_options=WriteOptions(batch_size=1_000, write_type=WriteType.batching))\
                .write(bucket=self._configuration2['bucket'],   record=points)

    @staticmethod
    def _convert_to_point(metric: dict):
        point = influxdb_client.Point(metric['measurement'])
        point.time(metric['time'])
        for key, value in metric['tags'].items():
            point.tag(key, value)
        for key, value in metric['fields'].items():
            point.field(key, value)
        return point
