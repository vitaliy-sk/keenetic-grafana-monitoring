FROM python:3-slim

ADD keentic_influxdb_exporter.py /home
ADD requirements.txt /home
ADD value_normalizer.py /home
ADD influxdb_writter.py /home
ADD config/metrics.json /home/config/metrics.json

RUN pip install -r /home/requirements.txt
CMD [ "python", "-u", "/home/keentic_influxdb_exporter.py" ]