"""Web interface built on FastAPI."""

import logging
import os
import socket
import tempfile
from contextlib import closing
from typing import Any

import tango
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic
from ska_tangoctl.tango_kontrol.get_namespaces import get_namespaces_list

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tangoktl")
_module_logger.setLevel(logging.INFO)


CFG_DATA: dict = {
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
    "svc_ports_ignore": ["10000", "45450"],
}

DATABASEDS_NAME: str = str(CFG_DATA["databaseds_name"])
CLUSTER_DOMAIN: str = str(CFG_DATA["cluster_domain"])
DATABASEDS_PORT: int = int(str(CFG_DATA["databaseds_port"]))

app: FastAPI = FastAPI()
templates: Jinja2Templates = Jinja2Templates(directory="templates")

tango_host: str | None = None

tango_hosts: dict = {}

app.mount("/static", StaticFiles(directory="static"), name="static")


def check_tango_host(ns_name: str) -> bool:
    """
    Check that there is a Tango host.

    :param ns_name: namespace to be checked
    :return: true when found
    """
    host = f"{DATABASEDS_NAME}.{ns_name}.svc.{CLUSTER_DOMAIN}"
    port = DATABASEDS_PORT
    hp_open: bool = False
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            if sock.connect_ex((host, port)) == 0:
                _module_logger.info("Host %s Port %d is open", host, port)
                hp_open = True
            else:
                _module_logger.info("Host %s Port %d is not open", host, port)
        except socket.gaierror:
            _module_logger.info("Host %s is unknown", host)
    tango_hosts[ns_name] = hp_open
    return hp_open


def check_tango_hosts() -> None:
    """Check all namespaces for active Tango host."""
    ns_list = get_namespaces_list(_module_logger, None)
    for ns in ns_list:
        check_tango_host(ns)


def set_tango_host(ns_name: str) -> None:
    """
    Get Tango host address.

    :param ns_name: K8S namespace
    """
    global tango_host
    tango_host = f"{DATABASEDS_NAME}.{ns_name}.svc.{CLUSTER_DOMAIN}:{DATABASEDS_PORT}"
    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)


@app.get("/")
def read_root(request: Request) -> Any:
    """
    Display the home page.

    :param request: HTTP connection
    :return: template tesponse
    """
    check_tango_hosts()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Home"},
    )


@app.get("/ns")
def show_namespaces(request: Request) -> Any:
    """
    Print K8S namespaces.

    :param request: HTTP connection
    :return: template response
    """
    ns_list = get_namespaces_list(_module_logger, None)
    _module_logger.info("Read %d K8S namespaces", len(ns_list))
    ns_html = "<h2>Namespaces</h2><table>"
    for ns in ns_list:
        if ns not in tango_hosts:
            check_tango_host(ns)
        if tango_hosts[ns]:
            ns_html += f'<tr>\n<td class="main"><a href="/devices/{ns}">{ns}</a></td>'
        else:
            ns_html += f'<tr>\n<td class="main">{ns}</td>'
        ns_html += f'<td class="main"><a href="/pods/{ns}">[Pods]</a></td>'
        ns_html += f'<td class="main"><a href="/services/{ns}">[Services]</a></td></tr>'
    ns_html += "<table>"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Namespaces", "body_html": Markup(ns_html)},
    )


@app.get("/tango_ns")
def show_tango_namespaces(request: Request) -> Any:
    """
    Print K8S namespaces.

    :param request: HTTP connection
    :return: template tesponse
    """
    ns_list = get_namespaces_list(_module_logger, None)
    _module_logger.info("Read %d K8S namespaces", len(ns_list))
    ns_html = "<h2>Namespaces</h2><table>"
    for ns in ns_list:
        if check_tango_host(ns):
            ns_html += f'<tr>\n<td class="main"><a href="/devices/{ns}">{ns}</a></td>'
        else:
            ns_html += f'<tr>\n<td class="main">{ns}</td>'
        ns_html += f'<td class="main"><a href="/pods/{ns}">[Pods]</a></td>'
        ns_html += f'<td class="main"><a href="/services/{ns}">[Services]</a></td></tr>'
    ns_html += "<table>"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Namespaces", "body_html": Markup(ns_html)},
    )


