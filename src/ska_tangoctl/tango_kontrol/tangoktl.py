#!/usr/bin/env python
"""Read all information about Tango devices."""

import logging
import os
import sys

from ska_tangoctl import __version__
from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.tango_database import TangoHostInfo, get_tango_hosts
from ska_tangoctl.tango_control.tango_device_tree import device_tree
from ska_tangoctl.tango_control.test_tango_device import TestTangoDevice
from ska_tangoctl.tango_kontrol.tango_kontrol import TangoKontrol
from ska_tangoctl.tla_jargon.tla_jargon import print_jargon

try:
    from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
except ModuleNotFoundError:
    KubernetesInfo = None  # type: ignore[assignment,misc]

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
_module_logger = logging.getLogger("tango_kontrol")
_module_logger.setLevel(logging.WARNING)


def main() -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :return: error condition
    """
    k8s: KubernetesInfo = KubernetesInfo(_module_logger, None)
    tangoktl: TangoKontrol = TangoKontrol(
        _module_logger, k8s.context, k8s.cluster, k8s.domain_name
    )

    # Read command line options
    rc: int = tangoktl.read_command_line_k8s(sys.argv)
    if rc == 0:
        pass
    elif rc == 3:
        tangoktl.usage3(os.path.basename(sys.argv[0]))
        return 1
    elif rc == 4:
        tangoktl.usage4(os.path.basename(sys.argv[0]))
        return 1
    else:
        _module_logger.error("Read command line returned %d", rc)
        return 1

    # Read configuration
    tangoktl.read_config()

    _module_logger.info("Read Tango:\n%s", tangoktl)
    # TODO not really needed
    # if _module_logger.getEffectiveLevel() in (logging.INFO, logging.DEBUG):
    #     tangoktl.disp_action.print()

    if tangoktl.disp_action.show_version:
        print(f"{os.path.basename(sys.argv[0])} version {__version__}")
        return 0

    if tangoktl.disp_action.show_jargon:
        print_jargon()
        return 0

    if tangoktl.disp_action.show_ctx:
        tangoktl.show_contexts()
        return 0

    if tangoktl.disp_action.show_ns:
        tangoktl.show_namespaces()
        return 0

    if tangoktl.disp_action.show_log and tangoktl.k8s_pod:
        tangoktl.show_pod_log()
        return 0

    if tangoktl.show_svc:
        tangoktl.show_services()
        return 0

    if tangoktl.disp_action.show_pod and tangoktl.disp_action.check(DispAction.TANGOCTL_TXT):
        tangoktl.set_output()
        tangoktl.list_pod_names(tangoktl.k8s_ns)
        tangoktl.unset_output()
        return 0

    if tangoktl.disp_action.show_proc and tangoktl.k8s_pod:
        tangoktl.print_pod_procs()
        return 0

    if tangoktl.json_dir:
        tangoktl.read_input_files(tangoktl.json_dir)
        return 0

    if tangoktl.pod_cmd and tangoktl.k8s_pod:
        tangoktl.show_pod(tangoktl.pod_cmd)
        return 0

    if tangoktl.pod_cmd:
        tangoktl.show_pods(tangoktl.pod_cmd)
        return 0

    if tangoktl.disp_action.check(DispAction.TANGOCTL_NONE):
        tangoktl.disp_action.format = DispAction.TANGOCTL_DEFAULT
        _module_logger.info("Use default format %s", tangoktl.disp_action)

    tangoktl.domain_name = k8s.get_domain()
    if tangoktl.domain_name is None:
        _module_logger.error("Could not read domain name for context %s", k8s.context)
        return 1
    _module_logger.info("Domain name for context %s : %s", k8s.context, k8s.domain_name)
    tango_hosts: list[TangoHostInfo]
    tango_hosts = get_tango_hosts(
        _module_logger,
        tangoktl.tango_host,
        tangoktl.k8s_ns,
        tangoktl.cfg_data["databaseds_name"],
        f"svc.{tangoktl.domain_name}",
        tangoktl.cfg_data["databaseds_port"],
        tangoktl.use_fqdn,
        [],
    )
    if not tango_hosts:
        _ctx_name, _cluster_name, ns_list = tangoktl.get_namespaces_list()
        tango_hosts = get_tango_hosts(
            _module_logger,
            tangoktl.tango_host,
            tangoktl.k8s_ns,
            tangoktl.cfg_data["databaseds_name"],
            f"svc.{tangoktl.domain_name}",
            tangoktl.cfg_data["databaseds_port"],
            tangoktl.use_fqdn,
            ns_list,
        )
    if not tango_hosts:
        _module_logger.error("Could not read Tango hosts")
        return 1
    if len(tango_hosts) > 1:
        tangoktl.disp_action.quiet_mode = True
    _module_logger.info("Use Tango hosts %s", tango_hosts)

    if tangoktl.logging_level and tangoktl.tgo_name:
        return tangoktl.set_logging_level()

    thost: TangoHostInfo
    rc = 0
    ntango: int = 0
    ntangos: int = len(tango_hosts)
    for thost in tango_hosts:
        ntango += 1
        os.environ["TANGO_HOST"] = str(thost.tango_host)
        _module_logger.info("Set TANGO_HOST to %s", thost.tango_host)

        if tangoktl.disp_action.show_tango:
            print(f"TANGO_HOST={thost.tango_fqdn}:{thost.tango_port}")
            if thost.tango_ip is not None:
                print(f"TANGO_HOST={thost.tango_ip}:{thost.tango_port}")
            print()
            continue

        if tangoktl.disp_action.show_tree:
            verbose_tree: bool = False
            if tangoktl.disp_action.size == "L" or tangoktl.disp_action.size == "M":
                verbose_tree = True
            device_tree(include_dserver=tangoktl.disp_action.evrythng, verbose=verbose_tree)
            continue

        if tangoktl.input_file is not None:
            tangoktl.read_input_file()
            continue

        if tangoktl.dev_test:
            tangoktl.dev_ping = True
            tangoktl.dev_status = {"attributes": ["Status", "adminMode"]}
            tangoktl.disp_action.show_attrib = True
            tangoktl.disp_action.show_cmd = True
            tangoktl.disp_action.show_prop = True
        dev_test: bool = False
        if (
            tangoktl.dev_off
            or tangoktl.dev_on
            or tangoktl.dev_ping
            or tangoktl.dev_sim
            or tangoktl.dev_standby
        ):
            dev_test = True
        if tangoktl.dev_admin is not None:
            dev_test = True
        if dev_test and tangoktl.tgo_name:
            dut: TestTangoDevice = TestTangoDevice(_module_logger, tangoktl.tgo_name)
            if dut.dev is None:
                print(f"[FAILED] could not open device {tangoktl.tgo_name}")
                return 1
            # Run tests on Tango devices
            rc += dut.run_test(
                tangoktl.dev_admin,
                tangoktl.dev_off,
                tangoktl.dev_on,
                tangoktl.dev_ping,
                tangoktl.dev_sim,
                tangoktl.dev_standby,
                tangoktl.dev_status,
                tangoktl.disp_action.show_attrib,
                tangoktl.disp_action.show_cmd,
                tangoktl.disp_action.show_prop,
                tangoktl.tgo_attrib,
                tangoktl.tgo_name,
            )
            continue

        if tangoktl.disp_action.show_attrib:
            pass

        if tangoktl.tgo_value and tangoktl.tgo_attrib and tangoktl.tgo_name:
            rc = tangoktl.set_value()
            continue

        # Read info from Tango host
        rc += tangoktl.read_tango_host(ntango, ntangos)
    return rc


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
