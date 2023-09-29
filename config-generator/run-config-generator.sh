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

pushd .

# Cleanup
rm ../onboard/yaml/*.yml
rm ../onboard/testbed.yml

# 1: Generate from CSV to DHALL
cd 1.dhall/schemas
bash create-dhall-files.sh
# Result is in 1.dhall/output

popd
pushd .

# 2: Generate from DHALL to YAML
cd 2.yaml
bash create-yaml-files.sh
# Result is in 2.yaml/output

# Copy resulting files to their appropriate slots
cp output/* ../../onboard/yaml/
cp output/pyats-testbed-switches.yml ../../onboard/testbed.yml

popd