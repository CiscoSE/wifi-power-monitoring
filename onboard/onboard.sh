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

echo "~ Onboard entities..."
python3 /onboard/onboard_entities.py

if [[ "$IS_OFFLINE" != True && "$IS_OFFLINE" != true && "$IS_OFFLINE" != TRUE ]];
    then
        echo "~ This is not offline onboarding! Trying to connect to real switches... ~";
        python3 /onboard/onboard_switches_online.py;
    else
        echo "~ This is offline onboarding! Will not try to connect to real switches. ~";
fi
