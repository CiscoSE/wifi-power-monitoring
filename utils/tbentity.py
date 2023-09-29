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
Generic class that covers entities and assets.
Enumerations for asset and entity types.
"""

from enum import Enum


class TbAssetType(Enum):
    SITE = 0
    ZONE = 1


class TbDeviceType(Enum):
    AP = 10
    SWITCH = 11
    DEFAULT = 12
    GATEWAY = 13


class TbEntityType(Enum):
    ASSET = TbAssetType
    DEVICE = TbDeviceType
    CUSTOMER = 1000


class TbEntity:
    """A class that represents a generic entity (asset, device, etc)"""

    asset_type = None

    def __init__(self, entity_name, entity_type):
        self.name = entity_name
        self.entity_type = entity_type
        self.children = {}  # self -> child
        self.parents = {}  # self <- parent
        self.attributes = {}

    def add_child(self, key, value):
        # Assume only 1 key for child (e.g. zone1)
        # sites: -> mapKey: site1 mapValue -> zone: zone1
        self.children[key] = value

    def add_parent(self, key, value):
        self.parents[key] = value

    def add_parents(self, parents):
        # aps: <- zones, sites, switches
        # switches: <- zones, sites
        for v, k in parents.items():
            self.add_parent(k, v)

    def add_attribute(self, key, value):
        # aps: ips
        self.attributes[key] = value


class TbAsset(TbEntity):
    def __init__(self, entity_name, entity_type, asset_type=None):
        super().__init__(entity_name, entity_type)
        self.asset_type = asset_type


class TbDevice(TbEntity):
    def __init__(self, entity_name, entity_type, device_type=None):
        super().__init__(entity_name, entity_type)
        self.device_type = device_type
