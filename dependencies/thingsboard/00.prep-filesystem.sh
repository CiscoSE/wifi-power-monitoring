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

# AS ROOT / user part of sudo group
if [ -z "$TARGET_USER" ]
  # Replace cisco by user that will run the application:
  then
    USER=cisco
    echo "Will create folder under home directory of default user $USER..."
  else
    echo "Will create folder under home directory of user $TARGET_USER..."
    USER=$TARGET_USER
fi

# ROOT: Change ownership to
# thingsboard-equivalent user and group IDs
# ROOT: Allow user $USER that runs the docker
# process to write in this folder

mkdir -p /home/$USER/thingsboard-db &&\
cd /home/$USER/thingsboard-db &&\
mkdir tb-data tb-logs &&\
chown -R 799:799 tb-data tb-logs &&\
chmod 777 tb-data tb-logs