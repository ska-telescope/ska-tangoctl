"""Read and display Tango stuff."""

import json
import logging
import os
from collections import OrderedDict
from typing import Any

import tango
import yaml

from ska_mid_itf_engineering_tools.tango_control.read_tango_device import (
    TangoctlDevice,
    TangoctlDeviceBasic,
)
from ska_mid_itf_engineering_tools.tango_control.tango_json import TangoJsonReader, progress_bar


class TangoctlDevicesBasic:
    """Compile a dictionary of available Tango devices."""

    devices: dict = {}
    quiet_mode: bool = True
    dev_classes: list = []
    logger: logging.Logger
    fmt: str

    def __init__(  # noqa: C901s
        self,
        logger: logging.Logger,
        uniq_cls: bool,
        quiet_mode: bool,
        evrythng: bool,
        cfg_data: Any,
        tgo_name: str | None,
        fmt: str,
    ):
        """
        Read list of Tango devices.

        :param logger: logging handle
        :param uniq_cls: only read one device per class
        :param quiet_mode: flag for displaying progress bar
        :param evrythng: read and display the whole thing
        :param cfg_data: configuration data
        :param fmt: output format
        :param tgo_name: device name
        :raises Exception: database connect failed
        """
        self.logger = logger
        # Get Tango database host
        tango_host: str | None = os.getenv("TANGO_HOST")
        # Connect to database
        try:
            database = tango.Database()
        except Exception as oerr:
            self.logger.error("Could not connect to Tango database %s : %s", tango_host, oerr)
            raise oerr

        # Read devices
        device_list: list = sorted(database.get_device_exported("*").value_string)
        self.logger.info("%d basic devices available", len(device_list))

        if tgo_name:
            tgo_name = tgo_name.lower()
        self.logger.info("Open basic device %s", tgo_name)

        self.logger.info("Read %d basic devices...", len(device_list))
        self.fmt = fmt
        list_values: dict = cfg_data["list_values"]
        self.quiet_mode = quiet_mode
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        # Run "for device in device_list:"
        device: str
        for device in progress_bar(
            device_list,
            not self.quiet_mode,
            prefix=f"Read {len(device_list)} exported basic devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            new_dev: TangoctlDeviceBasic
            if not evrythng:
                chk_fail: bool = False
                for dev_chk in cfg_data["ignore_device"]:
                    chk_len: int = len(dev_chk)
                    if device[0:chk_len] == dev_chk:
                        chk_fail = True
                        break
                if chk_fail:
                    self.logger.debug("'%s' matches '%s'", device, cfg_data["ignore_device"])
                    continue
            if tgo_name:
                ichk: str = device.lower()
                if tgo_name not in ichk:
                    self.logger.debug("Ignore basic device %s", device)
                    continue
            new_dev = TangoctlDeviceBasic(logger, device, list_values)
            if uniq_cls:
                dev_class: str = new_dev.dev_class
                if dev_class == "---":
                    self.logger.info(f"Skip basic device {device} with unknown class {dev_class}")
                elif dev_class not in self.dev_classes:
                    self.dev_classes.append(dev_class)
                    self.devices[device] = new_dev
                else:
                    self.logger.info(f"Skip basic device {device} with known class {dev_class}")
            else:
                self.devices[device] = new_dev

    def read_config(self) -> None:
        """Read additional data."""
        self.logger.info("Read %d basic device configs...", len(self.devices))
        # Run "device in self.devices:"
        for device in progress_bar(
            self.devices,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices)} device configs :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.devices[device].read_config()

    def make_json(self) -> dict:
        """
        Make dictionary of devices.

        :return: dictionary with device data
        """
        devdict = {}
        self.logger.info("List %d basic devices in JSON format...", len(self.devices))
        for device in self.devices:
            devdict[device] = self.devices[device].make_json()
        return devdict

    def print_txt_list(self) -> None:
        """Print list of devices."""
        self.logger.info("List %d devices in text format...", len(self.devices))
        print(f"{'DEVICE NAME':64} {'STATE':10} {'ADMIN':11} {'VERSION':8} CLASS")
        for device in self.devices:
            self.devices[device].print_list()

    def print_html(self, disp_action: int) -> None:
        """
        Print in HTML format.

        :param disp_action: display control flag
        """
        self.logger.info("List %d basic devices in HTML format...", len(self.devices))
        print("<table>")
        print(
            "<tr><td>DEVICE NAME</td><td>STATE</td><td>ADMIN</td><td>VERSION</td>"
            "<td>CLASS</td></tr>"
        )
        for device in self.devices:
            self.devices[device].print_html()
        print("<table>")

    def print_txt_classes(self) -> None:
        """Print list of classes."""
        self.logger.info("Read classes in %d devices...", len(self.devices))
        print(f"{'DEVICE NAME':64} {'STATE':10} {'ADMIN':11} {'VERSION':8} CLASS")
        dev_classes: list = []
        for device in self.devices:
            dev_class: str = self.devices[device].dev_class
            if dev_class != "---" and dev_class not in dev_classes:
                dev_classes.append(dev_class)
                self.devices[device].print_list()

    def get_classes(self) -> OrderedDict[Any, Any]:
        """
        Get list of classes.

        :return: dictionary of classes
        """
        self.logger.info("Get classes in %d devices", len(self.devices))
        dev_classes: dict = {}
        for device in self.devices:
            dev_class: str = self.devices[device].dev_class
            if dev_class == "---":
                continue
            if dev_class not in dev_classes:
                dev_classes[dev_class] = []
            dev_classes[dev_class].append(self.devices[device].dev_name)
        return OrderedDict(sorted(dev_classes.items()))

    def print_json(self, disp_action: int) -> None:
        """
        Print in JSON format.

        :param disp_action: not used
        """
        self.logger.info("Print JSON")
        devsdict: dict = self.make_json()
        print(json.dumps(devsdict, indent=4))

    def print_yaml(self, disp_action: int) -> None:
        """
        Print in YAML format.

        :param disp_action: not used
        """
        self.logger.info("Print YAML")
        devsdict: dict = self.make_json()
        print(yaml.dump(devsdict))


