#!/usr/bin/env python
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
"""
Exports APs data to a CSV file.

The file exports energy consumption per hour and day for 2 weeks, for each AP.

Assumes:
 - access to Thingsboard through its REST API (file onboard/thingsboard.yml)
"""

import os
import sys
import json
import yaml
import time
import logging
import argparse
import datetime
import pandas as pd
import multiprocessing
from collections import defaultdict

from utils import tbyaml
from utils.tbclient import TbRestClient
from utils.tbentity import TbEntityType, TbDeviceType

log = logging.getLogger("exporter")
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def read(client, aps):
    energy = defaultdict(list)

    key = "PoE"

    # TODO(): Allow user input for start / mid / end
    #  Get 2 chunks of data with average per h
    #  2 weeks: Wed Apr 05 2023 14:00:00 GMT+0000 (1680703200000)
    #          to Wed Apr 19 2023 14:00:00 GMT+0000 (1681912800000)

    start_ts = 1680703200000
    mid_ts = 1681308000000
    end_ts = 1681912800000

    factor = 3600000
    nr_h = (end_ts - start_ts) / factor
    h = 1

    time_tag = (
        str(datetime.datetime.fromtimestamp(start_ts / 1000))
        + "-"
        + str(datetime.datetime.fromtimestamp(end_ts / 1000))
    )
    output_file = "-data-hourly-" + time_tag
    output_file_json = key + output_file + ".json"
    output_file_excel = "energy-data-daily-" + time_tag + ".xlsx"
    output_file_excel_hourly = "energy" + output_file + ".xlsx"
    sheet = "APs-day-to-day"
    sheet_hourly = "APs-hour-by-hour"

    with open("data/" + output_file_json, "w+") as fj:
        with pd.ExcelWriter("data/" + output_file_excel, engine="xlsxwriter") as wfx:
            with pd.ExcelWriter(
                "data/" + output_file_excel_hourly, engine="xlsxwriter"
            ) as wfx_hourly:
                fj.write("[")
                l = len(aps)

                request_filters = "&interval=3600000&limit=10000&agg=AVG&keys=" + key

                # TODO: read device IDs for all APs
                for i, ap in enumerate(aps):
                    log.info("{} - AP:{}".format(i, ap.name))

                    try:
                        data = (
                            client.tb_read_historical_values(
                                ap, str(start_ts), str(mid_ts), request_filters
                            )[key]
                            + client.tb_read_historical_values(
                                ap, str(mid_ts), str(end_ts), request_filters
                            )[key]
                        )
                    except Exception as e:
                        log.warning(
                            "Failed reading value: {} - will try to read hour-by-hour...".format(
                                e
                            )
                        )
                        h = 1
                        hist = []
                        current_start_ts = start_ts
                        while h <= nr_h:
                            current_end_ts = current_start_ts + factor
                            try:
                                hist += client.tb_read_historical_values(
                                    ap,
                                    str(current_start_ts),
                                    str(current_end_ts),
                                    request_filters,
                                )[key]
                            except Exception as e:
                                log.warning(
                                    "Failed to read value for interval {} - {} : {}".format(
                                        current_start_ts, current_end_ts, e
                                    )
                                )
                            h += 1
                            current_start_ts = current_end_ts
                        data = hist
                        # time.sleep(30) # Sleep after making many requests to Tb - see rate limit

                    try:
                        if not data:
                            raise Exception("No data for this device.")
                        log.info(
                            "{} - Sample read for {}: {}".format(i, ap.name, (data)[0])
                        )

                        # Export raw data to JSON file
                        json.dump({ap.name: data}, fj)

                        # Simplify timestamps to hourly timestamps
                        data_daily = [
                            {
                                "Date": pd.Timestamp(
                                    datetime.datetime.fromtimestamp(
                                        e["ts"] / 1000
                                    ).replace(hour=0, minute=0, second=0, microsecond=0)
                                ).to_period(freq="d"),
                                # Convert value field from string to float
                                "Energy [Wh]": float(e["value"]),  # Assume Wh
                            }
                            for e in data
                        ]
                        data_hourly = [
                            {
                                "Date": pd.Timestamp(
                                    datetime.datetime.fromtimestamp(
                                        e["ts"] / 1000
                                    ).replace(minute=0, second=0, microsecond=0)
                                ).to_period(freq="h"),
                                # Convert value field from string to float
                                "Energy [Wh]": float(e["value"]),  # Assume Wh
                            }
                            for e in data
                        ]

                        # Hourly sample information
                        pd_data_hourly = pd.DataFrame.from_records(
                            data_hourly, index="Date"
                        )
                        pd_data_hourly = (
                            pd_data_hourly.groupby("Date").sum().sort_values(["Date"]).T
                        )
                        log.info("{} - Sample hourly energy for {}:".format(i, ap.name))
                        log.info((pd_data_hourly[0:2]))

                        # Aggregate information: sum hourly energy consumption, grouped by day
                        pd_data = pd.DataFrame.from_records(data_daily, index="Date")
                        pd_data = pd_data.groupby("Date").sum().sort_values(["Date"]).T

                        log.info("{} - Sample daily energy for {}:".format(i, ap.name))
                        log.info((pd_data[0:2]))

                        # Augment dataframe: append AP name
                        pd_data_o = {"AP": ap.name}
                        pd_data_o.update(pd_data)
                        pd_data_o = pd.DataFrame(pd_data_o)
                        pd_data_hourly_o = {"AP": ap.name}
                        pd_data_hourly_o.update(pd_data_hourly)
                        pd_data_hourly_o = pd.DataFrame(pd_data_hourly_o)

                        # Export to XLSX the daily energy consumption for each AP: [AP, day1, day2, ...]
                        if i == 0:
                            pd_data_o.to_excel(wfx, sheet_name=sheet)
                            pd_data_hourly_o.to_excel(
                                wfx_hourly, sheet_name=sheet_hourly
                            )
                        else:
                            pd_data_o.to_excel(
                                wfx, sheet_name=sheet, header=False, startrow=i + 1
                            )
                            pd_data_hourly_o.to_excel(
                                wfx_hourly,
                                sheet_name=sheet_hourly,
                                header=True,
                                startrow=2 * i,
                            )
                    except Exception as e:
                        log.warning("Error exporting data: {}".format(e))

                fj.write("]")
    return []


