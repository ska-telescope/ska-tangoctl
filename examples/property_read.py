#!/usr/bin/env python

import os
import sys
import tango


def read_property(device_name: str, property_name: str) -> int:
    """
    Read property of Tango device.

    :param device_name: device name
    :param property_name: property name
    :return: error condition
    """
    dev = tango.DeviceProxy(device_name)
    dev.set_timeout_millis(500)
    try:
        prop_vals = dev.get_property(property_name)[property_name]
    except tango.DevFailed as terr:
        err_msg = terr.args[0].desc.strip()
        print(f"Could not not read property {property_name} : {err_msg}")
        return 1
    print(f"Tango device {device_name} : property {property_name}")
    if type(prop_vals) is tango._tango.StdStringVector:
        for prop_val in prop_vals:
            print(f"\t{prop_val}")
    else:
        print(f"\t{prop_vals} (type {type(prop_vals)})")
    return 0


def main() -> int:
    device_name: str = sys.argv[1]
    property_name: str = sys.argv[2]
    return read_property(device_name, property_name)


if __name__ == "__main__":
    sys.exit(main())
