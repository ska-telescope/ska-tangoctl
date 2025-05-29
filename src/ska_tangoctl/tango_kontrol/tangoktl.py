#!/usr/bin/env python
"""Read all information about Tango devices."""

import getopt
import logging
import os
import sys
from typing import Any

from ska_tangoctl import __version__
from ska_tangoctl.tango_control.disp_action import DispAction
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
    show_attrib: bool,
    show_cmd: bool,
    show_prop: bool,
    show_status: dict,
    ntango: int,
    ntangos: int,
    ns_name: str | None,
    cfg_data: Any,
    disp_action: DispAction,
    evrythng: bool,
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

    :param show_attrib: flag to read attributes
    :param show_cmd: flag to read commands
    :param show_prop: flag to read properties
    :param show_status: flag to read status
    :param ntango: index number,
    :param ntangos: index count
    :param ns_name: K8S namespace
    :param cfg_data: config data
    :param disp_action: display output format
    :param evrythng: include all devices
    :param output_file: output file name
    :param quiet_mode: do not show progress bars
    :param reverse: sort in reverse order
    :param tango_host: Tango host and port
    :param tgo_attrib: attribute name
    :param tgo_cmd: command name
    :param tgo_name: device name
    :param tgo_prop: property name
    :param uniq_cls: list one device per class
    :return: error condition
    """
    rc: int = 0

    # Fork just in case,  so that ctrl-C will work
    pid: int = os.fork()
    if pid == 0:
        _module_logger.info("Processing namespace %s", ns_name)
        if (
            disp_action.check(DispAction.TANGOCTL_JSON)
            and ntango == 1
            and disp_action.check(DispAction.TANGOCTL_SHORT)
        ):
            print("[")
        elif disp_action.check(DispAction.TANGOCTL_JSON) and ntango == 1:
            pass
        else:
            pass
        tangoktl = TangoControlKubernetes(
            _module_logger, show_attrib, show_cmd, show_prop, show_status, cfg_data, ns_name
        )
        # Do the actual reading
        rc = tangoktl.run_info(
            uniq_cls,
            output_file,
            evrythng,
            quiet_mode,
            reverse,
            disp_action,
            tgo_name,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
            0,
            str(tango_host.ns_name),
        )
        # TODO this formatting stuff should not be here
        if (
            disp_action.check(DispAction.TANGOCTL_JSON)
            and ntango == ntangos
            and disp_action.check(DispAction.TANGOCTL_SHORT)
        ):
            print("]")
        elif disp_action.check(DispAction.TANGOCTL_JSON) and ntango == ntangos:
            pass
        elif disp_action.check(DispAction.TANGOCTL_JSON):
            print(",")
        else:
            pass
        _module_logger.info("Processed namespace %s", ns_name)
        sys.exit(rc)
    else:
        try:
            os.waitpid(pid, 0)
        except OSError:
            pass
        _module_logger.info("Processing %s finished (PID %d)", ns_name, pid)

    return rc


def main() -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :return: error condition
    """
    # TODO Feature to display a pod, not implemented yet
    # kube_pod: str | None = None
    dev_admin: int | None = None
    dev_off: bool = False
    dev_on: bool = False
    dev_sim: int | None = None
    dev_standby: bool = False
    disp_action: DispAction = DispAction(0)
    dry_run: bool = False
    evrythng: bool = False
    input_file: str | None = None
    json_dir: str | None = None
    kube_namespace: str | None = None
    output_file: str | None = None
    quiet_mode: bool = False
    rc: int
    reverse: bool = False
    show_attrib: bool = False
    show_cmd: bool = False
    show_dev: bool = False
    show_jargon: bool = False
    show_ns: bool = False
    show_pod: bool = False
    show_prop: bool = False
    show_status: dict = {}
    show_tango: bool = False
    show_tree: bool = False
    show_version: bool = False
    tango_host: str | None = None
    tango_port: int = 10000
    tangoktl: TangoControlKubernetes
    tgo_attrib: str | None = None
    tgo_cmd: str | None = None
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

    # Read command line options
    try:
        opts, _args = getopt.getopt(
            sys.argv[1:],
            "abcdefghijklmnopqrstuvwxyVA:C:H:D:I:J:K:p:O:P:Q:X:T:W:X:",
            [
                "class",
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
                "show-attribute",
                "show-command",
                "show-db",
                "show-dev",
                "show-namespace",
                "show-pod",
                "show-property",
                "tree",
                "txt",
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
                "namespace=",
                "pod=",
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

    # Set up command line options
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            tangoktl = TangoControlKubernetes(_module_logger, True, True, True, {}, cfg_data, None)
            tangoktl.usage(os.path.basename(sys.argv[0]))
            sys.exit(1)
        elif opt in ("--attribute", "-A"):
            tgo_attrib = arg
            show_attrib = True
        elif opt in ("--class", "-d"):
            disp_action.value = DispAction.TANGOCTL_CLASS  # 5
        elif opt in ("--cfg", "-X"):
            cfg_name = arg
        elif opt in ("--command", "-C"):
            tgo_cmd = arg.lower()
            show_cmd = True
        elif opt in ("--device", "-D"):
            tgo_name = arg.lower()
        elif opt in ("--dry-run", "-n"):
            # TODO Undocumented and unused feature for dry runs
            dry_run = True
        elif opt in ("--everything", "-e"):
            evrythng = True
            show_attrib = True
            show_cmd = True
            show_prop = True
        elif opt in ("--full", "-f"):
            disp_action.value = DispAction.TANGOCTL_FULL
        elif opt in ("--host", "-H"):
            tango_host = arg
        elif opt in ("--html", "-w"):
            disp_action.value = DispAction.TANGOCTL_HTML
        elif opt in ("--input", "-I"):
            input_file = arg
        elif opt in ("--ip", "-i"):
            use_fqdn = False
        elif opt in ("--json", "-j"):
            disp_action.value = DispAction.TANGOCTL_JSON
        elif opt in ("--list", "-l"):
            disp_action.value = DispAction.TANGOCTL_LIST
        elif opt in ("--json-dir", "-J"):
            json_dir = arg
        elif opt in ("--md", "-m"):
            disp_action.value = DispAction.TANGOCTL_MD
        elif opt in ("--namespace", "-K"):
            kube_namespace = arg
        # TODO make this work
        # elif opt in ("--pod", "-Q"):
        #     kube_pod = arg
        elif opt in ("--property", "-P"):
            tgo_prop = arg.lower()
            show_prop = True
        elif opt == "--off":
            dev_off = True
        elif opt == "--on":
            dev_on = True
        elif opt in ("--output", "-O"):
            output_file = arg
        elif opt in ("--port", "-P"):
            tango_port = int(arg)
        elif opt in ("--quiet", "-q"):
            quiet_mode = True
            _module_logger.setLevel(logging.ERROR)
        elif opt in ("--reverse", "-r"):
            reverse = True
        elif opt in ("--short", "-s"):
            disp_action.value = DispAction.TANGOCTL_SHORT
        elif opt in ("--show-attribute", "-a"):
            show_attrib = True
        elif opt in ("--show-command", "-c"):
            show_cmd = True
        elif opt in ("--show-db", "-g"):
            show_tango = True
        elif opt == "--show-dev":
            show_dev = True
        elif opt in ("--show-property", "-p"):
            show_prop = True
        elif opt in ("--show-namespace", "-k"):
            show_ns = True
        elif opt in ("--show-pod", "-x"):
            show_pod = True
        elif opt == "--simul":
            dev_sim = int(arg)
        elif opt == "--standby":
            dev_standby = True
        elif opt == "--status":
            show_status = {
                "attributes": list(cfg_data["list_items"]["attributes"].keys()),
                "commands": list(cfg_data["list_items"]["commands"].keys()),
                "properties": list(cfg_data["list_items"]["properties"].keys()),
            }
            _module_logger.info("Status set to %s", show_status)
        elif opt in ("--txt", "-t"):
            disp_action.value = DispAction.TANGOCTL_TXT
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
            disp_action.value = DispAction.TANGOCTL_YAML
        else:
            _module_logger.error("Invalid option %s", opt)
            return 1

    if cfg_name is not None:
        cfg_data = read_tangoktl_config(_module_logger, cfg_name)

    if show_version:
        print(f"{os.path.basename(sys.argv[0])} version {__version__}")
        return 0

    if show_jargon:
        print_jargon()
        return 0

    if show_ns:
        show_namespaces(_module_logger, output_file, disp_action, kube_namespace, reverse)
        return 0

    if show_pod:
        tangoktl = TangoControlKubernetes(
            _module_logger, True, True, True, {}, cfg_data, kube_namespace
        )
        tangoktl.show_pods(kube_namespace, quiet_mode, output_file, disp_action)
        return 0

    if json_dir:
        tangoktl = TangoControlKubernetes(
            _module_logger, True, True, True, {}, cfg_data, kube_namespace
        )
        tangoktl.read_input_files(json_dir, quiet_mode)
        return 0

    if disp_action.check(DispAction.TANGOCTL_NONE):
        disp_action.value = DispAction.TANGOCTL_DEFAULT
        _module_logger.info("Use default format %s", disp_action)

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
            if disp_action.check([DispAction.TANGOCTL_FULL, DispAction.TANGOCTL_SHORT]):
                verbose_tree = True
            device_tree(include_dserver=evrythng, verbose=verbose_tree)
            continue

        if input_file is not None:
            tangoktl = TangoControlKubernetes(_module_logger, True, True, True, {}, cfg_data, None)
            tangoktl.read_input_file(input_file, tgo_name, dry_run)
            continue

        dev_test: bool = False
        if dev_off or dev_on or dev_sim or dev_standby:
            dev_test = True
        if dev_admin is not None:
            dev_test = True
        if dev_test and tgo_name:
            dut: TestTangoDevice = TestTangoDevice(_module_logger, tgo_name)
            if dut.dev is None:
                print(f"[FAILED] could not open device {tgo_name}")
                return 1
            # Run tests on Tango devices
            rc += dut.run_test(
                dry_run,
                dev_admin,
                dev_off,
                dev_on,
                dev_sim,
                dev_standby,
                show_status,
                show_cmd,
                show_attrib,
                tgo_attrib,
                tgo_name,
                tango_port,
            )
            continue

        if show_attrib:
            pass

        if tgo_value and tgo_attrib and tgo_name:
            tangoktl = TangoControlKubernetes(
                _module_logger, True, True, True, {}, cfg_data, thost.ns_name
            )
            rc = tangoktl.set_value(tgo_name, quiet_mode, reverse, tgo_attrib, tgo_value)
            continue

        # Read info from Tango host
        rc += read_tango_host(
            show_attrib,
            show_cmd,
            show_prop,
            show_status,
            ntango,
            ntangos,
            thost.ns_name,
            cfg_data,
            disp_action,
            evrythng,
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
