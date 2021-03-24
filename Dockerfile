FROM python:3.8-alpine AS dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --user --no-warn-script-location -r requirements.txt

FROM python:3.8-alpine AS build-image
COPY --from=dependencies /root/.local /root/.local

COPY value_normalizer.py keentic_influxdb_exporter.py influxdb_writter.py keenetic_api.py /home/

CMD [ "python", "-u", "/home/keentic_influxdb_exporter.py" ]