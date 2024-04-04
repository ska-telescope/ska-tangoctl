"""
Test tangoctl options.

# type: ignore[import-untyped]
"""

import logging
from typing import Any

import pytest

from ska_mid_itf_engineering_tools.tango_control.read_tango_devices import (
    TangoctlDevices,
    TangoctlDevicesBasic,
)

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("test_tango_control")
_module_logger.setLevel(logging.WARNING)


def test_configuration_data(configuration_data: dict) -> None:
    """
    Check configuration data file.

    :param configuration_data: tangoctl setup
    """
    assert len(configuration_data) > 0


@pytest.mark.xfail()
def test_tango_host(tango_host: str, tango_control_handle: Any) -> None:
    """
    Test that Tango database is up and running.

    :param tango_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    _module_logger.info("Use Tango host %s", tango_host)

    rv = tango_control_handle.check_tango(tango_host, True)
    assert rv == 0


@pytest.mark.xfail()
def test_read_input_files(tango_control_handle: Any) -> None:
    """
    Check input files.

    :param tango_control_handle: instance of Tango control class
    """
    ipath = "resources"
    _module_logger.info("Read input files in %s", ipath)
    rv = tango_control_handle.read_input_files(ipath, True)
    assert rv == 0


@pytest.mark.xfail()
def test_basic_devices(configuration_data: dict) -> None:
    """
    Read basic devices.

    :param configuration_data: read from JSON file
    """
    _module_logger.info("List device classes")
    devices = TangoctlDevicesBasic(_module_logger, True, False, configuration_data, None, "json")

    devices.read_config()
    devdict = devices.make_json()
    assert len(devdict) > 0


@pytest.mark.xfail()
def test_device_read(configuration_data: dict, device_name: str) -> None:
    """
    Read devices.

    :param configuration_data: read from JSON file
    :param device_name: Tango device
    """
    devices = TangoctlDevices(
        _module_logger,
        True,
        True,
        False,
        configuration_data,
        device_name,
        None,
        None,
        None,
        0,
        None,
        "json",
    )
    devices.read_device_values()
    devdict = devices.make_json()
    assert len(devdict) > 0
