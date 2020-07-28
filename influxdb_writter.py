import requests
from influxdb import InfluxDBClient

class InfuxWritter(object):

    def __init__(self, configuration):
        requests.packages.urllib3.disable_warnings()
        self._configuration = configuration['influxdb']
        self._client = InfluxDBClient(self._configuration['host'], self._configuration['port'], self._configuration['username'], self._configuration['password'], self._configuration['db'])
        self.init_database()

    def init_database(self):
        print("Connecting to InfluxDB: " + self._configuration['host'])
        db_name = self._configuration['db']

        if db_name not in self._client.get_list_database():
            print("Creating InfluxDB database: " + db_name)
            self._client.create_database(db_name)

    def write_metrics(self, metrics):
        self._client.write_points( metrics )