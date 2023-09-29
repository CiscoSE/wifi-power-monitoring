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

# Run:
# online mode:   bash dependencies/install-deps-config-generator.sh online
# offline mode:  bash dependencies/install-deps-config-generator.sh

LOCATION_PKGS=~/dhall-packages
LOCATION_BASH_RC=~/.bashrc
LOCATION_BASH_ALIASES=~/.bash_aliases

mkdir $LOCATION_PKGS

if [ $# -ne 0 ]; then
  echo "Online mode ... downloading DHALL packages to $LOCATION_PKGS"

  wget https://github.com/dhall-lang/dhall-haskell/releases/download/1.41.1/dhall-1.41.1-x86_64-linux.tar.bz2 -O $LOCATION_PKGS/dhall-1.41.1-x86_64-linux.tar.bz2
  wget https://github.com/dhall-lang/dhall-haskell/releases/download/1.41.1/dhall-csv-1.0.2-x86_64-linux.tar.bz2 -O $LOCATION_PKGS/dhall-csv-1.0.2-x86_64-linux.tar.bz2
  wget https://github.com/dhall-lang/dhall-haskell/releases/download/1.41.1/dhall-yaml-1.2.10-x86_64-linux.tar.bz2 -O $LOCATION_PKGS/dhall-yaml-1.2.10-x86_64-linux.tar.bz2
else
  echo "Offline mode ... expecting DHALL packages in $LOCATION_PKGS"
fi


# Extract packages
tar --extract --bzip2 --file $LOCATION_PKGS/dhall-1.41.1-x86_64-linux.tar.bz2
tar --extract --bzip2 --file $LOCATION_PKGS/dhall-csv-1.0.2-x86_64-linux.tar.bz2
tar --extract --bzip2 --file $LOCATION_PKGS/dhall-yaml-1.2.10-x86_64-linux.tar.bz2

# Create aliases
echo "alias dhall=${PWD}/bin/dhall" | tee -a $LOCATION_BASH_RC $LOCATION_BASH_ALIASES
echo "alias dhall-to-csv=${PWD}/bin/dhall-to-csv" | tee -a $LOCATION_BASH_RC $LOCATION_BASH_ALIASES
echo "alias dhall-to-yaml-ng=${PWD}/bin/dhall-to-yaml-ng" | tee -a $LOCATION_BASH_RC $LOCATION_BASH_ALIASES
echo "alias csv-to-dhall=${PWD}/bin/csv-to-dhall" | tee -a $LOCATION_BASH_RC $LOCATION_BASH_ALIASES
echo "alias yaml-to-dhall=${PWD}/bin/yaml-to-dhall" | tee -a $LOCATION_BASH_RC $LOCATION_BASH_ALIASES

# Load aliases
. $LOCATION_BASH_RC
shopt -s expand_aliases
source $LOCATION_BASH_ALIASES

# Optional for ROOT USER
#sudo cp -r bin/* /usr/local/bin/