class TangoctlDevices(TangoctlDevicesBasic):
    """Compile a dictionary of available Tango devices."""

    devices: dict = {}
    attribs_found: list = []
    tgo_space: str = ""
    quiet_mode: bool = True
    dev_classes: list = []
    delimiter: str
    run_commands: list
    run_commands_name: list
    prog_bar: bool

    def __init__(  # noqa: C901s
        self,
        logger: logging.Logger,
        uniq_cls: bool,
        quiet_mode: bool,
        evrythng: bool,
        cfg_data: dict,
        tgo_name: str | None,
        tgo_attrib: str | None,
        tgo_cmd: str | None,
        tgo_prop: str | None,
        tango_port: int,
        output_file: str | None,
        fmt: str = "json",
        nodb: bool = False,
    ):
        """
        Get a dict of devices.

        :param logger: logging handle
        :param uniq_cls: only read one device per class
        :param cfg_data: configuration data in JSON format
        :param quiet_mode: flag for displaying progress bars
        :param evrythng: get commands and attributes regadrless of state
        :param tgo_name: filter device name
        :param tgo_attrib: filter attribute name
        :param tgo_cmd: filter command name
        :param tgo_prop: filter property name
        :param tango_port: device port
        :param output_file: output file name
        :param fmt: output format
        :param nodb: flag to run without database
        :raises Exception: when database connect fails
        """
        new_dev: TangoctlDevice

        self.logger = logger
        self.output_file = output_file
        self.logger.info(
            "Read devices %s : attribute %s command %s property %s",
            tgo_name,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
        )
        # Get Tango database host
        tango_host = os.getenv("TANGO_HOST")

        self.delimiter = cfg_data["delimiter"]
        self.run_commands = cfg_data["run_commands"]
        self.logger.info("Run commands %s", self.run_commands)
        self.run_commands_name = cfg_data["run_commands_name"]
        self.logger.info("Run commands with name %s", self.run_commands_name)
        self.prog_bar = not quiet_mode

        if nodb:
            trl = f"tango://127.0.0.1:{tango_port}/{tgo_name}#dbase=no"
            new_dev = TangoctlDevice(logger, not self.prog_bar, trl, tgo_attrib, tgo_cmd, tgo_prop)
            self.devices[tgo_name] = new_dev
        else:
            # Connect to database
            try:
                database = tango.Database()
            except Exception as oerr:
                self.logger.error("Could not connect to Tango database %s : %s", tango_host, oerr)
                raise oerr

            # Read devices
            device_list: list = sorted(database.get_device_exported("*").value_string)
            self.logger.info("Read %d devices available...", len(device_list))

            if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
                self.prog_bar = False
            # Run 'for device in device_list:'
            for device in progress_bar(
                device_list,
                self.prog_bar,
                prefix=f"Read {len(device_list)} exported devices :",
                suffix="Complete",
                length=100,
            ):
                # Check device name against mask
                if not evrythng:
                    chk_fail: bool = False
                    for dev_chk in cfg_data["ignore_device"]:
                        chk_len = len(dev_chk)
                        if device[0:chk_len] == dev_chk:
                            chk_fail = True
                            break
                    if chk_fail:
                        self.logger.debug("'%s' matches '%s'", device, cfg_data["ignore_device"])
                        continue
                if tgo_name:
                    ichk: str = device.lower()
                    if tgo_name not in ichk:
                        self.logger.debug("Ignore device %s", device)
                        continue
                try:
                    new_dev = TangoctlDevice(
                        logger, not self.prog_bar, device, tgo_attrib, tgo_cmd, tgo_prop
                    )
                except tango.ConnectionFailed:
                    logger.info("Could not read device %s", device)
                    continue
                if tgo_attrib:
                    attribs_found: list = new_dev.check_for_attribute(tgo_attrib)
                    if attribs_found:
                        self.logger.info("Device %s matched attributes %s", device, attribs_found)
                        self.devices[device] = new_dev
                    else:
                        logger.debug("Skip device %s (attribute %s not found)", device, tgo_attrib)
                elif tgo_cmd:
                    cmds_found: list = new_dev.check_for_command(tgo_cmd)
                    if cmds_found:
                        self.logger.info("Device %s matched commands %s", device, cmds_found)
                        self.devices[device] = new_dev
                    else:
                        logger.debug("Skip device %s (command %s not found)", device, tgo_cmd)
                elif tgo_prop:
                    props_found: list = new_dev.check_for_property(tgo_prop)
                    if props_found:
                        self.logger.info("Device %s matched properties %s", device, props_found)
                        self.devices[device] = new_dev
                    else:
                        logger.debug("Skip device %s (command %s not found)", device, tgo_cmd)
                elif uniq_cls:
                    dev_class: str = new_dev.dev_class
                    if dev_class == "---":
                        self.logger.info(
                            f"Skip basic device {device} with unknown class {dev_class}"
                        )
                    elif dev_class not in self.dev_classes:
                        self.dev_classes.append(dev_class)
                        self.devices[device] = new_dev
                    else:
                        self.logger.info(f"Skip device {device} with known class {dev_class}")
                else:
                    self.logger.debug("Add device %s", device)
                    self.devices[device] = new_dev
        logger.debug("Read %d devices", len(self.devices))

    def read_attribute_values(self) -> None:
        """Read device data."""
        self.logger.info("Read attributes of %d devices...", len(self.devices))
        # Run 'for device in self.devices:'
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} attributes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.devices[device].read_attribute_value()

    def read_command_values(self) -> None:
        """Read device data."""
        self.logger.info("Read commands of %d devices...", len(self.devices))
        # Run "for device in self.devices:"
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} device commands :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.devices[device].read_command_value(self.run_commands, self.run_commands_name)

    def read_property_values(self) -> None:
        """Read device data."""
        self.logger.info("Read properties of %d devices...", len(self.devices))
        # Run "for device in self.devices:"
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} property values :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.devices[device].read_property_value()

    def read_device_values(self) -> None:
        """Read device data."""
        self.logger.debug("Read attribute, command and property data from devices")
        self.read_attribute_values()
        self.read_command_values()
        self.read_property_values()
        self.logger.debug("Read devices %s", self.devices)

    def make_json(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devsdict: dict = {}
        self.logger.debug("Read %d JSON devices...", len(self.devices))
        # Run "for device in self.devices:"
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} JSON records :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            devsdict[device] = self.devices[device].make_json(self.delimiter)
        return devsdict

    def print_txt_list_attrib(self) -> None:
        """Print list of devices with attribute name."""
        self.logger.info("Listing %d devices...", len(self.devices))
        for device in self.devices:
            print(f"{device}")
        return

    def print_txt_list(self) -> None:
        """Print list of devices."""
        self.logger.info("List %d devices...", len(self.devices))
        if self.output_file is not None:
            self.logger.info("Write output file %s", self.output_file)
            with open(self.output_file, "w") as outf:
                for device in self.devices:
                    outf.write(f"{device}\n")
        else:
            for device in self.devices:
                print(f"{device}")

    def print_txt(self, disp_action: int) -> None:
        """
        Print in text format.

        :param disp_action: display control flag
        """
        json_reader: TangoJsonReader
        if disp_action == 4:
            self.print_txt_list()
        elif disp_action == 3:
            devsdict = self.make_json()
            json_reader = TangoJsonReader(
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
            )
            json_reader.print_txt_quick()
        else:
            devsdict = self.make_json()
            json_reader = TangoJsonReader(
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
            )
            json_reader.print_txt_all()

    def print_json(self, disp_action: int) -> None:
        """
        Print in JSON format.

        :param disp_action: display control flag
        """
        devsdict: dict = self.make_json()
        if self.output_file is not None:
            self.logger.info("Write output file %s", self.output_file)
            with open(self.output_file, "w") as outf:
                outf.write(json.dumps(devsdict, indent=4))
        else:
            print(json.dumps(devsdict, indent=4))

    def print_markdown(self, disp_action: int) -> None:
        """
        Print in JSON format.

        :param disp_action: display control flag
        """
        self.logger.info("Markdown")
        devsdict: dict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
        )
        json_reader.print_markdown_all()

    def print_html(self, disp_action: int) -> None:
        """
        Print in HTML format.

        :param disp_action: display control flag
        """
        self.logger.info("Print devices as HTML")
        devsdict: dict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
        )
        if disp_action == 4:
            json_reader.print_html_all(True)
        else:
            json_reader.print_html_quick(True)

    def print_yaml(self, disp_action: int) -> None:
        """
        Print in YAML format.

        :param disp_action: display control flag
        """
        self.logger.info("Print devices as YAML")
        devsdict: dict = self.make_json()
        if self.output_file is not None:
            self.logger.info("Write output file %s", self.output_file)
            with open(self.output_file, "w") as outf:
                outf.write(yaml.dump(devsdict))
        else:
            print(yaml.dump(devsdict))

    def print_txt_list_attributes(self) -> None:
        """Print list of devices."""
        self.logger.info("List %d devices...", len(self.devices))
        print(f"{'DEVICE NAME':64} {'STATE':10} {'ADMIN':11} {'VERSION':8} {'CLASS':24} ATTRIBUTE")
        for device in self.devices:
            if self.devices[device].attributes:
                self.devices[device].print_list_attribute()

    def print_txt_list_commands(self) -> None:
        """Print list of devices."""
        self.logger.info("List %d devices...", len(self.devices))
        print(f"{'DEVICE NAME':64} {'STATE':10} {'ADMIN':11} {'VERSION':8} {'CLASS':24} COMMAND")
        for device in self.devices:
            if self.devices[device].commands:
                self.devices[device].print_list_command()

    def print_txt_list_properties(self) -> None:
        """Print list of properties."""
        self.logger.info("List %d properties...", len(self.devices))
        print(f"{'DEVICE NAME':64} {'STATE':10} {'ADMIN':11} {'VERSION':8} {'CLASS':24} PROPERTY")
        for device in self.devices:
            if self.devices[device].properties:
                self.devices[device].print_list_property()
