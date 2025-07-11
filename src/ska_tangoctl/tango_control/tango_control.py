"""Read all information about Tango devices in a Kubernetes cluster."""

import json
import logging
import os
import socket
import sys
from typing import Any

import tango
import yaml

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_device import DEFAULT_TIMEOUT_MILLIS, TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices import NumpyEncoder, TangoctlDevices
from ska_tangoctl.tango_control.tango_control_help import TangoControlHelpMixin
from ska_tangoctl.tango_control.tango_control_setup import TangoControlSetupMixin
from ska_tangoctl.tango_control.tangoctl_config import TANGOCTL_CONFIG, read_tangoctl_config
from ska_tangoctl.tango_control.test_tango_script import TangoScript


class TangoControl(TangoControlHelpMixin, TangoControlSetupMixin):
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
        self.domain_name: str | None = None
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
                self.domain_name,
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
            self.logger.debug("Get device classes in JSON format")
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
                    self.domain_name,
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
            self.logger.info("Got classes for %d devices in JSON format", len(devices.device_names))
        elif self.disp_action.check(DispAction.TANGOCTL_TXT):
            self.logger.debug("List device classes (%s)", self.disp_action)
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
                    self.domain_name,
                )
            except tango.ConnectionFailed:
                self.logger.error("Tango connection for text class list failed")
                return 1
            devices.read_devices()
            devices.read_configs()
            devices.print_classes()
            self.logger.info(
                "Listed %d device classes (%s)", len(devices.device_names), self.disp_action
            )
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

        self.logger.debug("List devices (%s) with name %s", self.disp_action, self.tgo_name)
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
                self.domain_name,
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
            devices.print_html()
        else:
            devices.read_devices()
            devices.print_txt_list()
        self.logger.debug(
            "Listed %d devices (%s) with name %s",
            len(devices.device_names),
            self.disp_action,
            self.tgo_name,
        )

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
        self.logger.debug("List JSON files in %s", json_dir)
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
                    self.logger.warning("File %s is not a valid JSON file", file_name)
        self.logger.info("Listed %d JSON files in %s", len(file_names)-rv, json_dir)
        return rv

    def set_value(self) -> int:
        """
        Set value for a Tango device.

        :return: error condition
        """
        self.logger.debug(
            "Set device %s attribute %s value to %s",
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_value,
        )
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
            None,
            None,
            indent=self.disp_action.indent,
        )
        dev.read_attribute_value()
        dev.write_attribute_value(self.tgo_attrib, self.tgo_value)
        self.logger.info(
            "Device %s attribute %s value set to %s",
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_value,
        )
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
        if self.disp_action.size == "S" and not (
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
            self.logger.debug("Read device classes -->")
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
            self.logger.debug("List devices -->")
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
            self.logger.debug("List devices as txt -->")
            devices.read_devices()
            devices.read_device_values()
            devices.print_txt()
        elif self.disp_action.check(DispAction.TANGOCTL_HTML):
            self.logger.debug("List devices as HTML -->")
            devices.read_devices()
            devices.read_device_values()
            devices.print_html()
        elif self.disp_action.check(DispAction.TANGOCTL_JSON):
            self.logger.debug("List devices as JSON -->")
            devices.read_devices()
            devices.read_device_values()
            devices.print_json()
        elif self.disp_action.check(DispAction.TANGOCTL_MD):
            self.logger.debug("List devices as markdown -->")
            devices.read_devices()
            devices.read_device_values()
            devices.print_markdown()
        elif self.disp_action.check(DispAction.TANGOCTL_YAML):
            self.logger.debug("List devices as YAML -->")
            devices.read_devices()
            devices.read_device_values()
            devices.print_yaml()
        elif self.disp_action.check(DispAction.TANGOCTL_NAMES):
            self.logger.debug("List device names -->")
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
