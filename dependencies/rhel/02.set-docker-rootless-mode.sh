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

# ROOT: Disable system-wide Docker daemon
sudo systemctl disable --now docker.service docker.socket

# ROOT:
sudo sh -eux <<EOF
# Load ip_tables module
modprobe ip_tables
EOF

# NON-ROOT: Set up daemon as non-root user
/usr/bin/dockerd-rootless-setuptool.sh install # --skip-iptables

# Without iptables rules config
#/usr/bin/dockerd-rootless-setuptool.sh install --skip-iptables

# NON-ROOT: Export required env vars
echo "export PATH=/usr/bin:$PATH" >> ~/.bashrc
echo "export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock" >> ~/.bashrc
. ~/.bashrc

# Usage - see https://docs.docker.com/engine/security/rootless/
systemctl --user start docker
systemctl --user enable docker

# ROOT: for key user, where whoami can be replaced by user, e.g., cisco:
sudo loginctl enable-linger $(whoami)

# Client
#docker context use rootless # Specify the CLI context
#docker run -d -p 8080:80 nginx