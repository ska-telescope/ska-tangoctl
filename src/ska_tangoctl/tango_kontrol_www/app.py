"""Web interface built on Flask."""

import logging
import os
import tempfile

import tango
from flask import Flask, render_template
from markupsafe import Markup

from ska_tangoctl.k8s_info.get_k8s_info import KubernetesControl
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic
from ska_tangoctl.tango_kontrol.tango_kontrol import get_namespaces_list

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tangoktl")
_module_logger.setLevel(logging.INFO)

app = Flask(__name__)

CFG_DATA = {
    "timeout_millis": 500,
    "cluster_domain": "miditf.internal.skao.int",
    "databaseds_name": "tango-databaseds",
    "databaseds_port": 10000,
    "device_port": 45450,
    "run_commands": [
        "QueryClass",
        "QueryDevice",
        "QuerySubDevice",
        "GetVersionInfo",
        "State",
        "Status",
    ],
    "run_commands_name": ["DevLockStatus", "DevPollStatus", "GetLoggingTarget"],
    "long_attributes": ["internalModel", "transformedInternalModel"],
    "ignore_device": ["sys", "dserver"],
    "min_str_len": 4,
    "delimiter": ",",
    "list_items": {
        "attributes": [["adminMode", "10"], ["version", "10"]],
        "commands": [["State", "10"], ["Status", 30]],
    },
    "list_values": {"attributes": ["adminMode", "versionId"], "commands": ["Status", "State"]},
}

DATABASEDS_NAME: str = str(CFG_DATA["databaseds_name"])
CLUSTER_DOMAIN: str = str(CFG_DATA["cluster_domain"])
DATABASEDS_PORT: int = int(str(CFG_DATA["databaseds_port"]))


def set_tango_host(ns_name: str) -> None:
    """
    Get Tango host address.

    :param ns_name: K8S namespace
    """
    tango_host = f"{DATABASEDS_NAME}.{ns_name}.svc.{CLUSTER_DOMAIN}:{DATABASEDS_PORT}"
    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)


@app.route("/")
def hello_world() -> str:
    """
    Say hello.

    :return: HTML based on template.
    """
    return render_template("index.html", title="Home", KUBE_NAMESPACE="foo")


@app.route("/ns")
def show_namespaces() -> str:
    """
    Print K8S namespaces.

    :returns: HTML based on template.
    """
    ns_list = get_namespaces_list(_module_logger, None)
    ns_html = "<h2>Namespaces</h2><table>"
    for ns in ns_list:
        ns_html += f'<tr>\n<td><a href="/devices/{ns}">{ns}</a></td>'
        ns_html += f'<td><a href="/pods/{ns}">[Pods]</a></td></tr>'
    ns_html += "<table>"
    return render_template("index.html", title="Namespaces", body_html=Markup(ns_html))


@app.route("/devices/<ns_name>")
def show_devices(ns_name: str) -> str:
    """
    Print devices.

    :param ns_name: K8S namespace
    :return: HTML based on template.
    """
    set_tango_host(ns_name)
    try:
        devs = TangoctlDevicesBasic(
            _module_logger, False, True, False, False, CFG_DATA, None, "json"
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection failed")
        ns_html = "<p>Tango connection failed</p>"
        return render_template(
            "index.html", title="Namespaces", KUBE_NAMESPACE="foo", body_html=Markup(ns_html)
        )
    devs.read_configs()
    devs_dict = devs.make_json()
    _module_logger.debug("Devices: %s", devs_dict)
    res = list(devs_dict.keys())[0]
    table_headers = list(devs_dict[res].keys())
    table_headers.insert(0, "Device Name")
    dev_html = "<table><tr>"
    for header in table_headers:
        dev_html += f"<th>{header}</th>"
    dev_html += "</tr>\n"
    for device in devs_dict:
        dev = devs_dict[device]
        dev_name = device.replace("/", "+")
        dev_html += f'<tr><td><a href="/device/{dev_name}/ns/{ns_name}">{device}</a></td>'
        for header in table_headers[1:]:
            dev_html += f"<td>{dev[header]}</td>"
        dev_html += "</tr>\n"
    dev_html += "</table>"
    return render_template(
        "index_ns.html", title="Devices", KUBE_NAMESPACE=ns_name, body_html=Markup(dev_html)
    )


@app.route("/device/<dev_nm>/ns/<ns_name>")
def show_device(ns_name: str, dev_nm: str) -> str:  # noqa: C901
    """
    Print device.

    :param ns_name: K8S namespace
    :param dev_nm: device name

    :returns: HTML based on template.
    """
    dev_name = dev_nm.replace("+", "/")
    set_tango_host(ns_name)
    try:
        device = TangoctlDevice(
            _module_logger,
            True,
            False,
            dev_name,
            {},
            None,
            None,
            None,
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection failed")
        ns_html = "<p>Tango connection failed</p>"
        return render_template(
            "index.html", title="Namespaces", KUBE_NAMESPACE=ns_name, body_html=Markup(ns_html)
        )
    dev_html: str = f"<h2>Device {dev_name}</h2><p>"

    dev_html += "</p>"
    device.read_config_all()
    device.read_attribute_value()
    device.read_command_value(
        CFG_DATA["run_commands"], CFG_DATA["run_commands_name"]  # type: ignore[arg-type]
    )
    device.read_property_value()
    with tempfile.TemporaryDirectory() as temp_dir:
        _fd1, temp_file1_path = tempfile.mkstemp(dir=temp_dir)
        device.print_html_all(False, temp_file1_path)
        tmpf = open(temp_file1_path, "r")
        dev_html += tmpf.read()
        tmpf.close()
    # dev_html += "<table border=0 cellpadding=0 cellspacing=0>\n"
    # dev_html += device.get_html()
    # dev_html += "</table>"
    return render_template(
        "index_ns.html", title="Devices", KUBE_NAMESPACE=ns_name, body_html=Markup(dev_html)
    )


@app.route("/pods/<ns_name>")
def show_pods(ns_name: str) -> str:
    """
    Print K8S pods.

    :param ns_name: K8S namespace
    :returns: HTML based on template.
    """
    k8s = KubernetesControl(_module_logger)
    pods_dict = k8s.get_pods(ns_name, None)
    pods_html = f"<h2>Pods in namespace {ns_name}</h2>"
    pods_html += "<table><tr><th>POD NAME</th><th>IP ADDRESS</th></tr>"
    for pod in pods_dict:
        pods_html += (
            f'<tr><td><a href="/pod/{pod}/ns/{ns_name}">{pod}</a>'
            f"</td><td>{pods_dict[pod][0]}</td></tr>"
        )
    pods_html += "</table>"
    return render_template(
        "index_ns.html", title="Pods", KUBE_NAMESPACE=ns_name, body_html=Markup(pods_html)
    )


@app.route("/pod/<pod_name>/ns/<ns_name>")
def show_pod(ns_name: str, pod_name: str) -> str:
    """
    Print k8S pods.

    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    :returns: HTML based on template.
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Pod</b>&nbsp;{pod_name}</p>"
    k8s = KubernetesControl(_module_logger)
    pods_dict = k8s.get_pods(ns_name, None)
    if pod_name in pods_dict:
        pod_html += f"<p><b>IP address</b>&nbsp;{pods_dict[pod_name][0]}</p>"
    else:
        pod_html += f"<p>Pod {pod_name} not found</p>"
    return render_template(
        "index_ns.html", title="Pod", KUBE_NAMESPACE=ns_name, body_html=Markup(pod_html)
    )
