#!/usr/bin/env python3
"""Web interface for tangoctl."""
import json
import logging
import os

import tango
import yaml

from ska_tangoctl.k8s_info.get_k8s_info import KubernetesControl
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic
from ska_tangoctl.tango_kontrol.tango_kontrol import get_namespaces_list

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("cia")
_module_logger.setLevel(logging.INFO)


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

KUBE_NAMESPACE = ""


def show_namespaces() -> None:
    """Print K8S namespaces."""
    print("<h2>Namespaces</h2>")
    ns_list = get_namespaces_list(_module_logger, None)
    print("<table>")
    for ns in ns_list:
        print(f'<tr>\n<td><a href="/cgi-bin/tangocia.py?show=devices&ns={ns}">{ns}</a></td>')
        print(f'<td><a href="/cgi-bin/tangocia.py?show=pods&ns={ns}">[Pods]</a></td>')
        print("</tr>")
    print("</table>")


def show_pods(ns_name: str) -> None:
    """
    Print K8S pods.

    :param ns_name: K8S namespace
    """
    k8s = KubernetesControl(_module_logger)
    pods_dict = k8s.get_pods(ns_name, None)
    print(f"<h2>Pods in namespace {ns_name}</h2>")
    print("<table>")
    print("<tr><th>POD NAME</th><th>IP ADDRESS</th></tr>")
    for pod in pods_dict:
        print(
            f'<tr><td><a href="/cgi-bin/tangocia.py?pod={pod}&ns={ns_name}">{pod}</a>'
            f"</td><td>{pods_dict[pod][0]}</td></tr>"
        )
    print("</table>")


def show_pod(ns_name: str, pod_name: str) -> None:
    """
    Print k8S pods.

    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    """
    print(f"<p><b>Namepace</b>&nbsp;{ns_name}</p>")
    print(f"<p><b>Pod</b>&nbsp;{pod_name}</p>")
    k8s = KubernetesControl(_module_logger)
    pods_dict = k8s.get_pods(ns_name, None)
    if pod_name in pods_dict:
        print(f"<p><b>IP address</b>&nbsp;{pods_dict[pod_name][0]}</p>")
    else:
        print(f"<p>Pod {pod_name} not found</p>")


def set_tango_host(ns_name: str) -> None:
    """
    Get Tango host address.

    :param ns_name: K8S namespace
    """
    tango_host = f"{DATABASEDS_NAME}.{ns_name}.svc.{CLUSTER_DOMAIN}:{DATABASEDS_PORT}"
    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)


