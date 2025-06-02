"""Read all information about Tango devices in a Kubernetes cluster."""

import getopt
import json
import logging
import os
import sys
from typing import Any

import tango
import yaml

try:
    from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
except ModuleNotFoundError:
    KubernetesInfo = None  # type: ignore[assignment,misc]
from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevices
from ska_tangoctl.tango_control.tango_control import TangoControl
from ska_tangoctl.tango_kontrol.tangoktl_config import TANGOKTL_CONFIG, read_tangoktl_config


class TangoKontrol(TangoControl):
    """Read Tango devices running in a Kubernetes cluster."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize this thing.

        :param logger: logging handle
        """
        super().__init__(logger)
        self.cfg_data = TANGOKTL_CONFIG
        self.ns_name: str | None = None
        self.show_pod: bool = False
        self.show_ns: bool = False
        self.use_fqdn: bool = True

    def __repr__(self) -> str:
        """
        Do the string thing.

        :returns: string representation
        """
        rval = f"\tDisplay format {self.disp_action}"
        rval += f"\n\tShow {'attributes' if self.show_attrib else ''}"
        rval += f" {'commands' if self.show_cmd else ''}"
        rval += f" {'properties' if self.show_prop else ''}"
        rval += f"\n\tNamespace: {self.ns_name}"
        rval += f"\n\tConfiguration: {self.cfg_data}"
        return rval

    def setup(
        self,
        cfg_name: str | None = None,
        dev_on: bool = False,
        dev_off: bool = False,
        dev_standby: bool = False,
        dev_status: dict = {},
        dev_test: bool = False,
        dev_admin: int | None = None,
        dev_sim: int | None = None,
        disp_action: DispAction = DispAction(DispAction.TANGOCTL_NONE),
        dry_run: bool = False,
        evrythng: bool = False,
        input_file: str | None = None,
        json_dir: str | None = None,
        output_file: str | None = None,
        quiet_mode: bool = False,
        reverse: bool = False,
        show_attrib: bool = False,
        show_cmd: bool = False,
        show_dev: bool = False,
        show_jargon: bool = False,
        show_prop: bool = False,
        show_status: dict = {},
        show_tango: bool = False,
        show_tree: bool = False,
        show_version: bool = False,
        tango_host: str | None = None,
        tango_port: int = 10000,
        tgo_attrib: str | None = None,
        tgo_cmd: str | None = None,
        tgo_in_type: str | None = None,
        tgo_name: str | None = None,
        tgo_prop: str | None = None,
        tgo_value: str | None = None,
        uniq_cls: bool = False,
        cfg_data: dict = TANGOKTL_CONFIG,
        ns_name: str | None = None,
        show_pod: bool = False,
        show_ns: bool = False,
        use_fqdn: bool = True,
    ) -> None:
        """
        Set it up.

        TODO find a use for this

        :param cfg_name: config file name
        :param dev_on: device on
        :param dev_off: device off
        :param dev_standby: device standby
        :param dev_status: device status
        :param dev_test: device test
        :param dev_admin: device admin
        :param dev_sim: device simulation
        :param disp_action: dispay action
        :param dry_run: dry run
        :param evrythng: evrything
        :param input_file: input file
        :param json_dir: json file directory
        :param output_file: output file
        :param quiet_mode: quiet mode
        :param reverse: reverse
        :param show_attrib: show attributes
        :param show_cmd: show commands
        :param show_dev: show devices
        :param show_jargon: show jargon
        :param show_prop: show properties
        :param show_status: show status
        :param show_tango: show tango
        :param show_tree: show tree
        :param show_version: show version
        :param tango_host: tango host
        :param tango_port: tango port
        :param tgo_attrib: attribute name
        :param tgo_cmd: command name
        :param tgo_in_type: input type
        :param tgo_name: device name
        :param tgo_prop: property name
        :param tgo_value: value
        :param uniq_cls: unique class
        :param cfg_data: TANGOKTL CONFIG
        :param ns_name: K8S namespace
        :param show_pod: show K8S pods
        :param show_ns: show namespace
        :param use_fqdn: use FQDN for database server
        """
        self.cfg_name = cfg_name
        self.cfg_name = cfg_name
        self.dev_on = dev_on
        self.dev_off = dev_off
        self.dev_standby = dev_standby
        self.dev_status = dev_status
        self.dev_test = dev_test
        self.dev_admin = dev_admin
        self.dev_sim = dev_sim
        self.disp_action = disp_action
        self.dry_run = dry_run
        self.evrythng = evrythng
        self.input_file = input_file
        self.json_dir = json_dir
        self.output_file = output_file
        self.quiet_mode = quiet_mode
        self.reverse = reverse
        self.show_attrib = show_attrib
        self.show_cmd = show_cmd
        self.show_dev = show_dev
        self.show_jargon = show_jargon
        self.show_prop = show_prop
        self.show_status = show_status
        self.show_tango = show_tango
        self.show_tree = show_tree
        self.show_version = show_version
        self.tango_host = tango_host
        self.tango_port = tango_port
        self.tgo_attrib = tgo_attrib
        self.tgo_cmd = tgo_cmd
        # TODO Feature to search by input type not implemented yet
        self.tgo_in_type = tgo_in_type
        self.tgo_name = tgo_name
        self.tgo_prop = tgo_prop
        self.tgo_value = tgo_value
        self.uniq_cls = uniq_cls
        self.ns_name = ns_name
        self.show_pod = show_pod
        self.show_ns = show_ns
        self.use_fqdn = use_fqdn

    def read_config(self) -> None:
        """Read configuration."""
        self.cfg_data: Any = read_tangoktl_config(self.logger, self.cfg_name)

    def usage(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        bold: str = "\033[1m"
        italic: str = "\033[3m"
        unfmt: str = "\033[0m"
        if KubernetesInfo is None:
            super().usage(p_name)
            return

        print(f"{bold}Read Tango devices:{unfmt}")
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
        print(f"\t{p_name} --show-db --namespace=<NAMESPACE>")
        print(f"\t{p_name} -t -K <NAMESPACE>")
        print("\nShow device:")
        print(f"\t{p_name} -K <NAMESPACE> -D <DEVICE> -f")
        print(f"e.g.\n\t{italic}{p_name} -K integration -D mid_csp_cbf/talon_lru/001 -f{unfmt}")
        print(f"\t{italic}{p_name} -K integration -D mid_csp_cbf/talon_lru/001 -q{unfmt}")
        print(f"\t{italic}{p_name} -K integration -D mid_csp_cbf/talon_board/001 -f{unfmt}")
        print(f"\t{italic}{p_name} -K integration -D mid_csp_cbf/talon_board/001 -f --dry{unfmt}")
        print(f"\t{italic}{p_name} -K integration -D mid-sdp/control/0 --on{unfmt}")
        print("\nSearch for matching devices:")
        print(f"\t{p_name} -K integration -D talon -l")
        print("\nSearch for devices with matching command:")
        print(f"\t{p_name} -K <NAMESPACE> -C <COMMAND>")
        print(f"\t{p_name} -K integration -C Telescope")
        print("\nSearch for devices with matching property:")
        print(f"\t{p_name} -K <NAMESPACE> -C <PROPERTY>")
        print(f"e.g.\n\t{italic}{p_name} -K integration -P Power{unfmt}")
        # Display class names
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -d|--class --namespace=<NAMESPACE>")
        print(f"\t{p_name} -d|--class --host=<HOST>")
        print(f"\t{p_name} -d|--class -K <NAMESPACE>")
        print(f"\t{p_name} -d|--class -H <HOST>")
        print(f"e.g.\n\t{italic}{p_name} -d -K integration{unfmt}")
        # List device names
        print("\nList Tango device names")
        # TODO this does the same as class names above
        print(f"\t{p_name} --show-dev --namespace=<NAMESPACE>")
        print(f"\t{p_name} --show-dev --host=<HOST>")
        print(f"\t{p_name} -l -K <NAMESPACE>")
        print(f"\t{p_name} -l -H <HOST>")
        print(f"e.g.\n\t{italic}{p_name} -l -K integration\033[0m")
        print("\nDisplay all Tango devices (will take a long time)")
        # TODO full and short now does the same
        print(f"\t{p_name} -e|--everything --namespace=<NAMESPACE>")
        print(f"\t{p_name} -e|--everything --host=<HOST>")
        print(f"\t{p_name} -l -K integration\033[0m")
        print(f"e.g.\n\t{italic}{p_name} -K integration -l{unfmt}")
        print(f"\t{italic}{p_name} -K integration --json{unfmt}")
        print(f"\t{italic}{p_name} -K integration --md{unfmt}")
        print(f"\t{italic}{p_name} -K integration --txt{unfmt}")
        print(f"\t{italic}{p_name} -K integration --yaml{unfmt}")
        # Display devices
        print("\nFilter on device name")
        print(f"\t{p_name} -D <DEVICE> -K <NAMESPACE>")
        print(f"\t{p_name} -D <DEVICE> -H <HOST>")
        print(f"\t{p_name} --device=<DEVICE> --namespace=<NAMESPACE>")
        print(f"\t{p_name} --device=<DEVICE> --host=<HOST>")
        print(
            f"e.g.\n\t{italic}{p_name} -f -K integration"
            f" -D ska_mid/tm_leaf_node/csp_subarray01{unfmt}"
        )
        # Display attributes
        print("\nDisplay devices with matching attribute name")
        print(f"\t{p_name} --attribute=<ATTRIBUTE> --namespace=<NAMESPACE>")
        print(f"\t{p_name} --attribute=<ATTRIBUTE> --host=<HOST>")
        print(f"\t{p_name} -A <ATTRIBUTE> -K <NAMESPACE>")
        print(f"\t{p_name} -A <ATTRIBUTE> -H <HOST>")
        print(f"e.g.\n\t{italic}{p_name} -K integration -A timeout{unfmt}")
        print(f"\t{italic}{p_name} -K test-equipment -A power{unfmt}")
        # Display commands
        print("\nFilter on command name")
        print(f"\t{p_name} --command=<COMMAND> --namespace=<NAMESPACE>")
        print(f"\t{p_name} --command=<COMMAND> --host=<HOST>")
        print(f"\t{p_name} -f|-s -C <COMMAND> -K <NAMESPACE>|-H <HOST>")
        print(f"e.g.\n\t{italic}{p_name} -l -K integration -C status{unfmt}")
        # Display properties
        print("\nFilter on property name")
        print(f"\t{p_name} --property=<PROPERTY> --namespace=<NAMESPACE>")
        print(f"\t{p_name} --property=<PROPERTY> --host=<HOST>")
        print(f"\t{p_name} -P <PROPERTY> -K <NAMESPACE>")
        print(f"\t{p_name} -P <PROPERTY> -H <HOST>")
        print(f"e.g.\n\t{italic}{p_name} -l -K integration -P power{unfmt}")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")

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
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir=<PATH>")
        print(f"\t{p_name} -J <PATH>")
        print(f"e.g. \033[3mADMIN_MODE=1 {p_name} -J resources/\033[0m")
        print("\nRun test, reading from input file")
        print(f"\t{p_name} --namespace=<NAMESPACE> --input=<FILE>")
        print(f"\t{p_name} -K <NAMESPACE> -O <FILE>")
        print("\nRun test file:")
        print(f"\t{p_name} --K <NAMESPACE> -D <DEVICE> -f --in <PATH> -V")
        print(
            f"{italic}e.g.\tADMIN_MODE=1 {p_name} --K integration"
            f" -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V{unfmt}"
        )

        # ______________________
        # Options and parameters
        print("\n\033[1mParameters:\033[0m\n")
        print("\t-a|--show-attribute\t\tflag for reading attributes")
        print("\t-c|--show-command\t\tflag for reading commands")
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-e|--everything\t\t\tshow all devices - do not skip {ign}")
        print("\t-f|--full\t\t\tdisplay in full")
        print("\t-i|--ip\t\t\t\tuse IP address instead of FQDN")
        # print("\t-l|--list\t\t\tdisplay device name and status on one line")
        print("\t-p|--show-property\t\tflag for reading properties")
        # print("\t-s|--short\t\t\tdisplay device name, status and query devices")
        print("\t-q|--quiet\t\t\tdo not display progress bars")
        print("\t-w|--html\t\t\toutput in HTML format")
        print("\t-j|--json\t\t\toutput in JSON format")
        print("\t-m|--md\t\t\t\toutput in markdown format")
        print("\t-y|--txt\t\t\toutput in text format")
        print("\t-y|--yaml\t\t\toutput in YAML format")
        print("\t-u|--unique\t\t\tonly read one device for each class")
        print("\t--admin=<0|1>\t\t\tset admin mode off or on")
        print(
            "\t--attribute=<NAME>, -A <NAME>\tattribute name, e.g. 'obsState' (not case sensitive)"
        )
        print("\t--cfg=<FILE>, -X <FILE>\t\toverride configuration from file")
        print("\t--command=<NAME>, -C <NAME>\tcommand name, e.g. 'Status' (not case sensitive)")
        print(
            "\t--device=<NAME>, -D <NAME>\tdevice name, e.g. 'csp'"
            " (not case sensitive, only a part is needed)"
        )
        print("\t--host=<HOST>, -H <HOST>\tTango database host and port, e.g. 10.8.13.15:10000")
        print("\t--input=<FILE>, -I <FILE>\tinput file name")
        print("\t--json-dir=<PATH>, -J <PATH>\tdirectory with JSON input file, e.g. 'resources'")
        print(
            "\t--namespace=<NAMESPACE>, -K <NAMESPACE>\tKubernetes namespace for Tango database,"
            " e.g. 'integration'"
        )
        print("\t--output=<FILE>, -O <FILE>\toutput file name")
        print("\t--property=<NAME>, -P <NAME>\tproperty name, e.g. 'Status' (not case sensitive)")
        print(
            "\nNote that values for device, attribute, command or property are not case sensitive."
        )
        print("\t--simul=<0|1>\t\t\tset simulation mode off or on")
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
        print("\n\033[1mConfiguration:\033[0m\n")
        print(f"\ttimeout: {self.cfg_data['timeout_millis']}ms")
        print(f"\tTango database port\t: {self.cfg_data['databaseds_port']}")
        print(f"\tTango device port\t: {self.cfg_data['device_port']}")
        print(f"\tcommands safe to run: {','.join(self.cfg_data['run_commands'])}")
        print(
            "\tcommands safe to run with name as parameter:"
            f" {','.join(self.cfg_data['run_commands_name'])}"
        )
        print(f"\tlong attributes: {','.join(self.cfg_data['long_attributes'])}")
        print(f"\tignore devices: {','.join(self.cfg_data['ignore_device'])}")
        print(f"\tminimum string length for matches: {self.cfg_data['min_str_len']}")
        print(f"\tdelimiter: '{self.cfg_data['delimiter']}'")
        print(
            "\tlisted attributes:"
            f" {','.join(list(self.cfg_data['list_items']['attributes'].keys()))}"
        )
        print(
            "\tlisted commands:"
            f" {','.join(list(self.cfg_data['list_items']['commands'].keys()))}"
        )
        print(
            "\tlisted properties:"
            f" {','.join(list(self.cfg_data['list_items']['properties'].keys()))}"
        )
        print()

    def read_command_line(self, cli_args: list) -> int:  # noqa: C901
        """
        Read the command line interface.

        :param cli_args: arguments
        :return: error condition
        """
        self.logger.debug("Read options : %s", cli_args)
        try:
            opts, _args = getopt.getopt(
                cli_args[1:],
                "abcdefghijklmnopqrstuvwxyVA:C:H:D:I:J:K:O:P:Q:X:T:W:X:",
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

        for opt, arg in opts:
            if opt in ("-h", "--help"):
                self.usage(os.path.basename(cli_args[0]))
                return 1
            elif opt in ("--attribute", "-A"):
                self.tgo_attrib = arg
                self.show_attrib = True
            elif opt in ("--class", "-d"):
                self.disp_action.value = DispAction.TANGOCTL_CLASS
            elif opt in ("--cfg", "-X"):
                self.cfg_name = arg
            elif opt in ("--command", "-C"):
                self.tgo_cmd = arg.lower()
                self.show_cmd = True
            elif opt in ("--device", "-D"):
                self.tgo_name = arg.lower()
            elif opt in ("--dry-run", "-n"):
                # TODO Undocumented and unused feature for dry runs
                self.dry_run = True
            elif opt in ("--everything", "-e"):
                self.evrythng = True
                self.show_attrib = True
                self.show_cmd = True
                self.show_prop = True
            elif opt in ("--full", "-f"):
                self.disp_action.value = DispAction.TANGOCTL_FULL
            elif opt in ("--host", "-H"):
                self.tango_host = arg
            elif opt in ("--html", "-w"):
                self.disp_action.value = DispAction.TANGOCTL_HTML
            elif opt in ("--input", "-I"):
                self.input_file = arg
            elif opt in ("--json", "-j"):
                self.disp_action.value = DispAction.TANGOCTL_JSON
            elif opt in ("--list", "-l"):
                self.disp_action.value = DispAction.TANGOCTL_LIST
            elif opt in ("--json-dir", "-J"):
                self.json_dir = arg
            elif opt in ("--namespace", "-K"):
                self.ns_name = arg
            elif opt in ("--md", "-m"):
                self.disp_action.value = DispAction.TANGOCTL_MD
            elif opt in ("--property", "-P"):
                self.tgo_prop = arg.lower()
                self.show_prop = True
            elif opt == "--off":
                self.dev_off = True
            elif opt == "--on":
                self.dev_on = True
            elif opt in ("--output", "-O"):
                self.output_file = arg
            elif opt in ("--port", "-Q"):
                self.tango_port = int(arg)
            elif opt in ("--quiet", "-q"):
                self.quiet_mode = True
            elif opt in ("--reverse", "-r"):
                self.reverse = True
            elif opt in ("--short", "-s"):
                self.disp_action.value = DispAction.TANGOCTL_SHORT
            elif opt in ("--show-attribute", "-a"):
                self.show_attrib = True
            elif opt in ("--show-command", "-c"):
                self.show_cmd = True
            elif opt in ("--show-db", "-t"):
                self.show_tango = True
            elif opt == "--show-dev":
                self.show_dev = True
            elif opt in ("--show-ns", "-k"):
                self.show_ns = True
            elif opt in ("--show-pod", "-x"):
                self.show_pod = True
            elif opt in ("--show-property", "-p"):
                self.show_prop = True
            elif opt == "--simul":
                self.dev_sim = int(arg)
            elif opt == "--standby":
                self.dev_standby = True
            elif opt == "--status":
                show_status = {
                    "attributes": list(self.cfg_data["list_items"]["attributes"].keys()),
                    "commands": list(self.cfg_data["list_items"]["commands"].keys()),
                    "properties": list(self.cfg_data["list_items"]["properties"].keys()),
                }
                self.logger.info("Status set to %s", show_status)
            elif opt == "--test":
                self.dev_test = True
            elif opt in ("--tree", "-b"):
                self.show_tree = True
            elif opt in ("--txt", "-t"):
                self.disp_action.value = DispAction.TANGOCTL_TXT
            # TODO Feature to search by input type not implemented yet
            elif opt in ("--type", "-T"):
                self.tgo_in_type = arg.lower()
                self.logger.info("Input type %s not implemented", self.tgo_in_type)
                return 1
            elif opt in ("--unique", "-u"):
                self.uniq_cls = True
            elif opt == "-v":
                self.logger.setLevel(logging.INFO)
            elif opt == "-V":
                self.logger.setLevel(logging.DEBUG)
            elif opt in ("--value", "-W"):
                self.tgo_value = str(arg)
            elif opt == "--version":
                self.show_version = True
            elif opt in ("--yaml", "-y"):
                self.disp_action.value = DispAction.TANGOCTL_YAML
            else:
                self.logger.error("Invalid option %s", opt)
                return 1

        if self.disp_action.check(DispAction.TANGOCTL_NONE):
            self.disp_action.value = DispAction.TANGOCTL_DEFAULT
            self.logger.info("Use default format %s", self.disp_action)

        return 0

    def get_pods_dict(self, ns_name: str | None) -> dict:
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :return: dictionary with devices
        """
        self.logger.debug("Read Kubernetes pods")
        pods_dict: dict = {}
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return pods_dict
        k8s = KubernetesInfo(self.logger)
        pods_dict = k8s.get_pods(ns_name, None)
        self.logger.info("Read %d pods", len(pods_dict))
        return pods_dict

    def print_pods(self, ns_name: str | None, quiet_mode: bool) -> None:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param quiet_mode: flag to suppress extra output
        """
        self.logger.debug("Print Kubernetes pods")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return
        k8s: KubernetesInfo = KubernetesInfo(self.logger)
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
                        # TODO to show nginx or not to show nginx
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
        self.logger.debug("Get Kubernetes pods as JSON")
        pods: dict = {}
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return pods
        pod_exec: list = ["ps", "-ef"]
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return pods
        k8s: KubernetesInfo = KubernetesInfo(self.logger)
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

    def show_pods(self) -> None:
        """Display pods in Kubernetes namespace."""
        self.logger.debug("Show Kubernetes pods as JSON")
        pods: dict
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            pods = self.get_pods_json(self.ns_name, self.quiet_mode)
            if self.output_file is not None:
                self.logger.info("Write output file %s", self.output_file)
                with open(self.output_file, "a") as outf:
                    outf.write(json.dumps(pods, indent=4))
            else:
                print(json.dumps(pods, indent=4))
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            pods = self.get_pods_json(self.ns_name, self.quiet_mode)
            if self.output_file is not None:
                self.logger.info("Write output file %s", self.output_file)
                with open(self.output_file, "a") as outf:
                    outf.write(yaml.dump(pods))
            else:
                print(yaml.dump(pods))
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.print_pods(self.ns_name, self.quiet_mode)
        else:
            self.logger.warning("Output format %s not supported", self.disp_action)
            pass

    def run_info(self, file_name: str | None) -> int:  # noqa: C901
        """
        Read information on Tango devices.

        :param file_name: output file name
        :return: error condition
        """
        rc: int
        devices: TangoctlDevices
        self.logger.info(
            "Run info display action %s : device %s attribute %s command %s property %s...",
            self.disp_action,
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
        )

        # List Tango devices
        if (
            self.disp_action.check(DispAction.TANGOCTL_LIST)
            and self.tgo_attrib is None
            and self.tgo_cmd is None
            and self.tgo_prop is None
        ):
            rc = self.list_devices()
            return rc

        # Get device classes
        if self.disp_action.check(DispAction.TANGOCTL_CLASS):
            rc = self.list_classes()
            return rc

        # Check if there is something to do
        if (
            self.tgo_name is None
            and self.tgo_attrib is None
            and self.tgo_cmd is None
            and self.tgo_prop is None
            and self.disp_action.check(0)
            and (not self.evrythng)
            and not (self.show_attrib or self.show_cmd or self.show_prop or self.show_status)
            and self.disp_action.check(
                [DispAction.TANGOCTL_JSON, DispAction.TANGOCTL_TXT, DispAction.TANGOCTL_YAML]
            )
        ):
            self.logger.error(
                "No filters specified, use '-l' flag to list all devices"
                " or '-e' for a full display of every device in the namespace",
            )
            return 1

        # Get a dictionary of devices
        try:
            devices = TangoctlDevices(
                self.logger,
                self.show_attrib,
                self.show_cmd,
                self.show_prop,
                self.show_status,
                self.cfg_data,
                self.tgo_name,
                self.uniq_cls,
                self.reverse,
                self.evrythng,
                self.tgo_attrib,
                self.tgo_cmd,
                self.tgo_prop,
                self.quiet_mode,
                file_name,
                self.disp_action,
                self.ns_name,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for K8S info failed")
            return 1
        devices.read_device_values()

        self.logger.debug("Read devices running in K8S (action %s)", self.disp_action)

        # Display in specified format
        if self.disp_action.check(DispAction.TANGOCTL_LIST) and self.tgo_attrib is not None:
            devices.print_txt_list_attributes()
        elif self.disp_action.check(DispAction.TANGOCTL_LIST) and self.tgo_cmd is not None:
            devices.print_txt_list_commands()
        elif self.disp_action.check(DispAction.TANGOCTL_LIST) and self.tgo_prop is not None:
            devices.print_txt_list_properties()
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            devices.print_txt(self.disp_action, f"{self.ns_name}" if self.ns_name else None)
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            devices.print_html(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_JSON):
            devices.print_json(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_MD):
            devices.print_markdown()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            devices.print_yaml(self.disp_action)
        else:
            self.logger.error("Display action %s not supported", self.disp_action)

        return 0

    def get_namespaces_list(self) -> list:
        """
        Read namespaces in Kubernetes cluster.

        :return: list with devices
        """
        self.logger.debug("List Kubernetes namespaces")
        ns_list: list = []
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return ns_list
        k8s: KubernetesInfo = KubernetesInfo(self.logger)
        k8s_list: list = k8s.get_namespaces_list(self.ns_name)
        if self.ns_name is None:
            return k8s_list
        for k8s in k8s_list:
            if k8s == self.ns_name:
                ns_list.append(k8s)
        self.logger.info("Read %d namespaces: %s", len(ns_list), ",".join(ns_list))
        return ns_list

    def get_namespaces_dict(self) -> dict:
        """
        Read namespaces in Kubernetes cluster.

        :return: dictionary with devices
        """
        self.logger.debug("Read Kubernetes namespaces")
        ns_dict: dict = {}
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return ns_dict
        k8s: KubernetesInfo = KubernetesInfo(self.logger)
        ns_dict = k8s.get_namespaces_dict()
        self.logger.info("Read %d namespaces", len(ns_dict))
        return ns_dict

    def show_namespaces(self) -> None:
        """Display namespaces in Kubernetes cluster."""
        self.logger.debug("Show Kubernetes namespaces")
        ns_dict: dict
        ns_list: list
        ns_name: str

        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return

        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            ns_dict = self.get_namespaces_dict()
            if self.output_file is not None:
                self.logger.info("Write output file %s", self.output_file)
                with open(self.output_file, "a") as outf:
                    outf.write(json.dumps(ns_dict, indent=4))
            else:
                print(json.dumps(ns_dict, indent=4))
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            ns_dict = self.get_namespaces_dict()
            if self.output_file is not None:
                self.logger.info("Write output file %s", self.output_file)
                with open(self.output_file, "a") as outf:
                    outf.write(yaml.dump(ns_dict))
            else:
                print(yaml.dump(ns_dict))
        else:
            ns_list = self.get_namespaces_list()
            print(f"Namespaces : {len(ns_list)}")
            for ns_name in sorted(ns_list, reverse=self.reverse):
                print(f"\t{ns_name}")

    def read_tango_host(self, ntango: int, ntangos: int) -> int:  # noqa: C901
        """
        Read info from Tango host.

        :param ntango: index number,
        :param ntangos: index count
        :return: error condition
        """
        rc: int = 0

        # Fork just in case,  so that ctrl-C will work
        pid: int = os.fork()
        if pid == 0:
            self.logger.info("Processing namespace %s", self.ns_name)
            if (
                self.disp_action.check(DispAction.TANGOCTL_JSON)
                and ntango == 1
                and self.disp_action.check(DispAction.TANGOCTL_SHORT)
            ):
                print("[")
            elif self.disp_action.check(DispAction.TANGOCTL_JSON) and ntango == 1:
                pass
            else:
                pass
            # Do the actual reading
            rc = self.run_info(self.output_file)
            # TODO this formatting stuff should not be here
            if (
                self.disp_action.check(DispAction.TANGOCTL_JSON)
                and ntango == ntangos
                and self.disp_action.check(DispAction.TANGOCTL_SHORT)
            ):
                print("]")
            elif self.disp_action.check(DispAction.TANGOCTL_JSON) and ntango == ntangos:
                pass
            elif self.disp_action.check(DispAction.TANGOCTL_JSON):
                print(",")
            else:
                pass
            self.logger.info("Processed namespace %s", self.ns_name)
            sys.exit(rc)
        else:
            try:
                os.waitpid(pid, 0)
            except OSError:
                pass
            self.logger.info("Processing %s finished (PID %d)", self.ns_name, pid)

        return rc
