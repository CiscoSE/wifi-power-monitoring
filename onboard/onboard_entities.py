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
Defines assets (sites, zones) and their relations to assets and customer.
Optionally, defines entities (aps, switches) and their relations 
to assets and customer.

Relations are described in onboard/relations.yml.

Assignments:
 customer -> site
 customer -> zone

Relations:
 site -> zone

Switch devices:
- defined based on live data when IS_OFFLINE=false
- defined based on switches.yml when IS_OFFLINE=true, APS_ONLY=false
Defined here in case of offline mode:
IS_OFFLINE=false
or
IS_OFFLINE=true, APS_ONLY=false
 Assets:
  switch
 Assignments:
  customer -> switch
 Relations:
  zone -> switch

AP devices:
- always defined based on aps.yml
IS_OFFLINE=true/false, APS_ONLY=true/false
 Assets:
  ap
 Assignments:
  customer -> ap
 Relations:
  zone -> ap

Not defined here anymore (subject to debate):
 site -> ap

Not defined here:
 switch -> switch_stack_component1, switch_stack_component2 (requires knowledge of switch-stack)
 switch -> ap (requires knowledge of switch-stack)

Environment variables:
IS_OFFLINE = true/false (default: false)
APS_ONLY = true/false (default: true)
SETTINGS_FILE = default: - (see onboard/settings.ini)

Expects:
- REST API file         /onboard/thingsboard.yml

For real environment
- sites file            /onboard/yaml/sites.yml
- zones file            /onboard/yaml/zones.yml
- APs file              /onboard/yaml/aps.yml (optional)
- switches file         /onboard/yaml/switches.yml.

Assumes:
- settings file: onboard/settings.ini or environment variable SETTINGS_FILE

Run example:
  cd <main folder>
  pip3 install -r onboard/requirements.txt
  export SETTINGS_FILE=onboard/settings-test.ini

  python3.9 -m onboard.onboard_entities

Run example as a service:
  cd <main folder>

  docker-compose up -d onboard (runs multiple onboard scripts)
