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
Supports reading information from local disk.
"""

import json

from .logger import log
from .cdp import get_cdp_neighbors


def read_cdp_neigbors(source):
    """
    Reads CDP neighbors of a switch from a file saved on disk (cdp_file).
    Expects: source = (switch, cdp file)

    Returns: (switch, cdp_neighbors).
    """

    switch = source[0]
    cdp_file = source[1]

    # Get all CDP neighbors
    with open(cdp_file, encoding="utf-8") as fp:
        data = json.load(fp)
        cdp_neighbors = get_cdp_neighbors(data)
        log.debug("Switch %s has %i CDP entries", switch, len(cdp_neighbors))
        return (switch, cdp_neighbors)
