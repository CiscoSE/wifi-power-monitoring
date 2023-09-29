--  Copyright (c) 2023 Cisco and/or its affiliates.

--  This software is licensed to you under the terms of the Cisco Sample
--  Code License, Version 1.1 (the "License"). You may obtain a copy of the
--  License at

--                 https://developer.cisco.com/docs/licenses

--  All use of the material herein must be in accordance with the terms of
--  the License. All rights not expressly granted by the License are
--  reserved. Unless required by applicable law or agreed to separately in
--  writing, software distributed under the License is distributed on an "AS
--  IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
--  or implied.

let ListMap = https://prelude.dhall-lang.org/List/map
let Map = http://prelude.dhall-lang.org/v16.0.0/Map/package.dhall

let InputData = ../../../output/switches.dhall
let InputRecordSchema = ../../schema-switch.dhall
let OutputRecordSchema = ./schema-switches-pyats-testbed-output.dhall
let MapOutputRecordSchema = ./schema-switches-pyats-testbed-map-output.dhall

let fcSSH =
    \(args : { ip : Text, sshargs : Text }) ->
       "ssh -v ${args.ip} ${args.sshargs}"

let createSwitchesTestBed =
    \(args: InputRecordSchema) ->
        Map.keyValue OutputRecordSchema args.name {
         type = "iosxe"
        , os = "iosxe"
        , platform = args.platform
        , credentials.default.username = args.username
        , credentials.default.password = args.password
        , connections.cli.ip = args.ip
        , connections.cli.command = fcSSH { ip = args.ip, sshargs = args.ssharguments }
        }

let testbed = {name = "lab_devices"}

let devices =  ListMap
    InputRecordSchema
    MapOutputRecordSchema
    createSwitchesTestBed
    InputData

in {testbed, devices}