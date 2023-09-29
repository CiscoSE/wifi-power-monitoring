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
Streams data of switches to the disk under /streamer/pyats-power/extra-output.

This script runs only on real devices.

Cadence: 1h.

Naming convention for switch name:
switch_name

Expects:
- switches file          /onboard/minimal-testbed.yml

Run example:
  cd <main folder>
  pip3 install -r streamer/pyats-power/requirements.txt

  python3.9 -m streamer.pyats-power.streamer_switches_extra \
    --testbedyml=onboard/testbed.yml [--dry-run]

Run example as a service:
  cd <main folder>
  docker-compose up -d streamer-switches-extra
"""

import os
import sys
import json
import time
import getopt
import traceback
from multiprocessing.pool import ThreadPool

import unicon
from pyats.topology import loader
import pyats.utils.yaml.exceptions
from genie.libs.parser.utils.common import ParserNotFound

from ..utils.logger import log

# Set default paths
testbed_file = "/onboard/testbed.yml"

DRY_RUN = False  # Set to true for data display
ON_PREM_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "extra-output")


def connect_collect_and_save_data(device, commands):
    """
    Connects to switch, collects CLI data and save it on the local disk.
    Returns: data.
    """

    cli_format_data = {}
    json_format_data = {}
    d = testbed.devices[device]

    try:
        log.info("Device testbed: {}".format(d))
        d.connect(learn_hostname=True, log_stdout=False, init_config_commands=[])
        timestamp = str(int(time.time_ns() / 1000000))
        for command in commands:
            try:
                # Use CLI format
                cli_format_out = d.execute(command)
                json_format_out = d.parse(command)
                cli_format_data[command] = cli_format_out
                json_format_data[command] = json_format_out

                if not DRY_RUN:
                    # Create device directory
                    device_dir = os.path.join(
                        ON_PREM_OUTPUT_DIR, device, "_".join(command.split(" "))
                    )
                    os.makedirs(device_dir, exist_ok=True)

                    # Save files in directory in 2 formats: CLI and JSON
                    with open(
                        os.path.join(device_dir, timestamp + ".cli"),
                        "w",
                        encoding="utf-8",
                    ) as output_file:
                        output_file.write(cli_format_data[command])
                    with open(
                        os.path.join(device_dir, timestamp + ".json"),
                        "w",
                        encoding="utf-8",
                    ) as output_file:
                        output_file.write(
                            json.dumps(json_format_data[command], indent=2)
                        )

            except ParserNotFound:
                log.warning(
                    '{}: No parser found for command : "{}"'.format(device, command)
                )
            except Exception as e:
                log.warning(
                    "{}: Exception on [running] command {}: {}".format(
                        device, command, e
                    )
                )

        d.disconnect()
    except unicon.core.errors.ConnectionError:
        log.warning("Cannot connect to device {}".format(device))
    return cli_format_data


def collect(device):
    """
    Collects CLI data from switch based on a list of commands.
    The data is saved locally on the disk.
    Returns: data.
    """

    commands = [
        "show environment",
        "show environment all",
        "show environment power all",
        # "show environment status",
        # "show environment stack",
        # "show environment fan",
        # "show power",
        "show power status all",
        "show power total",
        "show power available",
        "show power used",
        # "show stack-power details",
        "show version",
        "show int status"
        # "show energywise",
    ]
    try:
        payload = connect_collect_and_save_data(device, commands)
        return payload

    except Exception as e:
        log.error(traceback.format_exc())
        log.error("Error on device : {}".format(device))

    return None


def main(argv):
    """Parses arguments and loads metadata."""

    global testbed, testbed_file, DRY_RUN

    try:
        opts, args = getopt.getopt(argv, "td:", ["testbedyml=", "dry-run"])
    except getopt.GetoptError:
        log.error("streamer_switches_extra.py --testbedyml=<testbedsyml>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-t", "--testbedyml"):
            testbed_file = arg
        if opt in ("-d", "--dry-run"):
            DRY_RUN = True

    log.info("§§§ On-prem-only collection. §§§")
    os.makedirs(ON_PREM_OUTPUT_DIR, exist_ok=True)

    # Load the switches testbed file
    try:
        testbed = loader.load(testbed_file)
    except pyats.utils.yaml.exceptions.LoadError as error:
        log.error("Failed to load testbed file: %s", str(error))
        sys.exit(1)


# Collect data from switches, save data on the disk
if __name__ == "__main__":
    main(sys.argv[1:])

    this_file = os.path.basename(__file__)

    while True:
        with ThreadPool(processes=4) as p:
            collections = p.map(collect, testbed.devices)

        if DRY_RUN:
            for c in collections:
                print(json.dumps(c))
            continue

        # Sleep 1h
        time.sleep(3600)
