"""
Copyright (c) 2023 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
"""
Covers connection to an MQTT broker.
"""

import os
import time
import json
import socks
import logging

import paho.mqtt.client as mqtt

log = logging.getLogger("mqtt-broker")
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def on_connect(client, userdata, flags, rc):
    log.info("Connected with result code %s", str(rc))


def on_disconnect(client, userdata, rc=0):
    log.info("Disconnected with result code %s", str(rc))
    client.loop_stop()


def create_client(broker, client_id):
    client = mqtt.Client(client_id)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # Set proxy:
    if "HTTPS_PROXY" in os.environ and os.environ["HTTPS_PROXY"]:
        proxy_addr = os.environ["HTTPS_PROXY"].rpartition(":")[0].rpartition("://")[2]
        proxy_port = int(os.environ["HTTPS_PROXY"].rpartition(":")[2])
        client.proxy_set(
            proxy_type=socks.HTTP, proxy_addr=proxy_addr, proxy_port=proxy_port
        )

    client.username_pw_set(username=broker["username"], password=broker["password"])

    # Try connecting to MQTT, repeat every 1s until successful
    while True:
        try:
            client.connect(broker["destination"], broker["port"], 60)
            break
        except Exception as e:
            log.info("Failed to connect to MQTT broker. %s", str(e))
        time.sleep(1)

    client.loop_start()

    return client


def publish_collections_telemetry(client, collections, sleep_once_s):
    """
    Publishes collections to Thingsboard's MQTT endpoint "v1/gateway/telemetry" with QOS=1.

    Sleeps once sleep_s seconds before finishing.

    Returns: msg_info.
    """

    for c in collections:
        log.info("Publishing content for %s", str(c.keys()))

        msg_info = client.publish(
            "v1/gateway/telemetry", json.dumps(c), qos=1, retain=False
        )

        try:
            log.info(msg_info.is_published())
        except Exception as exc:
            log.error("ERROR on telemetry publish: %s", str(exc))

    # Give MQTT client time to post messages before disconnecting
    time.sleep(sleep_once_s)

    return msg_info


def publish_connect_device(client, body):
    """
    Publishes the JSON body to Thingsboard's MQTT endpoint "v1/gateway/connect" with QOS=1.

    Returns: msg_info.
    """

    msg_info = client.publish(
        "v1/gateway/connect", json.dumps(body), qos=1, retain=False
    )

    # Give MQTT client time to post the message before disconnecting
    time.sleep(2)

    try:
        log.info(msg_info.is_published())
    except Exception as exc:
        log.error("ERROR on device connect publish: %s", str(exc))

    return msg_info


def publish_attributes(client, body):
    """
    Publishes the JSON body to Thingsboard's MQTT endpoint "v1/gateway/attributes" with QOS=1.

    Returns: msg_info.
    """

    msg_info = client.publish(
        "v1/gateway/attributes", json.dumps(body), qos=1, retain=False
    )

    # Give MQTT client time to post the message before disconnecting
    time.sleep(2)

    try:
        log.info(msg_info.is_published())
    except Exception as exc:
        log.error("ERROR on attributes publish: %s", str(exc))

    return msg_info
