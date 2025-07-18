"""
Test tangoctl options.

# type: ignore[import-untyped]
"""

import logging
import os
import sys
from typing import Any

import pytest

from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevices
from ska_tangoctl.tango_kontrol.tango_kontrol import TangoKontrol

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("test_tango_control")
_module_logger.setLevel(logging.WARNING)


def test_konfiguration_data(konfiguration_data: dict) -> None:
    """
    Check configuration data file.

    :param konfiguration_data: tangoctl setup
    """
    assert len(konfiguration_data) > 0


def test_tango_host(
    tgo_host: str,
    konfiguration_data: dict,
    kube_namespace: str,
    domain_name: str,
    k8s_info: KubernetesInfo,
    tango_kontrol_handle: TangoKontrol,
) -> None:
    """
    Test that Tango database is up and running.

    :param tgo_host: Tango host
    :param konfiguration_data: tangoctl setup
    :param kube_namespace: K8S namespace
    :param domain_name: doman name
    :param k8s_info: Kubernetes info
    :param tango_kontrol_handle: instance of Tango control class
    """
    databaseds_name: str = konfiguration_data["databaseds_name"]
    cluster_domain: str = domain_name
    databaseds_port: int = konfiguration_data["databaseds_port"]

    tango_fqdn = f"{databaseds_name}.{kube_namespace}.{cluster_domain}"
    tango_host = f"{tango_fqdn}:{databaseds_port}"

    _module_logger.info("Use Tango host %s (%s)", tango_host, tgo_host)

    os.environ["TANGO_HOST"] = tgo_host
    _module_logger.info("Set TANGO_HOST to %s", tgo_host)

    tango_kontrol_handle.setup_k8s(tango_host=tgo_host)
    rv = tango_kontrol_handle.check_tango()
    assert rv == 0


@pytest.mark.skip()
def test_read_input_files(tango_kontrol_handle: TangoKontrol) -> None:
    """
    Check input files.

    :param tango_kontrol_handle: instance of Tango control class
    """
    ipath = "resources"
    _module_logger.info("Read input files in %s", ipath)
    rv = tango_kontrol_handle.read_input_files(ipath, True)
    assert rv == 0


def test_namespaces_dict(kube_namespace: str, k8s_info: KubernetesInfo) -> None:
    """
    Test K8S namespaces.

    :param kube_namespace: K8S namespace
    :param k8s_info: instance of Kubernetes info class
    """
    _module_logger.info("Read namespaces")
    k8s_namespaces_dict = k8s_info.get_namespaces_dict()
    assert len(k8s_namespaces_dict) > 0


def test_namespaces_list(kube_namespace: str, k8s_info: Any) -> None:
    """
    Test K8S namespaces.

    :param kube_namespace: K8S namespace
    :param k8s_info: instance of Kubernetes info class
    """
    _module_logger.info("List namespaces")
    _ctx_name, _cluster, k8s_namespaces_list = k8s_info.get_namespaces_list(None)
    assert len(k8s_namespaces_list) > 0


def test_pods_dict(kube_namespace: str, tango_kontrol_handle: Any) -> None:
    """
    Test for reading pods.

    :param kube_namespace: K8S namespace
    :param tango_kontrol_handle: instance of Tango control class
    """
    _module_logger.info("Read pods")
    k8s_pods_dict = tango_kontrol_handle.get_pods_dict(kube_namespace)
    assert len(k8s_pods_dict) > 0


def test_device_read(tgo_host: str, konfiguration_data: dict, device_name: str) -> None:
    """
    Read devices.

    :param tgo_host: Tango host and port
    :param konfiguration_data: read from JSON file
    :param device_name: Tango device
    """
    devices = TangoctlDevices(
        _module_logger,
        tgo_host,
        sys.stdout,
        1000,
        {},
        konfiguration_data,
        device_name,
        False,
        DispAction(DispAction.TANGOCTL_JSON),
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        0,
    )
    devices.read_device_values()
    devdict = devices.make_devices_json_medium()
    assert len(devdict) > 0


def test_show_namespaces(tango_kontrol_handle: Any, device_name: str) -> None:
    """
    Test display of namespaces.

    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List namespaces")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        quiet_mode=True,
        show_ns=True,
    )
    rc: int = tango_kontrol_handle.show_namespaces()
    assert rc == 0


def test_show_pod_names(kube_namespace: str, tango_kontrol_handle: Any, device_name: str) -> None:
    """
    Test display of pod names.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List pods in namespace %s", kube_namespace)
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_TXT),
        ns_name=kube_namespace,
        quiet_mode=True,
        show_pod=True,
    )
    rc: int = tango_kontrol_handle.list_pod_names(tango_kontrol_handle.k8s_ns)
    assert rc == 0


def test_show_dev(kube_namespace: str, tango_kontrol_handle: Any, device_name: str) -> None:
    """
    Test display of device names.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device names")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_NAMES),
        ns_name=kube_namespace,
        quiet_mode=True,
        tgo_name=device_name,
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0


def test_show_class(kube_namespace: str, tango_kontrol_handle: Any, device_name: str) -> None:
    """
    Test display of device classes.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device classes")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_CLASS),
        ns_name=kube_namespace,
        quiet_mode=True,
        tgo_name=device_name,
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0


def test_list(kube_namespace: str, tango_kontrol_handle: Any, device_name: str) -> None:
    """
    List device states.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device states")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_LIST),
        ns_name=kube_namespace,
        quiet_mode=True,
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0


def test_json_attributes(kube_namespace: str, tango_kontrol_handle: Any, device_name: str) -> None:
    """
    List device attributes in JSON format.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device attributes in JSON format")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_JSON),
        ns_name=kube_namespace,
        quiet_mode=True,
        show_attrib=True,
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0


def test_json_commands(kube_namespace: str, tango_kontrol_handle: Any, device_name: str) -> None:
    """
    List device commands in JSON format.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device commands in JSON format")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_JSON),
        ns_name=kube_namespace,
        quiet_mode=True,
        show_cmd=True,
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0


def test_json_properties(kube_namespace: str, tango_kontrol_handle: Any, device_name: str) -> None:
    """
    List device properties in JSON format.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    :param device_name: Tango device
    """
    _module_logger.info("List device commands in JSON format")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_JSON),
        ns_name=kube_namespace,
        quiet_mode=True,
        show_prop=True,
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0


def test_json_build_state(kube_namespace: str, tango_kontrol_handle: Any) -> None:
    """
    List device attributes named 'buildState' in short YAML format.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    """
    _module_logger.info("List device attributes named 'buildState' in short YAML")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_YAML),
        ns_name=kube_namespace,
        quiet_mode=True,
        size="S",
        tgo_attrib="buildState",
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0


def test_yaml_attr_cmd_prop(kube_namespace: str, tango_kontrol_handle: Any) -> None:
    """
    List attributes, commands and properties in YAML format.

    :param kube_namespace: Kubernetes namespace
    :param tango_kontrol_handle: instance of Tango control class
    """
    _module_logger.info("List attributes, commands and properties in YAML")
    tango_kontrol_handle.reset()
    tango_kontrol_handle.setup_k8s(
        disp_action=DispAction(DispAction.TANGOCTL_YAML),
        ns_name=kube_namespace,
        quiet_mode=True,
        show_attrib=True,
        show_cmd=True,
        show_prop=True,
        size="M",
    )
    rc: int = tango_kontrol_handle.run_info()
    assert rc == 0
