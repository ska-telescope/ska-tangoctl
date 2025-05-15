#!/usr/bin/env python
"""Read all information about Tango devices."""

import getopt
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any

import tango

from ska_tangoctl import __version__
from ska_tangoctl.tango_control.disp_action import (
    TANGOCTL_CLASS,
    TANGOCTL_FULL,
    TANGOCTL_LIST,
    TANGOCTL_SHORT,
)
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevices
from ska_tangoctl.tango_control.tango_database import TangoHostInfo, get_tango_hosts
from ska_tangoctl.tango_control.tango_device_tree import device_tree
from ska_tangoctl.tango_control.test_tango_device import TestTangoDevice
from ska_tangoctl.tango_kontrol.tango_kontrol import TangoControlKubernetes, show_namespaces
from ska_tangoctl.tango_kontrol.tangoktl_config import read_tangoktl_config
from ska_tangoctl.tla_jargon.tla_jargon import print_jargon

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.WARNING)


def read_tango_host(  # noqa: C901
    ntango: int,
    ntangos: int,
    ns_name: str | None,
    cfg_data: Any,
    disp_action: int,
    evrythng: bool,
    fmt: str,
    output_file: str | None,
    quiet_mode: bool,
    reverse: bool,
    tango_host: TangoHostInfo,
    tgo_attrib: str | None,
    tgo_cmd: str | None,
    tgo_name: str | None,
    tgo_prop: str | None,
    uniq_cls: bool,
) -> int:
    """
    Read info from Tango host.

    :param cfg_data: config data

    :param ntango: index number,
    :param ntangos: index count,
    :param ns_name: K8S namespace
    :param disp_action: display output format
    :param evrythng: include all devices
    :param fmt: format
    :param output_file: output file name
    :param quiet_mode: do not show progress bars
    :param reverse: sort in reverse order
    :param tango_host: Tango host and port
    :param tgo_attrib: attribute name
    :param tgo_cmd: command name
    :param tgo_name: devicee name
    :param tgo_prop: property name
    :param uniq_cls: list one device per class
    :return: error condition
    """
    rc: int = 0

    pid: int = os.fork()
    if pid == 0:
        _module_logger.info("Processing %s", ns_name)
        start_now = datetime.now().strftime("%H:%M:%S")
        if fmt == "json" and ntango == 1 and disp_action in (TANGOCTL_FULL, 3):
            print("[")
        elif fmt == "json" and ntango == 1:
            print("{")
            print(f'"start_time": "{start_now}",')
            print('"devices":')
        else:
            pass
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data, ns_name)
        start_time = time.perf_counter()
        rc = tangoktl.run_info(
            uniq_cls,
            output_file,
            fmt,
            evrythng,
            quiet_mode,
            reverse,
            disp_action,
            tgo_name,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
            0,
        )
        end_time = time.perf_counter()
        end_now = datetime.now().strftime("%H:%M:%S")
        if fmt == "json" and ntango == ntangos and disp_action in (TANGOCTL_FULL, TANGOCTL_SHORT):
            print("]")
        elif fmt == "json" and ntango == ntangos:
            print(f',"end_time": "{end_now}"')
            print(f',"elapsed_time": "{end_time - start_time}"')
            print("}")
        elif fmt == "json":
            print("  ,")
        else:
            pass
        sys.exit(rc)
    else:
        try:
            os.waitpid(pid, 0)
        except OSError:
            pass
        _module_logger.info("Processing %s finished (PID %d)", ns_name, pid)

    return rc


def read_tango_attributes(cfg_data: Any) -> int:
    """
    Compile unique Tango attributes.

    :param cfg_data: configuration data
    :return: error condition
    """
    rc: int = 0
    devs: TangoctlDevices
    tango_devs: dict = {}
    try:
        devs = TangoctlDevices(
            _module_logger,
            True,
            True,
            False,
            False,
            cfg_data,
            None,
            None,
            None,
            None,
            None,
            "html",
        )
        devs.read_device_values()
        tango_devs = devs.make_json()
        _module_logger.error("Devices:> %s", tango_devs)
        the_attribs = devs.read_attribute_names()
        # TODO finish this thing
        for attr_name in the_attribs:
            if attr_name not in tango_devs:
                pass
            # tango_devs[attr_name] =
    except tango.ConnectionFailed as terr:
        err_msg = terr.args[0].desc.strip()
        _module_logger.error("%s", err_msg)
    except KeyboardInterrupt:
        pass
    return rc


