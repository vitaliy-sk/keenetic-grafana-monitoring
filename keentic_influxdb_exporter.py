import configparser
import json
import logging
import os
import time
from typing import Dict, List

from jsonpath_rw import parse

from influxdb_writter import InfuxWriter
from keenetic_api import KeeneticClient, KeeneticApiException
from value_normalizer import normalize_value

logging.basicConfig(level='INFO', format='%(asctime)s - %(filename)s - %(levelname)s - %(message)s')

BANNER = r"""
  _  __                    _   _         _____      _ _           _
 | |/ /                   | | (_)       / ____|    | | |         | |
 | ' / ___  ___ _ __   ___| |_ _  ___  | |     ___ | | | ___  ___| |_ ___  _ __🇺🇦  🇺🇦  🇺🇦
 |  < / _ \/ _ \ '_ \ / _ \ __| |/ __| | |    / _ \| | |/ _ \/ __| __/ _ \| '__|
 | . \  __/  __/ | | |  __/ |_| | (__  | |___| (_) | | |  __/ (__| || (_) | |
 |_|\_\___|\___|_| |_|\___|\__|_|\___|  \_____\___/|_|_|\___|\___|\__\___|_|
"""

REQUIRED_CONFIG = {
    'influx2': ['url', 'org', 'token', 'bucket'],
    'keenetic': ['admin_endpoint'],
    'collector': ['interval_sec'],
}


def validate_config(config: configparser.ConfigParser):
    missing = []
    for section, options in REQUIRED_CONFIG.items():
        if not config.has_section(section):
            missing.append(f"[{section}] section")
            continue
        missing.extend(f"{section}.{option}" for option in options
                       if not config.get(section, option, fallback='').strip())

    if config.getboolean('keenetic', 'skip_auth', fallback=False) is False:
        missing.extend(f"keenetic.{option}" for option in ('login', 'password')
                       if not config.get('keenetic', option, fallback='').strip())

    if missing:
        raise SystemExit(f"Invalid configuration, missing or empty options: {', '.join(missing)}")


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
        try:
            response = self._keenetic_client.metric(self._command, self._params)
        except KeeneticApiException as e:
            logging.warning(f"Skipping metric '{self._command}' collection. Reason keenetic api exception, "
                            f"status: {e.status_code}, response: {e.response_text}")
            return []

        roots = self._root.find(response)
        metrics = []
        start_time = time.time_ns()

        for root in roots:
            tags = self._params.copy()
            values = {}

            for tagName, tagPath in self._tags.items():
                if tagPath == '~':
                    tags[tagName] = root.path.fields[0]
                elif str(tagPath).startswith('`parent`'):
                    full_path = root.full_path.child(tagPath)
                    tags[tagName] = self.get_first_value(full_path.find(response))
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
    logging.info("\n\n%s\n", BANNER)
    pwd = os.path.dirname(os.path.realpath(__file__))
    metrics_configuration = json.load(open(pwd + "/config/metrics.json", "r"))

    metrics = metrics_configuration['metrics']

    config = configparser.ConfigParser(interpolation=None)
    config_path = pwd + "/config/config.ini"
    config.read(config_path)

    validate_config(config)

    infuxdb_writer = InfuxWriter(config['influx2'], config_path)

    keenetic_config = config['keenetic']
    logging.info("Connecting to router: " + keenetic_config['admin_endpoint'])

    collectors = []
    with KeeneticClient(keenetic_config['admin_endpoint'], keenetic_config.getboolean('skip_auth'),
                        keenetic_config['login'], keenetic_config['password']) as kc:
        for metric_configuration in metrics:
            logging.info("Configuring metric: " + metric_configuration['command'])
            collectors.append(KeeneticCollector(kc, metric_configuration))

        wait_interval = config['collector'].getint('interval_sec')
        logging.info(f"Configuration done. Start collecting with interval: {wait_interval} sec")
        while True:
            points = 0
            try:
                for collector in collectors:
                    points += infuxdb_writer.write_metrics(collector.collect())
                logging.info(f"Collection cycle finished, {points} points written to InfluxDB")
            except Exception as e:
                logging.exception(f"Collector failed")

            time.sleep(wait_interval)
