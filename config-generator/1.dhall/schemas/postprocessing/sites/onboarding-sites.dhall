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

let InputData = ../../../output/sites.dhall
let InputRecordSchema = ../../schema-site.dhall
let OutputRecordSchema = ./schema-sites-onboarding-output.dhall
let MapOutputRecordSchema = ./schema-sites-onboarding-map-output.dhall

let createSitesOnboarding =
    \(args: InputRecordSchema) ->
        Map.keyValue OutputRecordSchema args.name {
        zone = args.zone
        }

let sites = ListMap
    InputRecordSchema
    MapOutputRecordSchema
    createSitesOnboarding
    InputData
    {-Alternative, test data instead of InputData -}
    {-[ { name = "site1"
        , zone = "ZoneA"
        }
      , { name = "site2"
        , zone = "ZoneB"
        }
    ]-}

let final = { sites }

in final