def main() -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :return: error condition
    """
    # TODO Feature to dispaly a pod, not implemented yet
    # kube_pod: str | None = None
    disp_action: int = 0
    dev_admin: int | None = None
    dev_off: bool = False
    dev_on: bool = False
    dev_sim: int | None = None
    dev_standby: bool = False
    dev_status: bool = False
    dry_run: bool = False
    evrythng: bool = False
    fmt: str = "txt"
    input_file: str | None = None
    json_dir: str | None = None
    kube_namespace: str | None = None
    output_file: str | None = None
    quiet_mode: bool = False
    rc: int
    show_attrib: bool = False
    show_command: bool = False
    show_dev: bool = False
    show_jargon: bool = False
    show_ns: bool = False
    show_pod: bool = False
    show_tango: bool = False
    show_tree: bool = False
    show_version: bool = False
    reverse: bool = False
    tango_host: str | None = None
    tango_port: int = 10000
    tgo_attrib: str | None = None
    tgo_cmd: str | None = None
    tangoktl: TangoControlKubernetes
    # TODO Feature to search by input type, not implemented yet
    tgo_in_type: str | None = None
    tgo_name: str | None = None
    tgo_prop: str | None = None
    tgo_value: str | None = None
    uniq_cls: bool = False
    use_fqdn: bool = True

    # Read configuration
    cfg_data: Any = read_tangoktl_config(_module_logger)
    cfg_name: str | None = None

    databaseds_name: str = cfg_data["databaseds_name"]
    cluster_domain: str = cfg_data["cluster_domain"]
    databaseds_port: int = cfg_data["databaseds_port"]

    try:
        opts, _args = getopt.getopt(
            sys.argv[1:],
            "abcdefhijklmnoqrstuvwxyVA:C:H:D:I:J:K:p:O:P:Q:X:T:W:X:",
            [
                "class",
                "cmd",
                "dry-run",
                "everything",
                "full",
                "help",
                "html",
                "ip",
                "json",
                "list",
                "md",
                "off",
                "on",
                "quiet",
                "reverse",
                "standby",
                "status",
                "short",
                "show-acronym",
                "show-db",
                "show-dev",
                "show-ns",
                "show-pod",
                "tree",
                "unique",
                "version",
                "yaml",
                "admin=",
                "attribute=",
                "cfg=",
                "command=",
                "device=",
                "host=",
                "input=",
                "json-dir=",
                "k8s-ns=",
                "k8s-pod=",
                "output=",
                "port=",
                "property=",
                "simul=",
                "type=",
                "value=",
            ],
        )
    except getopt.GetoptError as opt_err:
        print(f"Could not read command line: {opt_err}")
        return 1

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            tangoktl = TangoControlKubernetes(_module_logger, cfg_data, None)
            tangoktl.usage(os.path.basename(sys.argv[0]))
            sys.exit(1)
        elif opt == "-a":
            show_attrib = True
        elif opt in ("--attribute", "-A"):
            tgo_attrib = arg
        elif opt in ("--class", "-d"):
            disp_action = TANGOCTL_CLASS  # 5
        elif opt in ("--cfg", "-X"):
            cfg_name = arg
        elif opt in ("--cmd", "-c"):
            show_command = True
        elif opt in ("--command", "-C"):
            tgo_cmd = arg.lower()
        elif opt in ("--device", "-D"):
            tgo_name = arg.lower()
        elif opt in ("--dry-run", "-n"):
            # TODO Undocumented and unused feature for dry runs
            dry_run = True
        elif opt in ("--everything", "-e"):
            evrythng = True
        elif opt in ("--full", "-f"):
            disp_action = TANGOCTL_FULL  # 1
        elif opt in ("--host", "-H"):
            tango_host = arg
        elif opt in ("--html", "-w"):
            fmt = "html"
        elif opt in ("--input", "-I"):
            input_file = arg
        elif opt in ("--ip", "-i"):
            use_fqdn = False
        elif opt in ("--json", "-j"):
            fmt = "json"
        elif opt in ("--list", "-l"):
            disp_action = TANGOCTL_LIST  # 4
        elif opt in ("--json-dir", "-J"):
            json_dir = arg
        elif opt in ("--md", "-m"):
            fmt = "md"
        elif opt in ("--k8s-ns", "-K"):
            kube_namespace = arg
        # TODO make this work
        # elif opt in ("--k8s-pod", "-Q"):
        #     kube_pod = arg
        elif opt in ("--property", "-P"):
            tgo_prop = arg.lower()
        elif opt == "--off":
            dev_off = True
        elif opt == "--on":
            dev_on = True
        elif opt in ("--output", "-O"):
            output_file = arg
        elif opt in ("--port", "-p"):
            tango_port = int(arg)
        elif opt in ("--quiet", "-q"):
            quiet_mode = True
            _module_logger.setLevel(logging.ERROR)
        elif opt in ("--reverse", "-r"):
            reverse = True
        elif opt in ("--short", "-s"):
            disp_action = TANGOCTL_FULL
        elif opt in ("--show-db", "-t"):
            show_tango = True
        elif opt == "--show-dev":
            show_dev = True
        elif opt in ("--show-ns", "-k"):
            show_ns = True
        elif opt in ("--show-pod", "-x"):
            show_pod = True
        elif opt == "--simul":
            dev_sim = int(arg)
        elif opt == "--standby":
            dev_standby = True
        elif opt == "--status":
            dev_status = True
        elif opt in ("--tree", "-b"):
            show_tree = True
        # TODO Feature to search by input type not implemented yet
        elif opt in ("--type", "-T"):
            tgo_in_type = arg.lower()
            _module_logger.info("Input type %s not implemented", tgo_in_type)
        elif opt in ("--unique", "-u"):
            uniq_cls = True
        elif opt == "-v":
            _module_logger.setLevel(logging.INFO)
        elif opt == "-V":
            _module_logger.setLevel(logging.DEBUG)
        elif opt in ("--value", "-W"):
            tgo_value = str(arg)
        elif opt == "--version":
            show_version = True
        elif opt in ("--yaml", "-y"):
            fmt = "yaml"
        else:
            _module_logger.error("Invalid option %s", opt)
            return 1

    if show_version:
        print(f"{os.path.basename(sys.argv[0])} version {__version__}")
        return 0

    if cfg_name is not None:
        cfg_data = read_tangoktl_config(_module_logger, cfg_name)

    if show_jargon:
        print_jargon()
        return 0

    if show_ns:
        show_namespaces(_module_logger, output_file, fmt, kube_namespace, reverse)
        return 0

    if show_pod:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data, kube_namespace)
        tangoktl.show_pods(kube_namespace, quiet_mode, output_file, fmt)
        return 0

    if json_dir:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data, kube_namespace)
        tangoktl.read_input_files(json_dir, quiet_mode)
        return 0

    tango_hosts: list[TangoHostInfo]
    tango_hosts = get_tango_hosts(
        _module_logger,
        tango_host,
        kube_namespace,
        databaseds_name,
        cluster_domain,
        databaseds_port,
        use_fqdn,
    )

    if len(tango_hosts) > 1:
        quiet_mode = True

    dut: TestTangoDevice

    _module_logger.info("Use Tango hosts %s", tango_hosts)
    thost: TangoHostInfo
    rc = 0
    ntango: int = 0
    ntangos: int = len(tango_hosts)
    for thost in tango_hosts:
        ntango += 1
        os.environ["TANGO_HOST"] = str(thost.tango_host)
        _module_logger.info("Set TANGO_HOST to %s", thost.tango_host)

        if show_tango:
            print(f"TANGO_HOST={thost.tango_fqdn}:{thost.tango_port}")
            if thost.tango_ip is not None:
                print(f"TANGO_HOST={thost.tango_ip}:{thost.tango_port}")
            print()
            continue

        if show_dev:
            _module_logger.info("Tango devices for host %s", thost)
            continue

        if show_tree:
            verbose_tree: bool = False
            if disp_action in (TANGOCTL_FULL, TANGOCTL_SHORT):
                verbose_tree = True
            device_tree(include_dserver=evrythng, verbose=verbose_tree)
            continue

        if input_file is not None:
            tangoktl = TangoControlKubernetes(_module_logger, cfg_data, None)
            tangoktl.read_input_file(input_file, tgo_name, dry_run)
            continue

        dev_test: bool = False
        if (
            dev_off
            or dev_on
            or dev_sim
            or dev_standby
            or dev_status
            or show_command
            or show_attrib
        ):
            dev_test = True
        if dev_admin is not None:
            dev_test = True
        if dev_test and tgo_name:
            dut = TestTangoDevice(_module_logger, tgo_name)
            if dut.dev is None:
                print(f"[FAILED] could not open device {tgo_name}")
                return 1
            rc += dut.run_test(
                dry_run,
                dev_admin,
                dev_off,
                dev_on,
                dev_sim,
                dev_standby,
                dev_status,
                show_command,
                show_attrib,
                tgo_attrib,
                tgo_name,
                tango_port,
            )
            continue

        if show_attrib:
            pass

        if tgo_value and tgo_attrib and tgo_name:
            tangoktl = TangoControlKubernetes(_module_logger, cfg_data, thost.ns_name)
            rc = tangoktl.set_value(tgo_name, quiet_mode, reverse, tgo_attrib, tgo_value)
            continue

        rc += read_tango_host(
            ntango,
            ntangos,
            thost.ns_name,
            cfg_data,
            disp_action,
            evrythng,
            fmt,
            output_file,
            quiet_mode,
            reverse,
            thost,
            tgo_attrib,
            tgo_cmd,
            tgo_name,
            tgo_prop,
            uniq_cls,
        )
    return rc


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
