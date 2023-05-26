```
  _  __                    _   _         _____      _ _           _             
 | |/ /                   | | (_)       / ____|    | | |         | |            
 | ' / ___  ___ _ __   ___| |_ _  ___  | |     ___ | | | ___  ___| |_ ___  _ __ 
 |  < / _ \/ _ \ '_ \ / _ \ __| |/ __| | |    / _ \| | |/ _ \/ __| __/ _ \| '__|
 | . \  __/  __/ | | |  __/ |_| | (__  | |___| (_) | | |  __/ (__| || (_) | |   
 |_|\_\___|\___|_| |_|\___|\__|_|\___|  \_____\___/|_|_|\___|\___|\__\___/|_|   
                                                                                
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

* Import Grafana dashboard from [grafana.com](https://grafana.com/grafana/dashboards/12723)

# Run

There are two options, you can run the collector directly on the router or in Docker on a separate host.

## Run in Docker on a separate host (recommended)

```
---
version: '3.7'

services:

  keenetic-grafana-monitoring:
    image: techh/keenetic-grafana-monitoring:2.0.2
    container_name: keenetic-grafana-monitoring
    # environment:
    #  - TZ=Europe/Kiev
    volumes:
      - ./config/config.ini:/home/config/config.ini:ro
      # Optionally you can override metrics
      - ./config/metrics.json:/home/config/metrics.json:ro
    restart: always
  
  # Influx 2.x

  influxdb:
    image: 'influxdb:2.1'
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
```

## Connect Grafana

Update your Grafana connection config

* Configuration -> Data sources
* Click add custom header
* Add header: 
```
Authorization		Token <TOKEN_VALUE>
```

**"Token"** word should be before the token value itself

Do not specify username/password

![Example](https://github.com/vitaliy-sk/keenetic-grafana-monitoring/assets/2773025/a3239473-8dc0-4bdc-a2d0-4b4719b810c6)

## Run on router

* Copy repository content to your router `/opt/home/keenetic-grafana-monitoring`
* Install Python `opkg install python3 python3-pip`
* Install dependencies ` pip install -r requirements.txt`
* Create script for autorun `/opt/etc/init.d/S99keeneticgrafana`

```$bash
#!/bin/sh

[ "$1" != "start" ] && exit 0

nohup python /opt/home/keenetic-grafana-monitoring/keentic_influxdb_exporter.py >/dev/null 2>&1 &
```

* Run `/opt/etc/init.d/S99keeneticgrafana start`

# Build Docker image

`docker build -t keenetic-grafana-monitoring .`

# InfluxDB 2.x / keenetic-grafana-monitoring 2.x migration manual

See on [wiki](https://github.com/vitaliy-sk/keenetic-grafana-monitoring/wiki/How-to-migrate-to-keenetic-grafana-monitoring-v2-and-Influx-v2)