@app.get("/devices/{ns_name}")
def show_devices(request: Request, ns_name: str) -> Any:
    """
    Print Tango devices.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :return: template response
    """
    set_tango_host(ns_name)
    dev_html: str = f"<h2>Devices in namespace {ns_name}</h2>"
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
            DispAction(DispAction.TANGOCTL_JSON),
            True,
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection to %s failed", tango_host)
        dev_html += f"<p>Tango connection to {tango_host} failed</p>"
        return templates.TemplateResponse(
            request=request,
            name="index_ns.html",
            context={"title": "Error", "body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
        )
    devs.read_configs()
    devs_dict = devs.make_json()
    _module_logger.debug("Devices: %s", devs_dict)
    try:
        res = list(devs_dict.keys())[0]
        table_headers = list(devs_dict[res].keys())
    except IndexError:
        table_headers = []
    table_headers.insert(0, "Device Name")
    dev_html += "<table><tr>"
    for header in table_headers:
        dev_html += f"<th>{header}</th>"
    dev_html += "</tr>\n"
    for device in devs_dict:
        dev = devs_dict[device]
        dev_name = device.replace("/", "+")
        dev_html += (
            f'<tr><td class="main"><a href="/device/{dev_name}/ns/{ns_name}/fmt/html">'
            f"{device}</a></td>"
        )
        for header in table_headers[1:]:
            dev_html += f'<td class="main">{dev[header]}</td>'
        dev_html += "</tr>\n"
    dev_html += "</table>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Devices", "body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/device/{dev_nm}/ns/{ns_name}/fmt/html")
