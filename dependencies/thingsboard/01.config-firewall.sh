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

# ROOT:
firewall-cmd --list-all

# ROOT: Open port for UI of Thingsboard
firewall-cmd --add-port=8080/tcp
# ROOT: Open port for webserver with custom widget resources
firewall-cmd --add-port=8999/tcp

# ROOT: Optionally, if streaming services run on a separate
# instance, open port for MQTT broker of Thingsboard
firewall-cmd --add-port=1883/tcp
