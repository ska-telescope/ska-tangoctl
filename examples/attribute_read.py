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


def read_attribute(device_name: str, attribute_name: str) -> int:
    """
    Read attributes of Tango device.

    :param device_name: device name
    :param attribute_name: attribute name
    :return: error condition
    """
    dev = tango.DeviceProxy(device_name)
    dev.set_timeout_millis(500)
    try:
        attrib_cfg = dev.get_attribute_config(attribute_name)
    except tango.DevFailed as terr:
        err_msg = terr.args[0].desc.strip()
        print(f"Could not not read attribute config {attribute_name} : {err_msg}")
        return 1
    print(f"Tango device {device_name} : attribute {attribute_name}")
    print(f"\t{'data_format':40} {attrib_cfg.data_format}")
    print(f"\t{'format':40} {attrib_cfg.format}")
    print(f"\t{'disp_level':40} {attrib_cfg.disp_level}")
    print(f"\t{'data_type':40} {str(attrib_cfg.data_type)}")
    print(f"\t{'data_type':40} {CmdArgTypeName[attrib_cfg.data_type]}")
    print(f"\t{'data_type':40} {str(attrib_cfg.data_type)}")
    print(f"\t{'display_unit':40} {attrib_cfg.display_unit}")
    print(f"\t{'standard_unit':40} {attrib_cfg.standard_unit}")
    print(f"\t{'writable':40} {attrib_cfg.writable}")
    print(f"\t{'writable_attr_name':40} {attrib_cfg.writable_attr_name}")
    return 0


def main() -> int:
    device_name: str = sys.argv[1]
    attribute_name: str = sys.argv[2]
    return read_attribute(device_name, attribute_name)


if __name__ == "__main__":
    sys.exit(main())
