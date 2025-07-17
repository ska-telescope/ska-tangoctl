"""
Test tangoctl options.

# type: ignore[import-untyped]
"""

import logging
import sys
from typing import Any

import pytest

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevices

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("test_tango_control")
_module_logger.setLevel(logging.WARNING)


def test_configuration_data(configuration_data: dict) -> None:
    """
    Check configuration data file.

    :param configuration_data: tangoctl setup
    """
    assert len(configuration_data) > 0


def test_tango_host(tgo_host: str, tango_control_handle: Any) -> None:
    """
    Test that Tango database is up and running.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    _module_logger.info("Use Tango host %s", tgo_host)

    tango_control_handle.reset()
    tango_control_handle.setup(tango_host=tgo_host)
    rv = tango_control_handle.check_tango()
    assert rv == 0


@pytest.mark.skip()
def test_read_input_files(tgo_host: str, tango_control_handle: Any) -> None:
    """
    Check input files.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    ipath = "resources"
    _module_logger.info("Read input files in %s", ipath)
    rv = tango_control_handle.read_input_files(ipath, True)
    assert rv == 0


def test_device_read(tgo_host: str, configuration_data: dict, device_name: str) -> None:
    """
    Read devices.

    :param tgo_host: hostname and port number
    :param configuration_data: read from JSON file
    :param device_name: Tango device
    """
    devices: TangoctlDevices = TangoctlDevices(
        _module_logger,
        tgo_host,
        sys.stdout,
        1000,
        {},
        configuration_data,
        device_name,
        False,
        DispAction(DispAction.TANGOCTL_JSON),
        None,
        None,
        None,
        None,
    )
    devices.read_device_values()
    devdict = devices.make_devices_json_medium()
    assert len(devdict) > 0


def test_show_dev(tgo_host: str, tango_control_handle: Any, device_name: str) -> None:
    """
    Test display of device names.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    :param device_name: Tango device
    """
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_NAMES),
        tango_host=tgo_host,
        tgo_name=device_name,
    )
    tango_control_handle.run_info()


def test_show_class(tgo_host: str, tango_control_handle: Any, device_name: str) -> None:
    """
    Test display of device classes.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    :param device_name: Tango device
    """
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_CLASS),
        tango_host=tgo_host,
        tgo_name=device_name,
    )
    tango_control_handle.run_info()


def test_list(tgo_host: str, tango_control_handle: Any, device_name: str) -> None:
    """
    Test list of device names.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    :param device_name: Tango device
    """
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_LIST),
        tango_host=tgo_host,
    )
    tango_control_handle.run_info()
