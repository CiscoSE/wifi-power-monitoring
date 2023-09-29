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
Supports cdp information processing.
"""

from .ap import AP
from .logger import log


def get_cdp_neighbors(data):
    """
    Extracts CDP neighbors from a dictionary, as outputted by
    PyATS's processing of the 'show cdp neighbors' IOS-XE CLI command.

    Returns: cdp_neighbors.
    """

    cdp_neighbors = []

    for neighbor in data["cdp"]["index"].items():
        if "AX" in neighbor[1]["platform"] or "AIR-" in neighbor[1]["platform"]:
            ap = AP(neighbor[1]["device_id"])

            # Optionally, enable AP name validation
            # if ap.is_valid():
            #    ap_name = ap.full_name()
            if True:
                # Replace this with validated name above
                ap_name = ap.id

                cdp_neighbors.append((ap_name, neighbor[1]["local_interface"]))
                log.debug(
                    "AP %s: %s - %s",
                    neighbor[0],
                    ap_name,
                    neighbor[1]["local_interface"],
                )

    return cdp_neighbors
