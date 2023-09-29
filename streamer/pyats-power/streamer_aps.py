#!/usr/bin/env python
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
Streams live data of APs to Thingsboard.

APs are the ones read from:
    disk, under /streamer/pyats-power/output.that

Expects:
 - broker file            '/onboard/thingsboard.yml'

Run example:
  cd <main folder>
  pip3 install -r streamer/pyats-power/requirements.txt

  python3.9 -m streamer.pyats-power.streamer_aps \
    --brokerfile=onboard/thingsboard.yml

Run example as a service:
  cd <main folder>
  docker-compose up -d streamer-aps
"""

import os
import sys
import time
import getopt
import multiprocessing

import json
import yaml

from ..utils import local
from ..utils import mqttutils
from ..utils.logger import log


# Thingsboard broker
broker = []

# Set default paths
broker_file = "/onboard/thingsboard.yml"
ON_PREM_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def read_aps_power(switch):
    """
    Read PoE information from local disk for all APs of a given switch.

    Returns: Thingsboard-MQTT formatted collection of sample points, e.g.:
    [AP_1: {"ts": ts, "values": {"PoE": 6.5}}]
    """

    collection = []

    # Get measured power for each CDP neighbor
    # from the power inline <if> details file.
    # Based on the latest file.

    # For each AP
    for i, neighbor in enumerate(switch[1]):
        # Only used only when patching missing data
        """
        if neighbor[0] in to_be_updated_TS:
            collection.append({})
            continue
        else:
        """
        collection.append({neighbor[0]: []})

        interface_dir = os.path.join(
            ON_PREM_OUTPUT_DIR,
            switch[0],
            "show_power_inline_" + neighbor[1] + "_detail",
        )
        try:
            # file = os.path.join(interface_dir, os.listdir(interface_dir)[0])
            with open(
                os.path.join(interface_dir, os.listdir(interface_dir)[0]),
                encoding="utf-8",
            ) as fp:
                # Initialize

                payload = json.load(fp)
                ts = os.path.basename(
                    os.path.join(interface_dir, os.listdir(interface_dir)[0])
                )

                measured_power = float(
                    payload["interface"][neighbor[1]]["measured_consumption"]
                )

                data = {"ts": ts, "values": {"PoE": measured_power}}
                collection[i].get(neighbor[0]).append(data)
        except FileNotFoundError as e:
            log.warning("Will skip reading data for {}".format(neighbor[0]))

    return collection


def main(argv):
    """Parses arguments and loads metadata."""

    global broker, broker_file

    try:
        opts, args = getopt.getopt(argv, "m:", ["brokerfile="])
    except getopt.GetoptError:
        log.error("streamer_aps.py --brokerfile=<new_thingsboard.yml>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-m", "--brokerfile"):
            broker_file = arg

    log.info("§§§ On-prem reading. §§§")

    # Load Thingsboard's MQTT broker information
    broker = yaml.load(open(broker_file, encoding="utf-8"), Loader=yaml.Loader)[
        "broker"
    ]


if __name__ == "__main__":
    main(sys.argv[1:])

    this_file = os.path.basename(__file__)

    # Read from local disk
    # Read switches
    switches = os.listdir(ON_PREM_OUTPUT_DIR)

    # Read CDP neighbors
    with multiprocessing.Pool(processes=8) as p:
        cdp_neighbors = p.map(
            local.read_cdp_neigbors,
            [
                (
                    s,
                    max(
                        [
                            os.path.join(ON_PREM_OUTPUT_DIR, s, "show_cdp_neighbors", f)
                            for f in os.listdir(
                                os.path.join(
                                    ON_PREM_OUTPUT_DIR, s, "show_cdp_neighbors"
                                )
                            )
                        ],
                        key=os.path.getctime,
                    ),
                )
                for s in switches
            ],
        )

    log.info("CDP Neighbors - %s", str(cdp_neighbors))

    # Read latest AP data, every ~13 minutes
    while True:
        # Read APs power based on show power inline <interface> detail CLI command
        with multiprocessing.Pool(processes=8) as p:
            collections = p.map(read_aps_power, cdp_neighbors)

        # Connect to Thingsboard's MQTT broker and send APs' data
        mqtt_client = mqttutils.create_client(broker, this_file)

        flatten_collections = [
            item for collection in collections for item in collection
        ]
        log.info("Publishing content for %i APs", len(flatten_collections))

        # Publish every ~11 minutes but give MQTT client
        # 120s time to post messages before disconnecting
        msg_info = mqttutils.publish_collections_telemetry(
            mqtt_client, flatten_collections, sleep_once_s=120
        )

        try:
            log.info(msg_info.is_published())
        except Exception as e:
            log.error("ERROR on telemetry publish: %s", str(e))
        mqtt_client.disconnect()

        # Wait another 9 minutes before querying again
        # (data is spaced at ~13 minutes)
        time.sleep(540)