def export(data, file):
    # TODO(): Export data to XLSX
    return


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--tb_file",
        type=str,
        required=False,
        default="/onboard/thingsboard.yml",
        help="Credentials file for authentication to Thingsboard",
    )
    parser.add_argument(
        "-a",
        "--aps_file",
        type=str,
        required=False,
        default="/onboard/yaml/aps.yml",
        help="XLSX file for saving the data",
    )
    parser.add_argument(
        "-x",
        "--xlsx",
        type=str,
        required=False,
        help="XLSX file for saving the data",
    )
    args = parser.parse_args(argv)

    if not args.tb_file:
        log.info(
            "Using default Thingsboard credentials in: " + "/onboard/thingsboard.yml"
        )
    if not args.aps_file:
        log.info("Using default APs file in: " + "/onboard/yaml/aps.yml")
    return args.tb_file, args.aps_file, args.xlsx


if __name__ == "__main__":
    tb_file, aps_file, xlsx_file = main(sys.argv[1:])
    thingsboard_file = yaml.load(open(tb_file), Loader=yaml.Loader)
    api = thingsboard_file["api"]

    rest_client = TbRestClient(api)

    aps = yaml.load(open(aps_file), Loader=yaml.Loader)["devices"]

    # Get lists of devices of type TbEntity
    with multiprocessing.Pool(processes=4) as p:
        devices_aps = p.map(
            tbyaml.create_entity,
            [(a, TbEntityType.DEVICE, TbDeviceType.AP) for a in aps.items()],
        )

    os.makedirs("data", exist_ok=True)
    data = read(rest_client, devices_aps)
    export(data, xlsx_file)

    log.info("FINISHED.")
