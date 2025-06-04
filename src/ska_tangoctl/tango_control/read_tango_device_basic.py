"""Basic Tango device information."""

import logging
import os
from typing import Any

import tango

from ska_tangoctl.tango_control.disp_action import BOLD, UNFMT


class TangoctlDeviceBasic:
    """Compile a basic dictionary for a Tango device."""

    logger: logging.Logger

    def __init__(  # noqa: C901
        self,
        logger: logging.Logger,
        show_attrib: bool,
        show_cmd: bool,
        show_prop: bool,
        show_status: dict,
        device: str,
        reverse: bool,
        xact_match: bool = False,
        list_items: dict = {},
        block_items: dict = {},
        timeout_millis: float = 500,
    ):
        """
        Iniltialise the thing.

        :param logger: logging handle
        :param show_attrib: flag to read attributes
        :param show_cmd: flag to read commands
        :param show_prop: flag to read properties
        :param show_status: flag to read status
        :param device: device name
        :param reverse: sort in reverse order
        :param xact_match: exact matches only
        :param list_items: dictionary with values to process
        :param block_items: dictionary with values not to process
        :param timeout_millis: timeout in milliseconds
        :raises Exception: error condition
        """
        self.logger = logger
        self.show_attrib = show_attrib
        self.show_cmd = show_cmd
        self.show_prop = show_prop
        self.dev: tango.DeviceProxy
        self.info: tango.DeviceInfo
        self.dev_name: str
        self.version: str = "?"
        self.status: str = "?"
        self.adminMode: int | None = None
        self.adminModeStr: str = "---"
        self.dev_class: str
        self.dev_state: Any = None
        self.xact_match = xact_match
        self.list_items: dict
        self.dev_errors: list = []
        self.dev_values: dict = {}
        err_msg: str

        # Set up Tango device
        tango_host = os.getenv("TANGO_HOST")
        self.list_items = list_items
        self.logger.debug(
            "Open basic device %s (%s) attrib %s cmd %s prop %s status %s (list items %s)",
            device,
            tango_host,
            self.show_attrib,
            self.show_cmd,
            self.show_prop,
            show_status,
            list_items,
        )
        try:
            self.dev = tango.DeviceProxy(device)
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.warning("Tango error: %s", err_msg)
            self.dev = None
        except RuntimeError as rerr:
            self.logger.warning("Error: %s", rerr)
            self.dev = None
        if self.dev is None:
            device = device.lower()
            self.logger.debug("Retry basic device %s", device)
            try:
                self.dev = tango.DeviceProxy(device)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.dev_name = f"{device} (N/A)"
                self.logger.info(
                    "Could not open basic device %s (%s) : %s", device, tango_host, err_msg
                )
                raise Exception(f"Could not open basic device {device} ({tango_host}) : {err_msg}")
        self.dev.set_timeout_millis(timeout_millis)
        # Read device name
        try:
            self.dev_name = self.dev.name()
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.warning("Could not read device %s name : %s", device, err_msg)
            self.dev_errors.append(f"Could not read device {device} name : {err_msg}")
            self.dev_name = f"{device} (N/A)"
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.warning("Could not read name for device %s", device)
            self.dev_name = f"{device} (N/A)"
            self.dev_errors.append(f"Could not read info : {err_msg}")
        # Read information on the device and device class name
        try:
            self.info = self.dev.info()
            self.dev_class = self.info.dev_class
        except Exception:
            self.dev_class = "N/A"
        # Read green mode and access control type for this DeviceProxy
        self.green_mode: Any = str(self.dev.get_green_mode())
        self.dev_access: str = str(self.dev.get_access_control())
        # Read status
        if show_status:
            self.attribs = show_status["attributes"]
            self.cmds = show_status["commands"]
            self.props = show_status["properties"]
            self.logger.debug(
                "Get status for %s: attributes %s commands %s properties %s",
                self.dev_name,
                self.attribs,
                self.cmds,
                self.props,
            )
        else:
            self.attribs = []
            self.cmds = []
            self.props = []
        # Read the names of all attributes implemented for this device
        if self.show_attrib:
            self.logger.debug("Get attribute list for %s", self.dev_name)
            try:
                self.attribs = sorted(self.dev.get_attribute_list())
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.warning("Could not read attributes for %s", device)
                self.dev_errors.append(f"Could not read attributes : {err_msg}")
                self.attribs = []
            self.logger.debug("Got %d attributes for %s", len(self.attribs), self.dev_name)
        # Read the names of all commands implemented for this device
        if self.show_cmd:
            try:
                self.cmds = sorted(self.dev.get_command_list(), reverse=reverse)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.warning("Could not read commands for %s", device)
                self.dev_errors.append(f"Could not read commands : {err_msg}")
                self.cmds = []
            self.logger.debug("Got %d commands for %s", len(self.cmds), self.dev_name)
        # Get the list of property names for the device
        if self.show_prop:
            try:
                self.props = sorted(self.dev.get_property_list("*"), reverse=reverse)
            except tango.NonDbDevice:
                self.logger.info("Not reading properties in nodb mode")
                self.props = []
            self.logger.debug("Got %d properties for %s", len(self.props), self.dev_name)

    def __repr__(self) -> str:
        """
        Do the string thing.

        :return: string representation
        """
        return f"Attributes {','.join(self.attribs)}"

    def __del__(self) -> None:
        """Destructor."""
        self.logger.debug("Shut down TangoctlDeviceBasic for %s", self.dev_name)

    def read_config(self) -> None:  # noqa: C901
        """
        Read additional data as configured in JSON file.

        State, adminMode and versionId are specific to devices
        """
        attribute: Any
        command: Any
        dev_val: Any
        err_msg: str

        self.logger.info("Read basic config : %s", self.list_items)
        self.logger.info("Attributes : %s", self.attribs)
        self.logger.info("Commands : %s", self.cmds)
        self.logger.info("Properties : %s", self.props)
        # Read configured attribute values
        if "attributes" in self.list_items:
            self.logger.info("Read attributes : %s", self.list_items["attributes"])
            for attribute in self.list_items["attributes"]:
                if type(attribute) is list:
                    attribute = attribute[0]
                if attribute not in self.attribs:
                    self.logger.info("Attribute %s not in %s", attribute, self.attribs)
                    try:
                        self.dev_values[attribute] = "-"
                    except TypeError:
                        self.logger.error("Could not update attribute %s", attribute)
                    continue
                # Read a single attribute
                try:
                    dev_val = self.dev.read_attribute(attribute).value
                    self.logger.debug(
                        "Read device %s attribute %s value : %s", self.dev_name, attribute, dev_val
                    )
                except tango.DevFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.info(
                        "Dev failed for device %s attribute %s : %s",
                        self.dev_name,
                        attribute,
                        err_msg,
                    )
                    dev_val = "N/A"
                except tango.CommunicationFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning(
                        "Communication failed for device %s attribute %s : %s",
                        self.dev_name,
                        attribute,
                        err_msg,
                    )
                    dev_val = "N/A"
                except AttributeError as oerr:
                    self.logger.warning(
                        "Attribute error for device %s attribute %s : %s",
                        self.dev_name,
                        attribute,
                        str(oerr),
                    )
                    dev_val = "N/A"
                except TypeError as yerr:
                    self.logger.warning(
                        "Type Error for device %s attribute %s : %s",
                        self.dev_name,
                        attribute,
                        str(yerr),
                    )
                    dev_val = "N/A"
                self.logger.debug("Read attribute %s value: %s", attribute, dev_val)
                self.dev_values[attribute] = dev_val
        # Read configured command values
        if "commands" in self.list_items:
            self.logger.info("Read commands : %s", self.list_items["commands"])
            for command in self.list_items["commands"]:
                if type(command) is list:
                    command = command[0]
                if command not in self.cmds:
                    self.logger.info("Command %s not in %s", command, self.cmds)
                    self.dev_values[command] = "-"
                    continue
                # Execute a command on a device
                try:
                    dev_val = str(self.dev.command_inout(command))
                    self.logger.debug(
                        "Read device %s command %s value : %s", self.dev_name, command, dev_val
                    )
                except tango.CommunicationFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning(
                        "Could not read device %s command %s : %s", self.dev_name, command, err_msg
                    )
                    dev_val = "N/A"
                except AttributeError as oerr:
                    self.logger.warning(
                        "Could not device %s command %s : %s", self.dev_name, command, str(oerr)
                    )
                    dev_val = "N/A"
                except TypeError as yerr:
                    self.logger.warning(
                        "Type Error for device %s command %s : %s",
                        self.dev_name,
                        command,
                        str(yerr),
                    )
                    dev_val = "N/A"
                self.logger.debug("Read command %s: %s", command, dev_val)
                self.dev_values[command] = dev_val
        # Read configured command values
        if "properties" in self.list_items:
            self.logger.info("Read properties : %s", self.list_items["properties"])
            for tproperty in self.list_items["properties"]:
                if tproperty not in self.props:
                    self.logger.info("Property %s not in %s", tproperty, self.props)
                    self.dev_values[tproperty] = "-"
                    continue
                # Get a list of properties for a device
                try:
                    dev_val = self.dev.get_property(tproperty)[tproperty]
                    # pylint: disable-next=c-extension-no-member
                    if type(dev_val) is tango._tango.StdStringVector:
                        dev_val = ",".join(dev_val)
                except tango.NonDbDevice:
                    self.logger.info("Not reading properties in nodb mode")
                    dev_val = "-"
                self.logger.debug("Read property %s: %s", property, dev_val)
                self.dev_values[tproperty] = dev_val

    def print_list(self, eol: str = "\n") -> None:
        """
        Print data.

        :param eol: printed at the end
        """
        self.read_config()
        self.logger.debug("Print list: %s", self.list_items)
        self.logger.debug("Use values: %s", self.dev_values)
        print(f"{BOLD}{self.dev_name:64}{UNFMT} ", end="")
        for attribute in self.list_items["attributes"]:
            field_value = self.dev_values[attribute]
            field_width = self.list_items["attributes"][attribute]
            self.logger.debug(f"Print attribute {attribute} : {field_value} {field_width=}")
            print(f"{field_value:{field_width}} ", end="")
        for command in self.list_items["commands"]:
            field_value = self.dev_values[command]
            field_width = self.list_items["commands"][command]
            self.logger.debug(f"Print command {command} : {field_value} ({field_width=})")
            print(f"{field_value:{field_width}} ", end="")
        for tproperty in self.list_items["properties"]:
            field_value = self.dev_values[tproperty]
            field_width = self.list_items["properties"][tproperty]
            self.logger.debug(f"Print property {tproperty} : {field_value} ({field_width=})")
            print(f"{field_value:{field_width}} ", end="")
        print(f"{self.dev_class:32}", end=eol)

    def print_html(self) -> None:
        """Print data."""
        self.read_config()
        print(f'<tr><td class="tangoctl">{self.dev_name}</td>', end="")
        for attribute in self.list_items["attributes"]:
            field_value = self.dev_values[attribute]
            self.logger.debug(f"Print attribute {attribute} : {field_value}")
            print(f'<td class="tangoctl">{field_value}</td>', end="")
        for command in self.list_items["commands"]:
            field_value = self.dev_values[command]
            self.logger.debug(f"Print command {command} : {field_value})")
            print(f'<td class="tangoctl">{field_value}</td>', end="")
        for tproperty in self.list_items["properties"]:
            field_value = self.dev_values[tproperty]
            self.logger.debug(f"Print property {tproperty} : {field_value})")
            print(f'<td class="tangoctl">{field_value}</td>', end="")
        print(f'<td class="tangoctl">{self.dev_class}</td></tr>\n')

    def get_html_header(self) -> str:
        """
        Print headings.

        :return: HTML string
        """
        r_buf: str = ""
        self.read_config()
        r_buf += "<tr><th>Device name</th>"
        for attribute in self.list_items["attributes"]:
            r_buf += f"<th>{attribute}</th>"
        for command in self.list_items["commands"]:
            r_buf += f"<th>{command}</th>"
        for t_property in self.list_items["properties"]:
            r_buf += f"<th>{t_property}</th>"
        r_buf += "<th>Class</th></tr>\n"
        return r_buf

    def get_html(self) -> str:
        """
        Print data in HTML format.

        :return: HTML string
        """
        r_buf: str = ""
        self.read_config()
        self.logger.warning(self.list_items)
        r_buf += '<tr><td class="tangoctl">{self.dev_name}</td>'
        for attribute in self.list_items["attributes"]:
            field_value = self.dev_values[attribute]
            self.logger.debug(f"Print attribute {attribute} : {field_value}")
            r_buf += f'<td class="tangoctl">{field_value}</td>'
        for command in self.list_items["commands"]:
            field_value = self.dev_values[command]
            self.logger.debug(f"Print command {command} : {field_value})")
            r_buf += f'<td class="tangoctl">{field_value}</td>'
        for t_property in self.list_items["properties"]:
            field_value = self.dev_values[t_property]
            self.logger.debug(f"Print property {t_property} : {field_value})")
            r_buf += f'<td class="tangoctl">{field_value}</td>'
        r_buf += f'<td class="tangoctl">{self.dev_class}</td></tr>\n'
        return r_buf

    def make_json(self) -> dict:
        """
        Build dictionary.

        :return: dictionary with device data
        """
        self.logger.debug("Build basic JSON")
        rval: dict = self.dev_values
        rval["dev_class"] = self.dev_class
        rval["attributes"] = self.attribs
        rval["commands"] = self.cmds
        rval["properties"] = self.props
        return rval
