"""
Unit tests for tangoctl.

# type: ignore[import-untyped]
"""

import json
import logging
import os
from typing import Any, TextIO

import pytest

from ska_mid_itf_engineering_tools.tango_control.tango_control import TangoControl

TANGO_HOST: str = "tango-databaseds.integration.svc.miditf.internal.skao.int:10000"
DEVICE_NAME: str = "mid-csp/capability-fsp/0"
CFG_NAME: str | bytes = "src/ska_mid_itf_engineering_tools/tango_control/tangoctl.json"

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("conftest")
_module_logger.setLevel(logging.WARNING)


@pytest.fixture(name="device_name")
def device_name() -> str:
    """
    Get Tango device name.

    :return: Tango device name
    """
    return DEVICE_NAME


@pytest.fixture(name="configuration_data")
def configuration_data() -> dict:
    """
    Read configuration file.

    :return: dictionary read from configuration file
    """
    cfg_file: TextIO = open(CFG_NAME)
    cfg_data: Any = json.load(cfg_file)
    cfg_file.close()
    return cfg_data


@pytest.fixture(name="tango_control_handle")
def tango_control_handle() -> Any:
    """
    Get instance of Tango control class.

    :return: instance of Tango control class
    """
    os.environ["TANGO_HOST"] = TANGO_HOST
    tangoctl = TangoControl(_module_logger, CFG_NAME)
    return tangoctl


@pytest.fixture(name="tango_host")
def tango_host() -> str:
    """
    Get Tango host.

    :return: host name and port number
    """
    os.environ["TANGO_HOST"] = TANGO_HOST
    return TANGO_HOST
