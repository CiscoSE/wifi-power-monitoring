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
let OutputRecordSchema = ./schema-switches-onboarding-output.dhall
let MapOutputRecordSchema = ./schema-switches-onboarding-map-output.dhall

let createSwitchesOnboarding =
    \(args: InputRecordSchema) ->
        Map.keyValue OutputRecordSchema args.name {
          zone = args.zone
        , site = args.site
        }

let devices =  ListMap
    InputRecordSchema
    MapOutputRecordSchema
    createSwitchesOnboarding
    InputData
    {-Alternative, test data instead of InputData -}
    {-[ { name = "switch1"
        , zone = "zone1"
        , site = "site1"
        , platform = "iosxe"
        , type = "iosxe"
        , ip = "10.55.66.77"
        , username = "test"
        , password = " dfgfgf"
        , ssharguments = "-fkffkfk=5858"
        }
      , { name = "switch2"
        , zone = "zone2"
        , site = "site2"
        , platform = "iosxe"
        , type = "iosxe"
        , ip = "10.55.66.78"
        , username = "test"
        , password = " dsdsds"
        , ssharguments = "-ffffff"
        }
    ]-}
let final = { devices }

in final