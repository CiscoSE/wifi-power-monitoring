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

if [ -z "$HTTPS_PROXY" ] ;\
  then echo "No proxy";\
  else sudo echo "proxy=$HTTPS_PROXY" >> /etc/yum.conf;\
fi

# Cleanup - remove conflicting container tools
sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine \
                  podman \
                  runc

sudo yum install -y yum-utils

# Add Centos instead
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Checks
ls /etc/yum.repos.d
yum repolist all | grep docker

# Download packages
mkdir ~/yum-packages
sudo yum install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin --downloadonly --downloaddir ~/yum-packages/