def show_device_html(
    request: Request,
    ns_name: str,
    dev_nm: str,
) -> Any:
    """
    Display device in HTML format.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param dev_nm: device name
    :return: template response
    """
    dev_html: str
    dev_name = dev_nm.replace("+", "/")
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
            {},
            None,
            None,
            None,
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection to %s failed", tango_host)
        dev_html = f"<p>Tango connection to {tango_host} failed</p>"
        return templates.TemplateResponse(
            request=request,
            name="index_ns.html",
            context={"body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
        )
    dev_html = "<p><b>HTML</b>"
    dev_html += f'&nbsp;<a href="/dev_json/{dev_nm}/ns/{ns_name}" target="_blank">JSON</a>'
    dev_html += f'&nbsp;<a href="/device/{dev_nm}/ns/{ns_name}/fmt/yaml">YAML</a>'
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
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Device", "body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/device/{dev_nm}/ns/{ns_name}/fmt/yaml")
def show_device_yaml(
    request: Request,
    ns_name: str,
    dev_nm: str,
) -> Any:
    """
    Display device in HTML format.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param dev_nm: device name
    :return: template response
    """
    dev_html: str
    dev_name = dev_nm.replace("+", "/")
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
            {},
            None,
            None,
            None,
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection to %s failed", tango_host)
        dev_html = f"<p>Tango connection to {tango_host} failed</p>"
        return templates.TemplateResponse(
            request=request,
            name="index_ns.html",
            context={"body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
        )
    dev_html = f'<p><a href="/device/{dev_nm}/ns/{ns_name}/fmt/html">HTML</a>'
    dev_html += f'&nbsp;<a href="/dev_json/{dev_nm}/ns/{ns_name}s" target="_blank">JSON</a>'
    dev_html += "&nbsp;<b>YAML</b>"
    dev_html += "</p>"
    device.read_config_all()
    device.read_attribute_value()
    device.read_command_value(
        CFG_DATA["run_commands"], CFG_DATA["run_commands_name"]  # type: ignore[arg-type]
    )
    device.read_property_value()
    devdict = device.make_json()
    dev_html += f"<pre>{yaml.dump(devdict)}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Device", "body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/dev_json/{dev_nm}/ns/{ns_name}")
def fastapi_device_json(
    request: Request,
    ns_name: str,
    dev_nm: str,
) -> Any:
    """
    Print specified Tango device.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param dev_nm: device name
    :return: template response
    """
    dev_name = dev_nm.replace("+", "/")
    set_tango_host(ns_name)
    dev_html: str
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
            {},
            None,
            None,
            None,
        )
    except tango.ConnectionFailed:
        _module_logger.error("Tango connection to %s failed", tango_host)
        dev_html = f"<p>Tango connection to {tango_host} failed</p>"
        return templates.TemplateResponse(
            request=request,
            name="index_ns.html",
            context={"body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
        )
    headers = {"X-Cat-Dog": "alone in the world", "Content-Language": "en-US"}
    devdict = device.make_json()
    return JSONResponse(content=devdict, headers=headers)


@app.get("/device/{dev_nm}/ns/{ns_name}/fmt/json")
def show_device_json(
    request: Request,
    ns_name: str,
    dev_nm: str,
) -> Any:  # noqa: C901
    """
    Print specified Tango device.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param dev_nm: device name
    :return: template response
    """
    set_tango_host(ns_name)
    dev_html: str
    dev_html = f'<p><a href="/device/{dev_nm}/ns/{ns_name}/fmt/html">HTML</a>'
    dev_html += "&nbsp;<b>JSON</b>"
    dev_html += f'&nbsp;<a href="/device/{dev_nm}/ns/{ns_name}/fmt/yaml">YAML</a></p>\n'
    return templates.TemplateResponse(
        request=request,
        name="index_json.html",
        context={
            "title": "Device",
            "body_html": Markup(dev_html),
            "KUBE_NAMESPACE": ns_name,
            "DEVICE_NAME": dev_nm,
        },
    )


@app.get("/pods/{ns_name}")
def show_pods(request: Request, ns_name: str) -> Any:
    """
    Print all K8S pods.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :return: template response
    """
    k8s = KubernetesInfo(_module_logger)
    pods_dict = k8s.get_pods(ns_name, None)
    _module_logger.debug("Pods: %s", pods_dict)
    pods_html: str = f"<h2>Pods in namespace {ns_name}</h2>"
    pods_html += (
        "<table><tr><th>POD NAME</th><th>IP ADDRESS</th><th>&nbsp;</th><th>&nbsp;</th></tr>"
    )
    for pod in pods_dict:
        pods_html += (
            f'<tr><td class="main"><a href="/pod/{pod}/ns/{ns_name}">{pod}</a>'
            f'</td><td class="main">{pods_dict[pod][0]}</td>'
            f'</td><td class="main"><a href="/pod_log/{pod}/ns/{ns_name}">Log</a></td>'
            f'</td><td class="main"><a href="/pod_desc/{pod}/ns/{ns_name}">'
            f"Description</a></td></tr>"
        )
    pods_html += "</table>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Pods", "body_html": Markup(pods_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/services/{ns_name}")
def show_services(request: Request, ns_name: str) -> Any:
    """
    Print all K8S services.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :return: template response
    """
    k8s = KubernetesInfo(_module_logger)
    svcs_dict = k8s.get_services(ns_name, None)
    _module_logger.debug("Services: %s", svcs_dict)
    svcs_html: str = f"<h2>Services in namespace {ns_name}</h2>"
    svcs_html += (
        "<table><tr><th>SERVICE NAME</th><th>IP ADDRESS</th><th>PORT</th>"
        "<th>PROTOCOL</th><th>&nbsp;</th></tr>"
    )
    for svc in svcs_dict:
        port_no: str = svcs_dict[svc][2]
        svc_ports_ignor: list[str] = CFG_DATA["svc_ports_ignore"]
        if port_no and (port_no not in svc_ports_ignor):
            svcs_html += (
                "<tr>"
                f'<td class="main"><a href="http://{svcs_dict[svc][1]}:{port_no}" target="_blank">'
                f"{svc}</a></td>"
            )
        else:
            svcs_html += f'<tr><td class="main">{svc}</td>'
        svcs_html += (
            f'</td><td class="main">{svcs_dict[svc][1]}</td>'
            f'</td><td class="main">{port_no}</td>'
            f'</td><td class="main">{svcs_dict[svc][3]}</td>'
            f'</td><td class="main"><a href="/service/{svc}/ns/{ns_name}">Description<a></td></tr>'
        )
    svcs_html += "</table>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Services", "body_html": Markup(svcs_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/service/{svc_name}/ns/{ns_name}")
def show_service(request: Request, ns_name: str, svc_name: str) -> Any:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param svc_name: K8S service name
    :return: template response
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Service</b>&nbsp;{svc_name}</p>"
    k8s = KubernetesInfo(_module_logger)
    pods_desc = k8s.get_service_desc(ns_name, svc_name)
    pod_html += f"<pre>{pods_desc}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Service", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/svc_status/{svc_name}/ns/{ns_name}")
def show_service_status(request: Request, ns_name: str, svc_name: str) -> Any:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param svc_name: K8S service name
    :return: template response
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Service</b>&nbsp;{svc_name}</p>"
    k8s = KubernetesInfo(_module_logger)
    svc_status = k8s.get_service_status(ns_name, svc_name)
    pod_html += f"<pre>{svc_status}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={
            "title": "Service status",
            "body_html": Markup(pod_html),
            "KUBE_NAMESPACE": ns_name,
        },
    )


@app.get("/pod/{pod_name}/ns/{ns_name}")
def show_pod(request: Request, ns_name: str, pod_name: str) -> Any:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    :return: template response
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Pod</b>&nbsp;{pod_name}</p>"
    k8s = KubernetesInfo(_module_logger)
    pods_dict = k8s.get_pods(ns_name, pod_name)
    _module_logger.debug("Pods: %s", pods_dict)
    if pod_name in pods_dict:
        pod_html += (
            f"<p><b>IP address</b>&nbsp;{pods_dict[pod_name][0]}</p>"
            f'<p/><a href="/pod_log/{pod_name}/ns/{ns_name}">Log</a>'
            f'<p/><a href="/pod_desc/{pod_name}/ns/{ns_name}">Description</a>'
        )
    else:
        pod_html += f"<p>Pod {pod_name} not found</p>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/pod_log/{pod_name}/ns/{ns_name}")
