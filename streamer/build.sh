#!/bin/bash
# Copyright (c) 2023 Cisco and/or its affiliates.
#
# This software is licensed to you under the terms of the Cisco Sample
# Code License, Version 1.1 (the "License"). You may obtain a copy of the
# License at
#
#                https://developer.cisco.com/docs/licenses
#
# All use of the material herein must be in accordance with the terms of
# the License. All rights not expressly granted by the License are
# reserved. Unless required by applicable law or agreed to separately in
# writing, software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.

set -exo pipefail

if [ -z "$HTTPS_PROXY" ]; then
    python -m pip install --no-cache-dir --upgrade pip
else
    python -m pip install --no-cache-dir --proxy $HTTPS_PROXY --upgrade pip 
fi

# Install pyats-based streamer requirements
if [ -z "$HTTPS_PROXY" ]; then
    python -m pip install --no-cache-dir -r /pyats-power/requirements.txt
else 
    python -m pip install --no-cache-dir --proxy $HTTPS_PROXY -r /pyats-power/requirements.txt
fi
