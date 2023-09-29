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

# Load aliases in case they are needed, e.g., for RHEL
shopt -s expand_aliases
source ~/.bash_aliases

# Cleanup before starting
rm output/*

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux GNU
    Command="/usr/local/bin/dhall-to-yaml-ng"
    if [ -f "$Command" ]; then
        echo "Using DHALL executable at $Command"
    else
        Command="dhall-to-yaml-ng"
        echo "Assuming alias was created for $Command"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OSX
    Command="/usr/local/bin/dhall-to-yaml"
else
    echo "Unsupported operating system for conversion of dhall to yaml. Exiting..."
    exit 1 
fi

# Create sites
# Special case: keep keys as separate instances in the association lists - TODO: merge these before map creation
eval $Command --generated-comment --file ../1.dhall/output/sites-postprocessing.dhall --no-maps --output ./output/sites.yml

# Create zones: keep keys as separate instances in the association lists - TODO: merge these before map creation
eval $Command --generated-comment --file ../1.dhall/output/zones-postprocessing.dhall --no-maps --output ./output/zones.yml

# Create switches
eval $Command --generated-comment --file ../1.dhall/output/switches-postprocessing.dhall --output ./output/switches.yml
eval $Command --generated-comment --file ../1.dhall/output/pyats-testbed-switches.dhall --output ./output/pyats-testbed-switches.yml

# Create access points
eval $Command --generated-comment --file ../1.dhall/output/aps-postprocessing.dhall --output ./output/aps.yml

exit 0
