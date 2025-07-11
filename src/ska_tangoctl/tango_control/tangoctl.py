#!/usr/bin/env python
"""Read all information about Tango devices."""

import logging
import os
import sys

from ska_tangoctl import __version__
from ska_tangoctl.tango_control.tango_control import TangoControl
from ska_tangoctl.tango_control.tango_device_tree import device_tree
from ska_tangoctl.tango_control.test_tango_device import TestTangoDevice
from ska_tangoctl.tla_jargon.tla_jargon import print_jargon

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.WARNING)


def main() -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :return: error condition
    """
    tangoctl = TangoControl(_module_logger)

    # Read command line options
    rc: int = tangoctl.read_command_line(sys.argv)
    if rc == 0:
        pass
    elif rc == 1:
        tangoctl.usage1(os.path.basename(sys.argv[0]))
        return 1
    elif rc == 2:
        tangoctl.usage2(os.path.basename(sys.argv[0]))
        return 1
    else:
        _module_logger.error("Read command line returned %d", rc)
        return 1

    # Read configuration
    tangoctl.read_config()

    if tangoctl.disp_action.show_tree:
        device_tree(tangoctl.tgo_name)
        return 0

    if tangoctl.disp_action.show_version:
        print(f"{os.path.basename(sys.argv[0])} version {__version__}")
        return 0

    if tangoctl.disp_action.show_jargon:
        print_jargon()
        return 0

    if tangoctl.json_dir:
        tangoctl.read_input_files(tangoctl.json_dir)
        return 0

    if tangoctl.logging_level and tangoctl.tgo_name:
        return tangoctl.set_logging_level()

    if tangoctl.disp_action.show_tango:
        tangoctl.check_tango()
        return 0

    if tangoctl.input_file is not None:
        tangoctl.read_input_file()
        return 0

    dev_test = False
    if (
        tangoctl.dev_off
        or tangoctl.dev_on
        or tangoctl.dev_ping
        or tangoctl.dev_sim
        or tangoctl.dev_standby
    ):
        dev_test = True
    if tangoctl.dev_admin is not None:
        dev_test = True
    if dev_test and tangoctl.tgo_name:
        dut = TestTangoDevice(_module_logger, tangoctl.tgo_name)
        if dut.dev is None:
            print(f"[FAILED] could not open device {tangoctl.tgo_name}")
            return 1
        rc = dut.run_test(
            tangoctl.dev_admin,
            tangoctl.dev_off,
            tangoctl.dev_on,
            tangoctl.dev_ping,
            tangoctl.dev_sim,
            tangoctl.dev_standby,
            tangoctl.dev_status,
            tangoctl.disp_action.show_attrib,
            tangoctl.disp_action.show_cmd,
            tangoctl.disp_action.show_prop,
            tangoctl.tgo_attrib,
            tangoctl.tgo_name,
        )
        return rc

    if tangoctl.tgo_name and tangoctl.tgo_attrib and tangoctl.tgo_value:
        rc = tangoctl.set_value()
        return rc

    rc = tangoctl.run_info()
    return rc


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
