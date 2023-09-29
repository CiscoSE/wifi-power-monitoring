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

# Assumes the Excel file has been exported to one of the following 2 special CSV formats: Comma-delimited CSV or Macintosh Comma-delimited CSV

# Load aliases in case they are needed, e.g., for RHEL
shopt -s expand_aliases
source ~/.bash_aliases

# Cleanup before starting
rm ../output/*

# Create sites
export schema=$(cat ./schema-sites-input.dhall)
echo "Sites" : $schema

Command_dhall="/usr/local/bin/dhall"
Command_csv_dhall="/usr/local/bin/csv-to-dhall"
if [ -f "$Command" ]; then
    echo "Using DHALL executable at $Command"
else
    Command="dhall"
    echo "Assuming alias was created for $Command"
fi
if [ -f "$Command_csv_dhall" ]; then
    echo "Using DHALL executable at $Command_csv_dhall"
else
    Command_csv_dhall="csv-to-dhall"
    echo "Assuming alias was created for $Command_csv_dhall"
fi

eval $Command_csv_dhall \"$schema\" --file ../../0.csv/csvs/sites.csv --output ../output/sites.dhall
eval $Command --file postprocessing/sites/onboarding-sites.dhall --output ../output/sites-postprocessing.dhall

# Create zones
export schema=$(cat ./schema-zones-input.dhall)
echo "Zones" : $schema

eval $Command_csv_dhall \"$schema\" --file ../../0.csv/csvs/zones.csv --output ../output/zones.dhall
eval $Command --file postprocessing/zones/onboarding-zones.dhall --output ../output/zones-postprocessing.dhall

# Create switches
export schema=$(cat ./schema-switches-input.dhall)
echo "Switches" : $schema

eval $Command_csv_dhall \"$schema\" --file ../../0.csv/csvs/switches.csv --output ../output/switches.dhall
eval $Command --file postprocessing/switches/onboarding-switches.dhall --output ../output/switches-postprocessing.dhall
eval $Command --file postprocessing/switches/pyats-testbed-switches.dhall --output ../output/pyats-testbed-switches.dhall

# Create access points
export schema=$(cat ./schema-aps-input.dhall)
echo "Access points" : $schema

eval $Command_csv_dhall \"$schema\" --file ../../0.csv/csvs/aps.csv --output ../output/aps.dhall
eval $Command --file postprocessing/aps/onboarding-aps.dhall --output ../output/aps-postprocessing.dhall
