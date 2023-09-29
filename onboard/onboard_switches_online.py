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
In online mode (not simulated).
This script runs only on real devices: IS_OFFLINE=false.

Defines switches and their relations to zones.

Relations are described in onboard/relations.yml.

Naming convention for switch name:
switch_name_[number]

Entities:
 switch

Assignments:
 customer -> switch

Relations:
 zone -> switch

Not defined here (subject to debate):
 site -> ap
 zone -> ap (done in onboard_entities.py)

Not defined here:
switch -> switch_stack_component1, switch_stack_component2 (requires knowledge of switch-stack)
switch -> ap (requires knowledge of switch-stack)

Environment variables:
IS_OFFLINE = false (default: false)
SETTINGS_FILE = default: - (see onboard/settings.ini)

Expects:
- broker file               /onboard/thingsboard.yml
- PyATS connection details  /onboard/testbed.yml
- switches file             /onboard/yaml/switches.yml.

Run example:
  cd <main folder>
  pip3 install -r onboard/requirements.txt
  export SETTINGS_FILE=onboard/settings-test.ini

  python3.9 -m onboard.onboard_switches_online

Run example as a service:
  cd <main folder>

  docker-compose up -d onboard (runs multiple onboard scripts)
"""

import os
import copy
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool


import yaml
import unicon
from pyats.topology import loader


from utils import tbyaml
from utils import mqttutils
from utils.logger import log
from utils.config import config
from utils.tbclient import TbRestClient
from utils.tbentity import TbEntity, TbEntityType, TbDevice, TbDeviceType


def connect_and_collect_data(device, commands):
    """
    Collects with PyATS to device and executes given set of commands.
    Returns: output of commands.
    """
    output_data = {}
    d = testbed.devices[device]
    try:
        d.connect(learn_hostname=True, log_stdout=False, init_config_commands=[])
        for command in commands:
            out = d.parse(command)
            output_data[command] = out
        d.disconnect()
    except unicon.core.errors.ConnectionError as exc:
        log.warning("Cannot connect to device {} - {}".format(d, exc))
    return output_data


def collect(device):
    """
    Collects CLI data from switch based on a list of commands:
     - show version
     - show cdp neighbors
    Returns: body with data.
    """
    commands = ["show version", "show cdp neighbors"]

    payload = connect_and_collect_data(device, commands)
    body = {}

    if "show version" in payload:
        sh_ver = payload["show version"]["version"]

        for sw in sh_ver["switch_num"]:
            device_name = "{}_{}".format(str(device), sw)
            attributes = {}
            attributes["serial"] = sh_ver["chassis_sn"]
            attributes["os"] = sh_ver["os"]
            attributes["address"] = str(testbed.devices[device].connections.cli.ip)
            attributes["version"] = sh_ver["version"]
            attributes["mac-address"] = sh_ver["switch_num"][sw]["mac_address"]
            attributes["model"] = sh_ver["switch_num"][sw]["model"]

            body[device_name] = attributes

    return body


def main():
    global testbed

    this_file = os.path.basename(__file__)

    tb_file = config["paths_apis"]["tb_file"]
    switches_file = config["paths_objects_real_env"]["switches_file"]
    testbed_file = config["paths_objects_real_env"]["pyats_testbed_file"]

    with open(tb_file, encoding="utf-8") as thingsboard_file_handle:

        thingsboard_file = yaml.load(thingsboard_file_handle, Loader=yaml.Loader)
        broker = thingsboard_file["broker"]

        api = thingsboard_file["api"]
        rest_client = TbRestClient(api)
        customer_id = tbyaml.get_customer_id(thingsboard_file, rest_client)

        try:
            if os.path.exists(testbed_file):
                testbed = loader.load(testbed_file)

                # Collect data from switches
                with ThreadPool(processes=4) as p:
                    collections = p.map(collect, testbed.devices)

                # Connect to the MQTT broker
                client = mqttutils.create_client(broker, this_file)

                log.info(collections)

                devices_switches = []
                # Load switches information (zone, site, etc)
                try:
                    if os.path.exists(switches_file):
                        with open(
                            switches_file, encoding="utf-8"
                        ) as switches_file_handle:
                            switches = yaml.load(
                                switches_file_handle, Loader=yaml.Loader
                            )["devices"]

                            # with Pool(processes=4) as p:
                            with ThreadPool(processes=4) as p:
                                devices_switches = p.map(
                                    tbyaml.create_entity,
                                    [
                                        (s, TbEntityType.DEVICE, TbDeviceType.SWITCH)
                                        for s in switches.items()
                                    ],
                                )

                    else:
                        log.warning("Switches file %s is missing", switches_file)
                except Exception as exc:
                    log.error(
                        "Cannot load content of switches file %s - %s",
                        switches_file,
                        exc,
                    )

                for devices in collections:
                    for device in devices:
                        switch = TbDevice(
                            entity_name=device,
                            entity_type=TbEntityType.DEVICE,
                            device_type=TbDeviceType.SWITCH,
                        )

                        # Define the device
                        rest_client.tb_create_device(switch)

                        # Assign device to customer
                        rest_client.tb_assign_to_customer(switch, customer_id)

                        # Save device attributes
                        # Create relations: device-asset (switch<-zone)
                        for d in devices_switches:
                            # Check if the name in the switches.yml file is
                            # a substring of the generated name.
                            if d.name + "_" in device:
                                for parent in d.parents.items():
                                    if parent[0] != "site" and parent[0] != "switch":
                                        copy_d = copy.deepcopy(d)
                                        copy_d.name = device
                                        entity_type = TbEntityType.ASSET
                                        rest_client.tb_create_relation(
                                            TbEntity(parent[1], entity_type), copy_d
                                        )

                        # Reference: https://thingsboard.io/docs/reference/gateway-mqtt-api/
                        log.info("Connecting... %s", device)
                        body = {
                            "device": device,
                        }
                        _ = mqttutils.publish_connect_device(client, body)

                        body = {device: devices[device]}
                        log.info("Registering attributes for this device... %s", body)
                        _ = mqttutils.publish_attributes(client, body)

            else:
                log.warning("Testbed switches file %s is missing", testbed_file)
        except Exception as exc:
            log.error(
                "Cannot load content of testbed switches file %s - %s",
                testbed_file,
                exc,
            )


if __name__ == "__main__":
    main()
