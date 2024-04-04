#!/usr/bin/env python
"""Read all information about Tango devices."""

import getopt
import json
import logging
import os
import sys
from typing import Any, TextIO

from ska_mid_itf_engineering_tools import __version__
from ska_mid_itf_engineering_tools.tango_control.ska_jargon import print_jargon
from ska_mid_itf_engineering_tools.tango_control.test_tango_device2 import TestTangoDevice
from ska_mid_itf_engineering_tools.tango_kontrol.tango_kontrol import TangoControlKubernetes

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.WARNING)


def main() -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :return: error condition
    """
    kube_namespace: str | None = None
    # TODO Feature to dispaly a pod, not implemented yet
    # kube_pod: str | None = None
    dry_run: bool = False
    tgo_name: str | None = None
    dev_on: bool = False
    dev_off: bool = False
    dev_standby: bool = False
    dev_status: bool = False
    dev_test: bool = False
    dev_admin: int | None = None
    dev_sim: int | None = None
    disp_action: int = 0
    evrythng: bool = False
    input_file: str | None = None
    json_dir: str | None = None
    output_file: str | None = None
    quiet_mode: bool = False
    show_attrib: bool = False
    show_command: bool = False
    show_jargon: bool = False
    show_ns: bool = False
    show_pod: bool = False
    show_tango: bool = False
    show_version: bool = False
    tgo_attrib: str | None = None
    tgo_cmd: str | None = None
    # TODO Feature to search by input type, not implemented yet
    tgo_in_type: str | None = None
    tgo_prop: str | None = None
    tgo_value: str | None = None
    tango_host: str | None = None
    tango_port: int = 10000
    uniq_cls: bool = False
    fmt: str = "txt"

    # Read configuration file
    cfg_name: str | bytes = os.path.splitext(sys.argv[0])[0] + ".json"
    try:
        cfg_file: TextIO = open(cfg_name)
    except FileNotFoundError:
        cfg_name = "src/ska_mid_itf_engineering_tools/tango_kontrol/tangoktl.json"
        cfg_file = open(cfg_name)
    cfg_data: Any = json.load(cfg_file)
    cfg_file.close()

    databaseds_name: str = cfg_data["databaseds_name"]
    cluster_domain: str = cfg_data["cluster_domain"]
    databaseds_port: int = cfg_data["databaseds_port"]

    try:
        opts, _args = getopt.getopt(
            sys.argv[1:],
            "acdefhjklmnoqstuvwxyVA:C:H:D:I:J:K:p:O:P:X:T:W:X:",
            [
                "class",
                "cmd",
                "dry-run",
                "everything",
                "full",
                "help",
                "html",
                "json",
                "list",
                "md",
                "off",
                "on",
                "quiet",
                "standby",
                "status",
                "short",
                "show-acronym",
                "show-db",
                "show-dev",
                "show-ns",
                "show-pod",
                "unique",
                "version",
                "yaml",
                "admin=",
                "attribute=",
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
            tangoctl = TangoControlKubernetes(_module_logger, cfg_data)
            tangoctl.usage(os.path.basename(sys.argv[0]))
            sys.exit(1)
        elif opt == "-a":
            show_attrib = True
        elif opt in ("--attribute", "-A"):
            tgo_attrib = arg
        elif opt in ("--class", "-d"):
            disp_action = 5
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
            disp_action = 1
        elif opt in ("--host", "-H"):
            tango_host = arg
        elif opt in ("--html", "-w"):
            fmt = "html"
        elif opt in ("--input", "-I"):
            input_file = arg
        elif opt in ("--json", "-j"):
            fmt = "json"
        elif opt in ("--list", "-l"):
            disp_action = 4
        elif opt in ("--json-dir", "-J"):
            json_dir = arg
        elif opt in ("--md", "-m"):
            fmt = "md"
        elif opt in ("--k8s-ns", "-K"):
            kube_namespace = arg
        # TODO make this work
        # elif opt in ("--k8s-pod", "-X"):
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
        elif opt in ("--short", "-s"):
            disp_action = 3
        elif opt in ("--show-db", "-t"):
            show_tango = True
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
        elif opt == "--test":
            dev_test = True
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

    if show_jargon:
        print_jargon()
        return 0

    if show_ns:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.show_namespaces(output_file, fmt)
        return 0

    if show_pod:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.show_pods(kube_namespace, quiet_mode, output_file, fmt)
        return 0

    if json_dir:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.read_input_files(json_dir, quiet_mode)
        return 0

    if kube_namespace is None and tango_host is None:
        tango_host = os.getenv("TANGO_HOST")
        if tango_host is None:
            kube_namespace = os.getenv("KUBE_NAMESPACE")
            if kube_namespace is None:
                print(
                    "No Kubernetes namespace or Tango database server specified,"
                    " TANGO_HOST and KUBE_NAMESPACE not set"
                )
                return 1

    if tango_host is None:
        tango_fqdn = f"{databaseds_name}.{kube_namespace}.svc.{cluster_domain}"
        tango_host = f"{tango_fqdn}:{databaseds_port}"
    elif ":" in tango_host:
        tango_fqdn = tango_host.split(":")[0]
    else:
        tango_fqdn = tango_host
        tango_host = f"{tango_fqdn}:{databaseds_port}"

    _module_logger.info("Use Tango host %s", tango_host)

    os.environ["TANGO_HOST"] = tango_host
    _module_logger.info("Set TANGO_HOST to %s", tango_host)

    if show_tango:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.check_tango(tango_fqdn, quiet_mode, tango_port)
        return 0

    if input_file is not None:
        tangoctl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoctl.read_input_file(input_file, tgo_name, dry_run)
        return 0

    if dev_off or dev_on or dev_sim or dev_standby or dev_status or show_command or show_attrib:
        dev_test = True
    if dev_admin is not None:
        dev_test = True
    if dev_test and tgo_name:
        dut = TestTangoDevice(_module_logger, tgo_name)
        if dut.dev is None:
            print(f"[FAILED] could not open device {tgo_name}")
            return 1
        rc: int = dut.run_test(
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
        return rc

    if tgo_value and tgo_attrib and tgo_name:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        rc = tangoktl.set_value(tgo_name, quiet_mode, tgo_attrib, tgo_value)
        return rc

    tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
    rc = tangoktl.run_info(
        uniq_cls,
        output_file,
        fmt,
        evrythng,
        quiet_mode,
        disp_action,
        tgo_name,
        tgo_attrib,
        tgo_cmd,
        tgo_prop,
        tango_port,
    )
    return rc


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
