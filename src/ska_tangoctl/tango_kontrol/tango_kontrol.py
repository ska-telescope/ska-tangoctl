"""Read all information about Tango devices in a Kubernetes cluster."""

import json
import logging
import os
import socket
from typing import Any

import tango
import yaml

from ska_mid_itf_engineering_tools.k8s_info.get_k8s_info import KubernetesControl
from ska_mid_itf_engineering_tools.tango_control.read_tango_devices import TangoctlDevices
from ska_mid_itf_engineering_tools.tango_control.tango_control import TangoControl


class TangoControlKubernetes(TangoControl):
    """Read Tango devices running in a Kubernetes cluster."""

    def __init__(self, logger: logging.Logger, cfg_data: Any):
        """
        Time to rock and roll.

        :param logger: logging handle
        :param cfg_data: configuration dictionary
        """
        super().__init__(logger, cfg_data)
        self.cfg_data = cfg_data

    def usage(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        print("\033[1mRead Tango devices:\033[0m")
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help")
        print(f"\t{p_name} -h")
        print("\nDisplay Kubernetes namespaces")
        print(f"\t{p_name} --show-ns")
        print(f"\t{p_name} -k")
        # Tango database address for a namespace
        print("\nDisplay Tango database address")
        print(f"\t{p_name} --show-db --k8s-ns=<NAMESPACE>")
        print(f"\t{p_name} -t -K <NAMESPACE>")
        print(f"e.g. \033[3m{p_name} -t -K integration\033[0m")
        # Display class names
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -d|--class --k8s-ns=<NAMESPACE>|--host=<HOST>")
        print(f"\t{p_name} -d|--class -K <NAMESPACE>|-H <HOST>")
        print(f"e.g. \033[3m{p_name} -d -K integration\033[0m")
        # List device names
        print("\nList Tango device names")
        print(f"\t{p_name} --show-dev --k8s-ns=<NAMESPACE>|--host=<HOST>")
        print(f"\t{p_name} -l -K <NAMESPACE>|-H <HOST>")
        print(f"e.g. \033[3m{p_name} -l -K integration\033[0m")
        print("\nDisplay all Tango devices (will take a long time)")
        print(f"\t{p_name} --full|--short -e|--everything [--namespace=<NAMESPACE>|--host=<HOST>]")
        print(f"\t{p_name} -l -K integration\033[0m")
        print(f"\te.g. \033[3m{p_name} -f|-s -K <NAMESPACE>|-H <HOST>")
        # Display devices
        print("\nFilter on device name")
        print(f"\t{p_name} --full|--short -D <DEVICE> -K <NAMESPACE>|-H <HOST>")
        print(f"\t{p_name} -f|-s --device=<DEVICE> --k8s-ns=<NAMESPACE>|--host=<HOST>")
        print(
            f"e.g. \033[3m{p_name} -f -K integration -D ska_mid/tm_leaf_node/csp_subarray01\033[0m"
        )
        # Display attributes
        print("\nFilter on attribute name")
        print(
            f"\t{p_name} --full|--short --attribute=<ATTRIBUTE> --k8s-ns=<NAMESPACE>|--host=<HOST>"
        )
        print(f"\t{p_name} -f|-s -A <ATTRIBUTE> -K <NAMESPACE>|-H <HOST>")
        print(f"e.g. \033[3m{p_name} -f -K integration -A timeout\033[0m")
        # Display commands
        print("\nFilter on command name")
        print(f"\t{p_name} --full|--short --command=<COMMAND> --k8s-ns=<NAMESPACE>|--host=<HOST>")
        print(f"\t{p_name} -f|-s -C <COMMAND> -K <NAMESPACE>|-H <HOST>")
        print(f"e.g. \033[3m{p_name} -l -K integration -C status\033[0m")
        # Display properties
        print("\nFilter on property name")
        print(
            f"\t{p_name} --full|--list|--short --property=<PROPERTY>"
            " --k8s-ns=<NAMESPACE>|--host=<HOST>"
        )
        print(f"\t{p_name} -f|-s -P <PROPERTY> --k8s-ns=<NAMESPACE>|--host=<HOST>")
        print(f"e.g. \033[3m{p_name} -l -K integration -P power\033[0m")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")
        # _______________________
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir=<PATH>")
        print(f"\t{p_name} -J <PATH>")
        print(f"e.g. \033[3mADMIN_MODE=1 {p_name} -J resources/\033[0m")
        print("\nRun test, reading from input file")
        print(f"\t{p_name} --k8s-ns=<NAMESPACE> --input=<FILE>")
        print(f"\t{p_name} --K <NAMESPACE> -O <FILE>")
        print("Files are in JSON format and contain values to be read and/or written, e.g:")
        print(
            """\033[3m{
    "description": "Turn admin mode on and check status",
    "test_on": [
        {
            "attribute": "adminMode",
            "read" : ""
        },
        {
            "attribute": "adminMode",
            "write": 1
        },
        {
            "attribute": "adminMode",
            "read": 1
        },
        {
            "command": "State",
            "return": "OFFLINE"
        },
        {
            "command": "Status"
        }
    ]
}\033[0m
"""
        )
        print("Files can contain environment variables that are read at run-time:")
        print(
            """\033[3m{
    "description": "Turn admin mode off and check status",
    "test_on": [
        {
            "attribute": "adminMode",
            "read": ""
        },
        {
            "attribute": "adminMode",
            "write": "${ADMIN_MODE}"
        },
        {
            "attribute": "adminMode",
            "read": "${ADMIN_MODE}"
        },
        {
            "command": "State",
            "return": "ONLINE"
        },
        {
            "command": "Status"
        }
    ]
}\033[0m
"""
        )
        print("To run the above:")
        print(
            f"\033[3mADMIN_MODE=1 {p_name}"
            " --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
            " -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V\033[0m"
        )
        # _______
        # Testing
        print("\n\033[1mTest Tango devices:\033[0m")
        print("\nTest a Tango device")
        print(f"\t{p_name} -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]")
        print("\nTest a Tango device and read attributes")
        print(f"\t{p_name} -a -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]")
        print("\nDisplay attribute and command names for a Tango device")
        print(f"\t{p_name} -c -K <NAMESPACE>|-H <HOST> -D <DEVICE>")
        print("\nTurn a Tango device on")
        print(f"\t{p_name} --on -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]")
        print("\nTurn a Tango device off")
        print(f"\t{p_name} --off -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]")
        print("\nSet a Tango device to standby mode")
        print(f"\t{p_name} --standby -K <NAMESPACE>|-H <HOST> -D <DEVICE> [--simul=<0|1>]")
        print("\nChange admin mode on a Tango device")
        print(f"\t{p_name} --admin=<0|1>")
        print("\nDisplay status of a Tango device")
        print(f"\t{p_name} --status -K <NAMESPACE>|-H <HOST> -D <DEVICE>")
        print("\nCheck events for attribute of a Tango device")
        print(f"\t{p_name} -K <NAMESPACE>|-H <HOST> -D <DEVICE> -A <ATTRIBUTE>")
        # ______________________
        # Options and parameters
        print("\n\033[1mParameters:\033[0m\n")
        print("\t-a\t\t\t\tflag for reading attributes during tests")
        print("\t-c|--cmd\t\t\tflag for running commands during tests")
        print("\t--simul=<0|1>\t\t\tset simulation mode off or on")
        print("\t--admin=<0|1>\t\t\tset admin mode off or on")
        print("\t-f|--full\t\t\tdisplay in full")
        print("\t-l|--list\t\t\tdisplay device name and status on one line")
        print("\t-s|--short\t\t\tdisplay device name, status and query devices")
        print("\t-q|--quiet\t\t\tdo not display progress bars")
        print("\t-j|--html\t\t\toutput in HTML format")
        print("\t-j|--json\t\t\toutput in JSON format")
        print("\t-m|--md\t\t\t\toutput in markdown format")
        print("\t-y|--yaml\t\t\toutput in YAML format")
        print("\t-u|--unique\t\t\tonly read one device for each class")
        print("\t--json-dir=<PATH>\t\tdirectory with JSON input file, e.g. 'resources'")
        print("\t-J <PATH>")
        print(
            "\t--device=<DEVICE>\t\tdevice name, e.g. 'csp'"
            " (not case sensitive, only a part is needed)"
        )
        print("\t-D <DEVICE>")
        print(
            "\t--k8s-ns=<NAMESPACE>\t\tKubernetes namespace for Tango database,"
            " e.g. 'integration'"
        )
        print("\t-K <NAMESPACE>")
        print("\t--host=<HOST>\t\t\tTango database host and port, e.g. 10.8.13.15:10000")
        print("\t-H <HOST>")
        print("\t--attribute=<ATTRIBUTE>\t\tattribute name, e.g. 'obsState' (not case sensitive)")
        print("\t-A <ATTRIBUTE>")
        print("\t--command=<COMMAND>\t\tcommand name, e.g. 'Status' (not case sensitive)")
        print("\t-C <COMMAND>")
        print("\t--output=<FILE>\t\t\toutput file name")
        print("\t-O <FILE>")
        print("\t--input=<FILE>\t\t\tinput file name")
        print("\t-I <FILE>")
        print(
            "\nNote that values for device, attribute, command or property are not case sensitive."
        )
        print(
            f"Partial matches for strings longer than {self.cfg_data['min_str_len']}"
            " charaters are OK."
        )
        print(
            "\nWhen a namespace is specified, the Tango database host will be made up as follows:"
        )
        print(
            f"\t{self.cfg_data['databaseds_name']}.<NAMESPACE>.{self.cfg_data['cluster_domain']}"
            f":{self.cfg_data['databaseds_port']}"
        )
        print(
            "\nRun the following commands where applicable:"
            f"\n\t{','.join(self.cfg_data['run_commands'])}"
        )
        print(
            f"\nRun commands with device name as parameter where applicable:\n"
            f"\t{','.join(self.cfg_data['run_commands_name'])}"
        )
        # __________________
        # Some more examples
        print("\n\033[1mExamples:\033[0m\n")
        print(f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2 -l")
        print(f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2 -D talon -l")
        print(f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2 -A timeout")
        print(f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2 -C Telescope")
        print(f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2 -P Power")
        print(
            f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
            " -D mid_csp_cbf/talon_lru/001 -f"
        )
        print(
            f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
            " -D mid_csp_cbf/talon_lru/001 -q"
        )
        print(
            f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
            " -D mid_csp_cbf/talon_board/001 -f"
        )
        print(
            f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
            " -D mid_csp_cbf/talon_board/001 -f --dry"
        )
        print(
            f"\t{p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
            " -D mid-sdp/control/0 --on"
        )
        print(
            f"\tADMIN_MODE=1 {p_name} --k8s-ns=ci-ska-mid-itf-at-1820-tmc-test-sdp-notebook-v2"
            f" -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V"
        )
        print()

    def check_tango(
        self,
        tango_fqdn: str,
        quiet_mode: bool,
        tango_port: int = 10000,
    ) -> int:
        """
        Check Tango host address.

        :param tango_fqdn: fully qualified domain name
        :param quiet_mode: flag to suppress extra output
        :param tango_port: port number
        :return: error condition
        """
        tango_addr: tuple[str, list[str], list[str]]
        tango_ip: str
        self.logger.info("Check Tango host %s:%d", tango_fqdn, tango_port)
        try:
            tango_addr = socket.gethostbyname_ex(tango_fqdn)
            tango_ip = tango_addr[2][0]
        except socket.gaierror as e:
            self.logger.error("Could not read address %s : %s" % (tango_fqdn, e))
            return 1
        if not quiet_mode:
            print(f"TANGO_HOST={tango_fqdn}:{tango_port}")
            print(f"TANGO_HOST={tango_ip}:{tango_port}")
        return 0

    def get_namespaces_list(self) -> list:
        """
        Read namespaces in Kubernetes cluster.

        :return: list with devices
        """
        k8s: KubernetesControl = KubernetesControl(self.logger)
        ns_list: list = k8s.get_namespaces_list()
        self.logger.info("Read %d namespaces", len(ns_list))
        return ns_list

    def get_namespaces_dict(self) -> dict:
        """
        Read namespaces in Kubernetes cluster.

        :return: dictionary with devices
        """
        k8s: KubernetesControl = KubernetesControl(self.logger)
        ns_dict: dict = k8s.get_namespaces_dict()
        self.logger.info("Read %d namespaces", len(ns_dict))
        return ns_dict

    def show_namespaces(self, output_file: str | None, fmt: str) -> None:
        """
        Display namespaces in Kubernetes cluster.

        :param output_file: output file name
        :param fmt: output format
        """
        ns_dict: dict
        ns_list: list
        ns_name: str
        if fmt == "json":
            ns_dict = self.get_namespaces_dict()
            if output_file is not None:
                self.logger.info("Write output file %s", output_file)
                with open(output_file, "w") as outf:
                    outf.write(json.dumps(ns_dict, indent=4))
            else:
                print(json.dumps(ns_dict, indent=4))
        elif fmt == "yaml":
            ns_dict = self.get_namespaces_dict()
            if output_file is not None:
                self.logger.info("Write output file %s", output_file)
                with open(output_file, "w") as outf:
                    outf.write(yaml.dump(ns_dict))
            else:
                print(yaml.dump(ns_dict))
        else:
            ns_list = self.get_namespaces_list()
            print(f"Namespaces : {len(ns_list)}")
            for ns_name in ns_list:
                print(f"\t{ns_name}")

    def get_pods_dict(self, ns_name: str | None) -> dict:
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :return: dictionary with devices
        """
        k8s = KubernetesControl(self.logger)
        pods_dict = k8s.get_pods(ns_name, None)
        self.logger.info("Read %d pods", len(pods_dict))
        return pods_dict

    def print_pods(self, ns_name: str | None, quiet_mode: bool) -> None:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param quiet_mode: flag to suppress extra output
        """
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return
        k8s: KubernetesControl = KubernetesControl(self.logger)
        pods_dict: dict = self.get_pods_dict(ns_name)
        print(f"Pods in namespace {ns_name} : {len(pods_dict)}")
        pod_name: str
        for pod_name in pods_dict:
            print(f"\t{pod_name}")
            if not quiet_mode:
                resps: str = k8s.exec_command(ns_name, pod_name, ["ps", "-ef"])
                if not resps:
                    pass
                elif "\n" in resps:
                    resp: str
                    for resp in resps.split("\n"):
                        self.logger.debug("Got '%s'", resp)
                        if not resp:
                            pass
                        elif resp[-6:] == "ps -ef":
                            pass
                        elif resp[0:3] == "UID":
                            pass
                        elif resp[0:3] == "PID":
                            pass
                        # elif "nginx" in resp:
                        #     pass
                        elif resp[0:5] in ("tango", "root ", "mysql") or resp[0:3] == "100":
                            respl = resp.split()
                            print(f"\t\t* {respl[0]:8} {' '.join(respl[7:])}")
                        else:
                            print(f"\t\t  {resp}")
                else:
                    print(f"\t\t- {resps}")

    def get_pods_json(self, ns_name: str | None, quiet_mode: bool) -> dict:  # noqa: C901
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param quiet_mode: print progress bars
        :return: dictionary with pod information
        """
        pods: dict = {}
        pod_exec: list = ["ps", "-ef"]
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return pods
        k8s: KubernetesControl = KubernetesControl(self.logger)
        self.logger.debug("Read pods running in namespace %s", ns_name)
        pods_list: dict = k8s.get_pods(ns_name, None)
        self.logger.info("Found %d pods running in namespace %s", len(pods_list), ns_name)
        pod_name: str
        for pod_name in pods_list:
            self.logger.info("Read processes running in pod %s", pod_name)
            resps: str = k8s.exec_command(ns_name, pod_name, pod_exec)
            pods[pod_name] = []
            if quiet_mode:
                continue
            if not resps:
                pass
            elif "\n" in resps:
                resp: str
                for resp in resps.split("\n"):
                    if not resp:
                        pass
                    elif resp[-6:] == "ps -ef":
                        pass
                    elif resp[0:3] == "UID":
                        pass
                    elif resp[0:3] == "PID":
                        pass
                    # TODO to show nginx or not to show nginx
                    # elif "nginx" in resp:
                    #     pass
                    else:
                        pods[pod_name].append(resp)
            else:
                pods[pod_name].append(resps)
        return pods

    def show_pods(
        self, ns_name: str | None, quiet_mode: bool, output_file: str | None, fmt: str | None
    ) -> None:
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param quiet_mode: flag to suppress progress bar etc.
        :param output_file: output file name
        :param fmt: output format
        """
        pods: dict
        if fmt == "json":
            pods = self.get_pods_json(ns_name, quiet_mode)
            if output_file is not None:
                self.logger.info("Write output file %s", output_file)
                with open(output_file, "w") as outf:
                    outf.write(json.dumps(pods, indent=4))
            else:
                print(json.dumps(pods, indent=4))
        elif fmt == "yaml":
            pods = self.get_pods_json(ns_name, quiet_mode)
            if output_file is not None:
                self.logger.info("Write output file %s", output_file)
                with open(output_file, "w") as outf:
                    outf.write(yaml.dump(pods))
            else:
                print(yaml.dump(pods))
        elif fmt == "txt":
            self.print_pods(ns_name, quiet_mode)
        else:
            # show_pods(ns_name, quiet_mode, output_file, fmt)
            self.logger.warning("Output format %s not supported", fmt)
            pass

    def run_info(  # noqa: C901
        self,
        uniq_cls: bool,
        file_name: str | None,
        fmt: str,
        evrythng: bool,
        quiet_mode: bool,
        disp_action: int,
        tgo_name: str | None,
        tgo_attrib: str | None,
        tgo_cmd: str | None,
        tgo_prop: str | None,
        tango_port: int,
    ) -> int:
        """
        Read information on Tango devices.

        :param uniq_cls: only read one device per class
        :param file_name: output file name
        :param fmt: output format
        :param evrythng: get commands and attributes regadrless of state
        :param quiet_mode: flag for displaying progress bars
        :param disp_action: flag for output format
        :param tgo_name: device name
        :param tgo_attrib: attribute name
        :param tgo_cmd: filter command name
        :param tgo_prop: filter property name
        :param tango_port: device port
        :return: error condition
        """
        rc: int
        devices: TangoctlDevices
        self.logger.info(
            "Info %d : device %s attribute %s command %s property %s",
            disp_action,
            tgo_name,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
        )

        # List Tango devices
        if disp_action in (4, 5) and tgo_attrib is None and tgo_cmd is None and tgo_prop is None:
            rc = self.list_devices(
                file_name,
                fmt,
                evrythng,
                quiet_mode,
                disp_action,
                tgo_name,
            )
            return rc

        # Get device classes
        if disp_action == 5 and fmt == "json":
            rc = self.list_classes(fmt, evrythng, quiet_mode, tgo_name)
            return rc

        if file_name is not None:
            if os.path.splitext(file_name)[-1] != f".{fmt}":
                file_name = f"{file_name}.{fmt}"
                self.logger.warning("File name changed to %s", file_name)

        if (
            tgo_name is None
            and tgo_attrib is None
            and tgo_cmd is None
            and tgo_prop is None
            and (not disp_action)
            and (not evrythng)
        ):
            self.logger.error(
                "No filters specified, use '-l' flag to list all devices"
                " or '-e' for a full display of every device in the namespace",
            )
            return 1

        try:
            devices = TangoctlDevices(
                self.logger,
                uniq_cls,
                quiet_mode,
                evrythng,
                self.cfg_data,
                tgo_name,
                tgo_attrib,
                tgo_cmd,
                tgo_prop,
                tango_port,
                file_name,
                fmt,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection failed")
            return 1
        devices.read_device_values()

        self.logger.debug("Read devices (action %d)", disp_action)

        if fmt == "txt" and disp_action == 4 and tgo_attrib is not None:
            devices.print_txt_list_attributes()
        elif fmt == "txt" and disp_action == 4 and tgo_cmd is not None:
            devices.print_txt_list_commands()
        elif fmt == "txt" and disp_action == 4 and tgo_prop is not None:
            devices.print_txt_list_properties()
        elif fmt == "txt":
            devices.print_txt(disp_action)
        elif fmt == "html":
            devices.print_html(disp_action)
        elif fmt == "json":
            devices.print_json(disp_action)
        elif fmt == "md":
            devices.print_markdown(disp_action)
        elif fmt == "yaml":
            devices.print_yaml(disp_action)
        else:
            print("---")

        return 0
