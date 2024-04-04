#!/usr/bin/env python

import os
import sys
import tango

CmdArgTypeName = [
    "DevVoid",
    "DevBoolean",
    "DevShort",
    "DevLong",
    "DevFloat",
    "DevDouble",
    "DevUShort",
    "DevULong",
    "DevString",
    "DevVarCharArray",
    "DevVarShortArray",
    "DevVarLongArray",
    "DevVarFloatArray",
    "DevVarDoubleArray",
    "DevVarUShortArray",
    "DevVarULongArray",
    "DevVarStringArray",
    "DevVarLongStringArray",
    "DevVarDoubleStringArray",
    "DevState",
    "ConstDevString",
    "DevVarBooleanArray",
    "DevUChar",
    "DevLong64",
    "DevULong64",
    "DevVarLong64Array",
    "DevVarULong64Array",
    "Unknown", # Corresponds to the form DEV_INT which is no longer used
    "DevEncoded",
    "DevEnum",
    "DevPipeBlob",
    "DevVarStateArray",
    "DevVarEncodedArray",
    "Unknown",
]


def read_command_config(device_name: str, command_name: str) -> int:
    """
    Read command of Tango device.

    :param device_name: device name
    :param command_name: attribute name
    :return: error condition
    """
    dev = tango.DeviceProxy(device_name)
    dev.set_timeout_millis(500)
    try:
        cmd_cfg = dev.get_command_config(command_name)
    except tango.DevFailed as terr:
        err_msg = terr.args[0].desc.strip()
        print(f"Could not not read command {command_name} config for {device_name} : {err_msg}")
        return 1
    print(f"Tango device {device_name} : command {command_name} configuration")
    print(f"\t{'cmd_tag':40} {cmd_cfg.cmd_tag}")
    print(f"\t{'in_type':40} {CmdArgTypeName[cmd_cfg.in_type]}")
    print(f"\t{'in_type_desc':40} {cmd_cfg.in_type_desc}")
    print(f"\t{'out_type':40} {CmdArgTypeName[cmd_cfg.out_type]}")
    print(f"\t{'out_type_desc':40} {cmd_cfg.out_type_desc}")
    print(f"\t{'disp_level':40} {cmd_cfg.disp_level}")
    return 0


def read_command_value(device_name: str, command_name: str) -> int:
    """
    Read command value of Tango device.

    :param device_name: device name
    :param command_name: attribute name
    :return: error condition
    """
    dev = tango.DeviceProxy(device_name)
    dev.set_timeout_millis(500)
    try:
        cmd_reply = dev.command_inout(command_name)
    except tango.DevFailed as terr:
        err_msg = terr.args[0].desc.strip()
        print(f"Could not not read command value {command_name} : {err_msg}")
        return 1
    print(f"Tango device {device_name} : command {command_name} value")
    print(f"\t{'type':40} {type(cmd_reply)}")
    print(f"\t{'value':40} {cmd_reply}")
    return 0


def main() -> int:
    device_name: str = sys.argv[1]
    command_name: str = sys.argv[2]
    rc: int = read_command_config(device_name, command_name)
    if len(sys.argv) == 4:
        rc += read_command_value(device_name, command_name)


if __name__ == "__main__":
    sys.exit(main())
