#!/usr/bin/env python

import os
import sys
import tango


def read_commands(device_name: str) -> int:
    """
    Read commands of Tango device.

    :param device_name: device name
    :return: error condition
    """
    dev = tango.DeviceProxy(device_name)
    dev.set_timeout_millis(500)
    # Read attributes
    try:
        cmds = sorted(dev.get_command_list())
    except tango.DevFailed as terr:
        err_msg = terr.args[0].desc.strip()
        print(f"Could not read commands : {err_msg}")
        return 1
    print(f"Tango device {device_name} commands : {len(cmds)}")
    for cmd in cmds:
        print(f"\t{cmd}")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <DEVICE_NAME>")
        return 1
    device_name: str = sys.argv[1]
    return read_commands(device_name)


if __name__ == "__main__":
    sys.exit(main())
