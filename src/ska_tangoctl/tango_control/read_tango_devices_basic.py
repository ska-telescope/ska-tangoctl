"""Read available Tango devices."""

import json
import logging
import os
import re
from typing import Any, OrderedDict

import numpy as np
import tango
import yaml

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.progress_bar import progress_bar
from ska_tangoctl.tango_control.read_tango_device_basic import TangoctlDeviceBasic


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
        disp_action: DispAction,
        quiet_mode: bool,
        xact_match: bool = False,
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
        :param disp_action: output format
        :param tgo_name: device name
        :param xact_match: exact matches only
        :param ns_name: K8S namespace
        :raises Exception: database connect failed
        """
        self.devices: dict = {}
        self.quiet_mode: bool = True
        self.dev_classes: list = []
        self.cfg_data: dict
        self.tango_host: str | None
        database: tango.Database
        device_list: list
        new_dev: TangoctlDeviceBasic
        dev_class: str
        self.list_items: dict
        self.block_items: dict
        self.ns_name: str | None = ns_name
        device: str

        self.logger = logger
        self.show_attrib: bool = show_attrib
        self.show_cmd: bool = show_cmd
        self.show_prop: bool = show_prop
        self.show_status: dict = show_status
        self.reverse: bool = reverse
        self.xact_match: bool = xact_match
        # Get Tango database host
        self.tango_host = os.getenv("TANGO_HOST")
        # Get high level Tango object which contains the link to the static database
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

        self.cfg_data = cfg_data
        self.list_items = self.cfg_data["list_items"]
        self.block_items = self.cfg_data["block_items"]
        self.quiet_mode = quiet_mode
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        self.logger.info("Reading %d basic devices (unique %s) -->", len(device_list), uniq_cls)
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
                    xact_match,
                    self.list_items,
                    self.block_items,
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
        self.logger.debug("Reading %d basic device configs -->", len(self.devices))
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
        the_attribs: dict = {}
        self.logger.debug("Reading attribute names of %d devices -->", len(self.devices))
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
        the_commands: dict = {}
        self.logger.debug("Reading command names of %d devices -->", len(self.devices))
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
        the_properties: dict = {}
        self.logger.debug("Reading property names of %d devices -->", len(self.devices))
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
        devsdict: dict

        devsdict = {}
        self.logger.debug("List %d basic devices in JSON format...", len(self.devices))
        for device in self.devices:
            if self.devices[device] is not None:
                devsdict[device] = self.devices[device].make_json()
        return devsdict

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

    def print_html(self, disp_action: DispAction) -> None:
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

    def get_html(self) -> str:
        """
        Print in HTML format.

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

    def print_json(self, disp_action: DispAction) -> None:
        """
        Print in JSON format.

        :param disp_action: not used
        """
        devsdict: dict

        devsdict = self.make_json()
        print(f'\n"{self.tango_host}":')
        print(f"{json.dumps(devsdict, indent=4, cls=NumpyEncoder)}")

    def print_yaml(self, disp_action: DispAction) -> None:
        """
        Print in YAML format.

        :param disp_action: not used
        """
        devsdict: dict
        ydevsdict: dict = {}

        devsdict = self.make_json()
        ydevsdict[self.tango_host] = devsdict
        # Serialize a Python object into a YAML stream
        print(yaml.dump(ydevsdict))
