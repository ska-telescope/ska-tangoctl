"""
Unit tests for tangoctl.

# type: ignore[import-untyped]
"""

import json
import logging
from typing import Any, TextIO

import pytest

from ska_mid_itf_engineering_tools.tango_kontrol.tango_kontrol import TangoControlKubernetes

KUBE_NAMESPACE: str = "integration"
DEVICE_NAME: str = "mid-csp/capability-fsp/0"
CFG_NAME: str | bytes = "src/ska_mid_itf_engineering_tools/tango_kontrol/tangoktl.json"

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("conftest")
_module_logger.setLevel(logging.WARNING)


@pytest.fixture(name="kube_namespace")
def kube_namespace() -> str:
    """
    Get K8S namespace.

    :return: K8S namespace
    """
    return KUBE_NAMESPACE


@pytest.fixture(name="device_name")
def device_name() -> str:
    """
    Get Tango device name.

    :return: Tango device name
    """
    return DEVICE_NAME


@pytest.fixture(name="konfiguration_data")
def konfiguration_data() -> dict:
    """
    Read configuration file.

    :return: dictionary read from configuration file
    """
    cfg_file: TextIO = open(CFG_NAME)
    cfg_data: Any = json.load(cfg_file)
    cfg_file.close()
    return cfg_data


@pytest.fixture(name="tango_kontrol_handle")
def tango_kontrol_handle() -> Any:
    """
    Get instance of Tango control class.

    :return: instance of Tango control class
    """
    tangoktl = TangoControlKubernetes(_module_logger, CFG_NAME)
    return tangoktl
