"""Read all information about Tango devices in a Kubernetes cluster."""

import getopt
import json
import logging
import os
import socket
from typing import Any, OrderedDict

import tango

from ska_tangoctl.tango_control.disp_action import BOLD, UNDERL, UNFMT, DispAction
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
        self.xact_match = False

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
        xact_match: bool = False,
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
        :param xact_match: exact matches only
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
        self.xact_match = xact_match
        # TODO Feature to search by input type not implemented yet
        self.tgo_in_type = tgo_in_type
        self.tgo_name = tgo_name
        self.tgo_prop = tgo_prop
        self.tgo_value = tgo_value
        self.uniq_cls = uniq_cls

    def read_config(self) -> None:
        """Read configuration."""
        self.cfg_data = read_tangoctl_config(self.logger, self.cfg_name)

    def __del__(self) -> None:
        """Destructor."""
        self.logger.debug("Shut down TangoControl")

    def usage(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        # Reading devices
        print(f"{BOLD}Read Tango devices:{UNFMT}")
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help")
        print(f"\t{p_name} -h")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -d|--class [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -d|--class [-H {UNDERL}HOST{UNFMT}]")
        print("\nList Tango device names")
        print(f"\t{p_name} --show-dev [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -l [-H {UNDERL}HOST{UNFMT}]")
        print("\nDisplay all Tango devices (will take a long time)")
        print(f"\t{p_name} --full|--short -e|--everything [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -l{UNFMT}")
        print("\nFilter on device name")
        print(f"\t{p_name} --full|--short -D {UNDERL}NAME{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -f|-s --device={UNDERL}NAME{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        print("\nFilter on attribute name")
        print(
            f"\t{p_name} --full|--short --attribute={UNDERL}NAME{UNFMT}"
            f" [--host={UNDERL}HOST{UNFMT}]"
        )
        print(f"\t{p_name} -f|-s -A {UNDERL}NAME{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print("\nFilter on command name")
        print(
            f"\t{p_name} --full|--short --command={UNDERL}NAME{UNFMT}"
            f" [--host={UNDERL}HOST{UNFMT}]"
        )
        print(f"\t{p_name} -f|-s -C {UNDERL}NAME{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print("\nFilter on property name")
        print(
            f"\t{p_name} --full|--list|--short --property={UNDERL}NAME{UNFMT}"
            f" [--host={UNDERL}HOST{UNFMT}]"
        )
        print(f"\t{p_name} -f|-s -P {UNDERL}NAME{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir={UNDERL}PATH{UNFMT}")
        print(f"\t{p_name} -J {UNDERL}PATH{UNFMT}")
        print(
            "\nRun test, reading from input file"
            " (in JSON format with values to be read and/or written)."
        )
        print(f"\t{p_name} --input={UNDERL}FILE{UNFMT}")
        print(f"\t{p_name} -I {UNDERL}FILE{UNFMT}")
        # Testing
        print(f"\n{BOLD}Test Tango devices:{UNFMT}")
        print("\nTest a Tango device")
        print(
            f"\t{p_name} [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}NAME{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
            f"")
        print("\nTest a Tango device and read attributes")
        print(
            f"\t{p_name} -a [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}NAME{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nDisplay attribute and command names for a Tango device")
        print(f"\t{p_name} -c [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}NAME{UNFMT}")
        print("\nTurn a Tango device on")
        print(
            f"\t{p_name} --on [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}NAME{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTurn a Tango device off")
        print(
            f"\t{p_name} --off [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}NAME{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nSet a Tango device to standby mode")
        print(
            f"\t{p_name} --standby [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}NAME{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nChange admin mode on a Tango device")
        print(f"\t{p_name} --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}")
        print("\nDisplay status of a Tango device")
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" [--host {UNDERL}HOST{UNFMT}] --device {UNDERL}NAME{UNFMT}"
        )
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}NAME{UNFMT}"
        )
        print("\nCheck events for attribute of a Tango device")
        print(
            f"\t{p_name} [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}NAME{UNFMT} -A {UNDERL}NAME{UNFMT}"
        )
        # Options and parameters
        print(f"\n{BOLD}Parameters:{UNFMT}\n")
        print(f"\t-a, --show-attribute\t\tflag for reading attributes")
        print(f"\t-b, --tree\t\t\tdisplay tree of devices")
        print(f"\t-c, --show-command\t\tread commands")
        print(f"\t-e, --everything\t\tshow all devices")
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-f, --full\t\t\tshow all devices - do not skip {ign}")
        print("\t-i, --ip\t\t\t\tuse IP address instead of FQDN")
        print(f"\t-j, --json\t\t\toutput in JSON format")
        print(f"\t-l, --list\t\t\tdisplay device name and status on one line")
        print(f"\t-m, --md\t\t\toutput in markdown format")
        print(f"\t-p, --show-property\t\tread properties")
        print(f"\t-q, --quiet\t\t\tdo not display progress bars")
        # print("\t-s, --short\t\t\tdisplay device name, status and query devices")
        print("\t-t, --txt\t\t\toutput in text format")
        print(f"\t-u, --unique\t\t\tonly read one device for each class")
        print(f"\t-w, --html\t\t\toutput in HTML format")
        print(f"\t-y, --yaml\t\t\toutput in YAML format")
        print(f"\t--admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset admin mode off or on")
        print(f"\t--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset simulation mode off or on")
        print(f"\t-A {UNDERL}NAME{UNFMT}, --attribute={UNDERL}NAME{UNFMT}\tattribute name")
        print(f"\t-C {UNDERL}NAME{UNFMT}, --command={UNDERL}NAME{UNFMT}\t\tcommand name")
        print(f"\t-D {UNDERL}NAME{UNFMT}, --device={UNDERL}NAME{UNFMT}\t\tdevice name")
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            f"\t\tTango database host and port"
        )
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT}\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            "\tdirectory with JSON input file"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\toutput file name")
        print(f"\t-P {UNDERL}NAME{UNFMT}, --property={UNDERL}NAME{UNFMT}\tproperty name")
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            f"\t\toverride configuration from file"
        )
        print(f"\t-v\t\t\t\tset logging level to INFO")
        print(f"\t-V\t\t\t\tset logging level to DEBUG")
        print(f"\t-0, --on\t\t\tturn device on")
        print(f"\t-1, --off\t\t\tturn device off")
        # Configuration
        print(f"\n{BOLD}Default configuration:{UNFMT}\n")
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
        # Et cetera
        print(f"\n{BOLD}See also:{UNFMT}\n")
        print(f"\t{BOLD}man tangoctl{UNFMT}")
        print()

    def read_command_line(self, cli_args: list) -> int:  # noqa: C901
        """
        Read the command line interface.

        :param cli_args: arguments
        :return: error condition
        """
        try:
            opts, _args = getopt.getopt(
                cli_args[1:],
                "abcdefhijlmnpqrstuvwxyV01A:C:H:D:H:I:J:O:P:Q:T:W:X:",
                [
                    "dry-run",
                    "everything",
                    "exact",
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
                    "standby",
                    "status",
                    "short",
                    "show-attribute",
                    "show-acronym",
                    "show-class",
                    "show-command",
                    "show-db",
                    "show-dev",
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
            if opt in ("-a", "--show-attribute"):
                self.show_attrib = True
            elif opt in ("-A", "--attribute"):
                self.tgo_attrib = arg
                self.show_attrib = True
            elif opt in ("-b", "--tree"):
                self.show_tree = True
            elif opt in ("-c", "--show-command"):
                self.show_cmd = True
            elif opt in ("-C", "--command"):
                self.tgo_cmd = arg.lower()
                self.show_cmd = True
            elif opt in ("-d", "--show-dev"):
                self.show_dev = True
            elif opt in ("-D", "--device"):
                self.tgo_name = arg.lower()
            elif opt in ("-e", "--everything"):
                self.evrythng = True
                self.show_attrib = True
                self.show_cmd = True
                self.show_dev = True
                self.show_prop = True
            elif opt in ("-f", "--full"):
                self.disp_action.value = DispAction.TANGOCTL_FULL
            elif opt in ("-g", "--show-class"):
                self.disp_action.value = DispAction.TANGOCTL_CLASS
            elif opt in ("-h", "--help"):
                self.usage(os.path.basename(cli_args[0]))
                return 1
            elif opt in ("-H", "--host"):
                self.tango_host = arg
            elif opt in ("-i", "--show-db"):
                self.show_tango = True
            elif opt in ("-I", "--input"):
                self.input_file = arg
            elif opt in ("-j", "--json"):
                self.disp_action.value = DispAction.TANGOCTL_JSON
            elif opt in ("-J", "--json-dir"):
                self.json_dir = arg
            elif opt in ("-l", "--list"):
                self.disp_action.value = DispAction.TANGOCTL_LIST
            elif opt in ("-m", "--md"):
                self.disp_action.value = DispAction.TANGOCTL_MD
            # TODO Undocumented and unused feature for dry runs
            elif opt in ("-n", "--dry-run"):
                self.dry_run = True
            elif opt in ("-O", "--output"):
                self.output_file = arg
            elif opt in ("-p", "--show-property"):
                self.show_prop = True
            elif opt in ("-P", "--property"):
                self.tgo_prop = arg.lower()
                self.show_prop = True
            elif opt in ("-q", "--quiet"):
                self.quiet_mode = True
            elif opt in ("-Q", "--port"):
                self.tango_port = int(arg)
            elif opt in ("-r", "--reverse"):
                self.reverse = True
            elif opt in ("-s", "--short"):
                self.disp_action.value = DispAction.TANGOCTL_SHORT
            elif opt == "--standby":
                self.dev_standby = True
            elif opt == "--status":
                self.dev_status = {"attributes": ["Status", "adminMode"]}
            elif opt in ("-t", "--txt"):
                self.disp_action.value = DispAction.TANGOCTL_TXT
            # TODO Feature to search by input type not implemented yet
            elif opt in ("-T", "--type"):
                tgo_in_type = arg.lower()
                self.logger.info("Input type %s not implemented", tgo_in_type)
            elif opt == "--test":
                self.dev_test = True
            elif opt in ("-u", "--unique"):
                self.uniq_cls = True
            elif opt == "-v":
                self.logger.setLevel(logging.INFO)
            elif opt == "-V":
                self.logger.setLevel(logging.DEBUG)
            elif opt == "--version":
                self.show_version = True
            elif opt in ("-w", "--html"):
                self.disp_action.value = DispAction.TANGOCTL_HTML
            elif opt in ("-W", "--value"):
                self.tgo_value = str(arg)
            elif opt in ("-x", "--exact"):
                self.xact_match = True
            elif opt in ("-X", "--cfg"):
                self.cfg_name = arg
            elif opt in ("-y", "--yaml"):
                self.disp_action.value = DispAction.TANGOCTL_YAML
            # TODO simulation to be deprecated
            elif opt in ("-Z", "--simul"):
                self.dev_sim = int(arg)
            elif opt in ("0", "--off"):
                self.dev_off = True
            elif opt in ("1", "--on"):
                self.dev_on = True
            else:
                self.logger.error("Invalid option %s", opt)
                return 1
        return 0

    def read_input_file(self) -> None:
        """Read instructions from JSON file."""
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

        :return: error condition
        """
        tango_fqdn: str | None
        tport: int
        tango_addr: tuple[str, list[str], list[str]]
        tango_ip: str

        if self.tango_host is not None and ":" in self.tango_host:
            tango_fqdn = self.tango_host.split(":")[0]
            tport = int(self.tango_host.split(":")[1])
        else:
            tango_fqdn = self.tango_host
            tport = self.tango_port
        self.logger.info("Check Tango host %s:%d", tango_fqdn, tport)
        try:
            tango_addr = socket.gethostbyname_ex(str(tango_fqdn))
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
                self.xact_match,
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
                    self.xact_match,
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
                    self.xact_match,
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

    def list_devices(self) -> int:
        """
        List Tango devices.

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
                self.xact_match,
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
            devices.print_yaml(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            devices.print_html(self.disp_action)
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

        :return: error condition
        """
        dev: TangoctlDevice

        if self.tgo_name is None:
            self.logger.error("Tango device name not set")
            return 1

        if self.tgo_attrib is None:
            self.logger.error("Tango attribute name not set")
            return 1

        if self.tgo_value is None:
            self.logger.error("Tango attribute value not set")
            return 1

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
            "Info display aktion %s : device %s attribute %s command %s property %s",
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

        # Get Tango device classes
        if self.disp_action.check(DispAction.TANGOCTL_CLASS):
            rc = self.list_classes()
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
                self.xact_match,
                self.disp_action,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for info failed")
            return 1
        devices.read_device_values()

        self.logger.debug("Read devices (action %s)", self.disp_action)

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
