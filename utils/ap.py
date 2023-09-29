"""
Copyright (c) 2023 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import re


class AP:
    def __init__(self, id):
        self.id = id
        self.groups = self._parser()

    def is_valid(self):
        return self.groups != []

    def _parser(self):
        # TODO(): Generalize this regex to support more AP naming conventions
        # Placeholder to add custom regex rule for parsing name of AP
        regex = r"([A-Z]{3}-[A-Z]{3}-[A-Z]{3}-[A-Z]{3}-[A-Z]{3}-[A-Z]{3})"
        return re.findall(regex, self.id)

    def full_name(self):
        return self.groups[0][0]

    def id(self):
        return self.groups[0][5]
