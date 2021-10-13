```
  _  __                    _   _         _____      _ _           _             
 | |/ /                   | | (_)       / ____|    | | |         | |            
 | ' / ___  ___ _ __   ___| |_ _  ___  | |     ___ | | | ___  ___| |_ ___  _ __ 
 |  < / _ \/ _ \ '_ \ / _ \ __| |/ __| | |    / _ \| | |/ _ \/ __| __/ _ \| '__|
 | . \  __/  __/ | | |  __/ |_| | (__  | |___| (_) | | |  __/ (__| || (_) | |   
 |_|\_\___|\___|_| |_|\___|\__|_|\___|  \_____\___/|_|_|\___|\___|\__\___/|_|   
                                                                                
```

![Example](https://user-images.githubusercontent.com/2773025/88829802-c5809900-d1d5-11ea-8cbe-de41118387b3.png)

# Supporter router

Tested with: 
- Keenetic Ultra (KN-1810) KeeneticOS 3.5.6
- Keenetic Giga (KN-1010) KeeneticOS 3.5.6

May work on other Keenetic routers

# Preparation

* Create configuration file `config.ini`

```ini
[influxdb]
host=<HOST>
port=80
username=admin
password=<INFLUX_PASS>
db=keenetic
[keenetic]
skip_auth=false
admin_endpoint=http://192.168.1.1:80
login=admin
password=<KEENETIC_PASS>
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

There are two options, you can run collector directly on the router or in Docker on separate host.

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

## Run on Docker

```
---
version: '3.7'
services:
  keenetic-grafana-monitoring:
    image: techh/keenetic-grafana-monitoring:1.1.1
    container_name: keenetic-grafana-monitoring
    # environment:
    #  - TZ=Europe/Kiev
    volumes:
      - ./config/config.ini:/home/config/config.ini:ro
      # Optionally you can override metrics
      - ./config/metrics.json:/home/config/metrics.json:ro
    restart: always
```

# Build Docker image

`docker build -t keenetic-grafana-monitoring .`
