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

let InputData = ../../../output/zones.dhall
let InputRecordSchema = ../../schema-zone.dhall
let OutputRecordSchema = ./schema-zones-onboarding-output.dhall
let MapOutputRecordSchema = ./schema-zones-onboarding-map-output.dhall

let createZonesOnboarding =
    \(args: InputRecordSchema) ->
        Map.keyValue OutputRecordSchema args.name {
        , site = args.site
        }

let zones =  ListMap
    InputRecordSchema
    MapOutputRecordSchema
    createZonesOnboarding
    InputData
    {-Alternative, test data instead of InputData -}
    {-[ { name = "zone1"
        , site = "site1"
        }
      , { name = "zone2"
        , site = "site2"
        }
    ]-}
let final = { zones }

in final