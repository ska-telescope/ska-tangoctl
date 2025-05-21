"""Read and display Tango stuff."""

import json
import logging
import os
import re
from collections import OrderedDict
from typing import Any

import numpy as np
import tango
import yaml

from ska_tangoctl.tango_control.disp_action import TANGOCTL_LIST, TANGOCTL_SHORT
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice, TangoctlDeviceBasic
from ska_tangoctl.tango_control.tango_json import TangoJsonReader, progress_bar


class NumpyEncoder(json.JSONEncoder):
    """Make a numpy object more JSON-friendly."""

    def default(self, np_obj: Any) -> Any:
        """
        Set values to default.

        :param np_obj: object to be read
        :returns: JSON-friendly thing
        """
        if isinstance(np_obj, np.ndarray):
            return np_obj.tolist()
        return super().default(np_obj)


class TangoctlDevicesBasic:
    """Compile a dictionary of available Tango devices."""

    logger: logging.Logger

    def __init__(  # noqa: C901s
        self,
        logger: logging.Logger,
        show_attrib: bool,
        show_cmd: bool,
        show_prop: bool,
        show_status: dict,
        cfg_data: Any,
        tgo_name: str | None,
        uniq_cls: bool,
        reverse: bool,
        evrythng: bool,
        fmt: str,
        quiet_mode: bool,
        ns_name: str | None = None,
    ):
        """
        Read list of Tango devices.

        :param logger: logging handle
        :param show_attrib: flag for processing attributes
        :param show_cmd: flag for processing commands
        :param show_prop: flag for processing properties
        :param show_status: flag for processing status
        :param uniq_cls: only read one device per class
        :param quiet_mode: flag for displaying progress bar
        :param reverse: sort in reverse order
        :param evrythng: read and display the whole thing
        :param cfg_data: configuration data
        :param fmt: output format
        :param tgo_name: device name
        :param ns_name: K8S namespace
        :raises Exception: database connect failed
        """
        self.devices: dict = {}
        self.quiet_mode: bool = True
        self.dev_classes: list = []
        self.fmt: str
        self.cfg_data: dict
        self.tango_host: str | None
        database: tango.Database
        device_list: list
        new_dev: TangoctlDeviceBasic
        dev_class: str
        self.list_items: dict
        self.ns_name: str | None = ns_name

        self.logger = logger
        # Get Tango database host
        self.tango_host = os.getenv("TANGO_HOST")
        # Connect to database
        try:
            database = tango.Database()
        except Exception as oerr:
            self.logger.warning("Could not connect to basic Tango database %s", self.tango_host)
            raise oerr
        self.logger.debug("Connect to basic Tango database %s", self.tango_host)

        # Read devices
        device_list = sorted(database.get_device_exported("*").value_string, reverse=reverse)
        self.logger.debug("%d basic devices available", len(device_list))

        if tgo_name:
            tgo_name = tgo_name.lower()
        self.logger.debug("Open basic devices for %s", tgo_name)

        self.logger.info("Read %d basic devices (unique %s) ...", len(device_list), uniq_cls)
        self.fmt = fmt
        self.cfg_data = cfg_data
        self.list_items = self.cfg_data["list_items"]
        self.quiet_mode = quiet_mode
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        # Run "for device in device_list:" in progress bar
        device: str
        for device in progress_bar(
            device_list,
            not self.quiet_mode,
            prefix=f"Read {len(device_list)} exported basic devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
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
            try:
                new_dev = TangoctlDeviceBasic(
                    logger,
                    show_attrib,
                    show_cmd,
                    show_prop,
                    show_status,
                    device,
                    reverse,
                    self.list_items,
                )
                if uniq_cls:
                    dev_class = new_dev.dev_class
                    if dev_class == "---":
                        self.logger.debug(
                            f"Skip basic device {device} with unknown class {dev_class}"
                        )
                    elif dev_class not in self.dev_classes:
                        self.dev_classes.append(dev_class)
                        self.devices[device] = new_dev
                    else:
                        self.logger.debug(
                            f"Skip basic device {device} with known class {dev_class}"
                        )
                else:
                    self.devices[device] = new_dev
            except Exception as e:
                self.logger.warning("%s", e)
                self.devices[device] = None

    def __del__(self) -> None:
        """Destructor."""
        tango_host = os.getenv("TANGO_HOST")
        self.logger.debug("Shut down TangoctlDevicesBasic for host %s", tango_host)
        os.environ.pop("TANGO_HOST", None)

    def read_configs(self) -> None:
        """Read additional data."""
        self.logger.debug("Read %d basic device configs...", len(self.devices))
        # Run "device in self.devices:"
        for device in progress_bar(
            self.devices,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices)} device configs :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                self.devices[device].read_config()

    def read_attribute_names(self) -> dict:
        """
        Read device data.

        :return: dictionary of devices
        """
        self.logger.debug("Read attribute names of %d devices", len(self.devices))
        the_attribs: dict = {}
        # Run 'for device in self.devices:'
        for device in progress_bar(
            self.devices,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices)} attributes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            dev_attribs = self.devices[device].attribs
            for attr in dev_attribs:
                if attr not in the_attribs:
                    the_attribs[attr] = []
                the_attribs[attr].append(device)
        self.logger.debug("Read attribute names of %d devices: %s", len(the_attribs), the_attribs)
        return the_attribs

    def read_command_names(self) -> dict:
        """
        Read device data.

        :return: dictionary of devices
        """
        self.logger.debug("Read command names of %d devices", len(self.devices))
        the_commands: dict = {}
        # Run 'for device in self.devices:'
        for device in progress_bar(
            self.devices,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices)} attributes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            try:
                dev_commands = self.devices[device].cmds
                for cmd in dev_commands:
                    if cmd not in the_commands:
                        the_commands[cmd] = []
                    the_commands[cmd].append(device)
            except AttributeError:
                self.logger.warning("Could not read device %s", device)
        self.logger.debug("Read command names of %d devices: %s", len(the_commands), the_commands)
        return the_commands

    def read_property_names(self) -> dict:
        """
        Read device data.

        :return: dictionary of devices
        """
        self.logger.debug("Read property names of %d devices", len(self.devices))
        the_properties: dict = {}
        # Run 'for device in self.devices:'
        for device in progress_bar(
            self.devices,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices)} attributes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            dev_properties = self.devices[device].props
            for prop in dev_properties:
                if prop not in the_properties:
                    the_properties[prop] = []
                the_properties[prop].append(prop)
        self.logger.debug(
            "Read property names of %d devices: %s", len(the_properties), the_properties
        )
        return the_properties

    def make_json(self) -> dict:
        """
        Make dictionary of devices.

        :return: dictionary with device data
        """
        devdict: dict

        devdict = {}
        self.logger.debug("List %d basic devices in JSON format...", len(self.devices))
        for device in self.devices:
            if self.devices[device] is not None:
                devdict[device] = self.devices[device].make_json()
        return devdict

    def print_txt_heading(self, eol: str = "\n") -> int:
        """
        Print heading for list of devices.

        :param eol: printed at the end
        :return: width of characters printed
        """
        line_width: int

        print(f"{'DEVICE NAME':64} ", end="")
        line_width = 65
        for attribute in self.list_items["attributes"]:
            field_name = attribute.upper()
            field_width = self.list_items["attributes"][attribute]
            line_width += int(re.sub(r"\D", "", field_width)) + 1
            print(f"{field_name:{field_width}} ", end="")
        for command in self.list_items["commands"]:
            field_name = command.upper()
            field_width = self.list_items["commands"][command]
            line_width += int(re.sub(r"\D", "", field_width)) + 1
            print(f"{field_name:{field_width}} ", end="")
        for tproperty in self.list_items["properties"]:
            field_name = tproperty.upper()
            field_width = self.list_items["properties"][tproperty]
            line_width += int(re.sub(r"\D", "", field_width)) + 1
            print(f"{field_name:{field_width}} ", end="")
        print(f"{'CLASS':32}", end=eol)
        line_width += 32
        return line_width

    def print_txt_list(self, heading: str | None = None) -> None:
        """
        Print list of devices.

        :param heading: print at the top
        """
        self.logger.debug("List %d devices in text format...", len(self.devices))
        if heading is not None:
            print(f"{heading}")
        elif self.ns_name is not None:
            print(f"Namespace {self.ns_name}")
        else:
            print(f"Host {os.getenv('TANGO_HOST')}")
        self.print_txt_heading()
        for device in self.devices:
            if self.devices[device] is not None:
                self.devices[device].print_list()
            else:
                print(f"{device} (N/A)")
        print()

    def print_html_heading(self) -> None:
        """Print heading for list of devices."""
        print("<tr><th>DEVICE NAME</th> ", end="")
        for attribute in self.list_items["attributes"]:
            field_name = attribute.upper()
            print(f"<th>{field_name}</th>", end="")
        for command in self.list_items["commands"]:
            field_name = command.upper()
            print(f"<th>{field_name}</th>", end="")
        for tproperty in self.list_items["properties"]:
            field_name = tproperty.upper()
            print(f"<th>{field_name}</th>", end="")
        print("<th>CLASS</th></tr>")

    def print_html(self, disp_action: int) -> None:
        """
        Print in HTML format.

        :param disp_action: display control flag
        """
        self.logger.debug("Show %d basic devices in HTML format...", len(self.devices))
        print("<table>")
        self.print_html_heading()
        for device in self.devices:
            self.devices[device].print_html()
        print("</table>")

    def get_html_header(self) -> str:
        """
        Use first key in dictionary as header.

        :return: HTML header
        """
        res = list(self.devices.keys())[0]
        dev = self.devices[res]
        return dev.get_html_header()

    def get_html(self, disp_action: int = 0) -> str:
        """
        Print in HTML format.

        :param disp_action: display control flag
        :return: HTML string
        """
        rbuf: str = ""
        self.logger.debug("List %d basic devices in HTML format...", len(self.devices))
        rbuf += "<table>\n"
        res = list(self.devices.keys())[0]
        dev = self.devices[res]
        rbuf += dev.get_html_header()
        self.print_html_heading()
        for device in self.devices:
            rbuf += self.devices[device].get_html()
        rbuf += "</table>\n"
        return rbuf

    def print_txt_classes(self) -> None:
        """Print list of classes."""
        dev_class: str

        self.logger.debug("Read classes in %d devices...", len(self.devices))
        self.print_txt_heading()
        dev_classes: list = []
        for device in self.devices:
            if self.devices[device] is not None:
                dev_class = self.devices[device].dev_class
                if dev_class != "---" and dev_class not in dev_classes:
                    dev_classes.append(dev_class)
                    self.devices[device].print_list()

    def get_classes(self, reverse: bool) -> OrderedDict[Any, Any]:
        """
        Get list of classes.

        :param reverse: sort in reverse order
        :return: dictionary of classes
        """
        dev_classes: dict

        self.logger.debug("Get classes in %d devices", len(self.devices))
        dev_classes = {}
        for device in self.devices:
            if self.devices[device] is not None:
                dev_class: str = self.devices[device].dev_class
                if dev_class == "---":
                    continue
                if dev_class not in dev_classes:
                    dev_classes[dev_class] = []
                dev_classes[dev_class].append(self.devices[device].dev_name)
        return OrderedDict(sorted(dev_classes.items(), reverse=reverse))

    def print_json(self, disp_action: int) -> None:
        """
        Print in JSON format.

        :param disp_action: not used
        """
        devsdict: dict

        self.logger.debug("Print JSON")
        devsdict = self.make_json()
        print(f'\n"{self.tango_host}":')
        print(f"{json.dumps(devsdict, indent=4, cls=NumpyEncoder)}")

    def print_yaml(self, disp_action: int) -> None:
        """
        Print in YAML format.

        :param disp_action: not used
        """
        devsdict: dict
        ydevsdict: dict = {}

        self.logger.debug("Print YAML")
        devsdict = self.make_json()
        ydevsdict[self.tango_host] = devsdict
        print(yaml.dump(ydevsdict))


