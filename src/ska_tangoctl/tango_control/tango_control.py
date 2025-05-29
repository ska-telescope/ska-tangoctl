"""Read all information about Tango devices in a Kubernetes cluster."""

import getopt
import json
import logging
import os
import socket
from typing import Any, OrderedDict

import tango

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevices, TangoctlDevicesBasic
from ska_tangoctl.tango_control.tangoctl_config import TANGOCTL_CONFIG, read_tangoctl_config
from ska_tangoctl.tango_control.test_tango_script import TangoScript


class TangoControl:
    """Connect to Tango environment and retrieve information."""

    def __init__(self, logger: logging.Logger):
        """
        Set it up.

        :param logger: logging handle
        """
        self.logger = logger
        self.cfg_name: str | None = None
        self.cfg_data: Any = TANGOCTL_CONFIG
        self.cfg_name: str | None = None
        self.dev_on: bool = False
        self.dev_off: bool = False
        self.dev_standby: bool = False
        self.dev_status: dict = {}
        self.dev_test: bool = False
        self.dev_admin: int | None = None
        self.dev_sim: int | None = None
        self.disp_action: DispAction = DispAction(DispAction.TANGOCTL_NONE)
        self.dry_run: bool = False
        self.evrythng: bool = False
        self.input_file: str | None = None
        self.json_dir: str | None = None
        self.output_file: str | None = None
        self.quiet_mode: bool = False
        self.rc: int
        self.reverse: bool = False
        self.show_attrib: bool = False
        self.show_cmd: bool = False
        self.show_dev: bool = False
        self.show_jargon: bool = False
        self.show_prop: bool = False
        self.show_status: dict = {}
        self.show_tango: bool = False
        self.show_tree: bool = False
        self.show_version: bool = False
        self.tango_host: str | None = None
        self.tango_port: int = 10000
        self.tgo_attrib: str | None = None
        self.tgo_cmd: str | None = None
        # TODO Feature to search by input type not implemented yet
        self.tgo_in_type: str | None = None
        self.tgo_name: str | None = None
        self.tgo_prop: str | None = None
        self.tgo_value: str | None = None
        self.uniq_cls: bool = False

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
    ):
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

    def read_config(self):
        # Read configuration
        self.cfg_data: Any = read_tangoctl_config(self.cfg_name, self.cfg_name)

    def __del__(self) -> None:
        """Destructor."""
        self.logger.debug("Shut down TangoControl")

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
        # Display class names
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -d|--class [--host=<HOST>]")
        print(f"\t{p_name} -d|--class [-H <HOST>]")
        print(f"e.g. \033[3m{p_name} \033[0m")
        # List device names
        print("\nList Tango device names")
        print(f"\t{p_name} --show-dev [--host=<HOST>]")
        print(f"\t{p_name} -l [-H <HOST>]")
        print(f"e.g. \033[3m{p_name} -l -K integration\033[0m")
        print("\nDisplay all Tango devices (will take a long time)")
        print(f"\t{p_name} --full|--short -e|--everything [--host=<HOST>]")
        print(f"\t{p_name} -l\033[0m")
        print(f"\te.g. \033[3m{p_name} -f|-s[-H <HOST>]\033[0m")
        # Display devices
        print("\nFilter on device name")
        print(f"\t{p_name} --full|--short -D <DEVICE>[-H <HOST>]")
        print(f"\t{p_name} -f|-s --device=<DEVICE> [--host=<HOST>]")
        print(f"e.g. \033[3m{p_name} -f -D ska_mid/tm_leaf_node/csp_subarray01\033[0m")
        # Display attributes
        print("\nFilter on attribute name")
        print(f"\t{p_name} --full|--short --attribute=<ATTRIBUTE> [--host=<HOST>]")
        print(f"\t{p_name} -f|-s -A <ATTRIBUTE>[-H <HOST>]")
        print(f"e.g. \033[3m{p_name} -f -K integration -A timeout\033[0m")
        # Display commands
        print("\nFilter on command name")
        print(f"\t{p_name} --full|--short --command=<COMMAND> [--host=<HOST>]")
        print(f"\t{p_name} -f|-s -C <COMMAND>[-H <HOST>]")
        print(f"e.g. \033[3m{p_name} -l -K integration -C status\033[0m")
        # Display properties
        print("\nFilter on property name")
        print(f"\t{p_name} --full|--list|--short --property=<PROPERTY> [--host=<HOST>]")
        print(f"\t{p_name} -f|-s -P <PROPERTY> [--host=<HOST>]")
        print(f"e.g. \033[3m{p_name} -l -K integration -P power\033[0m")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir=<PATH>")
        print(f"\t{p_name} -J <PATH>")
        print(f"e.g. \033[3mADMIN_MODE=1 {p_name} -J resources/\033[0m")
        print("\nRun test, reading from input file")
        print(f"\t{p_name} --input=<FILE>")
        print(f"\t{p_name} -I <FILE>")
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
        # Testing
        print("\n\033[1mTest Tango devices:\033[0m")
        print("\nTest a Tango device")
        print(f"\t{p_name}[-H <HOST>] -D <DEVICE> [--simul=<0|1>]")
        print("\nTest a Tango device and read attributes")
        print(f"\t{p_name} -a[-H <HOST>] -D <DEVICE> [--simul=<0|1>]")
        print("\nDisplay attribute and command names for a Tango device")
        print(f"\t{p_name} -c[-H <HOST>] -D <DEVICE>")
        print("\nTurn a Tango device on")
        print(f"\t{p_name} --on[-H <HOST>] -D <DEVICE> [--simul=<0|1>]")
        print("\nTurn a Tango device off")
        print(f"\t{p_name} --off[-H <HOST>] -D <DEVICE> [--simul=<0|1>]")
        print("\nSet a Tango device to standby mode")
        print(f"\t{p_name} --standby[-H <HOST>] -D <DEVICE> [--simul=<0|1>]")
        print("\nChange admin mode on a Tango device")
        print(f"\t{p_name} --admin=<0|1>")
        print("\nDisplay status of a Tango device")
        print(f"\t{p_name} --status[-H <HOST>] -D <DEVICE>")
        print("\nCheck events for attribute of a Tango device")
        print(f"\t{p_name}[-H <HOST>] -D <DEVICE> -A <ATTRIBUTE>")
        # Options and parameters
        print("\n\033[1mParameters:\033[0m\n")
        print("\t-a\t\t\t\tflag for reading attributes during tests")
        print("\t-c|--cmd\t\t\tflag for running commands during tests")
        print("\t--simul=<0|1>\t\t\tset simulation mode off or on")
        print("\t--admin=<0|1>\t\t\tset admin mode off or on")
        print("\t-e|--everything\t\t\tshow all devices")
        print("\t-f|--full\t\t\tdisplay in full")
        print("\t-l|--list\t\t\tdisplay device name and status on one line")
        print("\t-s|--short\t\t\tdisplay device name, status and query devices")
        print("\t-q|--quiet\t\t\tdo not display progress bars")
        print("\t-w|--html\t\t\toutput in HTML format")
        print("\t-j|--json\t\t\toutput in JSON format")
        print("\t-m|--md\t\t\t\toutput in markdown format")
        print("\t-y|--yaml\t\t\toutput in YAML format")
        print("\t-u|--unique\t\t\tonly read one device for each class")
        print("\t--cfg=<FILE>\t\toverride configuration from file")
        print("\t-X <FILE>")
        print("\t--json-dir=<PATH>\t\tdirectory with JSON input file, e.g. 'resources'")
        print("\t-J <PATH>")
        print(
            "\t--device=<DEVICE>\t\tdevice name, e.g. 'csp'"
            " (not case sensitive, only a part is needed)"
        )
        print("\t-D <DEVICE>")
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
            "\nRun the following commands where applicable:"
            f"\n\t{','.join(self.cfg_data['run_commands'])}"
        )
        print(
            f"\nRun commands with device name as parameter where applicable:\n"
            f"\t{','.join(self.cfg_data['run_commands_name'])}"
        )
        # Some more examples
        print("\n\033[1mExamples:\033[0m\n")
        print(f"\t{p_name} -l")
        print(f"\t{p_name} -D talon -l")
        print(f"\t{p_name} -A timeout")
        print(f"\t{p_name} -C Telescope")
        print(f"\t{p_name} -P Power")
        print(f"\t{p_name} -D mid_csp_cbf/talon_lru/001 -f")
        print(f"\t{p_name} -D mid_csp_cbf/talon_lru/001 -q")
        print(f"\t{p_name} -D mid_csp_cbf/talon_board/001 -f")
        print(f"\t{p_name} -D mid_csp_cbf/talon_board/001 -f --dry")
        print(f"\t{p_name} -D mid-sdp/control/0 --on")
        print(
            f"\tADMIN_MODE=1 {p_name} "
            f" -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V"
        )
        print()

    def read_command_line(self, cli_args: list) -> int:
        """
        Read the command line interface.

        :param cli_args: arguments
        :return: error condition
        """
        try:
            opts, _args = getopt.getopt(
                cli_args[1:],
                "abcdefhjklmnoqstuvwyVA:C:H:D:I:J:p:O:P:T:W:X:",
                [
                    "class",
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
                    "show-attribute",
                    "show-acronym",
                    "show-command",
                    "show-db",
                    "show-dev",
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
            elif opt in ("--port", "-p"):
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
            elif opt in ("--show-property", "-p"):
                self.show_prop = True
            elif opt == "--simul":
                self.dev_sim = int(arg)
            elif opt == "--standby":
                self.dev_standby = True
            elif opt == "--status":
                self.dev_status = {"attributes": ["Status", "adminMode"]}
            elif opt == "--test":
                self.dev_test = True
            elif opt in ("--tree", "-b"):
                self.show_tree = True
            # TODO Feature to search by input type not implemented yet
            elif opt in ("--type", "-T"):
                tgo_in_type = arg.lower()
                self.logger.info("Input type %s not implemented", tgo_in_type)
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
        return 0

    def read_input_file(self) -> None:
        """
        Read instructions from JSON file.

        :param input_file: input file name
        :param tgo_name: device name
        :param dry_run: flag for dry run
        """
        inf: str
        tgo_script: TangoScript

        if self.input_file is None:
            return
        inf = self.input_file
        tgo_script = TangoScript(self.logger, inf, self.tgo_name, self.dry_run)
        tgo_script.run()

    def check_tango(self) -> int:
        """
        Check Tango host address.

        :param tango_host: fully qualified domain name
        :param quiet_mode: flag to suppress extra output
        :param tango_port: port number
        :return: error condition
        """
        tango_fqdn: str
        tport: int
        tango_addr: tuple[str, list[str], list[str]]
        tango_ip: str

        if ":" in self.tango_host:
            tango_fqdn = self.tango_host.split(":")[0]
            tport = int(self.tango_host.split(":")[1])
        else:
            tango_fqdn = self.tango_host
            tport = self.tango_port
        self.logger.info("Check Tango host %s:%d", tango_fqdn, tport)
        try:
            tango_addr = socket.gethostbyname_ex(tango_fqdn)
            tango_ip = tango_addr[2][0]
        except socket.gaierror as e:
            self.logger.error("Could not read address %s : %s" % (tango_fqdn, e))
            return 1
        if not self.quiet_mode:
            print(f"TANGO_HOST={tango_fqdn}:{tport}")
            print(f"TANGO_HOST={tango_ip}:{tport}")
        return 0

    def get_tango_classes(self) -> dict:
        """
        Read tango classes.

        :param disp_action: output format
        :param evrythng: get commands and attributes regadrless of state
        :param quiet_mode: flag for displaying progress bars
        :param tgo_name: device name
        :param reverse: sort in reverse order
        :return: dictionary with devices
        """
        devices: TangoctlDevicesBasic
        dev_classes: OrderedDict

        try:
            devices = TangoctlDevicesBasic(
                self.logger,
                self.show_attrib,
                self.show_cmd,
                self.show_prop,
                self.show_status,
                self.cfg_data,
                self.tgo_name,
                False,
                self.reverse,
                self.evrythng,
                self.disp_action,
                self.quiet_mode,
                None,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for classes failed")
            return {}
        except Exception:
            self.logger.error("Tango connection for classes failed")
            return {}
        devices.read_configs()
        dev_classes = devices.get_classes(self.reverse)
        return dev_classes

    def list_classes(self) -> int:
        """
        Get device classes.

        :return: error condition
        """
        devices: TangoctlDevicesBasic
        dev_classes: OrderedDict

        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            self.logger.info("Get device classes in JSON format")
            try:
                devices = TangoctlDevicesBasic(
                    self.logger,
                    self.show_attrib,
                    self.show_cmd,
                    self.show_prop,
                    self.show_status,
                    self.cfg_data,
                    self.tgo_name,
                    False,
                    self.reverse,
                    self.evrythng,
                    self.disp_action,
                    self.quiet_mode,
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection for JSON class list failed")
                return 1
            devices.read_configs()
            dev_classes = devices.get_classes(self.reverse)
            print(json.dumps(dev_classes, indent=4))
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.logger.info("List device classes (%s)", self.disp_action)
            try:
                devices = TangoctlDevicesBasic(
                    self.logger,
                    self.show_attrib,
                    self.show_cmd,
                    self.show_prop,
                    self.show_status,
                    self.cfg_data,
                    self.tgo_name,
                    False,
                    self.reverse,
                    self.evrythng,
                    self.disp_action,
                    self.quiet_mode,
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection for text class list failed")
                return 1
            devices.read_configs()
            devices.print_txt_classes()
        else:
            self.logger.error("Format '%s' not supported for listing classes", self.disp_action)
            return 1
        return 0

    def list_devices(
        self,
        file_name: str | None,
    ) -> int:
        """
        List Tango devices.

        :param file_name: output file name
        :return: error condition
        """
        devices: TangoctlDevicesBasic

        self.logger.info("List devices (%s) with name %s", self.disp_action, self.tgo_name)
        try:
            devices = TangoctlDevicesBasic(
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
                self.disp_action,
                self.quiet_mode,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for listing devices failed")
            return 1
        except Exception as eerr:
            self.logger.error("Tango connection for listing devices failed : %s", eerr)
            return 1
        devices.read_configs()
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            devices.print_json(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            self.devices.print_yaml(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            self.devices.print_html(self.disp_action)
        else:
            devices.print_txt_list()

        return 0

    def read_input_files(self, json_dir: str) -> int:
        """
        Read info from JSON script files.

        :param json_dir: directory with script files
        :return: error condition
        """
        rv: int
        relevant_path: str
        file_names: list
        file_name: str
        cfg_data: Any
        description: str

        rv = 0
        self.logger.info("List JSON files in %s", json_dir)
        relevant_path = json_dir
        # TODO read YAML files as well
        # included_extensions = ["json", "yaml"]
        included_extensions: list = ["json"]
        file_names = [
            fn
            for fn in os.listdir(relevant_path)
            if any(fn.endswith(ext) for ext in included_extensions)
        ]
        if not file_names:
            self.logger.warning("No JSON files found in %s", json_dir)
            return 1
        for file_name in file_names:
            file_name = os.path.join(json_dir, file_name)
            with open(file_name) as cfg_file:
                try:
                    cfg_data = json.load(cfg_file)
                    try:
                        description = cfg_data["description"]
                        if not self.quiet_mode:
                            print(f"{file_name:40} {description}")
                    except KeyError:
                        self.logger.warning("File %s is not a tangoctl input file", file_name)
                        rv += 1
                except json.decoder.JSONDecodeError:
                    self.logger.warning("File %s is not a JSON file", file_name)
        return rv

    def set_value(self) -> int:
        """
        Set value for a Tango device.

        :param tgo_name: device name
        :param quiet_mode: flag for displaying progress bar
        :param reverse: sort in reverse order
        :param tgo_attrib: attribute name
        :param tgo_value: attribute value
        :return: error condition
        """
        dev: TangoctlDevice

        dev = TangoctlDevice(
            self.logger,
            self.show_attrib,
            self.show_cmd,
            self.show_prop,
            self.show_status,
            self.tgo_name,
            self.quiet_mode,
            self.reverse,
            {},
            {},
            None,
            None,
            None,
        )
        dev.read_attribute_value()
        self.logger.info(
            "Set device %s attribute %s value to %s",
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_value,
        )
        dev.write_attribute_value(self.tgo_attrib, self.tgo_value)
        return 0

    def run_info(self, file_name: str | None) -> int:  # noqa: C901
        """
        Read information on Tango devices.

        :param file_name: output file
        :return: error condition
        """
        rc: int
        devices: TangoctlDevices

        self.logger.info(
            "Info display aktion %d : device %s attribute %s command %s property %s",
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
            rc = self.list_devices(file_name)
            return rc

        # Get Tango device classes
        if self.disp_action.check(DispAction.TANGOCTL_CLASS):
            rc = self.list_classes(
                self.disp_action, self.evrythng, self.quiet_mode, self.reverse, self.tgo_name
            )
            return rc

        if file_name is not None:
            if os.path.splitext(file_name)[-1] != f".{str(self.disp_action)}":
                file_name = f"{file_name}.{str(self.disp_action)}"
                self.logger.warning("File name changed to %s", file_name)

        if (
            self.tgo_name is None
            and self.tgo_attrib is None
            and self.tgo_cmd is None
            and self.tgo_prop is None
            and self.disp_action.check(0)
            and (not self.evrythng)
            and self.disp_action.check(
                [DispAction.TANGOCTL_JSON, DispAction.TANGOCTL_TXT, DispAction.TANGOCTL_YAML]
            )
        ):
            self.logger.error(
                "No filters specified, use '-l' flag to list all devices"
                " or '-e' for a full display of every device in the namespace",
            )
            return 1

        # Read devices while applying filters
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
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for info failed")
            return 1
        devices.read_device_values(
            self.show_attrib, self.show_cmd, self.show_prop, self.show_status
        )

        self.logger.debug("Read devices (action %s)", disp_action)

        if self.disp_action.check(DispAction.TANGOCTL_TXT):
            devices.print_txt(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            devices.print_html(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_JSON):
            devices.print_json(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_MD):
            devices.print_markdown()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            devices.print_yaml(self.disp_action)
        else:
            print("---")

        return 0