"""

import os
import sys
import multiprocessing

import yaml

from utils import tbyaml
from utils.logger import log
from utils.config import config
from utils.tbclient import TbRestClient
from utils.tbentity import TbEntity, TbAsset
from utils.tbentity import TbEntityType, TbAssetType, TbDeviceType

# Set default paths
sites_file = config["paths_objects_real_env"]["sites_file"]
zones_file = config["paths_objects_real_env"]["zones_file"]
aps_file = config["paths_objects_real_env"]["aps_file"]
switches_file = config["paths_objects_real_env"]["switches_file"]


def main():
    global sites_file, zones_file, aps_file, switches_file

    customer_id = ""
    is_offline = False

    # Set to env var APS_ONLY to False if onboarding of
    # switches should also be done offline
    aps_only = True

    if "IS_OFFLINE" in os.environ and os.environ["IS_OFFLINE"]:
        is_offline = os.getenv("IS_OFFLINE", "False").lower() in ("true")

        log.info("Is offline? %s", is_offline)

    if "APS_ONLY" in os.environ and os.environ["APS_ONLY"]:
        aps_only = os.getenv("APS_ONLY", "True").lower() in ("false")

        log.info("Onboarding APs only? %s", aps_only)

    with open(
        config["paths_apis"]["tb_file"], encoding="utf-8"
    ) as thingsboard_file_handle:
        thingsboard_file = yaml.load(thingsboard_file_handle, Loader=yaml.Loader)

    api = thingsboard_file["api"]
    rest_client = TbRestClient(api)

    # Create customer
    _ = tbyaml.create_customer(thingsboard_file, rest_client)
    customer_id = tbyaml.get_customer_id(thingsboard_file, rest_client)
    customer_name = tbyaml.get_customer_name(thingsboard_file)

    # Create MQTT gateway for the MQTT client
    mqtt_gateway = tbyaml.create_entity(
        (
            ("MQTT-gateway-" + customer_name, {}),
            TbEntityType.DEVICE,
            TbDeviceType.GATEWAY,
        )
    )
    rest_client.tb_create_device(
        mqtt_gateway,
        gateway_credentials=(
            thingsboard_file["broker"]["username"],
            thingsboard_file["broker"]["password"],
        ),
    )

    # ASSETS
    with open(sites_file, encoding="utf-8") as sites_file_handle:
        sites = yaml.load(sites_file_handle, Loader=yaml.Loader)["sites"]
    with open(zones_file, encoding="utf-8") as zones_file_handle:
        zones = yaml.load(zones_file_handle, Loader=yaml.Loader)["zones"]

    # Get lists of assets of type TbEntity
    with multiprocessing.Pool(processes=4) as p:
        assets_sites = p.map(
            tbyaml.create_entity,
            [(s, TbEntityType.ASSET, TbAssetType.SITE) for s in sites],
        )
    with multiprocessing.Pool(processes=4) as p:
        assets_zones = p.map(
            tbyaml.create_entity,
            [(z, TbEntityType.ASSET, TbAssetType.ZONE) for z in zones],
        )

    log.info("Site assets: %s", [asset.name for asset in assets_sites])
    log.info("Zone assets: %s", [asset.name for asset in assets_zones])

    # TODO(): merge children for lists with duplicate assets

    # Define the assets with Thingsboard API
    _ = [rest_client.tb_create_asset(asset) for asset in assets_sites]
    _ = [rest_client.tb_create_asset(asset) for asset in assets_zones]

    # Assign assets to customer
    _ = [
        rest_client.tb_assign_to_customer(asset, customer_id)
        for asset in assets_sites + assets_zones
    ]

    # Create relations: asset-asset (site-zone)
    for asset in assets_sites:
        for child in asset.children:
            rest_client.tb_create_relation(
                asset, TbAsset(child, TbEntityType.ASSET, TbAssetType.ZONE)
            )

    # Skip onboarding of devices unless this is offline mode
    if is_offline or aps_only:
        # DEVICES
        devices_aps, devices_switches = [], []

        try:
            # Onboard APs if is offline, or APS_ONLY
            if os.path.exists(aps_file):
                with open(aps_file, encoding="utf-8") as aps_file_handle:
                    aps = yaml.load(aps_file_handle, Loader=yaml.Loader)["devices"]

                # Get lists of devices of type TbEntity
                with multiprocessing.Pool(processes=4) as p:
                    devices_aps = p.map(
                        tbyaml.create_entity,
                        [
                            (a, TbEntityType.DEVICE, TbDeviceType.AP)
                            for a in aps.items()
                        ],
                    )

                log.info("AP devices: %s", [device.name for device in devices_aps])

                # Define the devices with Thingsboard API
                _ = [rest_client.tb_create_device(device) for device in devices_aps]

                # Save device attributes with Thingsboard API
                _ = [
                    rest_client.tb_save_device_attributes(device)
                    for device in devices_aps
                ]
            else:
                log.warning("APs file %s is missing", aps_file)

        except yaml.YAMLError as exc:
            log.error("Cannot load content of APs file %s - %s", aps_file, str(exc))

        try:
            # Onboard switches if offline mode, not APS_ONLY
            if os.path.exists(switches_file) and not aps_only:
                with open(switches_file, encoding="utf-8") as switches_file_handle:
                    switches = yaml.load(switches_file_handle, Loader=yaml.Loader)[
                        "devices"
                    ]

                # Get lists of devices of type TbEntity
                with multiprocessing.Pool(processes=4) as p:
                    devices_switches = p.map(
                        tbyaml.create_entity,
                        [
                            (s, TbEntityType.DEVICE, TbDeviceType.SWITCH)
                            for s in switches.items()
                        ],
                    )

                log.info(
                    "Switch devices: %s", [device.name for device in devices_switches]
                )

                # Define the devices with Thingsboard API
                _ = [
                    rest_client.tb_create_device(device) for device in devices_switches
                ]
            else:
                log.warning("Switches file %s is missing", switches_file)
        except yaml.YAMLError as exc:
            log.error(
                "Cannot load content of switches file %s - %s",
                switches_file,
                str(exc),
            )

        # Assign devices to customer
        _ = [
            rest_client.tb_assign_to_customer(device, customer_id)
            for device in devices_aps + devices_switches
        ]

        # Save device attributes with Thingsboard API
        # Create relations: device-asset (ap,switch<-zone)
        for device in devices_aps + devices_switches:
            for parent in device.parents.items():
                if parent[0] != "site" and parent[0] != "switch":
                    entity_type = TbEntityType.ASSET
                    rest_client.tb_create_relation(
                        TbEntity(parent[1], entity_type), device
                    )

    log.info("FINISHED.")
    sys.exit(os.EX_OK)


if __name__ == "__main__":
    main()