def show_pod_log(request: Request, ns_name: str, pod_name: str) -> Any:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    :return: template response
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Pod</b>&nbsp;{pod_name}</p>"
    k8s = KubernetesInfo(_module_logger)
    pods_log = k8s.get_pod_log(ns_name, pod_name)
    pod_html += f"<pre>{pods_log}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/pod_desc/{pod_name}/ns/{ns_name}")
def show_pod_desc(request: Request, ns_name: str, pod_name: str) -> Any:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    :return: template response
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Pod</b>&nbsp;{pod_name}</p>"
    k8s = KubernetesInfo(_module_logger)
    # pods_desc = k8s.get_pod_desc(ns_name, pod_name).to_str()
    pod_desc = k8s.get_pod_desc(ns_name, pod_name)
    _module_logger.info("Pod describe %s: %s", type(pod_desc), pod_desc)
    # return templates.TemplateResponse(
    #     request=request,
    #     name="index_ns.html",
    #     context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    # )
    # headers = {"X-Cat-Dog": "alone in the world", "Content-Language": "en-US"}
    # json_data = pod_desc.to_str().replace('"', "\\\"").replace("'", '"')
    pod_html += f"<pre>{pod_desc}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    )
    # try:
    #     # json_data = ast.literal_eval(json.dumps(pod_desc.to_str()))
    #     return JSONResponse(content=json.loads(json_data), headers=headers)
    #     # return JSONResponse(content=json_data, headers=headers)
    # except json.decoder.JSONDecodeError as j_err:
    #     _module_logger.warning("Invalid pod describe: %s\n%s", j_err, json_data)
    #     pod_html += f"<pre>{pod_desc}</pre>"
    #     # pod_html += f"<pre>{pod_desc.data}</pre>"
    #     return templates.TemplateResponse(
    #         request=request,
    #         name="index_ns.html",
    #         context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    #     )
