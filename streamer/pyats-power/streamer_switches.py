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
Streams data of switches to Thingsboard MQTT broker.

Additionally,
    saves CDP neighbors on disk, under /streamer/pyats-power/output.

This script runs only on real devices.

Naming convention for switch name:
switch_name_[number]

Expects:
- broker file            /onboard/thingsboard.yml
- switches file          /onboard/testbed.yml

Run example:
  cd <main folder>
  pip3 install -r streamer/pyats-power/requirements.txt

  python3.9 -m streamer.pyats-power.streamer_switches \
    --brokerfile=onboard/thingsboard.yml --testbedyml=onboard/testbed.yml

Run example as a service:
  cd <main folder>
  docker-compose up -d streamer-switches
"""

import os
import sys
import json
import time
import shutil
import getopt
import traceback
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool

import yaml
import unicon
from ttp import ttp
from pyats.topology import loader
import pyats.utils.yaml.exceptions
from genie.libs.parser.utils.common import ParserNotFound
from genie.metaparser.util.exceptions import SchemaEmptyParserError

from ..utils import mqttutils
from ..utils.logger import log

# Set default paths
testbed_file = "/onboard/testbed.yml"
broker_file = "/onboard/thingsboard.yml"

DRY_RUN = False  # Set to true for data display
CDP_SAMPLED_ONCE = False  # Set to true once we take a first sample of CDP neighbors
ON_PREM_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def connect_collect(device, commands):
    """
    Connects to switch, collects CLI data and saves it on the local disk.
    Returns: data.
    """

    output_data = {}
    interfaces = []
    d = testbed.devices[device]

    try:
        log.info("Device testbed: {}".format(d))
        d.connect(learn_hostname=True, log_stdout=False, init_config_commands=[])
        output_data["date"] = int(time.time_ns() / 1000000)
        output_data["device"] = str(device)
        for idx, command in enumerate(commands):
            try:
                if idx == 2:  # show power inline %s detail
                    # traverse interfaces and run command for each
                    for i in interfaces:
                        composite_command = command % (i)
                        try:
                            out = d.parse(composite_command)
                            output_data[composite_command] = out
                        except SchemaEmptyParserError as e:
                            log.error(
                                "{} Failed to parse output of composite command {}: {}".format(
                                    str(d), composite_command, e
                                )
                            )
                            output_data[composite_command] = {}

                        # Save locally: command for power inline <interface> detail

                        # Create device directory
                        device_dir = os.path.join(ON_PREM_OUTPUT_DIR, device)
                        os.makedirs(device_dir, exist_ok=True)

                        interface_dir = os.path.join(
                            device_dir, "_".join(composite_command.split(" "))
                        )

                        # Remove old content
                        try:
                            shutil.rmtree(interface_dir)
                        except FileNotFoundError:
                            pass
                        try:
                            os.makedirs(interface_dir)
                        except FileExistsError:
                            pass

                        # Save file in directory
                        with open(
                            os.path.join(
                                interface_dir,
                                str(output_data["date"]),
                            ),
                            "w",
                            encoding="utf-8",
                        ) as output_file:
                            output_file.write(
                                json.dumps(output_data[composite_command])
                            )

                else:
                    if idx != 4 or not CDP_SAMPLED_ONCE:
                        try:
                            output_data[command] = d.parse(command)
                        except SchemaEmptyParserError as e:
                            log.error(
                                "{} Failed to parse output of command {}: {}".format(
                                    str(d), command, e
                                )
                            )
                            output_data[command] = {}
                    if idx == 1 and output_data[command]:  # show power inline
                        # retain the interface names
                        interfaces = output_data[command]["interface"].keys()

            except ParserNotFound:
                if command == "show energywise":
                    data = d.execute(command)
                    ttp_template = (
                        """Total: {{ total_usage }} (W), Count: {{ count }}"""
                    )
                    parser = ttp(data=data, template=ttp_template)
                    parser.parse()
                    out = float(parser.result()[0][0]["total_usage"])
                    output_data[command] = out
                else:
                    log.warning('No parser found for command : "{}"'.format(command))

            finally:
                if idx != 2:
                    # Save locally only once: command for CDP neighbors
                    if not CDP_SAMPLED_ONCE and idx == 4:
                        # Create device directory
                        device_dir = os.path.join(
                            ON_PREM_OUTPUT_DIR, device, "show_cdp_neighbors"
                        )
                        os.makedirs(device_dir, exist_ok=True)

                        # Save file in directory
                        with open(
                            os.path.join(device_dir, str(output_data["date"])),
                            "w",
                            encoding="utf-8",
                        ) as output_file:
                            output_file.write(json.dumps(output_data[command]))

        d.disconnect()
    except unicon.core.errors.ConnectionError:
        log.warning("Cannot connect to device {}".format(device))
    return output_data


def collect(device):
    """
    Collects CLI data from switch based on a list of commands.
    The data is saved locally on the disk.
    Returns: data.
    """

    json_body = {}
    commands = [
        "show env all",
        "show power inline",  # Must be at index 1
        "show power inline %s detail",  # Must be at index 2
        "show version",
        "show cdp neighbors",  # Must be at index 4
        # "show energywise",
        # "show env temperature status"
    ]
    payload = connect_collect(device, commands)

    try:
        # show env all
        if "show env all" in payload:
            switchstack = payload["show env all"]["switch"]
            for switch in switchstack:
                log.info("Device {} - switch {}.".format(payload["device"], switch))
                device = "{}_{}".format(payload["device"], switch)
                values = {}
                if "fan" in switchstack[switch]:
                    for fan in switchstack[switch]["fan"]:
                        values["fan_{}_state".format(fan)] = switchstack[switch]["fan"][
                            fan
                        ]["state"]
                else:
                    log.warning("No FAN information for {}".format(device))

                if "hotspot_temperature" in switchstack[switch]:
                    values["hotspot_temperature"] = float(
                        switchstack[switch]["hotspot_temperature"]["value"]
                    )
                else:
                    log.warning(
                        "No hotspot_temperature information for {}".format(device)
                    )

                if "inlet_temperature" in switchstack[switch]:

                    values["inlet_temperature"] = float(
                        switchstack[switch]["inlet_temperature"]["value"]
                    )
                else:
                    log.warning(
                        "No inlet_temperature information for {}".format(device)
                    )

                if "outlet_temperature" in switchstack[switch]:
                    values["outlet_temperature"] = float(
                        switchstack[switch]["outlet_temperature"]["value"]
                    )
                else:
                    log.warning(
                        "No outlet_temperature information for {}".format(device)
                    )

                # show power inline
                if payload["show power inline"]:
                    pw_inline_watts = payload["show power inline"]["watts"]
                    try:
                        values["watts_available"] = int(
                            pw_inline_watts[str(switch)]["available"]
                        )
                        values["watts_remaining"] = int(
                            pw_inline_watts[str(switch)]["remaining"]
                        )
                        values["used"] = int(pw_inline_watts[str(switch)]["used"])
                    except KeyError:
                        values["watts_available"] = int(
                            pw_inline_watts[switch]["available"]
                        )
                        values["watts_remaining"] = int(
                            pw_inline_watts[switch]["remaining"]
                        )
                        values["used"] = int(pw_inline_watts[switch]["used"])

                    pw_inline_interfaces = payload["show power inline"]["interface"]
                    total_power = 0
                    for intf in pw_inline_interfaces:
                        # TODO(): more robust testing
                        if "{}/0/".format(switch) in intf:
                            values["{}_oper_state".format(intf)] = pw_inline_interfaces[
                                intf
                            ]["oper_state"]
                            values["{}_power".format(intf)] = int(
                                pw_inline_interfaces[intf]["power"]
                            )
                            values["{}_device".format(intf)] = pw_inline_interfaces[
                                intf
                            ].get("device", None)
                            total_power += int(pw_inline_interfaces[intf]["power"])
                    values["total_interfaces_power"] = total_power
                else:
                    values["total_interfaces_power"] = 0

                # show energywise
                # values["energywise"] = float(payload['show energywise'])
                tb_payload = {"ts": payload["date"], "values": values}
                json_body[device] = [tb_payload]
    except Exception as e:
        log.error(traceback.format_exc())
        log.error("Error on device : {}".format(device))

    return json_body


def main(argv):
    """Parses arguments and loads metadata."""

    global client, broker, broker_file, testbed, testbed_file, DRY_RUN, CDP_SAMPLED_ONCE

    try:
        opts, args = getopt.getopt(
            argv, "mtdbp:", ["brokerfile=", "testbedyml=", "dry-run"]
        )
    except getopt.GetoptError:
        log.error(
            "streamer_switches.py --brokerfile=<mqttbrokerfileyml> --testbedyml=<testbedsyml>"
        )
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-m", "--brokerfile"):
            broker_file = arg
        if opt in ("-t", "--testbedyml"):
            testbed_file = arg
        if opt in ("-d", "--dry-run"):
            DRY_RUN = True

    log.info("§§§ On-prem-only streaming. §§§")
    os.makedirs(ON_PREM_OUTPUT_DIR, exist_ok=True)

    # Load Thingsboard's MQTT broker information
    broker = yaml.load(open(broker_file, encoding="utf-8"), Loader=yaml.Loader)[
        "broker"
    ]

    # Load the switches testbed file
    try:
        testbed = loader.load(testbed_file)
    except pyats.utils.yaml.exceptions.LoadError as error:
        log.error("Failed to load testbed file: %s", str(error))
        sys.exit(1)


# Collect data from switches, save data on the disk
# and to the Thingsboard's MQTT broker (to Thingsboard: all except APs data).
if __name__ == "__main__":
    main(sys.argv[1:])

    this_file = os.path.basename(__file__)

    while True:
        # with ThreadPool(processes=4) as p:
        with Pool(processes=4) as p:
            collections = p.map(collect, testbed.devices)

        if DRY_RUN:
            for c in collections:
                print(json.dumps(c))
            continue

        # Post data to Thingsboard
        client = mqttutils.create_client(broker, this_file)
        log.info("Finished gathering data.")

        # Publish every 5 minutes but give MQTT client
        # 60s time to post messages before disconnecting
        msg_info = mqttutils.publish_collections_telemetry(
            client, collections, sleep_once_s=60
        )

        client.disconnect()
        time.sleep(270)
        CDP_SAMPLED_ONCE = True
