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

let InputData = ../../../output/aps.dhall
let InputRecordSchema = ../../schema-ap.dhall
let OutputRecordSchema = ./schema-aps-onboarding-output.dhall
let MapOutputRecordSchema = ./schema-aps-onboarding-map-output.dhall

let createAPsOnboarding =
    \(args: InputRecordSchema) ->
        Map.keyValue OutputRecordSchema args.name {
          zone = args.zone
        , site = args.site
        , switch = args.switch
        }

let devices =  ListMap
    InputRecordSchema
    MapOutputRecordSchema
    createAPsOnboarding
    InputData
    {-Alternative, test data instead of InputData -}
    {-[ { name = "ap1"
        , zone = "zone1"
        , site = "site1"
        , switch = "Switch1"
        }
      , { name = "ap2"
        , zone = "zone2"
        , site = "site2"
        , switch = "Switch2"
        }
    ]-}
let final = { devices }

in final