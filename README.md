```
  _  __                    _   _         _____      _ _           _             
 | |/ /                   | | (_)       / ____|    | | |         | |            
 | ' / ___  ___ _ __   ___| |_ _  ___  | |     ___ | | | ___  ___| |_ ___  _ __ 🇺🇦🇺🇦🇺🇦 
 |  < / _ \/ _ \ '_ \ / _ \ __| |/ __| | |    / _ \| | |/ _ \/ __| __/ _ \| '__|
 | . \  __/  __/ | | |  __/ |_| | (__  | |___| (_) | | |  __/ (__| || (_) | |   
 |_|\_\___|\___|_| |_|\___|\__|_|\___|  \_____\___/|_|_|\___|\___|\__\___|_|   
                                                                                
```

![Example](https://user-images.githubusercontent.com/2773025/88829802-c5809900-d1d5-11ea-8cbe-de41118387b3.png)

# Supported routers

Tested with KeeneticOS 3.5+

# Supported InfluxDB version

InfluxDB 2.x (recommended) and InfluxDB 1.8+

# Preparation

* Create configuration file `config.ini`

```ini
[influx2]
# If you are using docker-compose it should be http://influxdb:8086
url=http://influxdb:8086
# For influx v1.x please use "-" as a value
org=keenetic
# For influx v1.x please use "username:password" as a token
# See DOCKER_INFLUXDB_INIT_ADMIN_TOKEN in docker-compose.yml
token=admin_token
timeout=6000
# For influx v1.x DB name
bucket=keenetic
[keenetic]
admin_endpoint=http://<keenetic_ip>:80
skip_auth=false
login=<user>
password=<pass>
[collector]
interval_sec=30
```

* Copy [metrics.json](https://github.com/vitaliy-sk/keenetic-grafana-monitoring/blob/master/config/metrics.json) and edit (Optional)

* InfluxDB 2.x only: create a DBRP mapping

The bundled Grafana dashboard queries InfluxDB with **InfluxQL**. InfluxDB 2.x serves InfluxQL only through the 1.x compatibility API, which requires a DBRP mapping between a 1.x-style database name and a bucket. Without it every dashboard panel fails with `database not found`.

```bash
# one-time command, requires the bucket id
influx v1 dbrp create --db keenetic --rp autogen --bucket-id <bucket_id> --default
```

If you use the `docker-compose.yml` from this repository, the one-shot `influxdb-init-dbrp` service creates this mapping automatically.

> **Note**
> Do not switch the Grafana datasource to Flux to fix this: the dashboard queries are written in InfluxQL and will not work with a Flux datasource.

* Create admin user (Users and access -> Create user, allow 'Web interface' and 'Prohibit saving system settings') 

* (Alternative to create user) Expose Keenetic API on your router

For doing this add port forwarding (Network rules -> Forwarding):
```
Input: Other destination
IP address: Your network ip (like 192.168.1.0)
Subnet mask: 255.255.255.0
Output: This Keenetic
Open the port: 79
Destination port: 79 
```
Update `conifg.ini`
```
[keenetic]
skip_auth=true
```

* Import Grafana dashboard from [grafana.com](https://grafana.com/grafana/dashboards/12723) (not needed when using the provisioning files from this repository)

# Run

There are three options: run the collector locally with `uv`, run it in Docker on a separate host, or copy it to the router directly.

## Run locally with uv

* Install `uv`
* Create and update the project environment `uv sync`
* Start the collector `uv run python keentic_influxdb_exporter.py`

## Run in Docker on a separate host (recommended)

The collector starts writing points to InfluxDB on its own, but to see any graphs you also need the DBRP mapping and a Grafana datasource, which first-time users often miss. The `docker-compose.yml` in this repository wires everything together: InfluxDB with a healthcheck, a one-shot job that creates the DBRP mapping, Grafana with the datasource and dashboard provisioned automatically.

```
---
version: '3.7'

services:

  keenetic-grafana-monitoring:
    image: techh/keenetic-grafana-monitoring:2.0.3
    container_name: keenetic-grafana-monitoring
    # environment:
    #  - TZ=Europe/Kiev
    volumes:
      - ./config/config.ini:/home/config/config.ini:ro
      # Optionally you can override metrics
      - ./config/metrics.json:/home/config/metrics.json:ro
    restart: always
    depends_on:
      influxdb:
        condition: service_healthy

  # Influx 2.x

  influxdb:
    image: 'influxdb:2.7'
    volumes:
      - ./_data/influxdb:/var/lib/influxdb
    ports:
      - 8086:8086
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_ORG=keenetic
      - DOCKER_INFLUXDB_INIT_BUCKET=keenetic
      - DOCKER_INFLUXDB_INIT_RETENTION=52w
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=admin_token
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=password
    healthcheck:
      test: ["CMD", "influx", "ping"]
      interval: 5s
      timeout: 3s
      retries: 12
      start_period: 10s

  # One-shot job. The bundled Grafana dashboard queries InfluxDB with InfluxQL,
  # which requires a DBRP mapping between a 1.x-style database name and the bucket.
  # Without this mapping every panel fails with "database not found".
  influxdb-init-dbrp:
    image: 'influxdb:2.7'
    depends_on:
      influxdb:
        condition: service_healthy
    environment:
      - INFLUX_HOST=http://influxdb:8086
      - INFLUX_ORG=keenetic
      - INFLUX_TOKEN=admin_token
      - DOCKER_INFLUXDB_INIT_BUCKET=keenetic
    command: >
      /bin/sh -c '
      set -e;
      BUCKET_ID=$$(influx bucket list --name "$$DOCKER_INFLUXDB_INIT_BUCKET" --hide-headers | awk '"'"'{print $$1}'"'"');
      if influx v1 dbrp list --db "$$DOCKER_INFLUXDB_INIT_BUCKET" --hide-headers | grep -q .; then
        echo "DBRP mapping for db=$$DOCKER_INFLUXDB_INIT_BUCKET already exists, skipping";
      else
        influx v1 dbrp create --db "$$DOCKER_INFLUXDB_INIT_BUCKET" --rp autogen --bucket-id "$$BUCKET_ID" --default;
        echo "DBRP mapping for db=$$DOCKER_INFLUXDB_INIT_BUCKET created";
      fi
      '

  # Optional all-in-one Grafana with automatic datasource and dashboard provisioning.
  # Remove this service if you use an existing Grafana installation.
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    depends_on:
      influxdb:
        condition: service_healthy
    ports:
      - 3000:3000
    environment:
      # Referenced by grafana/provisioning/datasources/influxdb.yml,
      # keep it in sync with DOCKER_INFLUXDB_INIT_ADMIN_TOKEN above.
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=admin_token
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    restart: always

volumes:
  grafana_data: {}
```

## Connect Grafana

> **Note**
> You need to have own Grafana installation or you could use free-tier [Grafana Cloud](https://grafana.com/grafana/)

**Option A: automatic (when using the compose file above)**

The datasource `InfluxDB-Keenetic` and the `Keenetic` dashboard folder are provisioned from `grafana/provisioning/`, nothing to do in the UI. The datasource takes the InfluxDB token from the `DOCKER_INFLUXDB_INIT_ADMIN_TOKEN` environment variable.

**Option B: manual**

Update your Grafana connection config

* Configuration -> Data sources
* Query language: InfluxQL
* URL: `http://<influxdb-host>:8086`
* Database: `keenetic` (the bucket name)
* Click add custom header
* Add header: 
```
Authorization		Token <TOKEN_VALUE>
```

> **Warning**

**"Token"** word should be before the token value itself

Do not specify username/password

![Example](https://github.com/vitaliy-sk/keenetic-grafana-monitoring/assets/2773025/a3239473-8dc0-4bdc-a2d0-4b4719b810c6)

# Troubleshooting

* The collector logs one line per cycle, e.g. `Collection cycle finished, 148 points written to InfluxDB`. If this line is missing or reports 0 points for a long time, check the router credentials in `config.ini` and the error messages above it.
* Dashboard panels show `database not found`: the DBRP mapping is missing, see [Preparation](#preparation).
* Dashboard panels show `database name required`: the datasource has no database set (manual setup: the Database field; provisioning: `jsonData.dbName`).
* Not sure the data reaches InfluxDB:

```bash
docker exec -it influxdb influx query 'from(bucket: "keenetic") |> range(start: -2m) |> limit(n: 5)'
```

# Run on router

* Copy repository content to your router `/opt/home/keenetic-grafana-monitoring`
* Install Python `opkg install python3`
* Preferred: install dependencies with `uv sync --frozen`
* Fallback if `uv` is unavailable on the router: install `python3-pip` and run `pip install -r requirements.txt`
* Create script for autorun `/opt/etc/init.d/S99keeneticgrafana`

```$bash
#!/bin/sh

[ "$1" != "start" ] && exit 0

PYTHON_BIN=/opt/home/keenetic-grafana-monitoring/.venv/bin/python
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python

nohup "$PYTHON_BIN" /opt/home/keenetic-grafana-monitoring/keentic_influxdb_exporter.py >/dev/null 2>&1 &
```

* Run `/opt/etc/init.d/S99keeneticgrafana start`

# Build Docker image

`docker build -t keenetic-grafana-monitoring .`

The Docker build now installs dependencies from `pyproject.toml` and `uv.lock`.

# InfluxDB 2.x / keenetic-grafana-monitoring 2.x migration manual

See on [wiki](https://github.com/vitaliy-sk/keenetic-grafana-monitoring/wiki/How-to-migrate-to-keenetic-grafana-monitoring-v2-and-Influx-v2)
