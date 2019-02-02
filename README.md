# Description

Simple MQTT client for [DHT22](https://www.adafruit.com/product/385) temperature and humidity sensor

MQTT client is configured with specific to AWS IoT Broker


## How to start

Install dependencies
```bash
pip3 install -r requirements.txt
```

Adjust configuration, specify DHT22 pin, broker configuration and other options
```bash
cp config.ini.example config.ini
```

Configure daemon. copy service description and adjust execution command
```bash
cp dht22_mqtt.service.example dht22_mqtt.service
```

Make adjustments and then install service:
```bash
cp dht22_mqtt.service /etc/systemd/system/
sudo systemctl enable dht22_mqtt
sudo systemctl daemon-reload
sudo systemctl start dht22_mqtt.service
sudo systemctl status dht22_mqtt.service
```
