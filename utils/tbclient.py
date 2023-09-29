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
Class that cover Thingsboard connections: REST operations.
"""

import os
import sys
import logging
import requests

from .tbentity import TbDeviceType


log = logging.getLogger("thingsboard-clients")
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

gettrace = getattr(sys, "gettrace", None)


class TbRestClient:
    """A class that represents a REST client to Thingsboard."""

    api = []
    proxies = {}

    def __init__(self, api):
        self.api = api
        # Set proxy
        if "HTTPS_PROXY" in os.environ and os.environ["HTTPS_PROXY"]:
            self.proxies["http"] = os.environ["HTTPS_PROXY"]
            self.proxies["https"] = os.environ["HTTPS_PROXY"]

        self._client_token = self._tb_get_client_token()
        self._headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-Authorization": "Bearer " + self._client_token,
        }

    def _tb_get_client_token(self):
        # Auth with credentials
        # Ridiculous requirement for escaped apostrophes
        data = (
            '''{
            \"username\": \"'''
            + self.api["username"]
            + '''\",
            \"password\": \"'''
            + self.api["password"]
            + """\"
        }"""
        )

        # Retrieve the token by sending the username and password
        try:
            r = requests.post(
                url=self.api["url"] + "/auth/login",
                data=data,
                proxies=self.proxies,
                timeout=10,
            )
            r.raise_for_status()
        except requests.HTTPError as err:
            log.error("Failed to connect to Thingsboard API %s:", str(err))
            return ""

        return r.json()["token"]

    def tb_create_customer(self, customer):
        """Creates a customer over Thingsboard's REST API."""

        # Ridiculous
        data = '{"title": "' + customer.name + '"}'

        r = None
        try:
            r = requests.post(
                url=self.api["url"] + "/customer",
                headers=self._headers,
                data=data,
                proxies=self.proxies,
                timeout=10,
            )
            if r.status_code == 200:
                log.debug("Created customer %s", customer.name)
                return
            if gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.error("Failed to create customer: %s - %s", err, r)
        log.error("Failed to create customer: %s", r)

    def tb_get_customer_id(self, customer):
        r = None
        try:
            r = requests.get(
                url=self.api["url"]
                + "/tenant/customers?customerTitle="
                + customer.name,
                headers=self._headers,
                proxies=self.proxies,
                timeout=10,
            )
            if r.status_code == 200:
                log.debug(
                    "Customer ID for customer %s is %s",
                    customer.name,
                    r.json()["id"]["id"],
                )
                return r.json()["id"]["id"]
            elif gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.debug("Failed to get customer ID: %s - %s", err, r.json())

        log.error("Failed to get customer ID: %s", r.json())
        return -1

    def tb_get_entity_id(self, entity):
        r = None
        try:
            r = requests.get(
                url=self.api["url"]
                + "/tenant/"
                + entity.entity_type.name.lower()
                + "s?"
                + entity.entity_type.name.lower()
                + "Name="
                + entity.name,
                headers=self._headers,
                proxies=self.proxies,
                timeout=10,
            )
            if r.status_code == 200:
                log.debug(
                    "Entity ID for entity %s is %s", entity.name, r.json()["id"]["id"]
                )
                return r.json()["id"]["id"]
            elif gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.debug("Failed to get entity ID: %s - %s", err, r.json())

        log.error("Failed to get entity ID: %s", r.json())
        return -1

    def tb_create_asset(self, asset):
        log.info(
            "About to define asset: %s of type: %s",
            asset.name,
            asset.asset_type.name.lower(),
        )

        # Ridiculous
        data = (
            '{"name": "'
            + asset.name
            + '", "type": "'
            + asset.asset_type.name.lower()
            + '"}'
        )

        r = None
        try:
            r = requests.post(
                url=self.api["url"] + "/asset",
                headers=self._headers,
                data=data,
                proxies=self.proxies,
                timeout=10,
            )
            if r.status_code == 200:
                log.info("Created asset: %s", asset.name)
                return
            elif gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.debug("Failed to create asset: %s - %s", err, r.json())

        log.error("Failed to create asset: %s", r.json())

    def tb_create_device(self, device, gateway_credentials=()):
        log.info(
            "About to define device: %s of type: %s",
            device.name,
            device.device_type.name,
        )

        # Ridiculous
        is_gateway = False
        if device.device_type == TbDeviceType.GATEWAY:
            is_gateway = True

        url = self.api["url"] + "/device"
        data = (
            '{"name": "'
            + device.name
            + '", "type": "'
            + device.device_type.name.lower()
            + '"'
            + ', "additionalInfo":{ "gateway": '
            + str(is_gateway).lower()
            + "}"
        )
        if device.device_type == TbDeviceType.GATEWAY:
            data = (
                '{"device":'
                + data
                + '}, "credentials": { "credentialsType": "MQTT_BASIC", "credentialsId": "", "credentialsValue": "{\\"clientId\\":null,\\"userName\\":\\"'
                + gateway_credentials[0]
                + '\\",\\"password\\":\\"'
                + gateway_credentials[1]
                + '\\"}"}'
            )
            url += "-with-credentials"
        data += "}"

        r = None

        try:
            r = requests.post(
                url=url,
                headers=self._headers,
                data=data,
                proxies=self.proxies,
                timeout=10,
            )
            if r.status_code == 200:
                log.info("Created device: %s", device.name)
                return
            if gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.debug("Failed to create device: %s - %s", err, r.json())

        log.error("Failed to create device: %s", r.json())

    def tb_save_device_attributes(self, device):
        device_id = self.tb_get_entity_id(device)

        log.info("About to save attributes for device: %s - %s", device.name, device_id)

        attributes = "".join(
            ['"' + a[0] + '":' + '"' + a[1] + '",' for a in device.attributes.items()]
        )

        # Ridiculous
        data = "{" + str(attributes)
        data = data[:-1]
        data = data + "}"

        r = None

        try:
            # Save attributes under the SHARED_SCOPE (does not allow under CLIENT_SCOPE)
            r = requests.post(
                url=self.api["url"]
                + "/plugins/telemetry/"
                + device_id
                + "/SHARED_SCOPE",
                headers=self._headers,
                data=data,
                proxies=self.proxies,
                timeout=10,
            )
            if r.status_code == 200:
                log.info("Saved attributes for device: %s - %s", device.name, device_id)
                return
            elif gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.debug(
                "Failed to save attributes for device %s - %s: %s - %s",
                device.name,
                device_id,
                err,
                r,
            )

        log.error(
            'Failed to save attributes for device %s - %s": %s',
            device.name,
            device_id,
            r,
        )

    def tb_create_relation(self, entity1, entity2):
        id1 = self.tb_get_entity_id(entity1)
        id2 = self.tb_get_entity_id(entity2)

        log.info(
            "About to create relation for: "
            + "entity1: %s - id1: %s, entity2: %s - id2: %s",
            entity1.name,
            id1,
            entity2.name,
            id2,
        )

        r = None
        try:
            # Ridiculous
            data = (
                '''
            {
                "from": {
                    "id": "'''
                + id1
                + '''",
                    "entityType": "'''
                + entity1.entity_type.name
                + '''"
                },
                "to": {
                    "id": "'''
                + id2
                + '''",
                    "entityType": "'''
                + entity2.entity_type.name
                + """"
                },
                "type": "Contains"
            }
            """
            )

            r = requests.post(
                url=self.api["url"] + "/relation",
                headers=self._headers,
                data=data,
                proxies=self.proxies,
                timeout=10,
            )
            if r.status_code == 200:
                log.info(
                    "Created relation between: %s: %s and %s:%s",
                    entity1.name,
                    id1,
                    entity2.name,
                    id2,
                )
                return
            if gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.debug(
                "Failed to define relations between: %s: %s and %s:%s - %s - %s",
                entity1.name,
                id1,
                entity2.name,
                id2,
                err,
                r,
            )

        log.info(
            "Failed to define relations between: %s: %s and %s:%s - %s",
            entity1.name,
            id1,
            entity2.name,
            id2,
            r.json(),
        )

    def tb_assign_to_customer(self, entity, customer_id):

        entity_id = self.tb_get_entity_id(entity)

        log.info(
            "About to assign entity: %s - %s to customer: %s",
            entity.name,
            entity_id,
            customer_id,
        )

        # Assign customer in case there is one
        if customer_id:

            r = None
            try:
                r = requests.post(
                    url=self.api["url"]
                    + "/customer/"
                    + str(customer_id)
                    + "/"
                    + entity.entity_type.name.lower()
                    + "/"
                    + entity_id,
                    headers=self._headers,
                    proxies=self.proxies,
                    timeout=10,
                )
                if r.status_code == 200:
                    log.info(
                        "Assigned entity %s to customer: %s", entity.name, customer_id
                    )
                    return
                if gettrace():  # Dump stack trace if program is run in debug mode
                    r.raise_for_status()
            except requests.HTTPError as err:
                log.debug("Failed to assign to customer: %s - %s", err, r.json())

            log.error("Failed to assign to customer: %s", r.json())

    def tb_read_historical_values(self, device, start_ts, end_ts, request_filters=""):
        device_id = self.tb_get_entity_id(device)

        r = None
        try:
            r = requests.get(
                url=self.api["url"]
                + "/plugins/telemetry/DEVICE/"
                + device_id
                + "/values/timeseries?startTs="
                + start_ts
                + "&endTs="
                + end_ts
                + request_filters,
                headers=self._headers,
                proxies=self.proxies,
            )
            if r.status_code == 200:
                log.debug(
                    "Retrieved historical values for %s: startTs: %s, endTs: %s",
                    device_id,
                    start_ts,
                    end_ts,
                )
                return r.json()
            if gettrace():  # Dump stack trace if program is run in debug mode
                r.raise_for_status()
        except requests.HTTPError as err:
            log.debug(
                "Failed to get historical values for %s: startTs: %s, endTs: %s - %s, %s",
                device_id,
                start_ts,
                end_ts,
                err,
                r.json(),
            )

        log.error("Failed to get historical values for %s", r.json())
        return -1
