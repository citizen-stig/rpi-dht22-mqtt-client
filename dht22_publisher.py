#!/usr/bin/env python
import configparser
import json
import logging
import os
import ssl
import sys
import time
from datetime import datetime
from logging.config import dictConfig
from pathlib import Path
from typing import Tuple

import Adafruit_DHT
import paho.mqtt.client as mqtt

log_level = 'DEBUG'
log_format = '%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(funcName)s: %(message)s'

logging_configuration = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': log_format,
        },
    },
    'handlers': {
        'default': {
            'level': log_level,
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'syslog': {
            'level': log_level,
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',
            'formatter': 'standard',
        },

    },
    'loggers': {
        '': {
            'handlers': ['default', 'syslog'],
            'level': log_level,
            'propagate': False
        },
    },
    'root': {
        'level': log_level,
        'handlers': ['default', 'syslog'],
        'propagate': False,
    }
}

logger = logging.getLogger('dht22_publisher')


def get_config() -> configparser.ConfigParser:
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'config.ini'
    )
    if not Path(config_path):
        sys.stderr.write('Cannot open config {}'.format(config_path))
        raise FileNotFoundError

    config = configparser.ConfigParser()
    config.read(config_path)

    return config


def build_mqtt_client(config: configparser.ConfigParser) -> mqtt.Client:
    """Specific for AWS IoT Broker"""
    config_section = 'mqtt'
    endpoint = config.get(config_section, 'endpoint')
    ca_path = 'AmazonRootCA1.pem'
    cert_path = config.get(config_section, 'cert_path')
    key_path = config.get(config_section, 'key_path')
    client_id = config.get(config_section, 'client_id')
    port = int(config.get(config_section, 'port', fallback=8883))

    mqtt_client = mqtt.Client(client_id=client_id)
    mqtt_client.tls_set(ca_certs=ca_path,
                        certfile=cert_path,
                        keyfile=key_path,
                        cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLSv1_2)
    mqtt_client.connect(endpoint, port)

    return mqtt_client


def get_humidity_and_temperature(pin: int) -> Tuple[datetime, float, float]:
    """Temperature in celsius, humidity in percentage"""
    timestamp = datetime.utcnow()
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, pin)
    return timestamp, humidity, temperature


def main():
    dictConfig(logging_configuration)
    config = get_config()

    mqtt_client = build_mqtt_client(config)
    mqtt_client.on_connect = lambda client, userdata, flags, rc: logger.debug('Connected to MQTT: %s'.format(rc))
    mqtt_client.loop_start()

    pin = int(config.get('main', 'dht22_pin'))
    location = config.get('main', 'location')
    topic = config.get('mqtt', 'topic')
    sleep_interval = int(config.get('main', 'sleep_interval'))

    while True:
        timestamp, humidity, temperature = get_humidity_and_temperature(pin)
        logger.debug("Data from DHT Sensor: %s, %s, %s", timestamp, humidity, temperature)
        data = {
            'timestamp': timestamp.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'location': location,
            'temperature': round(temperature, 3),
            'humidity': round(humidity, 3)
        }
        logger.debug('Going to send this data: %s', data)
        logger.debug('Publishing...')
        response = mqtt_client.publish(topic, json.dumps(data), qos=1)
        response.wait_for_publish()
        logger.debug('Published, going to sleep for %s seconds', sleep_interval)
        time.sleep(sleep_interval)


if __name__ == '__main__':
    main()
