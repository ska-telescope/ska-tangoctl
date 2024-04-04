#!/usr/bin/env python

import os
import sys
import tango


def read_devices() -> int:
    # Get Tango database host
    tango_host = os.getenv("TANGO_HOST")
    # Connect to database
    try:
        database = tango.Database()
    except Exception as oerr:
        print(f"Could not connect to Tango database {tango_host} : {oerr}")
        return 1

    # Read devices
    device_list = sorted(database.get_device_exported("*").value_string)
    print(f"Exported Tango devices : {len(device_list)}")

    for device in device_list:
        print(f"\t{device}")

    return 0


def main() -> int:
    return read_devices()


if __name__ == "__main__":
    sys.exit(main())
