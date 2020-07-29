```
  _  __                    _   _         _____      _ _           _             
 | |/ /                   | | (_)       / ____|    | | |         | |            
 | ' / ___  ___ _ __   ___| |_ _  ___  | |     ___ | | | ___  ___| |_ ___  _ __ 
 |  < / _ \/ _ \ '_ \ / _ \ __| |/ __| | |    / _ \| | |/ _ \/ __| __/ _ \| '__|
 | . \  __/  __/ | | |  __/ |_| | (__  | |___| (_) | | |  __/ (__| || (_) | |   
 |_|\_\___|\___|_| |_|\___|\__|_|\___|  \_____\___/|_|_|\___|\___|\__\___/|_|   
                                                                                
```

# Build from sources

`docker build -t keenetic-grafana-monitoring .`

# Preparation

* Create InfluxDB configuration file `influx.json`

```json
{
  "influxdb": {
    "host": "<HOST>",
    "port": 80,
    "username": "admin",
    "password": "<PASS>",
    "db": "keenetic"
  }
}
```

* Expose Keenetic API on your router

For doing this add port forwarding (Network rules -> Forwarding):
```
Input: Other destination
IP address: Your network ip (like 192.168.1.0)
Subnet mask: 255.255.255.0
Output: This Keenetic
Open the port: 79
Destination port: 79 
```

# Run with docker-compose.yml

```

```