def show_devices(ns_name: str) -> None:
    """
    Print devices.

    :param ns_name: K8S namespace
    """
    set_tango_host(ns_name)
    try:
        devs = TangoctlDevicesBasic(
            _module_logger,
            True,
            True,
            True,
            {},
            CFG_DATA,
            None,
            False,
            True,
            False,
            "json",
            False,
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection failed")
        return
    devs.read_configs()
    devs_dict = devs.make_json()
    _module_logger.debug("Devices: %s", devs_dict)
    res = list(devs_dict.keys())[0]
    table_headers = list(devs_dict[res].keys())
    table_headers.insert(0, "Device Name")
    print("<table><tr>")
    for header in table_headers:
        print(f"<th>{header}</th>")
    print("</tr>\n")
    for device in devs_dict:
        dev = devs_dict[device]
        print(
            f'<tr><td><a href="/cgi-bin/tangocia.py?dev={device}&ns={ns_name}&fmt=shtml">'
            f"{device}</a></td>"
        )
        for header in table_headers[1:]:
            print(f"<td>{dev[header]}</td>")
        print("</tr>\n")
    print("</table>")


def show_device(ns_name: str, dev_name: str, fmt: str) -> None:  # noqa: C901
    """
    Print device.

    :param ns_name: K8S namespace
    :param dev_name: device name
    :param fmt: output format
    """
    set_tango_host(ns_name)
    try:
        device = TangoctlDevice(
            _module_logger,
            True,
            True,
            True,
            {},
            dev_name,
            True,
            False,
            {},
            None,
            None,
            None,
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection failed")
        print("<p>Tango connection failed</p>")
        return
    print(f"<h2>Device {dev_name}</h2><p>")
    # Short HTML
    if fmt == "shtml":
        print("<b>Info</b>")
    else:
        print(f'<a href="/cgi-bin/tangocia.py?dev={dev_name}&ns={ns_name}&fmt=shtml">Info</a>')
    # Long HTML
    if fmt == "html":
        print("&nbsp;<b>Detail</b>")
    else:
        print(
            f'&nbsp;<a href="/cgi-bin/tangocia.py?dev={dev_name}&ns={ns_name}&fmt=html">Detail</a>'
        )
    # JSON
    if fmt == "json":
        print("&nbsp;<b>JSON</b>")
    else:
        print(
            f'&nbsp;<a href="/cgi-bin/tangocia.py?dev={dev_name}&ns={ns_name}&fmt=json">JSON</a>'
        )
    # YAML
    if fmt == "yaml":
        print("&nbsp;<b>YAML</b>")
    else:
        print(
            f'&nbsp;<a href="/cgi-bin/tangocia.py?dev={dev_name}&ns={ns_name}&fmt=yaml">YAML</a>'
        )
    # Markdown
    if fmt == "md":
        print("&nbsp;<b>Markdown</b>")
    else:
        print(
            f'&nbsp;<a href="/cgi-bin/tangocia.py?dev={dev_name}&ns={ns_name}&fmt=md">Markdown</a>'
        )
    # Plain text
    if fmt == "txt":
        print("&nbsp;<b>Text</b>")
    else:
        print(f'&nbsp;<a href="/cgi-bin/tangocia.py?dev={dev_name}&ns={ns_name}&fmt=txt">Text</a>')
    print("</p>")
    device.read_config_all()
    device.read_attribute_value()
    device.read_command_value(
        CFG_DATA["run_commands"], CFG_DATA["run_commands_name"]  # type: ignore[arg-type]
    )
    device.read_property_value()
    if fmt == "json":
        devdict = device.make_json()
        print('<div style="background-color: AliceBlue"><pre>')
        print(f"{json.dumps(devdict, indent=4)}")
        print("</pre></div>")
    elif fmt == "yaml":
        devdict = device.make_json()
        print('<div style="background-color: AliceBlue"><pre>')
        print(f"{yaml.dump(devdict)}")
        print("</pre></div>")
    elif fmt == "shtml":
        device.print_html_quick(False)
    elif fmt == "md":
        print('<div style="background-color: AliceBlue"><pre>')
        device.print_markdown_all()
        print("</pre></div>")
    elif fmt == "txt":
        print('<div style="background-color: AliceBlue"><pre>')
        device.print_txt_all()
        print("</pre></div>")
    else:
        device.print_html_all(False)


def page_header() -> None:
    """Print HTML header."""
    print(
        """\
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
<title>CIA</title>
<style>
table {width: 98%}
th {text-align: left; border-bottom: 2px solid; padding: 0px}
td {border-bottom: 1px solid; padding: 0px}
</style>
</head>
"""
    )
    print(
        f"""<body>
<h1 align="center">Tango CIA</h1>
<!--
CONTENT_TYPE    : {os.getenv("CONTENT_TYPE")}
HTTP_USER_AGENT : {os.getenv("HTTP_USER_AGENT")}
QUERY_STRING    : {query_string}
REQUEST_METHOD  : {request_method}
-->
"""
    )
    print("<hr/><p>")
    print('&nbsp;<a href="/">Home</a>&nbsp;<a href="/cgi-bin/tangocia.py?show=ns">Namespaces</a>')
    if KUBE_NAMESPACE:
        print(f'&nbsp;<a href="/cgi-bin/tangocia.py?show=pods&ns={KUBE_NAMESPACE}">Pods</a>')
        print(f'&nbsp;<a href="/cgi-bin/tangocia.py?show=devices&ns={KUBE_NAMESPACE}">Devices</a>')
    print("</p><hr/><br/>")


def page_footer() -> None:
    """Print HTML footer."""
    print(
        """
<br/><hr/>
<div align="center"><a href=\"https://www.skao.int/en\">SKAO</a></div>
</body>
</html>
"""
    )


# Start here
query_string = os.getenv("QUERY_STRING")
request_method = os.getenv("REQUEST_METHOD")

if not query_string:  # noqa: C901
    page_header()
else:
    queries = query_string.split("&")
    query_dict = {}
    for query in queries:
        parts = query.split("=")
        query_dict[parts[0]] = parts[1]
    if "ns" in query_dict:
        KUBE_NAMESPACE = query_dict["ns"]
    page_header()
    if "show" in query_dict:
        if query_dict["show"] == "ns":
            show_namespaces()
        elif query_dict["show"] == "pods":
            show_pods(query_dict["ns"])
        elif query_dict["show"] == "devices":
            show_devices(query_dict["ns"])
        else:
            pass
    elif "pod" in query_dict:
        pod_name = query_dict["pod"]
        show_pod(query_dict["ns"], query_dict["pod"])
    elif "dev" in query_dict:
        if "fmt" in query_dict:
            fmt = query_dict["fmt"]
        else:
            fmt = "html"
        show_device(query_dict["ns"], query_dict["dev"], fmt)
    else:
        print(
            f"<li><b>QUERY_STRING:</b> {query_string}</li>"
            f"<li><b>REQUEST_METHOD:</b> {request_method}</li>"
        )

page_footer()
