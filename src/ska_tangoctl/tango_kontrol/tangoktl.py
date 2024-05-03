#!/usr/bin/env python
"""Read all information about Tango devices."""

import getopt
import json
import logging
import os
import sys
from typing import Any, TextIO

from ska_tangoctl import __version__
from ska_tangoctl.tango_control.tango_device_tree import device_tree
from ska_tangoctl.tango_control.test_tango_device import TestTangoDevice
from ska_tangoctl.tango_kontrol.tango_kontrol import TangoControlKubernetes
from ska_tangoctl.tango_kontrol.tangoktl_config import TANGOKTL_CONFIG
from ska_tangoctl.tla_jargon.tla_jargon import print_jargon

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.WARNING)


def read_tango_host(  # noqa: C901
    cfg_data: Any,
    cluster_domain: str,
    databaseds_name: str,
    databaseds_port: int,
    dev_admin: int | None,
    dev_off: bool,
    dev_on: bool,
    dev_sim: int | None,
    dev_standby: bool,
    dev_status: bool,
    disp_action: int,
    dry_run: bool,
    evrythng: bool,
    fmt: str,
    input_file: str | None,
    kube_namespace: str | None,
    output_file: str | None,
    quiet_mode: bool,
    reverse: bool,
    show_attrib: bool,
    show_command: bool,
    show_tango: bool,
    show_tree: bool,
    tango_host: str | None,
    tango_port: int,
    tgo_attrib: str | None,
    tgo_cmd: str | None,
    tgo_name: str | None,
    tgo_prop: str | None,
    tgo_value: str | None,
    uniq_cls: bool,
) -> int:
    """
    Read info from Tango host.

    :param cfg_data: config data
    :param cluster_domain: domain name
    :param databaseds_name: database device
    :param databaseds_port: database port
    :param dev_admin: device admin value
    :param dev_off: turn device off
    :param dev_on: turn device on
    :param dev_sim: device simulation
    :param dev_standby: set device to standby
    :param dev_status: get device status
    :param disp_action: display output format
    :param dry_run: dry run
    :param evrythng: include all devices
    :param fmt: format
    :param input_file: JSON file to read values from
    :param kube_namespace: K8S namespace
    :param output_file: output file name
    :param quiet_mode: do not show progress bars
    :param reverse: sort in reverse order
    :param show_attrib: display device attributes
    :param show_command: display commands
    :param show_tango: display Tango stuff
    :param show_tree:  display device tree
    :param tango_host: Tango host name
    :param tango_port: Tango host port
    :param tgo_attrib: attribute name
    :param tgo_cmd: command name
    :param tgo_name: devicee name
    :param tgo_prop: property name
    :param tgo_value: value for attribute, command or property
    :param uniq_cls: list one device per class
    :return: error condition
    """
    rc: int = 0
    tango_fqdn: str
    dut: TestTangoDevice

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

    if show_tree:
        verbose_tree: bool = False
        if disp_action in (1, 3):
            verbose_tree = True
        device_tree(include_dserver=evrythng, verbose=verbose_tree)
        return 0

    if show_tango:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.check_tango(tango_fqdn, quiet_mode, tango_port)
        return 0

    if input_file is not None:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.read_input_file(input_file, tgo_name, dry_run)
        return 0

    dev_test: bool = False
    if dev_off or dev_on or dev_sim or dev_standby or dev_status or show_command or show_attrib:
        dev_test = True
    if dev_admin is not None:
        dev_test = True
    if dev_test and tgo_name:
        dut = TestTangoDevice(_module_logger, tgo_name)
        if dut.dev is None:
            print(f"[FAILED] could not open device {tgo_name}")
            return 1
        rc = dut.run_test(
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
        rc = tangoktl.set_value(tgo_name, quiet_mode, reverse, tgo_attrib, tgo_value)
        return rc

    tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
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
        tango_port,
    )
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

    # Read configuration
    cfg_data: Any = TANGOKTL_CONFIG
    cfg_name: str | None = None

    databaseds_name: str = cfg_data["databaseds_name"]
    cluster_domain: str = cfg_data["cluster_domain"]
    databaseds_port: int = cfg_data["databaseds_port"]

    try:
        opts, _args = getopt.getopt(
            sys.argv[1:],
            "abcdefhjklmnoqrstuvwxyVA:C:H:D:I:J:K:p:O:P:Q:X:T:W:X:",
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
            tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
            tangoktl.usage(os.path.basename(sys.argv[0]))
            sys.exit(1)
        elif opt == "-a":
            show_attrib = True
        elif opt in ("--attribute", "-A"):
            tgo_attrib = arg
        elif opt in ("--class", "-d"):
            disp_action = 5
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
        elif opt in ("--reverse", "-r"):
            reverse = True
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

    if cfg_name is not None:
        try:
            _module_logger.info("Read config file %s", cfg_name)
            cfg_file: TextIO = open(cfg_name)
            cfg_data = json.load(cfg_file)
            cfg_file.close()
        except FileNotFoundError:
            _module_logger.error("Could not read config file %s", cfg_name)
            return 1

    if show_version:
        print(f"{os.path.basename(sys.argv[0])} version {__version__}")
        return 0

    if show_jargon:
        print_jargon()
        return 0

    if show_ns:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.show_namespaces(output_file, fmt, kube_namespace, reverse)
        return 0

    if show_pod:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.show_pods(kube_namespace, quiet_mode, output_file, fmt)
        return 0

    if json_dir:
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        tangoktl.read_input_files(json_dir, quiet_mode)
        return 0

    kube_namespaces: list
    if kube_namespace is None:
        kube_namespaces = [None]
    elif "," in kube_namespace:
        kube_namespaces = kube_namespace.split(",")
    else:
        kube_namespaces = []
        # pat = re.compile(kube_namespace)
        tangoktl = TangoControlKubernetes(_module_logger, cfg_data)
        namespaces_list: list = tangoktl.get_namespaces_list(kube_namespace)
        for namespace in namespaces_list:
            # if re.fullmatch(pat, namespace):
            #     kube_namespaces.append(namespace)
            kube_namespaces.append(namespace)
        # kube_namespaces = [kube_namespace]

    if len(kube_namespaces) > 1:
        quiet_mode = True

    rc = 0
    # random.shuffle(kube_namespaces)
    _module_logger.info(
        "Process %d namespaces: %s", len(kube_namespaces), ",".join(kube_namespaces)
    )
    ns_done = []
    for kube_namespace in kube_namespaces:
        print()
        if kube_namespace in ns_done:
            continue
        # Fork a child process
        processid = os.fork()
        # print(processid)
        if processid > 0:
            # Parent process
            # print("Process ID:", os.getpid())
            _module_logger.info("Wait for process ID %d", processid)
            # os.waitid(os.P_PID, processid, os.WEXITED)
            # os.wait()
            # _module_logger.info("Process ID %d finished", processid)
        else:
            # Child process
            _module_logger.warning("Process %d for namespace %s", os.getpid(), kube_namespace)
            # print("Parent's process ID:", os.getppid())
            rc += read_tango_host(
                cfg_data,
                cluster_domain,
                databaseds_name,
                databaseds_port,
                dev_admin,
                dev_off,
                dev_on,
                dev_sim,
                dev_standby,
                dev_status,
                disp_action,
                dry_run,
                evrythng,
                fmt,
                input_file,
                kube_namespace,
                output_file,
                quiet_mode,
                reverse,
                show_attrib,
                show_command,
                show_tango,
                show_tree,
                tango_host,
                tango_port,
                tgo_attrib,
                tgo_cmd,
                tgo_name,
                tgo_prop,
                tgo_value,
                uniq_cls,
            )
            # os.waitpid(processid, os.WEXITED)
            _module_logger.info("Processed namespace %s", kube_namespace)
            print()
            # return 0
        ns_done.append(kube_namespace)
    return rc


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