class TangoctlDevices(TangoctlDevicesBasic):
    """Compile a dictionary of available Tango devices."""

    def __init__(  # noqa: C901s
        self,
        logger: logging.Logger,
        show_attrib: bool,
        show_cmd: bool,
        show_prop: bool,
        show_status: dict,
        cfg_data: dict,
        tgo_name: str | None,
        uniq_cls: bool,
        reverse: bool,
        evrythng: bool,
        tgo_attrib: str | None,
        tgo_cmd: str | None,
        tgo_prop: str | None,
        quiet_mode: bool,
        output_file: str | None,
        fmt: str = "json",
        k8s_ns: str = "",
        nodb: bool = False,

    ):
        """
        Get a dict of devices.

        :param logger: logging handle
        :param show_attrib: flag to read attributes
        :param show_cmd: flag to read commands
        :param show_prop: flag to read properties
        :param uniq_cls: only read one device per class
        :param cfg_data: configuration data in JSON format
        :param quiet_mode: flag for displaying progress bars
        :param reverse: sort in reverse order
        :param evrythng: read devices regardless of ignore list
        :param tgo_name: filter device name
        :param tgo_attrib: filter attribute name
        :param tgo_cmd: filter command name
        :param tgo_prop: filter property name
        :param output_file: output file name
        :param fmt: output format
        :param nodb: flag to run without database
        :raises Exception: when database connect fails
        """
        self.devices: dict = {}
        self.attribs_found: list = []
        self.tgo_space: str = ""
        self.quiet_mode: bool = True
        self.dev_classes: list = []
        self.delimiter: str
        self.run_commands: list
        self.run_commands_name: list
        self.prog_bar: bool
        new_dev: TangoctlDevice
        self.cfg_data: dict
        self.list_items: dict
        self.k8s_ns = k8s_ns

        self.logger = logger
        self.cfg_data = cfg_data
        self.output_file = output_file
        self.logger.debug(
            "Read devices %s : attribute %s command %s property %s",
            tgo_name,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
        )
        # Get Tango database host
        self.tango_host = os.getenv("TANGO_HOST")

        self.delimiter = self.cfg_data["delimiter"]
        self.run_commands = self.cfg_data["run_commands"]
        self.logger.debug("Run commands %s", self.run_commands)
        self.run_commands_name = self.cfg_data["run_commands_name"]
        self.list_items = self.cfg_data["list_items"]
        self.logger.debug("Run commands with name %s", self.run_commands_name)
        self.prog_bar = not quiet_mode

        if nodb:
            trl = f"tango://{self.tango_host}/{tgo_name}#dbase=no"
            new_dev = TangoctlDevice(
                logger,
                show_attrib,
                show_cmd,
                show_prop,
                show_status,
                trl,
                not self.prog_bar,
                reverse,
                self.list_items,
                tgo_attrib,
                tgo_cmd,
                tgo_prop,
            )
            self.devices[tgo_name] = new_dev
        else:
            # Connect to database
            try:
                database = tango.Database()
            except Exception as oerr:
                self.logger.error(
                    "Could not connect to Tango database %s : %s", self.tango_host, oerr
                )
                raise oerr

            # Read devices
            device_list: list = sorted(
                database.get_device_exported("*").value_string, reverse=reverse
            )
            self.logger.debug("Read %d devices available...", len(device_list))

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
                        logger,
                        show_attrib,
                        show_cmd,
                        show_prop,
                        show_status,
                        device,
                        not self.prog_bar,
                        reverse,
                        self.list_items,
                        tgo_attrib,
                        tgo_cmd,
                        tgo_prop,
                    )
                except tango.ConnectionFailed as terr:
                    err_msg: str = terr.args[0].desc.strip()
                    logger.info("Could not read device %s : %s", device, err_msg)
                    continue
                if tgo_attrib:
                    attribs_found: list = new_dev.check_for_attribute(tgo_attrib)
                    if attribs_found:
                        self.logger.debug("Device %s matched attributes %s", device, attribs_found)
                        self.devices[device] = new_dev
                    else:
                        logger.debug("Skip device %s (attribute %s not found)", device, tgo_attrib)
                elif tgo_cmd:
                    cmds_found: list = new_dev.check_for_command(tgo_cmd)
                    if cmds_found:
                        self.logger.debug("Device %s matched commands %s", device, cmds_found)
                        self.devices[device] = new_dev
                    else:
                        logger.debug("Skip device %s (command %s not found)", device, tgo_cmd)
                elif tgo_prop:
                    props_found: list = new_dev.check_for_property(tgo_prop)
                    if props_found:
                        self.logger.debug("Device %s matched properties %s", device, props_found)
                        self.devices[device] = new_dev
                    else:
                        logger.debug("Skip device %s (command %s not found)", device, tgo_cmd)
                elif uniq_cls:
                    dev_class: str = new_dev.dev_class
                    if dev_class == "---":
                        self.logger.debug(
                            f"Skip basic device {device} with unknown class {dev_class}"
                        )
                    elif dev_class not in self.dev_classes:
                        self.dev_classes.append(dev_class)
                        self.devices[device] = new_dev
                    else:
                        self.logger.debug(f"Skip device {device} with known class {dev_class}")
                else:
                    self.logger.debug("Add device %s", device)
                    self.devices[device] = new_dev
        logger.debug("Read %d devices", len(self.devices))

    def __del__(self) -> None:
        """Desctructor."""
        tango_host = os.getenv("TANGO_HOST")
        self.logger.debug("Shut down TangoctlDevices for host %s", tango_host)

    # def read_attribute_names(self) -> dict:
    #     """Read device data."""
    #     self.logger.debug("Read attribute names of %d devices...", len(self.devices))
    #     the_attribs: dict = {}
    #     # Run 'for device in self.devices:'
    #     for device in progress_bar(
    #         self.devices,
    #         self.prog_bar,
    #         prefix=f"Read {len(self.devices)} attributes :",
    #         suffix="complete",
    #         decimals=0,
    #         length=100,
    #     ):
    #         dev_attribs = self.devices[device].attribs
    #         for attr in dev_attribs:
    #             if attr not in the_attribs:
    #                 the_attribs[attr] = []
    #             the_attribs[attr].append(device)
    #     self.logger.debug("Read attribute names of %d devices: ", len(the_attribs), the_attribs)

    def read_attribute_values(self) -> None:
        """Read device data."""
        self.logger.debug("Read attribute values of %d devices...", len(self.devices))
        # Run 'for device in self.devices:'
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} attributes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                self.devices[device].read_attribute_value()

    def read_command_values(self) -> None:
        """Read device data."""
        self.logger.debug("Read commands of %d devices...", len(self.devices))
        # Run "for device in self.devices:" in progress bar
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} device commands :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                self.devices[device].read_command_value(self.run_commands, self.run_commands_name)

    def read_property_values(self) -> None:
        """Read device data."""
        self.logger.debug("Read properties of %d devices...", len(self.devices))
        # Run "for device in self.devices:" in progress bar
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} property values :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                self.devices[device].read_property_value()

    def read_device_values(
        self, show_attrib: bool, show_cmd: bool, show_prop: bool, show_status: dict
    ) -> None:
        """
        Read device values.

        :param show_attrib: flag to read attributes
        :param show_cmd: flag to read commands
        :param show_prop: flag to read properties
        :param show_status: flag to read status
        """
        if show_status and not show_attrib:
            self.logger.debug("Read status of devices")
        if show_attrib:
            self.logger.debug("Read attribute values from devices")
            self.read_attribute_values()
        if show_cmd:
            self.logger.debug("Read command values from devices")
            self.read_command_values()
        if show_prop:
            self.logger.debug("Read property values from devices")
            self.read_property_values()
        self.logger.debug("Read %d devices", len(self.devices))

    def read_configs_all(self) -> None:
        """Read additional data."""
        self.logger.debug("Read %d basic device configs...", len(self.devices))
        # Run "device in self.devices:"
        for device in progress_bar(
            self.devices,
            not self.quiet_mode,
            prefix=f"Read {len(self.devices)} device configs :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                self.devices[device].read_config_all()

    def make_json(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devsdict: dict = {}
        self.logger.debug("List %d devices in JSON format...", len(self.devices))
        # Run "for device in self.devices:" in progress bar
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} JSON records :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                devsdict[device] = self.devices[device].make_json(self.delimiter)
        self.logger.debug("Read %d devices in JSON format: %s", len(self.devices), devsdict)
        return devsdict

    def print_txt_list_attrib(self) -> None:
        """Print list of devices with attribute name."""
        self.logger.debug("Listing %d devices...", len(self.devices))
        for device in self.devices:
            print(f"{device}")
        return

    def print_txt_list(self, heading: str | None = None) -> None:
        """
        Print list of devices.

        :param heading: print at the top
        """
        self.logger.debug("List %d devices...", len(self.devices))
        for device in self.devices:
            print(f"{device}")

    def print_txt(self, disp_action: int, heading: str | None = None) -> None:
        """
        Print in text format.

        :param disp_action: display control flag
        :param heading: to be printed on the top
        """
        devsdict: dict
        json_reader: TangoJsonReader

        if disp_action == TANGOCTL_LIST:
            self.logger.debug("Print devices as text")
            self.print_txt_list(heading)
            print()
        elif disp_action == TANGOCTL_SHORT:
            self.logger.debug("Print devices as text")
            devsdict = self.make_json()
            json_reader = TangoJsonReader(
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
            )
            json_reader.print_txt_quick()
        else:
            self.logger.debug("Print devices as default (display action %d)", disp_action)
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
        devsdict: dict
        ydevsdict: dict = {}

        self.logger.debug("Print devices as JSON")
        devsdict = self.make_json()
        devsdict["tango_host"] = self.tango_host
        if self.k8s_ns:
            ykey = self.k8s_ns
        else:
            ykey = self.tango_host
        ydevsdict[ykey] = devsdict
        if self.output_file is not None:
            self.logger.debug("Write output file %s", self.output_file)
            with open(self.output_file, "a") as outf:
                outf.write(json.dumps(ydevsdict, indent=4, cls=NumpyEncoder))
        else:
            print(json.dumps(ydevsdict, indent=4, cls=NumpyEncoder))

    def print_markdown(self, disp_action: int) -> None:
        """
        Print in JSON format.

        :param disp_action: display control flag
        """
        devsdict: dict

        self.logger.debug("Print devices as markdown")
        devsdict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
        )
        json_reader.print_markdown_all()

    def print_html(self, disp_action: int) -> None:
        """
        Print in HTML format.

        :param disp_action: display control flag
        """
        devsdict: dict

        self.logger.debug("Print devices as HTML")
        devsdict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
        )
        if disp_action == TANGOCTL_LIST:
            json_reader.print_html_all(True)
        else:
            json_reader.print_html_quick(True)

    def print_yaml(self, disp_action: int) -> None:
        """
        Print in YAML format.

        :param disp_action: display control flag
        """
        devsdict: dict
        ydevsdict: dict = {}

        self.logger.debug("Print devices as YAML")
        devsdict = self.make_json()
        devsdict["tango_host"] = self.tango_host
        if self.k8s_ns:
            ykey = self.k8s_ns
        else:
            ykey = self.tango_host
        ydevsdict[ykey] = devsdict
        if self.output_file is not None:
            self.logger.debug("Write output file %s", self.output_file)
            with open(self.output_file, "a") as outf:
                outf.write(yaml.dump(ydevsdict))
        else:
            print(yaml.dump(ydevsdict))

    def print_txt_list_attributes(self) -> None:
        """Print list of devices."""
        device: str
        lwid: int

        self.logger.debug("List %d device attributes...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'ATTRIBUTE':32}")
        # lwid += 33
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].attributes:
                    self.devices[device].read_config()
                    self.devices[device].print_list_attribute(lwid)

    def print_txt_list_commands(self) -> None:
        """Print list of devices."""
        device: str
        lwid: int

        self.logger.debug("List %d device commands...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'COMMAND':32}")
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].commands:
                    self.devices[device].read_config()
                    self.devices[device].print_list_command(lwid)

    def print_txt_list_properties(self) -> None:
        """Print list of properties."""
        device: str

        self.logger.debug("List %d device properties...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'PROPERTY':32}")
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].properties:
                    self.devices[device].read_config()
                    self.devices[device].print_list_property(lwid)
