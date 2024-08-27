import json
import logging
import os
import socket
import tango
import tempfile
from contextlib import closing
from markupsafe import escape, Markup
from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.routing import Route
from starlette.responses import PlainTextResponse

from ska_tangoctl.k8s_info.get_k8s_info import KubernetesControl
from ska_tangoctl.tango_kontrol.tango_kontrol import get_namespaces_list
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tangoktl")
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
    "svc_ports": ["8765"],
}

DATABASEDS_NAME: str = str(CFG_DATA["databaseds_name"])
CLUSTER_DOMAIN: str = str(CFG_DATA["cluster_domain"])
DATABASEDS_PORT: int = int(str(CFG_DATA["databaseds_port"]))

app = FastAPI()
templates = Jinja2Templates(directory="templates")

tango_host: str | None = None

tango_hosts: dict = {}

app.mount("/static", StaticFiles(directory="static"), name="static")


def check_tango_host(ns_name: str) -> bool:
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


def check_tango_hosts():
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
def read_root(request: Request) -> templates.TemplateResponse:
    """
    This is the home page.

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
def show_namespaces(request: Request) -> templates.TemplateResponse:
    """
    Print K8S namespaces.

    :param request: HTTP connection
    :return: template tesponse
    """
    ns_list = get_namespaces_list(_module_logger, None)
    _module_logger.info("Read %d K8S namespaces", len(ns_list))
    ns_html = "<h2>Namespaces</h2><table>"
    for ns in ns_list:
        if ns not in tango_hosts:
            check_tango_host(ns)
        if tango_hosts[ns]:
            ns_html += f'<tr>\n<td><a href="/devices/{ns}">{ns}</a></td>'
        else:
            ns_html += f'<tr>\n<td>{ns}</td>'
        ns_html += f'<td><a href="/pods/{ns}">[Pods]</a></td>'
        ns_html += f'<td><a href="/services/{ns}">[Services]</a></td></tr>'
    ns_html += "<table>"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Namespaces", "body_html": Markup(ns_html)},
    )


@app.get("/tango_ns")
def show_tango_namespaces(request: Request) -> templates.TemplateResponse:
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
            ns_html += f'<tr>\n<td><a href="/devices/{ns}">{ns}</a></td>'
        else:
            ns_html += f'<tr>\n<td>{ns}</td>'
        ns_html += f'<td><a href="/pods/{ns}">[Pods]</a></td>'
        ns_html += f'<td><a href="/services/{ns}">[Services]</a></td></tr>'
    ns_html += "<table>"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Namespaces", "body_html": Markup(ns_html)},
    )


@app.get("/devices/{ns_name}")
def show_devices(request: Request, ns_name: str) -> templates.TemplateResponse:
    """
    Print Tango devices.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    """
    dev_html: str = f"<h2>Devices in namespace {ns_name}</h2>"
    set_tango_host(ns_name)
    try:
        devs = TangoctlDevicesBasic(
            _module_logger, False, True, False, False, CFG_DATA, None, "json"
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
            f'<tr><td><a href="/device/{dev_name}/ns/{ns_name}">'
            f"{device}</a></td>"
        )
        for header in table_headers[1:]:
            dev_html += f"<td>{dev[header]}</td>"
        dev_html += "</tr>\n"
    dev_html += "</table>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Devices", "body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/device/{dev_nm}/ns/{ns_name}")
def show_device(
    request: Request,
    ns_name: str,
    dev_nm: str
) -> templates.TemplateResponse:  # noqa: C901
    """
    Print specified Tango device.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param dev_nm: device name
    """
    dev_name = dev_nm.replace("+", "/")
    set_tango_host(ns_name)
    dev_html: str
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
        _module_logger.error("Tango connection to %s failed", tango_host)
        dev_html = f"<p>Tango connection to {tango_host} failed</p>"
        return templates.TemplateResponse(
            request=request,
            name="index_ns.html",
            context={"body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
        )
    dev_html = f"<h2>Device {dev_name}</h2><p>"

    dev_html += "</p>"
    device.read_config_all()
    device.read_attribute_value()
    device.read_command_value(
        CFG_DATA["run_commands"], CFG_DATA["run_commands_name"]  # type: ignore[arg-type]
    )
    device.read_property_value()
    with tempfile.TemporaryDirectory() as temp_dir:
        fd1, temp_file1_path = tempfile.mkstemp(dir=temp_dir)
        device.print_html_all(False, temp_file1_path)
        tmpf = open(temp_file1_path, "r")
        dev_html += tmpf.read()
        tmpf.close()
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Device", "body_html": Markup(dev_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/pods/{ns_name}")
def show_pods(request: Request, ns_name: str) -> templates.TemplateResponse:
    """
    Print all K8S pods.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    """
    k8s = KubernetesControl(_module_logger)
    pods_dict = k8s.get_pods(ns_name, None)
    _module_logger.info("Pods: %s", pods_dict)
    pods_html: str = f"<h2>Pods in namespace {ns_name}</h2>"
    pods_html += (
        "<table><tr><th>POD NAME</th><th>IP ADDRESS</th><th>&nbsp;</th><th>&nbsp;</th></tr>"
    )
    for pod in pods_dict:
        pods_html += (
            f'<tr><td><a href="/pod/{pod}/ns/{ns_name}">{pod}</a>'
            f"</td><td>{pods_dict[pod][0]}</td>"
            f'</td><td><a href="/pod_log/{pod}/ns/{ns_name}">Log</a></td>'
            f'</td><td><a href="/pod_desc/{pod}/ns/{ns_name}">Description</a></td></tr>'
        )
    pods_html += "</table>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Pods", "body_html": Markup(pods_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/services/{ns_name}")
def show_services(request: Request, ns_name: str) -> templates.TemplateResponse:
    """
    Print all K8S services.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    """
    k8s = KubernetesControl(_module_logger)
    svcs_dict = k8s.get_services(ns_name, None)
    _module_logger.info("Services: %s", svcs_dict)
    svcs_html: str = f"<h2>Services in namespace {ns_name}</h2>"
    svcs_html += (
        "<table><tr><th>POD NAME</th><th>IP ADDRESS</th><th>PORT</th>"
        "<th>PROTOCOL</th><th>&nbsp;</th></tr>"
    )
    for svc in svcs_dict:
        port_no: str = svcs_dict[svc][2]
        if port_no in CFG_DATA["svc_ports"]:
            svcs_html += (
                f'<tr><td><a href="http://{svcs_dict[svc][1]}:{port_no}" target="_blank">'
                f"{svc}</a></td>"
            )
        else:
            svcs_html += f'<tr><td>{svc}</td>'
        svcs_html += (
            f"</td><td>{svcs_dict[svc][1]}</td>"
            f"</td><td>{port_no}</td>"
            f"</td><td>{svcs_dict[svc][3]}</td>"
            f'</td><td><a href="/service/{svc}/ns/{ns_name}">Description<a></td></tr>'
        )
    svcs_html += "</table>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Services", "body_html": Markup(svcs_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/service/{svc_name}/ns/{ns_name}")
def show_service(request: Request, ns_name: str, svc_name: str) -> templates.TemplateResponse:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param svc_name: K8S service name
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Service</b>&nbsp;{svc_name}</p>"
    k8s = KubernetesControl(_module_logger)
    pods_desc = k8s.get_service_desc(ns_name, svc_name)
    pod_html += f"<pre>{pods_desc}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Service", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/svc_status/{svc_name}/ns/{ns_name}")
def show_service_status(request: Request, ns_name: str, svc_name: str) -> templates.TemplateResponse:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param svc_name: K8S service name
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Service</b>&nbsp;{svc_name}</p>"
    k8s = KubernetesControl(_module_logger)
    svc_status = k8s.get_service_status(ns_name, svc_name)
    pod_html += f"<pre>{svc_status}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={
            "title": "Service status", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name
        },
    )


@app.get("/pod/{pod_name}/ns/{ns_name}")
def show_pod(request: Request, ns_name: str, pod_name: str) -> templates.TemplateResponse:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Pod</b>&nbsp;{pod_name}</p>"
    k8s = KubernetesControl(_module_logger)
    pods_dict = k8s.get_pods(ns_name, pod_name)
    _module_logger.info(pods_dict)
    if pod_name in pods_dict:
        pod_html += f"<p><b>IP address</b>&nbsp;{pods_dict[pod_name][0]}</p>"
    else:
        pod_html += f"<p>Pod {pod_name} not found</p>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/pod_log/{pod_name}/ns/{ns_name}")
def show_pod_log(request: Request, ns_name: str, pod_name: str) -> templates.TemplateResponse:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Pod</b>&nbsp;{pod_name}</p>"
    k8s = KubernetesControl(_module_logger)
    pods_log = k8s.get_pod_log(ns_name, pod_name)
    pod_html += f"<pre>{pods_log}</pre>"
    return templates.TemplateResponse(
        request=request,
        name="index_ns.html",
        context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    )


@app.get("/pod_desc/{pod_name}/ns/{ns_name}")
def show_pod_desc(request: Request, ns_name: str, pod_name: str) -> templates.TemplateResponse:
    """
    Print specified K8S pod.

    :param request: HTTP connection
    :param ns_name: K8S namespace
    :param pod_name: K8S pod name
    """
    pod_html = f"<p><b>Namepace</b>&nbsp;{ns_name}</p>"
    pod_html += f"<p><b>Pod</b>&nbsp;{pod_name} log</p>"
    k8s = KubernetesControl(_module_logger)
    pods_desc = k8s.get_pod_desc(ns_name, pod_name).to_str()
    _module_logger.info(pods_desc)
    pod_html += f"<pre>{pods_desc}</pre>"
    # return templates.TemplateResponse(
    #     request=request,
    #     name="index_ns.html",
    #     context={"title": "Pod", "body_html": Markup(pod_html), "KUBE_NAMESPACE": ns_name},
    # )
    headers = {"X-Cat-Dog": "alone in the world", "Content-Language": "en-US"}
    return JSONResponse(content=json.loads(pods_desc), headers=headers)
