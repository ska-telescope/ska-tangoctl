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
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.WARNING)


def main() -> int:  # noqa: C901
    """
    Read and display Tango devices.

    :return: error condition
    """
    k8s: KubernetesInfo = KubernetesInfo(_module_logger)
    tangoktl: TangoKontrol = TangoKontrol(_module_logger, k8s.context)

    # Read command line options
    rc: int = tangoktl.read_command_line(sys.argv)
    if rc:
        return 1

    # Read configuration
    tangoktl.read_config()

    _module_logger.info("Read Tango:\n%s", tangoktl)

    if tangoktl.show_version:
        print(f"{os.path.basename(sys.argv[0])} version {__version__}")
        return 0

    if tangoktl.show_jargon:
        print_jargon()
        return 0

    if tangoktl.show_ns:
        tangoktl.show_namespaces()
        return 0

    if tangoktl.show_pod:
        tangoktl.show_pods()
        return 0

    if tangoktl.show_svc:
        tangoktl.show_services()
        return 0

    if tangoktl.json_dir:
        tangoktl.read_input_files(tangoktl.json_dir)
        return 0

    if tangoktl.disp_action.check(DispAction.TANGOCTL_NONE):
        tangoktl.disp_action.value = DispAction.TANGOCTL_DEFAULT
        _module_logger.info("Use default format %s", tangoktl.disp_action)
    tango_hosts: list[TangoHostInfo]
    tango_hosts = get_tango_hosts(
        _module_logger,
        tangoktl.tango_host,
        tangoktl.ns_name,
        tangoktl.cfg_data["databaseds_name"],
        tangoktl.cfg_data["cluster_domain"][k8s.context],
        tangoktl.cfg_data["databaseds_port"],
        tangoktl.use_fqdn,
        [],
    )
    if not tango_hosts:
        _ctx_name, ns_list = tangoktl.get_namespaces_list()
        tango_hosts = get_tango_hosts(
            _module_logger,
            tangoktl.tango_host,
            tangoktl.ns_name,
            tangoktl.cfg_data["databaseds_name"],
            tangoktl.cfg_data["cluster_domain"][k8s.context],
            tangoktl.cfg_data["databaseds_port"],
            tangoktl.use_fqdn,
            ns_list,
        )
    if not tango_hosts:
        _module_logger.error("Could not read Tango hosts")
        return 1
    if len(tango_hosts) > 1:
        tangoktl.quiet_mode = True

    _module_logger.info("Use Tango hosts %s", tango_hosts)
    thost: TangoHostInfo
    rc = 0
    ntango: int = 0
    ntangos: int = len(tango_hosts)
    for thost in tango_hosts:
        ntango += 1
        os.environ["TANGO_HOST"] = str(thost.tango_host)
        _module_logger.info("Set TANGO_HOST to %s", thost.tango_host)

        if tangoktl.show_tango:
            print(f"TANGO_HOST={thost.tango_fqdn}:{thost.tango_port}")
            if thost.tango_ip is not None:
                print(f"TANGO_HOST={thost.tango_ip}:{thost.tango_port}")
            print()
            continue

        if tangoktl.show_tree:
            verbose_tree: bool = False
            if tangoktl.disp_action.check([DispAction.TANGOCTL_FULL, DispAction.TANGOCTL_SHORT]):
                verbose_tree = True
            device_tree(include_dserver=tangoktl.evrythng, verbose=verbose_tree)
            continue

        if tangoktl.input_file is not None:
            tangoktl.read_input_file()
            continue

        dev_test: bool = False
        if tangoktl.dev_off or tangoktl.dev_on or tangoktl.dev_sim or tangoktl.dev_standby:
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
                tangoktl.dry_run,
                tangoktl.dev_admin,
                tangoktl.dev_off,
                tangoktl.dev_on,
                tangoktl.dev_sim,
                tangoktl.dev_standby,
                tangoktl.show_status,
                tangoktl.show_cmd,
                tangoktl.show_attrib,
                tangoktl.tgo_attrib,
                tangoktl.tgo_name,
                tangoktl.tango_port,
            )
            continue

        if tangoktl.show_attrib:
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
