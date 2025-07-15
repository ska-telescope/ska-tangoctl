"""
Unit tests for tangoctl.

# type: ignore[import-untyped]
"""

import json
import logging
import os
from typing import Any, TextIO

import pytest

from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
from ska_tangoctl.tango_kontrol.tango_kontrol import TangoKontrol

KUBE_NAMESPACE: str = "test-equipment"
DEVICE_NAME: str = "mid-itf/spectana/1"
DOMAIN_NAME = "svc.miditf.internal.skao.int"
CFG_NAME: str | bytes = "src/ska_tangoctl/tango_kontrol/tangoktl.json"
# TANGO_HOST: str = "tango-databaseds.test-equipment.svc.miditf.internal.skao.int:10000"
TANGO_HOST: str = "10.164.11.25:10000"

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("conftest")
_module_logger.setLevel(logging.WARNING)


@pytest.fixture(name="kube_namespace")
def kube_namespace() -> str:
    """
    Get K8S namespace.

    :returns: K8S namespace
    """
    return KUBE_NAMESPACE


@pytest.fixture(name="domain_name")
def domain_name() -> str:
    """
    Get K8S namespace.

    :returns: K8S namespace
    """
    return DOMAIN_NAME


@pytest.fixture(name="device_name")
def device_name() -> str:
    """
    Get Tango device name.

    :returns: Tango device name
    """
    return DEVICE_NAME


@pytest.fixture(name="konfiguration_data")
def konfiguration_data() -> dict:
    """
    Read configuration file.

    :returns: dictionary read from configuration file
    """
    cfg_file: TextIO = open(CFG_NAME)
    cfg_data: Any = json.load(cfg_file)
    cfg_file.close()
    return cfg_data


@pytest.fixture(name="tango_kontrol_handle")
def tango_kontrol_handle() -> TangoKontrol:
    """
    Get instance of Tango control class.

    :returns: instance of Tango control class
    """
    tangoktl = TangoKontrol(_module_logger, None, None, None)
    tangoktl.setup_k8s(
        show_attrib=True,
        show_cmd=True,
        show_prop=True,
        cfg_data=konfiguration_data,
        ns_name=KUBE_NAMESPACE,
    )
    return tangoktl


@pytest.fixture(name="k8s_info")
def k8s_info_handle() -> KubernetesInfo:
    """
    Get instance of Kubernetes info class.

    :returns: Kubernetes info
    """
    k8s_handle = KubernetesInfo(_module_logger, None)
    return k8s_handle


@pytest.fixture(name="tgo_host")
def tgo_host() -> str:
    """
    Get Tango host.

    :returns: host name and port number
    """
    os.environ["TANGO_HOST"] = TANGO_HOST
    return TANGO_HOST
