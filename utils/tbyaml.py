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
Helper methods for reading yaml content.
"""

import logging

from .tbentity import TbAsset, TbDevice, TbEntity, TbEntityType

log = logging.getLogger("thingsboard-yaml")
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_customer(thingsboard_file):
    # Read customer in case it is defined
    if (
        "customer" in thingsboard_file
        and "name" in thingsboard_file["customer"]
        and thingsboard_file["customer"]["name"]
    ):
        customer = TbEntity(
            entity_name=thingsboard_file["customer"]["name"],
            entity_type=TbEntityType.CUSTOMER,
        )
        log.info("Customer %s is defined!", customer.name)
        return customer

    return None


def get_customer_name(thingsboard_file):
    customer = get_customer(thingsboard_file)
    if customer:
        return customer.name
    return ""


def get_customer_id(thingsboard_file, rest_client):
    customer = get_customer(thingsboard_file)
    if customer:
        return rest_client.tb_get_customer_id(customer)
    else:
        log.error("Cannot retrieve customer ID: missing customer name!")

    return ""


def create_customer(thingsboard_file, rest_client):
    customer = get_customer(thingsboard_file)
    if customer:
        return rest_client.tb_create_customer(customer)
    else:
        log.error("Cannot create customer: missing customer name!")
    return ""


def create_entity(properties):
    if "mapKey" in properties[0]:
        # Treat case association lists: sites and zones
        entity = TbAsset(
            entity_name=properties[0]["mapKey"],
            entity_type=properties[1],
            asset_type=properties[2],
        )
        entity.add_child(
            list(properties[0]["mapValue"].values())[0],
            list(properties[0]["mapValue"].keys())[0],
        )
    else:
        # Treat devices: APs and switches
        entity = TbDevice(
            entity_name=properties[0][0],
            entity_type=properties[1],
            device_type=properties[2],
        )
        # APs, switches: parents are switches, zones and sites
        entity.add_parents({v: k for k, v in properties[0][1].items() if k != "ip"})

        # APs: attributes are ip and switch
        attributes = ["ip", "switch"]
        [
            entity.add_attribute(a, properties[0][1][a])
            for a in attributes
            if a in properties[0][1]
        ]

    return entity
