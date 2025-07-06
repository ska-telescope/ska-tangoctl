"""Read all information about Tango devices in a Kubernetes cluster."""

import getopt
import json
import logging
import os
import socket
import sys
from typing import Any

import tango
import yaml

from ska_tangoctl.tango_control.disp_action import BOLD, UNDERL, UNFMT, DispAction
from ska_tangoctl.tango_control.read_tango_device import DEFAULT_TIMEOUT_MILLIS, TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices import NumpyEncoder, TangoctlDevices
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
        self.dev_count: int = 0
        self.dev_on: bool = False
        self.dev_off: bool = False
        self.dev_ping: bool = False
        self.dev_standby: bool = False
        self.dev_status: dict = {}
        self.dev_test: bool = False
        self.dev_admin: int | None = None
        self.dev_sim: int | None = None
        self.disp_action: DispAction = DispAction(DispAction.TANGOCTL_NONE)
        self.disp_action.indent = 0
        self.dry_run: bool = False
        self.input_file: str | None = None
        self.json_dir: str | None = None
        self.logging_level: int | None = None
        self.output_file: str | None = None
        self.rc: int
        self.tango_host: str | None = None
        self.tgo_attrib: str | None = None
        self.tgo_cmd: str | None = None
        self.tgo_class: str | None = None
        # TODO Feature to search by input type not implemented yet
        self.tgo_in_type: str | None = None
        self.tgo_name: str | None = None
        self.tgo_prop: str | None = None
        self.tgo_value: str | None = None
        self.uniq_cls: bool = False
        self.k8s_ns: str | None = None
        self.k8s_ctx: str | None = None
        self.k8s_cluster: str | None = None
        self.timeout_millis: int | None = DEFAULT_TIMEOUT_MILLIS

    def reset(self) -> None:
        """Reset it to defaults."""
        self.logger.debug("Reset")
        self.cfg_name = None
        self.cfg_data = TANGOCTL_CONFIG
        self.dev_count = 0
        self.dev_on = False
        self.dev_off = False
        self.dev_ping = False
        self.dev_standby = False
        self.dev_status = {}
        self.dev_test = False
        self.dev_admin = None
        self.dev_sim = None
        self.disp_action = DispAction(DispAction.TANGOCTL_NONE)
        self.disp_action.indent = 0
        self.dry_run = False
        self.disp_action.evrythng = False
        self.input_file = None
        self.json_dir = None
        self.logging_level = None
        self.output_file = None
        self.disp_action.quiet_mode = False
        self.disp_action.reverse = False
        self.disp_action.show_attrib = False
        self.disp_action.show_class = False
        self.disp_action.show_cmd = False
        self.disp_action.show_jargon = False
        self.disp_action.show_prop = False
        self.disp_action.show_tango = False
        self.disp_action.show_tree = False
        self.disp_action.show_version = False
        self.tango_host = None
        self.tgo_attrib = None
        self.tgo_cmd = None
        self.tgo_class = None
        # TODO Feature to search by input type not implemented yet
        self.tgo_in_type = None
        self.tgo_name = None
        self.tgo_prop = None
        self.tgo_value = None
        self.uniq_cls = False
        self.disp_action.xact_match = False
        self.k8s_ns = None
        self.k8s_ctx = None
        self.k8s_cluster = None
        self.timeout_millis = DEFAULT_TIMEOUT_MILLIS

    def setup(  # noqa: C901
        self,
        cfg_name: str | None = None,
        cfg_data: dict = TANGOCTL_CONFIG,
        dev_on: bool | None = None,
        dev_off: bool | None = None,
        dev_ping: bool | None = None,
        dev_standby: bool | None = None,
        dev_status: dict = {},
        dev_test: bool | None = None,
        dev_admin: int | None = None,
        dev_sim: int | None = None,
        disp_action: DispAction = DispAction(DispAction.TANGOCTL_NONE),
        dry_run: bool | None = None,
        evrythng: bool | None = None,
        indent: int = 0,
        input_file: str | None = None,
        json_dir: str | None = None,
        logging_level: int | None = None,
        output_file: str | None = None,
        quiet_mode: bool | None = None,
        reverse: bool | None = None,
        show_attrib: bool | None = None,
        show_class: bool | None = None,
        show_cmd: bool | None = None,
        show_jargon: bool | None = None,
        show_prop: bool | None = None,
        show_tango: bool | None = None,
        show_tree: bool | None = None,
        show_version: bool | None = None,
        tango_host: str | None = None,
        tgo_attrib: str | None = None,
        tgo_class: str | None = None,
        tgo_cmd: str | None = None,
        tgo_in_type: str | None = None,
        tgo_name: str | None = None,
        tgo_prop: str | None = None,
        tgo_value: str | None = None,
        timeout_millis: int | None = None,
        uniq_cls: bool | None = None,
        xact_match: bool | None = None,
    ) -> None:
        """
        Set it up.

        TODO find a use for this

        :param cfg_name: config file name
        :param dev_on: device on
        :param dev_off: device off
        :param dev_ping: ping the device
        :param dev_standby: device standby
        :param dev_status: device status
        :param dev_test: device test
        :param dev_admin: device admin
        :param dev_sim: device simulation
        :param disp_action: display action
        :param dry_run: dry run
        :param evrythng: evrything
        :param indent: indentation for JSON
        :param input_file: input file
        :param json_dir: json file directory
        :param logging_level: Tango device logging level
        :param output_file: output file
        :param quiet_mode: quiet mode
        :param reverse: reverse
        :param show_attrib: show attributes
        :param show_class: show classes
        :param show_cmd: show commands
        :param show_jargon: show jargon
        :param show_prop: show properties
        :param dev_status: show status
        :param show_tango: show tango
        :param show_tree: show tree
        :param show_version: show version
        :param tango_host: tango host
        :param tgo_attrib: attribute name
        :param tgo_class: class name
        :param tgo_cmd: command name
        :param tgo_in_type: input type
        :param tgo_name: device name
        :param tgo_prop: property name
        :param tgo_value: value
        :param timeout_millis: Tango device timeout in milliseconds
        :param uniq_cls: unique class
        :param cfg_data: TANGOCTL config
        :param xact_match: exact matches only
        """
        if cfg_name is not None:
            self.cfg_name = cfg_name
        if dev_on is not None:
            self.dev_on = dev_on
        if dev_off is not None:
            self.dev_off = dev_off
        if dev_ping is not None:
            self.dev_ping = dev_ping
        if dev_standby is not None:
            self.dev_standby = dev_standby
        if dev_status:
            self.dev_status = dev_status
        if dev_test is not None:
            self.dev_test = dev_test
        if dev_admin is not None:
            self.dev_admin = dev_admin
        if dev_sim is not None:
            self.dev_sim = dev_sim
        if not disp_action.check(DispAction.TANGOCTL_NONE):
            self.disp_action = disp_action
        if dry_run is not None:
            self.dry_run = dry_run
        if evrythng is not None:
            self.disp_action.evrythng = evrythng
        if indent:
            self.disp_action.indent = indent
        if input_file is not None:
            self.input_file = input_file
        if json_dir is not None:
            self.json_dir = json_dir
        if logging_level is not None:
            self.logging_level = logging_level
        if output_file is not None:
            self.output_file = output_file
        if quiet_mode is not None:
            self.disp_action.quiet_mode = quiet_mode
        if reverse is not None:
            self.disp_action.reverse = reverse
        if show_attrib is not None:
            self.disp_action.show_attrib = show_attrib
        if show_class is not None:
            self.disp_action.show_class = show_class
        if show_cmd is not None:
            self.disp_action.show_cmd = show_cmd
        if show_jargon is not None:
            self.disp_action.show_jargon = show_jargon
        if show_prop is not None:
            self.disp_action.show_prop = show_prop
        if dev_status:
            self.dev_status = dev_status
        if show_tango is not None:
            self.disp_action.show_tango = show_tango
        if show_tree is not None:
            self.disp_action.show_tree = show_tree
        if show_version is not None:
            self.disp_action.show_version = show_version
        if tango_host is not None:
            self.tango_host = tango_host
        if tgo_attrib is not None:
            self.tgo_attrib = tgo_attrib
        if tgo_class is not None:
            self.tgo_class = tgo_class
        if tgo_cmd is not None:
            self.tgo_cmd = tgo_cmd
        if xact_match is not None:
            self.disp_action.xact_match = xact_match
        # TODO Feature to search by input type not implemented yet
        if tgo_in_type is not None:
            self.tgo_in_type = tgo_in_type
        if tgo_name is not None:
            self.tgo_name = tgo_name
        if tgo_prop is not None:
            self.tgo_prop = tgo_prop
        if tgo_value is not None:
            self.tgo_value = tgo_value
        if timeout_millis is not None:
            self.timeout_millis = timeout_millis
        if uniq_cls is not None:
            self.uniq_cls = uniq_cls

    def set_logging_level(self) -> int:
        """
        Set logging level for a device.

        Change a device's logging level, where:
        - 0=OFF
        - 1=FATAL
        - 2=ERROR
        - 3=WARNING
        - 4=INFO
        - 5=DEBUG

        :returns: error condition
        """
        self.logger.info("Set logging level for device %s", self.tgo_name)
        try:
            dev = tango.DeviceProxy(self.tgo_name)
            dev.set_logging_level(self.logging_level)
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.error("Could not open device %s : %s", self.tgo_name, err_msg)
            return 1
        return 0

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
        print(f"{BOLD}Read Tango devices:{UNFMT}")

        # Reading devices
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help|-h")
        print(f"\t{p_name} -vh")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nList Tango device names")
        print(f"\t{p_name} -d|--show-dev [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -k|--show-class [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay all Tango devices")
        print(f"\t{p_name} [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] [FORMAT] [MISC]")
        print("\nFilter on attribute, command or property name")
        print(f"\t{p_name} [TANGODB] [SELECT] [FORMAT] [MISC]")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")

        # Testing Tango devices
        print(f"\n{BOLD}Test Tango devices:{UNFMT}")
        print("\nTest a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] [TEST]")
        print("\nTest a Tango device and read attributes")
        print(f"\t{p_name} -a [TANGODB] [DEVICE] [SELECT] [TEST]")
        print("\nTurn a Tango device on")
        print(f"\t{p_name} --on [TANGODB] [DEVICE] [TEST]")
        print("\nTurn a Tango device off")
        print(f"\t{p_name} --off [TANGODB] [DEVICE] [TEST]")
        print("\nSet a Tango device to standby mode")
        print(f"\t{p_name} --standby [TANGODB] [DEVICE] [TEST]")
        print("\nChange admin mode for a Tango device")
        print(f"\t{p_name} --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT} [TANGODB] [DEVICE]")
        print("\nSet status of Tango device")
        print(f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT} [TANGODB] [DEVICE]")
        # print("\nCheck events for attribute of a Tango device")
        # print(
        #     f"\t{p_name} -K {UNDERL}CLASS{UNFMT}|-H {UNDERL}HOST{UNFMT}"
        #     f" [DEVICE] -A {UNDERL}CLASS{UNFMT}"
        # )
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir={UNDERL}PATH{UNFMT}|-J {UNDERL}PATH{UNFMT} [MISC]")
        print("\nRun test, reading from input file")
        print(f"\t{p_name} [TANGODB] --input={UNDERL}FILE{UNFMT}|-I {UNDERL}FILE{UNFMT} [MISC]")
        # print(
        #     f"{italic}e.g.\tADMIN_MODE=1 {p_name} --K integration"
        #     f" -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V{UNFMT}"
        # )

        # Options and parameters
        print(f"\n{BOLD}Set Tango database{UNFMT} [TANGODB]\n")
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            "\t\t\tTango database host and port, e.g. 10.8.13.15:10000"
        )

        print(f"\n{BOLD}Tango device selection{UNFMT} [DEVICE]\n")
        print(
            f"\t-D {UNDERL}DEVICE{UNFMT}, --device={UNDERL}DEVICE{UNFMT}"
            f"\t\tdevice name, e.g. 'csp' (not case sensitive, only a part is needed)"
        )

        # Selecting what to read
        print(f"\n{BOLD}Data selection{UNFMT} [SELECT]\n")
        print("\t-e, --everything\t\t\tread attributes, commands and properties")
        print("\t-a, --show-attribute\t\t\tflag for reading attributes")
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}"
            f"\tattribute name e.g. 'obsState' (not case sensitive)"
        )
        print("\t-c, --show-command\t\t\tflag for reading commands")
        print(
            f"\t-C {UNDERL}COMMAND{UNFMT}, --command={UNDERL}COMMAND{UNFMT}"
            "\t\tcommand name, e.g. 'Status' (not case sensitive)"
        )
        print("\t-k, --show-class\t\t\tflag for reading classes")
        print(
            f"\t-K {UNDERL}CLASS{UNFMT}, --class={UNDERL}CLASS{UNFMT}"
            "\t\t\tclass name, e.g. 'DishLogger' (not case sensitive)"
        )
        print("\t-p, --show-property\t\t\tread properties")
        print(
            f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}"
            "\tproperty name, e.g. 'Status' (not case sensitive)"
        )
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-f, --full\t\t\t\tshow all devices - do not skip {ign}")
        print("\t    --exact\t\t\t\tmatch names exactly")
        print("\t-u, --unique\t\t\t\tonly read one device for each class")

        print(f"\n{BOLD}Format control{UNFMT} [FORMAT]\n")
        print("\t-s, --short\t\t\t\tdisplay device name and status")
        print("\t-l, --list\t\t\t\tdisplay device name, status and values")
        print("\t-j, --json\t\t\t\toutput in JSON format")
        print("\t-m, --md\t\t\t\toutput in markdown format")
        print("\t-t, --txt\t\t\t\toutput in text format")
        print("\t-w, --html\t\t\t\toutput in HTML format")
        print("\t-y, --yaml\t\t\t\toutput in YAML format")
        print(f"\t    ---indent={UNDERL}INDENT{UNFMT}\t\tindentation for JSON, default is 4")

        # Running tests
        print(f"\n{BOLD}Simple testing{UNFMT} [TEST]\n")
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT}\t\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            f"\t\tdirectory with JSON input file, e.g. 'resources'"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\t\toutput file name")
        print("\t-0, --on\t\t\t\tturn device on")
        print("\t-1, --off\t\t\t\tturn device off")
        print("\t    --ping\t\t\t\tping device")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset simulation mode off or on"
        )

        # Other
        print(f"\n{BOLD}Miscellaneous{UNFMT} [MISC]\n")
        print("\t-v\t\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\t\tset logging level to DEBUG")
        print("\t-q\t\t\t\t\tdo not display progress bars and set log level to WARNING")
        print("\t-Q\t\t\t\t\tdo not display progress bars and set log level to ERROR")
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            "\t\t\toverride configuration from file"
        )

        # Configuration
        print(f"\n{BOLD}Default configuration:{UNFMT}\n")
        print(f"\ttimeout: {self.cfg_data['timeout_millis']}ms")
        print(f"\tTango database port\t: {self.cfg_data['databaseds_port']}")
        print(f"\tTango device port\t: {self.cfg_data['device_port']}")
        print(f"\tCommands safe to run: {','.join(self.cfg_data['run_commands'])}")
        print(
            "\tcommands safe to run with name as parameter:"
            f" {','.join(self.cfg_data['run_commands_name'])}"
        )
        print(f"\tLong attributes: {','.join(self.cfg_data['long_attributes'])}")
        print(f"\tMgnore devices: {','.join(self.cfg_data['ignore_device'])}")
        print(f"\tMinimum string length for matches: {self.cfg_data['min_str_len']}")
        print(f"\tDelimiter: '{self.cfg_data['delimiter']}'")
        print(
            "\tListed attributes:"
            f" {','.join(list(self.cfg_data['list_items']['attributes'].keys()))}"
        )
        print(
            "\tListed commands:"
            f" {','.join(list(self.cfg_data['list_items']['commands'].keys()))}"
        )
        print(
            "\tListed properties:"
            f" {','.join(list(self.cfg_data['list_items']['properties'].keys()))}"
        )

        # Further reading
        print(f"\n{BOLD}See also:{UNFMT}\n")
        print(f"\t{BOLD}man tangoctl{UNFMT}")
        print()

    def usage2(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        print(f"{BOLD}Read Tango devices:{UNFMT}")

        # Reading devices
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help")
        print(f"\t{p_name} -h")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -k|--show-class [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -k|--show-class [-H {UNDERL}HOST{UNFMT}]")
        print("\nList Tango device names")
        print(f"\t{p_name} --show-dev [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -l [-H {UNDERL}HOST{UNFMT}]")
        print("\nDisplay all Tango devices (will take a long time)")
        print(f"\t{p_name} --full|--short -e|--everything [--host={UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -l{UNFMT}")
        print("\nFilter on device name")
        print(f"\t{p_name} --full|--short -D {UNDERL}DEVICE{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print(f"\t{p_name} -f|-s --device={UNDERL}DEVICE{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
        print("\nFilter on attribute name")
        print(
            f"\t{p_name} --full|--short --attribute={UNDERL}ATTRIBUTE{UNFMT}"
            f" [--host={UNDERL}HOST{UNFMT}]"
        )
        print(f"\t{p_name} -f|-s -A {UNDERL}ATTRIBUTE{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print("\nFilter on command name")
        print(
            f"\t{p_name} --full|--short --command={UNDERL}COMMAND{UNFMT}"
            f" [--host={UNDERL}HOST{UNFMT}]"
        )
        print(f"\t{p_name} -f|-s -C {UNDERL}COMMAND{UNFMT} [-H {UNDERL}HOST{UNFMT}]")
        print("\nFilter on property name")
        print(
            f"\t{p_name} --full|--list|--short --property={UNDERL}PROPERTY{UNFMT}"
            f" [--host={UNDERL}HOST{UNFMT}]"
        )
        print(f"\t{p_name} -f|-s -P {UNDERL}COMMAND{UNFMT} [--host={UNDERL}HOST{UNFMT}]")
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
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
            f""
        )
        print("\nTest a Tango device and read attributes")
        print(
            f"\t{p_name} -a [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nDisplay attribute and command names for a Tango device")
        print(f"\t{p_name} -c [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}DEVICE{UNFMT}")
        print("\nTurn a Tango device on")
        print(
            f"\t{p_name} --on [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTurn a Tango device off")
        print(
            f"\t{p_name} --off [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nSet a Tango device to standby mode")
        print(
            f"\t{p_name} --standby [-H {UNDERL}HOST{UNFMT}]"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nChange admin mode on a Tango device")
        print(f"\t{p_name} --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}")
        print("\nDisplay status of a Tango device")
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" [--host {UNDERL}HOST{UNFMT}] --device {UNDERL}DEVICE{UNFMT}"
        )
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}DEVICE{UNFMT}"
        )
        print("\nCheck events for attribute of a Tango device")
        print(
            f"\t{p_name} [-H {UNDERL}HOST{UNFMT}] -D {UNDERL}DEVICE{UNFMT}"
            f" -A {UNDERL}ATTRIBUTE{UNFMT}"
        )
        # Options and parameters
        print(f"\n{BOLD}Parameters:{UNFMT}\n")
        print("\t-a, --show-attribute\t\t\tflag for reading attributes")
        print("\t-b, --tree\t\t\t\tdisplay tree of devices")
        print("\t-c, --show-command\t\t\tread commands")
        print("\t-d, --show-dev\t\t\t\tlist Tango device names")
        print("\t-e, --everything\t\t\tshow all devices")
        ign = ", ".join(self.cfg_data["ignore_device"])
        print("\t    --exact\t\t\t\texact matches only")
        print(f"\t-f, --full\t\t\t\tshow all devices - do not skip {ign}")
        print("\t-i, --show-db\t\t\t\tdisplay hostname and IP address of Tango host")
        print("\t-j, --json\t\t\t\toutput in JSON format")
        print("\t-k, --show-class\t\t\tlist Tango device classes")
        print("\t-l, --list\t\t\t\tdisplay device name and status on one line")
        print("\t-m, --md\t\t\t\toutput in markdown format")
        print("\t-p, --show-property\t\t\tread properties")
        print("\t-q\t\t\t\t\tdo not display progress bars")
        print("\t-Q\t\t\t\t\tdo not display progress bars or error messages")
        print("\t    --reverse\t\t\t\treverse sort order")
        print("\t-s, --short\t\t\t\tdisplay attribute and command values in short format")
        print("\t-t, --txt\t\t\t\toutput in text format")
        print("\t    --unique\t\t\t\tonly read one device for each class")
        print("\t-v\t\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\t\tset logging level to DEBUG")
        print("\t-w, --html\t\t\t\toutput in HTML format")
        print("\t-y, --yaml\t\t\t\toutput in YAML format")
        print("\t-0, --off\t\t\t\tturn device off")
        print("\t-1, --on\t\t\t\tturn device on")
        print("\t    --ping\t\t\tping device")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\t\tset simulation mode off or on"
        )
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}\tattribute name"
        )
        print(f"\t-C {UNDERL}ATTRIBUTE{UNFMT}, --command={UNDERL}COMMAND{UNFMT}\t\tcommand name")
        print(f"\t-D {UNDERL}ATTRIBUTE{UNFMT}, --device={UNDERL}DEVICE{UNFMT}\t\tdevice name")
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            f"\t\t\tTango database host and port"
        )
        print(f"\t---indent={UNDERL}INDENT{UNFMT}\t\tindentation for JSON, default is 4")
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT}\t\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            "\t\tdirectory with JSON input file"
        )
        print(
            f"\t-K {UNDERL}PATH{UNFMT}, --class={UNDERL}PATH{UNFMT}"
            f"\t\t\tTango device class, e.g. 'MidCspSubarray' (not case sensitive)"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\t\t\toutput file name")
        print(f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}\t\tproperty name")
        print(
            f"\t-W {UNDERL}VALUE{UNFMT}, --value={UNDERL}VALUE{UNFMT}"
            "\t\tvalue for Tango attribute"
        )
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            f"\t\toverride configuration from file"
        )
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
                "acdefhijklmnpqQstvwxyV01A:C:H:D:H:I:J:O:P:Q:T:W:X:Z:",
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
                    "ping",
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
                    "test",
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
                    "indent=",
                    "input=",
                    "json-dir=",
                    "log-level=",
                    "output=",
                    "port=",
                    "property=",
                    "simul=",
                    "timeout=",
                    "type=",
                    "value=",
                ],
            )
        except getopt.GetoptError as opt_err:
            print(f"Could not read command line: {opt_err}")
            return 1

        for opt, arg in opts:
            if opt in ("-a", "--show-attribute"):
                self.disp_action.show_attrib = True
            elif opt in ("-A", "--attribute"):
                self.tgo_attrib = arg
                self.disp_action.show_attrib = True
            elif opt == "--admin":
                self.dev_admin = int(arg)
            elif opt in ("-c", "--show-command"):
                self.disp_action.show_cmd = True
            elif opt in ("-C", "--command"):
                self.tgo_cmd = arg.lower()
                self.disp_action.show_cmd = True
            elif opt in ("-d", "--show-dev"):
                self.disp_action.value = DispAction.TANGOCTL_NAMES
            elif opt in ("-D", "--device"):
                self.tgo_name = arg.lower()
            # TODO Undocumented and unused feature for dry runs
            elif opt == "--dry-run":
                self.dry_run = True
            elif opt in ("-e", "--everything"):
                self.disp_action.evrythng = True
                self.disp_action.show_attrib = True
                self.disp_action.show_cmd = True
                self.disp_action.show_prop = True
            elif opt == "--exact":
                self.disp_action.xact_match = True
            elif opt in ("-f", "--full"):
                self.disp_action.value = DispAction.TANGOCTL_FULL
            elif opt in ("-h", "--help"):
                if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
                    self.usage2(os.path.basename(cli_args[0]))
                else:
                    self.usage(os.path.basename(cli_args[0]))
                return 1
            elif opt in ("-H", "--host"):
                self.tango_host = arg
            elif opt in ("-i", "--show-db"):
                self.disp_action.show_tango = True
            elif opt in ("-I", "--input"):
                self.input_file = arg
            elif opt == "--indent":
                self.disp_action.indent = int(arg)
            elif opt in ("-j", "--json"):
                self.disp_action.value = DispAction.TANGOCTL_JSON
            elif opt in ("-J", "--json-dir"):
                self.json_dir = arg
            elif opt in ("-k", "--show-class"):
                self.disp_action.value = DispAction.TANGOCTL_CLASS
            elif opt in ("-K", "--class"):
                self.tgo_class = arg
            elif opt in ("-l", "--list"):
                self.disp_action.value = DispAction.TANGOCTL_LIST
            elif opt == "--log-level":
                self.logging_level = int(arg)
            elif opt in ("-m", "--md"):
                self.disp_action.value = DispAction.TANGOCTL_MD
            elif opt in ("-O", "--output"):
                self.output_file = arg
            elif opt == "--ping":
                self.dev_ping = True
            elif opt in ("-p", "--show-property"):
                self.disp_action.show_prop = True
            elif opt in ("-P", "--property"):
                self.tgo_prop = arg.lower()
                self.disp_action.show_prop = True
            elif opt == "-q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.WARNING)
            elif opt == "-Q":
                self.disp_action.quiet_mode = True
                self.logger.setLevel(logging.ERROR)
            elif opt == "--reverse":
                self.disp_action.reverse = True
            # TODO simulation to be deprecated
            elif opt == "--simul":
                self.dev_sim = int(arg)
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
            elif opt == "--table":
                self.disp_action.value = DispAction.TANGOCTL_TABL
            elif opt == "--test":
                self.dev_test = True
            elif opt == "--tree":
                self.disp_action.show_tree = True
            elif opt == "--unique":
                self.uniq_cls = True
            elif opt == "-v":
                self.disp_action.quiet_mode = False
                self.logger.setLevel(logging.INFO)
            elif opt == "-V":
                self.disp_action.quiet_mode = False
                self.logger.setLevel(logging.DEBUG)
            elif opt == "--version":
                self.disp_action.show_version = True
            elif opt in ("-w", "--html"):
                self.disp_action.value = DispAction.TANGOCTL_HTML
            elif opt in ("-W", "--value"):
                self.tgo_value = str(arg)
            elif opt in ("-X", "--cfg"):
                self.cfg_name = arg
            elif opt in ("-y", "--yaml"):
                self.disp_action.value = DispAction.TANGOCTL_YAML
            elif opt in ("-Z", "--timeout"):
                self.timeout_millis = int(arg)
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
            tport = 10000
        self.logger.info("Check Tango host %s:%d", tango_fqdn, tport)
        try:
            tango_addr = socket.gethostbyname_ex(str(tango_fqdn))
            tango_ip = tango_addr[2][0]
        except socket.gaierror as e:
            self.logger.error("Could not read address %s : %s" % (tango_fqdn, e))
            return 1
        if not self.disp_action.quiet_mode:
            print(f"TANGO_HOST={tango_fqdn}:{tport}")
            print(f"TANGO_HOST={tango_ip}:{tport}")
        return 0

    def get_tango_classes(self) -> dict:
        """
        Read tango classes.

        :return: dictionary with devices
        """
        devices: TangoctlDevices
        dev_classes: dict

        try:
            devices = TangoctlDevices(
                self.logger,
                self.tango_host,
                self.output_file,
                self.timeout_millis,
                self.dev_status,
                self.cfg_data,
                self.tgo_name,
                False,
                self.disp_action,
                self.k8s_ctx,
                self.k8s_cluster,
                self.k8s_ns,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for classes failed")
            return {}
        # TODO this a bit too broad
        except Exception:
            self.logger.error("Tango connection for classes failed")
            return {}
        devices.read_devices()
        devices.read_configs()
        dev_classes = devices.get_classes()
        return dev_classes

    def list_classes(self) -> int:
        """
        Get device classes.

        :return: error condition
        """
        devices: TangoctlDevices
        dev_classes: dict

        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            self.logger.info("Get device classes in JSON format")
            try:
                devices = TangoctlDevices(
                    self.logger,
                    self.tango_host,
                    self.output_file,
                    self.timeout_millis,
                    self.dev_status,
                    self.cfg_data,
                    self.tgo_name,
                    False,
                    self.disp_action,
                    self.k8s_ctx,
                    self.k8s_cluster,
                    self.k8s_ns,
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection for JSON class list failed")
                return 1
            devices.read_devices()
            devices.read_configs()
            dev_classes = devices.get_classes()
            if not self.disp_action.indent:
                self.disp_action.indent = 4
            print(json.dumps(dev_classes, indent=self.disp_action.indent))
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.logger.info("List device classes (%s)", self.disp_action)
            try:
                devices = TangoctlDevices(
                    self.logger,
                    self.tango_host,
                    self.output_file,
                    self.timeout_millis,
                    self.dev_status,
                    self.cfg_data,
                    self.tgo_name,
                    False,
                    self.disp_action,
                    self.k8s_ctx,
                    self.k8s_cluster,
                    self.k8s_ns,
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection for text class list failed")
                return 1
            devices.read_devices()
            devices.read_configs()
            devices.print_classes()
        else:
            self.logger.error("Format '%s' not supported for listing classes", self.disp_action)
            return 1
        return 0

    def list_devices(self) -> int:
        """
        List Tango devices.

        :return: error condition
        """
        devices: TangoctlDevices

        self.logger.info("List devices (%s) with name %s", self.disp_action, self.tgo_name)
        try:
            devices = TangoctlDevices(
                self.logger,
                self.tango_host,
                self.output_file,
                self.timeout_millis,
                self.dev_status,
                self.cfg_data,
                self.tgo_name,
                self.uniq_cls,
                self.disp_action,
                self.k8s_ctx,
                self.k8s_cluster,
                self.k8s_ns,
            )
        except tango.ConnectionFailed as cerr:
            self.logger.error("Tango connection for listing devices failed: %s", cerr)
            return 1
        except Exception as eerr:
            self.logger.error("Listing of Tango devices failed : %s", eerr)
            return 1
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            devices.read_devices()
            devices.read_configs()
            devices.print_json()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            devices.read_devices()
            devices.read_configs()
            devices.print_yaml()
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            devices.read_devices()
            devices.read_configs()
            devices.print_html(self.disp_action)
        else:
            devices.read_devices()
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
            file_name
            for file_name in os.listdir(relevant_path)
            if any(file_name.endswith(ext) for ext in included_extensions)
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
                        if not self.disp_action.quiet_mode:
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
            self.disp_action,
            sys.stdout,
            self.timeout_millis,
            self.dev_status,
            self.tgo_name,
            {},
            {},
            None,
            None,
            None,
            indent=self.disp_action.indent,
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

    def run_info(self) -> int:  # noqa: C901
        """
        Read information on Tango devices.

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

        # List Tango device names only
        if self.disp_action.check(DispAction.TANGOCTL_SHORT) and not (
            self.disp_action.show_attrib
            or self.disp_action.show_cmd
            or self.disp_action.show_attrib
        ):
            rc = self.list_devices()
            return rc

        # Get Tango device classes
        if self.disp_action.check(DispAction.TANGOCTL_CLASS):
            rc = self.list_classes()
            return rc

        if self.output_file is not None:
            if os.path.splitext(self.output_file)[-1] != f".{str(self.disp_action)}":
                self.output_file = f"{self.output_file}.{str(self.disp_action)}"
                self.logger.warning("File name changed to %s", self.output_file)

        if (
            self.tgo_name is None
            and self.tgo_attrib is None
            and self.tgo_cmd is None
            and self.tgo_prop is None
            and self.disp_action.check(0)
            and (not self.disp_action.evrythng)
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
                self.tango_host,
                self.output_file,
                self.timeout_millis,
                self.dev_status,
                self.cfg_data,
                self.tgo_name,
                self.uniq_cls,
                self.disp_action,
                None,
                None,
                None,
                self.tgo_attrib,
                self.tgo_cmd,
                self.tgo_prop,
                self.tgo_class,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for info failed")
            return 1

        self.logger.debug("Read devices (action %s)", repr(self.disp_action))

        # Display in specified format
        if self.disp_action.show_class:
            self.logger.debug("Read device classes")
            devices.read_devices()
            if self.disp_action.check(DispAction.TANGOCTL_JSON):
                klasses = devices.get_classes()
                if not self.disp_action.indent:
                    self.disp_action.indent = 4
                print(json.dumps(klasses, indent=self.disp_action.indent, cls=NumpyEncoder))
            elif self.disp_action.check(DispAction.TANGOCTL_YAML):
                klasses = devices.get_classes()
                print((yaml.safe_dump(klasses, default_flow_style=False, sort_keys=False)))
            else:
                devices.print_classes()
        elif self.disp_action.check(DispAction.TANGOCTL_LIST):
            self.logger.debug("List devices")
            # TODO this is messy
            devices.read_devices()
            devices.read_device_values()
            if (
                self.disp_action.show_attrib
                or self.disp_action.show_cmd
                or self.disp_action.show_prop
            ):
                if self.disp_action.show_attrib:
                    devices.print_txt_list_attributes(True)
                if self.disp_action.show_cmd:
                    devices.print_txt_list_commands(True)
                if self.disp_action.show_prop:
                    devices.print_txt_list_properties(True)
            else:
                devices.print_txt_list()
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.logger.debug("List devices as txt")
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt_all()
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            self.logger.debug("List devices as HTML")
            devices.read_devices()
            devices.read_device_values()
            devices.print_html(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_JSON):
            self.logger.debug("List devices as JSON")
            devices.read_devices()
            devices.read_device_values()
            if self.disp_action.check(DispAction.TANGOCTL_SHORT):
                devices.print_json_short()
            else:
                devices.print_json()
        elif self.disp_action.check(DispAction.TANGOCTL_MD):
            self.logger.debug("List devices as markdown")
            devices.read_devices()
            devices.read_device_values()
            devices.print_markdown()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            self.logger.debug("List devices as YAML")
            devices.read_devices()
            devices.read_device_values()
            if self.disp_action.check(DispAction.TANGOCTL_SHORT):
                devices.print_yaml_short()
            else:
                devices.print_yaml()
        elif self.disp_action.check(DispAction.TANGOCTL_SHORT):
            self.logger.debug("List devices in short form")
            devices.read_devices()
            devices.print_txt_short()
        elif self.disp_action.check(DispAction.TANGOCTL_NAMES):
            self.logger.debug("List device names")
            devices.print_names_list()
        else:
            self.logger.error("Display action %s not supported", self.disp_action)
        # TODO nothing to see here?
        """
        elif (
            self.disp_action.check([DispAction.TANGOCTL_LIST, DispAction.TANGOCTL_SHORT])
            and self.tgo_attrib is not None
        ):
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt_list_attributes(self.disp_action.check(DispAction.TANGOCTL_LIST))
        elif (
            self.disp_action.check([DispAction.TANGOCTL_LIST, DispAction.TANGOCTL_SHORT])
            and self.tgo_cmd is not None
        ):
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt_list_commands(self.disp_action.check(DispAction.TANGOCTL_LIST))
        elif (
            self.disp_action.check([DispAction.TANGOCTL_LIST, DispAction.TANGOCTL_SHORT])
            and self.tgo_prop is not None
        ):
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt_list_properties(self.disp_action.check(DispAction.TANGOCTL_LIST))
        elif self.disp_action.check([DispAction.TANGOCTL_LIST, DispAction.TANGOCTL_SHORT]):
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt_list_attributes(self.disp_action.check(DispAction.TANGOCTL_LIST))
            devices.print_txt_list_commands(self.disp_action.check(DispAction.TANGOCTL_LIST))
            devices.print_txt_list_properties(self.disp_action.check(DispAction.TANGOCTL_LIST))
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt(self.disp_action)
        """

        return 0
