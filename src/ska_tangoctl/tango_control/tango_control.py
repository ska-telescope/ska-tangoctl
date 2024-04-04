"""Read all information about Tango devices in a Kubernetes cluster."""

import json
import logging
import os
import socket
from typing import Any, OrderedDict

import tango

from ska_mid_itf_engineering_tools.tango_control.read_tango_device import TangoctlDevice
from ska_mid_itf_engineering_tools.tango_control.read_tango_devices import (
    TangoctlDevices,
    TangoctlDevicesBasic,
)
from ska_mid_itf_engineering_tools.tango_control.test_tango_script import TangoScript


class TangoControl:
    """Connect to Tango environment and retrieve information."""

    def __init__(self, logger: logging.Logger, cfg_data: Any):
        """
        Get the show on the road.

        :param logger: logging handle
        :param cfg_data: configuration in JSON format
        """
        self.logger = logger
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
        print(f"\te.g. \033[3m{p_name} -f|-s[-H <HOST>]")
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

    def read_input_file(self, input_file: str | None, tgo_name: str | None, dry_run: bool) -> None:
        """
        Read instructions from JSON file.

        :param input_file: input file name
        :param tgo_name: device name
        :param dry_run: flag for dry run
        """
        if input_file is None:
            return
        inf: str = input_file
        tgo_script: TangoScript = TangoScript(self.logger, inf, tgo_name, dry_run)
        tgo_script.run()

    def check_tango(
        self,
        tango_host: str,
        quiet_mode: bool,
        tango_port: int = 10000,
    ) -> int:
        """
        Check Tango host address.

        :param tango_host: fully qualified domain name
        :param quiet_mode: flag to suppress extra output
        :param tango_port: port number
        :return: error condition
        """
        tango_fqdn: str
        tport: int
        if ":" in tango_host:
            tango_fqdn = tango_host.split(":")[0]
            tport = int(tango_host.split(":")[1])
        else:
            tango_fqdn = tango_host
            tport = tango_port
        self.logger.info("Check Tango host %s:%d", tango_fqdn, tport)
        try:
            tango_addr = socket.gethostbyname_ex(tango_fqdn)
            tango_ip = tango_addr[2][0]
        except socket.gaierror as e:
            self.logger.error("Could not read address %s : %s" % (tango_fqdn, e))
            return 1
        if not quiet_mode:
            print(f"TANGO_HOST={tango_fqdn}:{tport}")
            print(f"TANGO_HOST={tango_ip}:{tport}")
        return 0

    def get_tango_classes(
        self,
        fmt: str,
        evrythng: bool,
        quiet_mode: bool,
        tgo_name: str | None,
    ) -> dict:
        """
        Read tango classes.

        :param fmt: output format
        :param evrythng: get commands and attributes regadrless of state
        :param quiet_mode: flag for displaying progress bars
        :param tgo_name: device name
        :return: dictionary with devices
        """
        try:
            devices: TangoctlDevicesBasic = TangoctlDevicesBasic(
                self.logger, False, quiet_mode, evrythng, self.cfg_data, tgo_name, fmt
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection failed")
            return {}
        devices.read_config()
        dev_classes = devices.get_classes()
        return dev_classes

    def list_classes(
        self,
        fmt: str,
        evrythng: bool,
        quiet_mode: bool,
        tgo_name: str | None,
    ) -> int:
        """
        Get device classes.

        :param fmt: output format
        :param evrythng: get commands and attributes regadrless of state
        :param quiet_mode: flag for displaying progress bars
        :param tgo_name: device name
        :return: error condition
        """
        self.logger.info("List classes")
        if fmt == "json":
            self.logger.info("Get device classes")
            try:
                devices: TangoctlDevicesBasic = TangoctlDevicesBasic(
                    self.logger, False, quiet_mode, evrythng, self.cfg_data, tgo_name, fmt
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection failed")
                return 1
            devices.read_config()
            dev_classes: OrderedDict = devices.get_classes()
            print(json.dumps(dev_classes, indent=4))
        return 0

    def list_devices(
        self,
        file_name: str | None,
        fmt: str,
        evrythng: bool,
        quiet_mode: bool,
        disp_action: int,
        tgo_name: str | None,
    ) -> int:
        """
        List Tango devices.

        :param file_name: output file name
        :param fmt: output format
        :param evrythng: get commands and attributes regadrless of state
        :param quiet_mode: flag for displaying progress bars
        :param disp_action: flag for output format
        :param tgo_name: device name
        :return: error condition
        """
        devices: TangoctlDevicesBasic
        if disp_action == 4:
            self.logger.info("List devices (%s) with name %s", fmt, tgo_name)
            try:
                devices = TangoctlDevicesBasic(
                    self.logger, False, quiet_mode, evrythng, self.cfg_data, tgo_name, fmt
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection failed")
                return 1
            devices.read_config()
            if fmt == "json":
                devices.print_json(0)
            elif fmt == "yaml":
                devices.print_yaml(0)
            else:
                devices.print_txt_list()
        elif disp_action == 5:
            self.logger.info("List device classes (%s)", fmt)
            try:
                devices = TangoctlDevicesBasic(
                    self.logger, False, quiet_mode, evrythng, self.cfg_data, tgo_name, fmt
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection failed")
                return 1
            devices.read_config()
            devices.print_txt_classes()
        else:
            pass
        return 0

    def read_input_files(self, json_dir: str, quiet_mode: bool = True) -> int:
        """
        Read info from JSON script files.

        :param json_dir: directory with script files
        :param quiet_mode: turn off progress bar
        :return: error condition
        """
        rv: int = 0
        self.logger.info("List JSON files in %s", json_dir)
        relevant_path: str = json_dir
        # TODO read YAML files as well
        # included_extensions = ["json", "yaml"]
        included_extensions: list = ["json"]
        file_names: list = [
            fn
            for fn in os.listdir(relevant_path)
            if any(fn.endswith(ext) for ext in included_extensions)
        ]
        if not file_names:
            self.logger.info("No JSON files found in %s", json_dir)
            return 1
        for file_name in file_names:
            file_name = os.path.join(json_dir, file_name)
            with open(file_name) as cfg_file:
                try:
                    cfg_data: Any = json.load(cfg_file)
                    try:
                        description = cfg_data["description"]
                        if not quiet_mode:
                            print(f"{file_name:40} {description}")
                    except KeyError:
                        self.logger.info("File %s is not a tangoctl input file", file_name)
                        rv += 1
                except json.decoder.JSONDecodeError:
                    self.logger.info("File %s is not a JSON file", file_name)
        return rv

    def set_value(self, tgo_name: str, quiet_mode: bool, tgo_attrib: str, tgo_value: str) -> int:
        """
        Set value for a Tango device.

        :param tgo_name: device name
        :param quiet_mode: flag for displaying progress bar,
        :param tgo_attrib: attribute name
        :param tgo_value: attribute value
        :return: error condition
        """
        dev: Any = TangoctlDevice(self.logger, quiet_mode, tgo_name, None, None, None)
        dev.read_attribute_value()
        self.logger.info("Set device %s attribute %s value to %s", tgo_name, tgo_attrib, tgo_value)
        dev.write_attribute_value(tgo_attrib, tgo_value)
        return 0

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
            rc: int = self.list_devices(
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

        # Read devices while applying filters
        devices: TangoctlDevices
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
