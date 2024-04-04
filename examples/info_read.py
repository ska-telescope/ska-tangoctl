#!/usr/bin/env python

import os
import sys
import tango


def read_info(device_name: str) -> int:
    """
    Read properties of Tango device.

    :param device_name: device name
    :return: error condition
    """
    dev = tango.DeviceProxy(device_name)
    dev.set_timeout_millis(500)
    # Read info
    try:
        info = dev.info()
    except tango.DevFailed as terr:
        err_msg = terr.args[0].desc.strip()
        print(f"Could not read info: {err_msg}")
    print(f"Tango device {device_name} information :")
    print(f"\t{'dev_class':40} {info.dev_class}")
    print(f"\t{'dev_type':40} {info.dev_type}")
    print(f"\t{'doc_url':40} {info.doc_url}")
    print(f"\t{'server_host':40} {info.server_host}")
    print(f"\t{'server_id':40} {info.server_id}")
    print(f"\t{'server_version':40} {info.server_version}")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <DEVICE_NAME>")
        return 1
    device_name: str = sys.argv[1]
    return read_info(device_name)


if __name__ == "__main__":
    sys.exit(main())
