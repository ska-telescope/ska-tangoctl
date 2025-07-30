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
    _module_logger.info("List device names")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_NAMES),
        quiet_mode=True,
        tango_host=tgo_host,
        tgo_name=device_name,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0


def test_show_class(tgo_host: str, tango_control_handle: Any, device_name: str) -> None:
    """
    Test display of device classes.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device classes")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_CLASS),
        quiet_mode=True,
        tango_host=tgo_host,
        tgo_name=device_name,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0


def test_list(tgo_host: str, tango_control_handle: Any, device_name: str) -> None:
    """
    List device states.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device states")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_LIST),
        quiet_mode=True,
        tango_host=tgo_host,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0


def test_json_attributes(tgo_host: str, tango_control_handle: Any) -> None:
    """
    List device attributes in JSON format.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    _module_logger.info("List device attributes in JSON")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_JSON),
        quiet_mode=True,
        show_attrib=True,
        tango_host=tgo_host,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0


def test_json_commands(tgo_host: str, tango_control_handle: Any) -> None:
    """
    List device commands in JSON format.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    _module_logger.info("List device commands in JSON")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_JSON),
        quiet_mode=True,
        show_cmd=True,
        tango_host=tgo_host,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0


def test_json_properties(tgo_host: str, tango_control_handle: Any) -> None:
    """
    List device properties in JSON format.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    _module_logger.info("List device properties in JSON")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_JSON),
        quiet_mode=True,
        show_prop=True,
        tango_host=tgo_host,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0


def test_json_build_state(tgo_host: str, tango_control_handle: Any) -> None:
    """
    List device attributes named 'buildState' in short YAML format.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    _module_logger.info("List device attributes named 'buildState' in short YAML")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_YAML),
        quiet_mode=True,
        size="S",
        tgo_attrib="buildState",
        tango_host=tgo_host,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0


def test_yaml_attr_cmd_prop(tgo_host: str, tango_control_handle: Any) -> None:
    """
    List attributes, commands and properties in YAML format.

    :param tgo_host: hostname and port number
    :param tango_control_handle: instance of Tango control class
    """
    _module_logger.info("List attributes, commands and properties in YAML")
    tango_control_handle.reset()
    tango_control_handle.setup(
        disp_action=DispAction(DispAction.TANGOCTL_YAML),
        quiet_mode=True,
        show_attrib=True,
        show_cmd=True,
        show_prop=True,
        size="M",
        tango_host=tgo_host,
    )
    rc: int = tango_control_handle.run_info()
    assert rc == 0
