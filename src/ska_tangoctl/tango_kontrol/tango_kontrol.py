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
from ska_tangoctl.tango_control.disp_action import BOLD, UNDERL, UNFMT, DispAction
from ska_tangoctl.tango_control.read_tango_devices import NumpyEncoder, TangoctlDevices
from ska_tangoctl.tango_control.tango_control import TangoControl
from ska_tangoctl.tango_kontrol.tangoktl_config import TANGOKTL_CONFIG, read_tangoktl_config


class TangoKontrol(TangoControl):
    """Read Tango devices running in a Kubernetes cluster."""

    def __init__(self, logger: logging.Logger, k8s_ctx: str | None):
        """
        Initialize this thing.

        :param logger: logging handle
        :param k8s_ctx: Kubernetes context
        """
        super().__init__(logger)
        self.cfg_data = TANGOKTL_CONFIG
        self.show_pod: str = ""
        self.show_ns: bool = False
        self.show_svc: bool = False
        self.use_fqdn: bool = True
        self.k8s_ns: str | None = None
        self.k8s_ctx: str | None = k8s_ctx
        self.logger.info("Initialize with context %s", self.k8s_ctx)

    def __repr__(self) -> str:
        """
        Do the string thing.

        :returns: string representation
        """
        rval = f"\tDisplay format {repr(self.disp_action)}"
        rval += f"\n\tShow {'attributes' if self.show_attrib else ''}"
        rval += f" {'commands' if self.show_cmd else ''}"
        rval += f" {'properties' if self.show_prop else ''}"
        rval += f"\n\tNamespace: {self.k8s_ns}"
        rval += f"\n\tConfiguration: {self.cfg_data}"
        return rval

    def setup(  # noqa: C901
        self,
        cfg_name: str | None = None,
        cfg_data: dict = TANGOKTL_CONFIG,
        dev_on: bool | None = None,
        dev_off: bool | None = None,
        dev_standby: bool | None = None,
        dev_status: dict = {},
        dev_test: bool | None = None,
        dev_admin: int | None = None,
        dev_sim: int | None = None,
        disp_action: DispAction = DispAction(DispAction.TANGOCTL_NONE),
        dry_run: bool | None = None,
        evrythng: bool | None = None,
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
        show_status: dict = {},
        show_tango: bool | None = None,
        show_tree: bool | None = None,
        show_version: bool | None = None,
        tango_host: str | None = None,
        tango_port: int = 10000,
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
        ns_name: str | None = None,
        show_pod: str | None = None,
        show_ns: bool | None = None,
        show_svc: bool | None = None,
        use_fqdn: bool | None = None,
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
        :param disp_action: display action
        :param dry_run: dry run
        :param evrythng: evrything
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
        :param show_status: show status
        :param show_tango: show tango
        :param show_tree: show tree
        :param show_version: show version
        :param tango_host: tango host
        :param tango_port: tango port
        :param tgo_attrib: attribute name
        :param tgo_class: class name
        :param tgo_cmd: command name
        :param tgo_in_type: input type
        :param tgo_name: device name
        :param tgo_prop: property name
        :param tgo_value: value
        :param timeout_millis: Tango device timeout in milliseconds
        :param uniq_cls: unique class
        :param cfg_data: TANGOKTL config
        :param xact_match: exact matches only
        :param ns_name: K8S namespace
        :param show_pod: show K8S pods
        :param show_ns: show namespace
        :param show_svc: show services
        :param use_fqdn: use FQDN for database server
        """
        if cfg_name is not None:
            self.cfg_name = cfg_name
        if dev_on is not None:
            self.dev_on = dev_on
        if dev_off is not None:
            self.dev_off = dev_off
        if dev_standby is not None:
            self.dev_standby = dev_standby
        if dev_status is not None:
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
            self.evrythng = evrythng
        if input_file is not None:
            self.input_file = input_file
        if json_dir is not None:
            self.json_dir = json_dir
        if logging_level is not None:
            self.logging_level = logging_level
        if output_file is not None:
            self.output_file = output_file
        if quiet_mode is not None:
            self.quiet_mode = quiet_mode
        if reverse is not None:
            self.reverse = reverse
        if show_attrib is not None:
            self.show_attrib = show_attrib
        if show_cmd is not None:
            self.show_cmd = show_cmd
        if show_jargon is not None:
            self.show_jargon = show_jargon
        if show_prop is not None:
            self.show_prop = show_prop
        if show_status:
            self.show_status = show_status
        if show_svc is not None:
            self.show_svc = show_svc
        if show_tango is not None:
            self.show_tango = show_tango
        if show_tree is not None:
            self.show_tree = show_tree
        if show_version is not None:
            self.show_version = show_version
        if tango_host is not None:
            self.tango_host = tango_host
        if tango_port is not None:
            self.tango_port = tango_port
        if tgo_attrib is not None:
            self.tgo_attrib = tgo_attrib
        if tgo_class is not None:
            self.tgo_class = tgo_class
        if tgo_cmd is not None:
            self.tgo_cmd = tgo_cmd
        # TODO Feature to search by input type not implemented yet
        if tgo_in_type is not None:
            self.tgo_in_type = tgo_in_type
        if tgo_name is not None:
            self.tgo_name = tgo_name
        if tgo_prop is not None:
            self.tgo_prop = tgo_prop
        if tgo_value is not None:
            self.tgo_value = tgo_value
        if cfg_data:
            self.cfg_data = cfg_data
        if uniq_cls is not None:
            self.uniq_cls = uniq_cls
        if ns_name is not None:
            self.k8s_ns = ns_name
        if show_pod is not None:
            self.show_pod = show_pod
        if show_ns is not None:
            self.show_ns = show_ns
        if use_fqdn is not None:
            self.use_fqdn = use_fqdn
        if timeout_millis is not None:
            self.timeout_millis = timeout_millis

    def read_config(self) -> None:
        """Read configuration."""
        self.cfg_data: Any = read_tangoktl_config(self.logger, self.cfg_name)

    def usage(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        if KubernetesInfo is None:
            super().usage(p_name)
            return
        # Reading devices
        print(f"{BOLD}Read Tango devices in Kubernetes:{UNFMT}")
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help|-h")
        print(f"\t{p_name} -vh")
        print("\nDisplay Kubernetes namespaces")
        print(f"\t{p_name} --show-ns|-n [MISC]")
        print("\nDisplay information on pods in Kubernetes namespaces")
        print(f"\t{p_name} [NAMESPACE] [K8S]")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nDisplay Tango database address for Kubernetes namespace")
        print(f"\t{p_name} -i|--show-db [NAMESPACE] [MISC]")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} -g|--show-class [TANGODB] [FORMAT] [MISC]")
        print("\nList Tango device names")
        print(f"\t{p_name} -d|--show-dev [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay all Tango devices")
        print(f"\t{p_name} [TANGODB] [FORMAT] [MISC]")
        print("\nDisplay a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] [FORMAT] [MISC]")
        print("\nFilter on attribute, command or property name")
        print(f"\t{p_name} [TANGODB] [SELECT] [FORMAT] [MISC]")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")
        # Testing
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
        print("\nDisplay status of a Tango device")
        print(f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT} [TANGODB] [DEVICE]")
        # print("\nCheck events for attribute of a Tango device")
        # print(
        #     f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT}|-H {UNDERL}HOST{UNFMT}"
        #     f" [DEVICE] -A {UNDERL}ATTRIBUTE{UNFMT}"
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
        print(f"\n{BOLD}Tango database{UNFMT} [TANGODB]\n")
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            "\t\tTango database host and port, e.g. 10.8.13.15:10000"
        )
        print(
            f"\t-N {UNDERL}K8S_NS{UNFMT}, --ns={UNDERL}K8S_NS{UNFMT}"
            "\t\tKubernetes namespace for Tango database, e.g. 'integration'"
        )

        print(f"\n{BOLD}Tango device selection{UNFMT} [DEVICE]\n")
        print(
            f"\t-D {UNDERL}DEVICE{UNFMT}, --device={UNDERL}DEVICE{UNFMT}"
            f"\t\tdevice name, e.g. 'csp' (not case sensitive, only a part is needed)"
        )

        print(f"\n{BOLD}Kubernetes namespace{UNFMT} [NAMESPACE]\n")
        print(
            f"\t-K {UNDERL}K8S_NS{UNFMT}, --ns={UNDERL}K8S_NS{UNFMT},"
            f" --namespace={UNDERL}K8S_NS{UNFMT}\tKubernetes namespace"
        )

        print(f"\n{BOLD}Kubernetes information{UNFMT} [K8S]\n")
        print("\t-o, --show-pod\t\t\tread pod names")
        print("\t    --pod-df\t\t\tread pod file systems space usage")
        print("\t    --pod-domain\t\tread pod domain names")
        print("\t    --pod-env\t\t\tread pod environment variables")
        print("\t    --pod-free\t\t\tread free memory for pod host")
        print("\t    --pod-host\t\t\tread pod host names")
        print("\t    --pod-mpstat\t\tread processor related statistics for pod host")
        print("\t    --pod-ps\t\t\tread active processes in pods")
        print("\t    --pod-top\t\t\tread system summary information in pods")
        print("\t    --pod-uptime\t\tread how long pods have been running")

        print(f"\n{BOLD}Data selection{UNFMT} [SELECT]\n")
        print("\t-e, --everything\t\tread attributes, commands and properties")
        print("\t-a, --show-attribute\t\tflag for reading attributes")
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}"
            f"\tattribute name e.g. 'obsState' (not case sensitive)"
        )
        print("\t-c, --show-command\t\tflag for reading commands")
        print(
            f"\t-C {UNDERL}COMMAND{UNFMT}, --command={UNDERL}COMMAND{UNFMT}"
            "\t\tcommand name, e.g. 'Status' (not case sensitive)"
        )
        print("\t-k, --show-class\t\tflag for reading classes")
        print(
            f"\t-K {UNDERL}CLASS{UNFMT}, --class={UNDERL}CLASS{UNFMT}"
            "\t\tclass name, e.g. 'DishLogger' (not case sensitive)"
        )
        print("\t-p, --show-property\t\tread properties")
        print(
            f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}"
            "\tproperty name, e.g. 'Status' (not case sensitive)"
        )
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-f, --full\t\t\tshow all devices - do not skip {ign}")
        print("\t-u, --unique\t\t\tonly read one device for each class")

        print(f"\n{BOLD}Format control{UNFMT} [FORMAT]\n")
        print("\t-s, --short\t\t\tdisplay device name and status")
        print("\t-l, --list\t\t\tdisplay device name, status and values")
        print("\t-j, --json\t\t\toutput in JSON format")
        print("\t-m, --md\t\t\toutput in markdown format")
        print("\t-t, --txt\t\t\toutput in text format")
        print("\t-w, --html\t\t\toutput in HTML format")
        print("\t-y, --yaml\t\t\toutput in YAML format")
        # print("\t-i, --ip\t\t\tuse IP address instead of FQDN")

        print(f"\n{BOLD}Simple testing{UNFMT} [TEST]\n")
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT},\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            f"\tdirectory with JSON input file, e.g. 'resources'"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\toutput file name")
        print("\t-0, --on\t\t\tturn device on")
        print("\t-1, --off\t\t\tturn device off")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset simulation mode off or on"
        )

        print(f"\n{BOLD}Miscellaneous{UNFMT} [MISC]\n")
        print("\t-v\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\tset logging level to DEBUG")
        print("\t-q\t\t\t\tdo not display progress bars")
        print("\t-Q\t\t\t\tdo not display progress bars and set log level to WARNING")
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            "\t\toverride configuration from file"
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
        # Et cetera
        print(f"\n{BOLD}See also:{UNFMT}\n")
        print(f"\t{BOLD}man tangoktl{UNFMT}")
        print()

    def usage2(self, p_name: str) -> None:
        """
        Show how it is done.

        :param p_name: executable name
        """
        if KubernetesInfo is None:
            super().usage(p_name)
            return
        # Reading devices
        print(f"{BOLD}Read Tango devices:{UNFMT}")
        print("\nDisplay version number")
        print(f"\t{p_name} --version")
        print("\nDisplay help")
        print(f"\t{p_name} --help")
        print(f"\t{p_name} -h")
        print("\nDisplay Kubernetes namespaces")
        print(f"\t{p_name} --show-ns")
        print(f"\t{p_name} -n")
        print("\nDisplay Tango database address")
        print(f"\t{p_name} --show-db --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -i -N {UNDERL}K8S_NS{UNFMT}")
        print("\nSet logging level for a Tango device")
        print(f"\t{p_name} [TANGODB] [DEVICE] --log_level={UNDERL}0{UNFMT}-{UNDERL}5{UNFMT}")
        print("\nShow device:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT} -f")
        print("\nSearch for matching devices:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D talon -l")
        print("\nSearch for devices with matching command:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -C {UNDERL}COMMAND{UNFMT}")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -C {UNDERL}COMMAND{UNFMT}")
        print("\nSearch for devices with matching property:")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT}")
        print("\nDisplay classes and Tango devices associated with them")
        print(f"\t{p_name} --show-class --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --show-class --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -k -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -k -H {UNDERL}HOST{UNFMT}")
        print("\nList Tango device names")
        print(f"\t{p_name} --show-dev --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --show-dev --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -l -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -l -H {UNDERL}HOST{UNFMT}")
        print("\nDisplay all Tango devices (will take a long time)")
        # TODO full and short now does the same
        print(f"\t{p_name} -e -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --everything --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --everything --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -e -H {UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} --everything --host={UNDERL}HOST{UNFMT}")
        print("\nFilter on device name")
        print(f"\t{p_name} -D {UNDERL}DEVICE{UNFMT} -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -D {UNDERL}DEVICE{UNFMT} -H {UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} --device={UNDERL}DEVICE{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --device={UNDERL}DEVICE{UNFMT} --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --device={UNDERL}DEVICE{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print("\nFilter on attribute name")
        print(f"\t{p_name} --attribute={UNDERL}ATTRIBUTE{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --attribute={UNDERL}ATTRIBUTE{UNFMT} --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --attribute={UNDERL}ATTRIBUTE{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -A {UNDERL}ATTRIBUTE{UNFMT} -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -A {UNDERL}ATTRIBUTE{UNFMT} -H {UNDERL}HOST{UNFMT}")
        print("\nFilter on command name")
        print(f"\t{p_name} --command={UNDERL}COMMAND{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --command={UNDERL}COMMAND{UNFMT} --namespace={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --command={UNDERL}COMMAND{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print(
            f"\t{p_name} -f|-s -C {UNDERL}COMMAND{UNFMT} -N {UNDERL}K8S_NS{UNFMT}|-H"
            f" {UNDERL}HOST{UNFMT}"
        )
        print("\nFilter on property name")
        print(f"\t{p_name} --property={UNDERL}PROPERTY{UNFMT} --ns={UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} --property={UNDERL}PROPERTY{UNFMT} --host={UNDERL}HOST{UNFMT}")
        print(f"\t{p_name} -P {UNDERL}PROPERTY{UNFMT} -N {UNDERL}K8S_NS{UNFMT}")
        print(f"\t{p_name} -P {UNDERL}PROPERTY{UNFMT} -H {UNDERL}HOST{UNFMT}")
        # TODO make this work
        # print("\nDisplay known acronyms")
        # print(f"\t{p_name} -j")
        # Testing
        print(f"\n{BOLD}Test Tango devices:{UNFMT}")
        print("\nTest a Tango device")
        print(
            f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTest a Tango device and read attributes")
        print(
            f"\t{p_name} -a -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} -a -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nDisplay attribute and command names for a Tango device")
        print(f"\t{p_name} -c -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT}")
        print(f"\t{p_name} -c -H {UNDERL}HOST{UNFMT} -D {UNDERL}DEVICE{UNFMT}")
        print("\nTurn a Tango device on")
        print(
            f"\t{p_name} --on -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nTurn a Tango device off")
        print(
            f"\t{p_name} --off -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} --off -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nSet a Tango device to standby mode")
        print(
            f"\t{p_name} --standby -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print(
            f"\t{p_name} --standby -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} [--simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}]"
        )
        print("\nChange admin mode on a Tango device")
        print(f"\t{p_name} --admin=<0|1>")
        print("\nDisplay status of a Tango device")
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" -H {UNDERL}HOST{UNFMT} -D {UNDERL}DEVICE{UNFMT}"
        )
        print(
            f"\t{p_name} --status={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}"
            f" --ns={UNDERL}K8S_NS{UNFMT} --device={UNDERL}DEVICE{UNFMT}"
        )
        print("\nCheck events for attribute of a Tango device")
        print(
            f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} -A {UNDERL}ATTRIBUTE{UNFMT}"
        )
        print(
            f"\t{p_name} -H {UNDERL}HOST{UNFMT}"
            f" -D {UNDERL}DEVICE{UNFMT} -A {UNDERL}ATTRIBUTE{UNFMT}"
        )
        # print(
        #     f"\t{p_name} --ns={UNDERL}K8S_NS{UNFMT}|--host={UNDERL}HOST{UNFMT}"
        #     f" --device={UNDERL}DEVICE{UNFMT} --attribute={UNDERL}ATTRIBUTE{UNFMT}"
        # )
        # Testing with input file
        print(f"\nDisplay {p_name} test input files")
        print(f"\t{p_name} --json-dir={UNDERL}PATH{UNFMT}")
        print(f"\t{p_name} -J {UNDERL}PATH{UNFMT}")
        print("\nRun test, reading from input file")
        print(f"\t{p_name} --ns={UNDERL}K8S_NS{UNFMT} --input={UNDERL}FILE{UNFMT}")
        print(f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -O {UNDERL}FILE{UNFMT}")
        print("\nRun test file:")
        print(
            f"\t{p_name} -N {UNDERL}K8S_NS{UNFMT} -D {UNDERL}DEVICE{UNFMT} -f"
            f" --in {UNDERL}PATH{UNFMT} -V"
        )
        # print(
        #     f"{italic}e.g.\tADMIN_MODE=1 {p_name} --K integration"
        #     f" -D mid_csp_cbf/talon_board/001 -f --in resources/dev_online.json -V{UNFMT}"
        # )
        # Options and parameters
        print(f"\n{BOLD}Parameters:{UNFMT}\n")
        print("\t-a, --show-attribute\t\tflag for reading attributes")
        print("\t-b, --tree\t\t\tdisplay Tango device names as a tree")
        print("\t-c, --show-command\t\tflag for reading commands")
        print("\t-d, --show-dev\t\t\tlist Tango device names")
        ign = ", ".join(self.cfg_data["ignore_device"])
        print(f"\t-e, --everything\t\tshow all devices - do not skip {ign}")
        print("\t-f, --full\t\t\tdisplay in full")
        print("\t-i, --show-db\t\t\tdisplay hostname and IP address of Tango host")
        print("\t-j, --json\t\t\toutput in JSON format")
        print("\t-k, --show-class\t\tlist Tango device classes")
        print("\t-l, --list\t\t\tlist status of Tango devices")
        print("\t-m, --md\t\t\toutput in markdown format")
        # print("\t-l|--list\t\t\tdisplay device name and status on one line")
        print("\t-n, --show-ns\t\t\tread Kubernetes namespaces")
        print("\t-o, --show-pod\t\t\tread pod names")
        print("\t    --pod-df\t\t\tread pod file system space usage")
        print("\t    --pod-domain\t\tread pod domain name")
        print("\t    --pod-env\t\t\tread pod environment variables")
        print("\t    --pod-free\t\t\tread pod free memory")
        print("\t    --pod-host\t\t\tread pod host name")
        print("\t    --pod-mpstat\t\tread pod processor related statistics")
        print("\t    --pod-ps\t\t\tread active processes in pod")
        print("\t    --pod-top\t\t\tread system summary information in pod")
        print("\t    --pod-uptime\t\tread how long pods have been running")
        print("\t-p, --show-property\t\tread properties")
        print("\t-q, --quiet\t\t\tdo not display progress bars")
        print("\t-Q         \t\t\tdo not display progress bars or error messages")
        print("\t-r, --reverse\t\t\treverse sort order")
        print("\t-s, --short\t\t\tdisplay attribute and command values in short format")
        print("\t-t, --txt\t\t\toutput in text format")
        print("\t-u, --unique\t\t\tonly read one device for each class")
        print("\t-v\t\t\t\tset logging level to INFO")
        print("\t-V\t\t\t\tset logging level to DEBUG")
        print("\t-w, --html\t\t\toutput in HTML format")
        print("\t-x, --exact\t\t\texact matches only")
        print("\t-y, --yaml\t\t\toutput in YAML format")
        print("\t-z, --show-svc\t\t\tread Kubernetes service names")
        print("\t-0, --off\t\t\tturn device off")
        print("\t-1, --on\t\t\tturn device on")
        print(f"\t    --admin={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset admin mode off or on")
        print(
            f"\t    --simul={UNDERL}0{UNFMT},{UNDERL}1{UNFMT}\t\t\tset simulation mode off or on"
        )
        print(
            f"\t-A {UNDERL}ATTRIBUTE{UNFMT}, --attribute={UNDERL}ATTRIBUTE{UNFMT}"
            f"\n\t\t\t\t\tattribute name e.g. 'obsState' (not case sensitive)"
        )
        print(
            f"\t-C {UNDERL}COMMAND{UNFMT}, --command={UNDERL}COMMAND{UNFMT}"
            "\tcommand name, e.g. 'Status' (not case sensitive)"
        )
        print(
            f"\t-D {UNDERL}device{UNFMT}, --device={UNDERL}DEVICE{UNFMT}"
            f"\tdevice name, e.g. 'csp' (not case sensitive, only a part is needed)"
        )
        print(
            f"\t-H {UNDERL}HOST{UNFMT}, --host={UNDERL}HOST{UNFMT}"
            "\t\tTango database host and port, e.g. 10.8.13.15:10000"
        )
        print(f"\t-I {UNDERL}FILE{UNFMT}, --input={UNDERL}FILE{UNFMT},\t\tinput file name")
        print(
            f"\t-J {UNDERL}PATH{UNFMT}, --json-dir={UNDERL}PATH{UNFMT}"
            f"\tdirectory with JSON input file, e.g. 'resources'"
        )
        print(
            f"\t-K {UNDERL}PATH{UNFMT}, --class={UNDERL}PATH{UNFMT}"
            f"\t\tTango device class, e.g. 'MidCspSubarray' (not case sensitive)"
        )
        print(
            f"\t-N {UNDERL}K8S_NS{UNFMT}, --namespace={UNDERL}K8S_NS{UNFMT},"
            f" --ns={UNDERL}K8S_NS{UNFMT}"
            "\n\t\t\t\t\tKubernetes namespace for Tango database, e.g. 'staging'"
        )
        print(f"\t-O {UNDERL}FILE{UNFMT}, --output={UNDERL}FILE{UNFMT}\t\toutput file name")
        print(
            f"\t-P {UNDERL}PROPERTY{UNFMT}, --property={UNDERL}PROPERTY{UNFMT}"
            "\n\t\t\t\t\tproperty name, e.g. 'Status' (not case sensitive)"
        )
        print(
            f"\t-W {UNDERL}VALUE{UNFMT}, --value={UNDERL}VALUE{UNFMT}"
            "\t\tvalue for Tango attribute"
        )
        print(
            f"\t-X {UNDERL}FILE{UNFMT}, --cfg={UNDERL}FILE{UNFMT}"
            "\t\toverride configuration from file"
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
        print(f"\t{BOLD}man tangoktl{UNFMT}")
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
                "abcdefghijklmnopqQrstuvwxxyzV01A:C:H:D:I:J:K:N:O:P:Q:X:T:X:Z:",
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
                    "pod-df",
                    "pod-domain",
                    "pod-env",
                    "pod-free",
                    "pod-host",
                    "pod-lscpu",
                    "pod-mpstat",
                    "pod-ps",
                    "pod-top",
                    "pod-uptime",
                    "reverse",
                    "standby",
                    "status",
                    "short",
                    "show-acronym",
                    "show-attribute",
                    "show-class",
                    "show-command",
                    "show-db",
                    "show-dev",
                    "show-ns",
                    "show-pod",
                    "show-property",
                    "show-svc",
                    "table",
                    "tree",
                    "txt",
                    "unique",
                    "version",
                    "yaml",
                    "admin=",
                    "attribute=",
                    "class=",
                    "cfg=",
                    "command=",
                    "count=",
                    "device=",
                    "host=",
                    "input=",
                    "json-dir=",
                    "log-level=",
                    "ns=",
                    "namespace=",
                    "pod=",
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
            elif opt == "--count":
                self.dev_count = int(arg)
            elif opt in ("-d", "--show-dev"):
                self.disp_action.value = DispAction.TANGOCTL_NAMES
            elif opt in ("-D", "--device"):
                self.tgo_name = arg.lower()
            elif opt in ("-e", "--everything"):
                self.evrythng = True
                self.show_attrib = True
                self.show_cmd = True
                self.show_prop = True
            elif opt in ("-f", "--full"):
                self.disp_action.value = DispAction.TANGOCTL_FULL
            elif opt == "--log-level":
                self.logging_level = int(arg)
            elif opt in ("-g", "--show-class"):
                self.disp_action.value = DispAction.TANGOCTL_CLASS
            elif opt in ("-h", "--help"):
                if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
                    self.usage2(os.path.basename(cli_args[0]))
                else:
                    self.usage(os.path.basename(cli_args[0]))
                return 1
            elif opt in ("-H", "--host"):
                self.tango_host = arg
                self.logger.debug("Set host to %s", self.tango_host)
            elif opt in ("-i", "--show-db"):
                self.show_tango = True
            elif opt in ("-I", "--input"):
                self.input_file = arg
            elif opt in ("-j", "--json"):
                self.disp_action.value = DispAction.TANGOCTL_JSON
            elif opt in ("-J", "--json-dir"):
                self.json_dir = arg
            elif opt in ("-k", "--show-class"):
                self.show_class = True
            elif opt in ("-K", "--class"):
                self.tgo_class = arg
            elif opt in ("-l", "--list"):
                self.disp_action.value = DispAction.TANGOCTL_LIST
            elif opt in ("-m", "--md"):
                self.disp_action.value = DispAction.TANGOCTL_MD
            elif opt in ("-o", "--show-pod"):
                self.show_pod = "?"
            elif opt in ("-n", "--show-ns"):
                self.show_ns = True
            elif opt in ("-N", "--ns", "--namespace"):
                self.k8s_ns = arg
            elif opt == "--pod-df":
                self.show_pod = "df -h"
            elif opt == "--pod-domain":
                self.show_pod = "domainname"
            elif opt == "--pod-env":
                self.show_pod = "env"
            elif opt == "--pod-free":
                self.show_pod = "free -h"
            elif opt == "--pod-host":
                self.show_pod = "hostname"
            elif opt == "--pod-lscpu":
                self.show_pod = "lscpu -e"
            elif opt == "--pod-mpstat":
                self.show_pod = "mpstat"
            elif opt == "--pod-ps":
                self.show_pod = "ps -ef"
            elif opt == "--pod-top":
                self.show_pod = "top -b -n1"
            elif opt == "--pod-uptime":
                self.show_pod = "uptime"
            elif opt in ("-O", "--output"):
                self.output_file = arg
            elif opt in ("-p", "--show-property"):
                self.show_prop = True
            elif opt in ("-P", "--property"):
                self.tgo_prop = arg.lower()
                self.show_prop = True
            elif opt == "-q":
                self.quiet_mode = True
                self.logger.setLevel(logging.WARNING)
            elif opt == "-Q":
                self.quiet_mode = True
                self.logger.setLevel(logging.ERROR)
            elif opt in ("-r", "--reverse"):
                self.reverse = True
            elif opt in ("-R", "--port"):
                self.tango_port = int(arg)
            # TODO simulation to be deprecated
            elif opt == "--simul":
                self.dev_sim = int(arg)
            elif opt in ("-s", "--short"):
                self.disp_action.value = DispAction.TANGOCTL_SHORT
            elif opt == "--standby":
                self.dev_standby = True
            elif opt == "--status":
                show_status = {
                    "attributes": list(self.cfg_data["list_items"]["attributes"].keys()),
                    "commands": list(self.cfg_data["list_items"]["commands"].keys()),
                    "properties": list(self.cfg_data["list_items"]["properties"].keys()),
                }
                self.logger.info("Status set to %s", show_status)
            elif opt == "--table":
                self.disp_action.value = DispAction.TANGOCTL_TABL
            elif opt == "--test":
                self.dev_test = True
            elif opt in ("-t", "--txt"):
                self.disp_action.value = DispAction.TANGOCTL_TXT
            # TODO Feature to search by input type, not implemented yet
            elif opt in ("-T", "--type"):
                self.tgo_in_type = arg.lower()
                self.logger.info("Input type %s not implemented", self.tgo_in_type)
                return 1
            elif opt in ("-u", "--unique"):
                self.uniq_cls = True
            elif opt == "-v":
                self.quiet_mode = False
                self.logger.setLevel(logging.INFO)
            elif opt == "-V":
                self.quiet_mode = False
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
            elif opt in ("-z", "--show-svc"):
                self.show_svc = True
            elif opt in ("-Z", "--timeout"):
                self.timeout_millis = int(arg)
            elif opt in ("0", "--off"):
                self.dev_off = True
            elif opt in ("1", "--on"):
                self.dev_on = True
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

    def print_pod_names(self, ns_name: str | None) -> None:  # noqa: C901
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        """
        self.logger.debug("Print Kubernetes pods")
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return
        pods_dict: dict = self.get_pods_dict(ns_name)
        print(f"Pods in namespace {ns_name} : {len(pods_dict)}")
        pod_name: str
        for pod_name in pods_dict:
            print(f"\t{pod_name}")

    def print_pods(  # noqa: C901
        self, ns_name: str | None, quiet_mode: bool, pod_cmd: str
    ) -> None:
        """
        Display pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param quiet_mode: flag to suppress extra output
        :param pod_cmd: command to run
        """
        self.logger.debug("Print Kubernetes pods: %s", pod_cmd)
        pod_exec: list = pod_cmd.split(" ")
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
                resps: str = k8s.exec_command(ns_name, pod_name, pod_exec)
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

    def get_pods_json(  # noqa: C901
        self, ns_name: str | None, quiet_mode: bool, pod_cmd: str
    ) -> list:
        """
        Read pods in Kubernetes namespace.

        :param ns_name: namespace name
        :param quiet_mode: print progress bars
        :param pod_cmd: command to run on pod
        :return: dictionary with pod information
        """
        self.logger.debug("Get Kubernetes pods as JSON: %s", pod_cmd)
        pods: list = []
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return pods
        # pod_exec: list = ["ps", "-ef"]
        pod_exec: list = pod_cmd.split(" ")
        if ns_name is None:
            self.logger.error("K8S namespace not specified")
            return pods
        k8s: KubernetesInfo = KubernetesInfo(self.logger)
        self.logger.debug("Read pods running in namespace %s", ns_name)
        pods_list: dict = k8s.get_pods(ns_name, None)
        self.logger.info("Found %d pods running in namespace %s", len(pods_list), ns_name)
        pod_name: str
        for pod_name in pods_list:
            pod: dict = {}
            pod["name"] = pod_name
            pod["command"] = pod_cmd
            self.logger.info("Read processes running in pod %s", pod_name)
            resps: str = k8s.exec_command(ns_name, pod_name, pod_exec)
            pod["output"] = []
            if quiet_mode:
                continue
            if not resps:
                pod["output"].append("N/A")
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
                        pod["output"].append(resp)
            else:
                pod["output"].append(resps)
            pods.append(pod)
        return pods

    def show_pods(self, pod_cmd: str) -> None:
        """
        Display pods in Kubernetes namespace.

        :param pod_cmd: command to run
        """
        self.logger.debug("Show Kubernetes pods as JSON")
        pods: list
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            pods = self.get_pods_json(self.k8s_ns, self.quiet_mode, pod_cmd)
            if self.output_file is not None:
                self.logger.info("Write output file %s", self.output_file)
                with open(self.output_file, "a") as outf:
                    outf.write(json.dumps(pods, indent=4))
            else:
                print(json.dumps(pods, indent=4))
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            pods = self.get_pods_json(self.k8s_ns, self.quiet_mode, pod_cmd)
            if self.output_file is not None:
                self.logger.info("Write output file %s", self.output_file)
                with open(self.output_file, "a") as outf:
                    outf.write(yaml.dump(pods))
            else:
                print(yaml.dump(pods))
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            if pod_cmd == "?":
                self.print_pod_names(self.k8s_ns)
            else:
                self.print_pods(self.k8s_ns, self.quiet_mode, pod_cmd)
        else:
            self.logger.warning("Output format %s not supported", self.disp_action)
            pass

    def print_k8s_info(self) -> None:
        """Print kubernetes context and namespace."""
        if self.k8s_ctx:
            print(f"K8S context : {self.k8s_ctx}")
        if self.k8s_ns:
            print(f"K8S namespace : {self.k8s_ns}")

    def run_info(self, file_name: str | None) -> int:  # noqa: C901
        """
        Read information on Tango devices.

        :param file_name: output file name
        :return: error condition
        """
        rc: int
        devices: TangoctlDevices
        self.logger.info(
            "Run info display %s : device %s attribute %s command %s property %s for K8S...",
            repr(self.disp_action),
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
        )

        # List Tango devices
        if self.disp_action.check(DispAction.TANGOCTL_SHORT) and not (
            self.show_attrib or self.show_cmd or self.show_attrib
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
                self.timeout_millis,
                self.show_attrib,
                self.show_cmd,
                self.show_prop,
                self.show_status,
                self.cfg_data,
                self.tgo_name,
                self.uniq_cls,
                self.reverse,
                self.evrythng,
                self.quiet_mode,
                self.xact_match,
                self.disp_action,
                self.k8s_ctx,
                self.k8s_ns,
                self.tgo_attrib,
                self.tgo_cmd,
                self.tgo_prop,
                file_name,
                dev_count=self.dev_count,
            )
        except tango.ConnectionFailed:
            self.logger.error("Tango connection for K8S info failed")
            return 1

        self.logger.debug("Read devices running for K8S (action %s)", repr(self.disp_action))

        # Display in specified format
        if self.show_class:
            if self.disp_action.check(DispAction.TANGOCTL_JSON):
                klasses = devices.get_classes()
                klasses["namespace"] = self.k8s_ns
                klasses["context"] = self.k8s_ctx
                print(json.dumps(klasses, indent=4, cls=NumpyEncoder))
            elif self.disp_action.check(DispAction.TANGOCTL_YAML):
                klasses = devices.get_classes()
                klasses["namespace"] = self.k8s_ns
                klasses["context"] = self.k8s_ctx
                print((yaml.safe_dump(klasses, default_flow_style=False, sort_keys=False)))
            else:
                devices.print_classes()
        elif self.disp_action.check(DispAction.TANGOCTL_LIST):
            # TODO this is messy
            self.print_k8s_info()
            devices.read_devices()
            devices.read_device_values()
            if self.show_attrib or self.show_cmd or self.show_prop:
                if self.show_attrib:
                    devices.print_txt_list_attributes(True)
                if self.show_cmd:
                    devices.print_txt_list_commands(True)
                if self.show_prop:
                    devices.print_txt_list_properties(True)
            else:
                devices.print_txt_list()
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.print_k8s_info()
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt_all()
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            devices.read_devices()
            devices.read_device_values()
            devices.print_html(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_JSON):
            devices.read_devices()
            devices.read_device_values()
            if self.disp_action.check(DispAction.TANGOCTL_SHORT):
                devices.print_json_short(self.disp_action)
            else:
                devices.print_json(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_MD):
            devices.read_devices()
            devices.read_device_values()
            devices.print_markdown()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            devices.read_devices()
            devices.read_device_values()
            if self.disp_action.check(DispAction.TANGOCTL_SHORT):
                devices.print_yaml_short(self.disp_action)
            else:
                devices.print_yaml(self.disp_action)
        elif self.disp_action.check(DispAction.TANGOCTL_SHORT):
            self.print_k8s_info()
            devices.read_devices()
            devices.print_txt_short()
            # if self.show_attrib:
            #     devices.print_txt_list_attributes()
            # if self.show_cmd:
            #     devices.print_txt_list_commands()
            # if self.show_prop:
            #     devices.print_txt_list_properties()
        elif self.disp_action.check(DispAction.TANGOCTL_NAMES):
            self.print_k8s_info()
            devices.print_names_list()
        elif self.disp_action.check(DispAction.TANGOCTL_TABL):
            devices.read_devices()
            devices.read_device_values()
            devices.print_json_table()
        else:
            self.logger.error("Display action %s not supported", self.disp_action)

        return 0

    def get_namespaces_list(self) -> tuple:
        """
        Read namespaces in Kubernetes cluster.

        :return: tupe with context name and list with devices
        """
        self.logger.debug("List Kubernetes namespaces")
        ns_list: list = []
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes package is not installed")
            return None, ns_list
        k8s: KubernetesInfo = KubernetesInfo(self.logger)
        k8s_list: list
        _ctx_name: str | None
        _ctx_name, k8s_list = k8s.get_namespaces_list(self.k8s_ns)
        if self.k8s_ns is None:
            return k8s.context, k8s_list
        for k8s_name in k8s_list:
            if k8s_name == self.k8s_ns:
                ns_list.append(k8s_name)
        self.logger.info("Read %d namespaces: %s", len(ns_list), ",".join(ns_list))
        return k8s.context, ns_list

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
        ctx_name: str | None
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
            ctx_name, ns_list = self.get_namespaces_list()
            print(f"Context : {ctx_name}")
            print(f"Namespaces : {len(ns_list)}")
            for ns_name in sorted(ns_list, reverse=self.reverse):
                print(f"\t{ns_name}")

    def show_services(self) -> None:
        """Display services in Kubernetes namespace."""
        self.logger.debug("Show Kubernetes services (%s)", self.disp_action)
        # self.get_services_json(self.ns_name, self.quiet_mode)
        k8s: KubernetesInfo = KubernetesInfo(self.logger)
        if self.disp_action.check(DispAction.TANGOCTL_JSON):
            service_dict = k8s.get_services_dict(self.k8s_ns)
            print(f"***\n{json.dumps(service_dict, indent=4)}")
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            service_list = k8s.get_services_data(self.k8s_ns)
            self.logger.debug("Kubernetes services:\n%s", service_list)
            if not service_list.items:
                self.logger.error("No services found in namespace %s", self.k8s_ns)
                return
            for service in service_list.items:
                print(f"Service Name: {service.metadata.name}")
                print(f"  Type: {service.spec.type}")
                print(f"    IP: {service.spec.cluster_ip}")
                if service.spec.ports:
                    for port in service.spec.ports:
                        print(
                            f"  Port: {port.port}, Target Port: {port.target_port},"
                            f" Protocol: {port.protocol}"
                        )
                print("-" * 20)
        else:
            self.logger.warning("Nothing to do!")

    def read_tango_host(self, ntango: int, ntangos: int) -> int:  # noqa: C901
        """
        Read info from Tango host.

        :param ntango: index number,
        :param ntangos: index count
        :return: error condition
        """
        rc: int = 0

        # Fork just in case, so that ctrl-C will work (most of the time)
        pid: int = os.fork()
        if pid == 0:
            # Do the actual reading
            self.logger.info("Processing namespace %s", self.k8s_ns)
            rc = self.run_info(self.output_file)
            self.logger.info("Processed namespace %s", self.k8s_ns)
            sys.exit(rc)
        else:
            # Wait for the reading process
            try:
                os.waitpid(pid, 0)
            except OSError:
                pass
            self.logger.info("Processing %s finished (PID %d)", self.k8s_ns, pid)

        return rc
