"""Read and display Tango stuff."""

import json
import logging
import sys
from typing import Any

import numpy
import tango

from ska_tangoctl.tango_control.progress_bar import progress_bar
from ska_tangoctl.tango_control.read_tango_device_basic import TangoctlDeviceBasic
from ska_tangoctl.tango_control.tango_json import TangoJsonReader
from ska_tangoctl.tla_jargon.tla_jargon import find_jargon


class TangoctlDevice(TangoctlDeviceBasic):
    """Compile a dictionary for a Tango device."""

    def __init__(  # noqa: C901
        self,
        logger: logging.Logger,
        show_attrib: bool,
        show_cmd: bool,
        show_prop: bool,
        show_status: dict,
        device: str,
        quiet_mode: bool,
        reverse: bool,
        list_items: dict,
        block_items: dict,
        tgo_attrib: str | None,
        tgo_cmd: str | None,
        tgo_prop: str | None,
        xact_match: bool = False,
        show_jargon: bool = False,
    ):
        """
        Iniltialise the thing.

        :param logger: logging handle
        :param show_attrib: flag to read attributes
        :param show_cmd: flag to read commands
        :param show_prop: flag to read properties
        :param show_status: flag to read status
        :param device: device name
        :param quiet_mode: flag for displaying progress bars
        :param reverse: sort in reverse order
        :param list_items: attributes, commands or properties in list output
        :param block_items: attributes, commands or properties not to be shown in list output
        :param tgo_attrib: attribute filter
        :param tgo_cmd: command filter
        :param tgo_prop: property filter
        :param xact_match: exact matches only
        :param show_jargon: flag to show jargon and acronyms
        """
        self.commands: dict = {}
        self.attributes: dict = {}
        self.properties: dict = {}
        self.attribs_found: list = []
        self.props_found: list = []
        self.cmds_found: list = []
        self.info: tango.DeviceInfo
        self.quiet_mode: bool = True
        self.outf = sys.stdout
        self.attribs: list
        self.cmds: list
        self.props: list
        self.list_items: dict
        self.show_jargon = show_jargon

        # Run base class constructor
        super().__init__(
            logger, show_attrib, show_cmd, show_prop, show_status, device, reverse, xact_match
        )
        self.logger.debug(
            "Open device %s (attributes %s, commands %s, properties %s)",
            device,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
        )
        self.quiet_mode = quiet_mode
        self.list_items = list_items
        self.block_items = block_items
        # Set quiet mode, i.e. do not display progress bars
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        if tgo_attrib:
            tgo_attrib = tgo_attrib.lower()
        # Check commands
        for cmd in self.cmds:
            if self.xact_match and tgo_cmd:
                if tgo_cmd == cmd.lower():
                    self.logger.debug("Add matched command %s", cmd)
                    self.commands[cmd] = {}
            elif tgo_cmd:
                if tgo_cmd in cmd.lower():
                    self.logger.debug("Add command %s", cmd)
                    self.commands[cmd] = {}
            elif tgo_attrib or tgo_prop:
                pass
            else:
                self.logger.debug("Add command %s", cmd)
                self.commands[cmd] = {}
        # Check attributes
        for attrib in self.attribs:
            if self.xact_match and tgo_attrib:
                if tgo_attrib == attrib.lower():
                    self.logger.debug("Add matched attribute %s", attrib)
                    self.attributes[attrib] = {}
            elif tgo_attrib:
                if tgo_attrib in attrib.lower():
                    self.logger.debug("Add attribute %s", attrib)
                    self.attributes[attrib] = {}
            elif tgo_cmd or tgo_prop:
                pass
            else:
                self.logger.debug("Add attribute %s", attrib)
                self.attributes[attrib] = {}
        # Check properties
        for prop in self.props:
            if self.xact_match and tgo_prop:
                if tgo_prop == prop.lower():
                    self.logger.debug("Add matched property %s", prop)
                    self.properties[prop] = {}
            elif tgo_prop:
                if tgo_prop in prop.lower():
                    self.logger.debug("Add property %s", prop)
                    self.properties[prop] = {}
            elif tgo_attrib or tgo_cmd:
                pass
            else:
                self.logger.debug("Add property %s", prop)
                self.properties[prop] = {}
        # Check information
        try:
            self.info = self.dev.info()
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.warning("Could not read info from %s : %s", device, err_msg)
            self.dev_errors.append(f"Could not read info: {err_msg}")
            self.info = None
        # Check version
        try:
            self.version = self.dev.versionId
        except AttributeError as oerr:
            self.logger.debug("Could not read device %s version ID : %s", self.dev_name, str(oerr))
            self.version = "N/A"
        except tango.CommunicationFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.debug("Could not read device %s version ID : %s", self.dev_name, err_msg)
            self.version = "N/A"
        self.logger.info(
            "Read device %s with %d attributes, %d commands and %d properties, class %s",
            device,
            len(self.attributes),
            len(self.commands),
            len(self.properties),
            self.dev_class,
        )
        # Check name for acronyms
        if self.show_jargon:
            self.jargon = find_jargon(self.dev_name)
        else:
            self.jargon = ""

    def __del__(self) -> None:
        """Destructor."""
        self.logger.debug("Shut down TangoctlDevice for %s", self.dev_name)

    def read_config_all(self) -> None:
        """Read attribute and command configuration."""
        attrib: str
        cmd: str
        err_msg: str

        self.logger.debug("Read config from device %s", self.dev_name)
        # Read attribute configuration
        for attrib in self.attributes:
            self.logger.debug("Read attribute config from %s", attrib)
            # Read the attribute configuration for a single attribute
            try:
                self.attributes[attrib]["config"] = self.dev.get_attribute_config(attrib)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.warning(
                    "Could not not read attribute %s config for %s : %s",
                    attrib,
                    self.dev_name,
                    err_msg,
                )
                self.attributes[attrib]["error"] = err_msg
                self.attributes[attrib]["config"] = None
        self.logger.debug("Device %s attributes: %s", self.dev_name, self.attributes)
        # Read command configuration
        for cmd in self.commands:
            self.logger.debug("Read command config from %s", cmd)
            # Read the configuration for a single command
            try:
                self.commands[cmd]["config"] = self.dev.get_command_config(cmd)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.warning(
                    "Could not not read config for command %s on %s : %s",
                    cmd,
                    self.dev_name,
                    err_msg,
                )
                self.commands[cmd]["error"] = err_msg
                self.commands[cmd]["config"] = None
        self.logger.debug("Device %s commands: %s", self.dev_name, self.commands)

    def check_for_attribute(self, tgo_attrib: str | None) -> list:
        """
        Filter by attribute name.

        :param tgo_attrib: attribute name
        :return: list of device names matched
        """
        chk_attrib: str

        self.logger.debug(
            "Check %d attributes for %s : %s", len(self.attributes), tgo_attrib, self.attributes
        )
        self.attribs_found = []
        if not tgo_attrib:
            return self.attribs_found
        chk_attrib = tgo_attrib.lower()
        for attrib in self.attributes:
            if chk_attrib in attrib.lower():
                self.attribs_found.append(attrib)
        return self.attribs_found

    def check_for_command(self, tgo_cmd: str | None) -> list:
        """
        Filter by command name.

        :param tgo_cmd: command name
        :return: list of device names matched
        """
        self.logger.debug(
            "Check %d commands for %s : %s", len(self.commands), tgo_cmd, self.commands
        )
        self.cmds_found = []
        if not tgo_cmd:
            return self.cmds_found
        chk_cmd: str = tgo_cmd.lower()
        for cmd in self.commands:
            if chk_cmd in cmd.lower():
                self.cmds_found.append(cmd)
        return self.cmds_found

    def check_for_property(self, tgo_prop: str | None) -> list:
        """
        Filter by command name.

        :param tgo_prop: property name
        :return: list of device names matched
        """
        chk_prop: str

        self.logger.debug(
            "Check %d props for %s : %s", len(self.commands), tgo_prop, self.commands
        )
        self.props_found = []
        if not tgo_prop:
            return self.props_found
        chk_prop = tgo_prop.lower()
        for cmd in self.properties:
            if chk_prop in cmd.lower():
                self.props_found.append(cmd)
        return self.props_found

    def make_json(self) -> dict:  # noqa: C901
        """
        Convert internal values to JSON.

        :return: dictionary
        """

        def read_json_attribute(attr_name: str) -> None:
            """
            Add attribute to dictionary.

            :param attr_name: attribute name
            """
            self.logger.debug("Read JSON attribute %s", attr_name)
            # Read alias where applicable
            try:
                devdict["aliases"] = self.dev.get_device_alias_list()
            except AttributeError as oerr:
                self.logger.debug("Could not read device %s alias : %s", self.dev_name, str(oerr))
                devdict["aliases"] = "N/A"
            # Check for unknown attribute
            devdict["attributes"][attr_name] = {}
            if attr_name not in self.attributes:
                self.logger.debug("Unknown attribute %s not shown", attr_name)
                return
            devdict["attributes"][attr_name]["data"] = {}
            # Check for error messages
            if "error" in self.attributes[attr_name]:
                devdict["attributes"][attr_name]["error"] = self.attributes[attr_name]["error"]
            # Check that data value has been read
            if "data" not in self.attributes[attr_name]:
                pass
            elif "value" in self.attributes[attr_name]["data"]:
                data_val: Any = self.attributes[attr_name]["data"]["value"]
                self.logger.debug(
                    "Attribute %s data type %s: %s", attr_name, type(data_val), data_val
                )
                # Check data type
                if type(data_val) is dict:
                    devdict["attributes"][attr_name]["data"]["value"] = {}
                    for key in data_val:
                        devdict["attributes"][attr_name]["data"]["value"][key] = data_val[key]
                elif type(data_val) is numpy.ndarray:
                    devdict["attributes"][attr_name]["data"]["value"] = data_val.tolist()
                elif type(data_val) is list:
                    devdict["attributes"][attr_name]["data"]["value"] = data_val
                elif type(data_val) is tuple:
                    devdict["attributes"][attr_name]["data"]["value"] = list(data_val)
                elif type(data_val) is str:
                    if not data_val:
                        devdict["attributes"][attr_name]["data"]["value"] = ""
                    elif data_val[0] == "{" and data_val[-1] == "}":
                        devdict["attributes"][attr_name]["data"]["value"] = json.loads(data_val)
                    else:
                        devdict["attributes"][attr_name]["data"]["value"] = data_val
                else:
                    devdict["attributes"][attr_name]["data"]["value"] = str(data_val)
                devdict["attributes"][attr_name]["data"]["type"] = str(
                    self.attributes[attr_name]["data"]["type"]
                )
                devdict["attributes"][attr_name]["data"]["data_format"] = str(
                    self.attributes[attr_name]["data"]["data_format"]
                )
            else:
                pass
            # Check for attribute error
            if "error" in self.attributes[attr_name]:
                devdict["attributes"][attr_name]["error"] = str(
                    self.attributes[attr_name]["error"]
                )
            # Check attribute configuration
            if self.attributes[attr_name]["config"] is not None:
                devdict["attributes"][attr_name]["config"] = {}
                # Description
                try:
                    devdict["attributes"][attr_name]["config"]["description"] = self.attributes[
                        attr_name
                    ]["config"].description
                except UnicodeDecodeError:
                    devdict["attributes"][attr_name]["config"]["description"] = "N/A"
                # Root name
                devdict["attributes"][attr_name]["config"]["root_attr_name"] = self.attributes[
                    attr_name
                ]["config"].root_attr_name
                # Format
                devdict["attributes"][attr_name]["config"]["format"] = self.attributes[attr_name][
                    "config"
                ].format
                # Data format
                devdict["attributes"][attr_name]["config"]["data_format"] = str(
                    self.attributes[attr_name]["config"].data_format
                )
                # Display level
                devdict["attributes"][attr_name]["config"]["disp_level"] = str(
                    self.attributes[attr_name]["config"].disp_level
                )
                # Data type
                devdict["attributes"][attr_name]["config"]["data_type"] = str(
                    self.attributes[attr_name]["config"].data_type
                )
                # Display unit
                devdict["attributes"][attr_name]["config"]["display_unit"] = self.attributes[
                    attr_name
                ]["config"].display_unit
                # Standard unit
                devdict["attributes"][attr_name]["config"]["standard_unit"] = self.attributes[
                    attr_name
                ]["config"].standard_unit
                # Writable
                devdict["attributes"][attr_name]["config"]["writable"] = str(
                    self.attributes[attr_name]["config"].writable
                )
                # Writable attribute name
                devdict["attributes"][attr_name]["config"]["writable_attr_name"] = self.attributes[
                    attr_name
                ]["config"].writable_attr_name

        def read_json_command(cmd_name: str) -> None:
            """
            Add commands to dictionary.

            :param cmd_name: command name
            """
            devdict["commands"][cmd_name] = {}
            # Check for error message
            if "error" in self.commands[cmd_name]:
                devdict["commands"][cmd_name]["error"] = self.commands[cmd_name]["error"]
            # Check command configuration
            if self.commands[cmd_name]["config"] is not None:
                # Input type
                devdict["commands"][cmd_name]["in_type"] = repr(
                    self.commands[cmd_name]["config"].in_type
                )
                # Input type description
                devdict["commands"][cmd_name]["in_type_desc"] = self.commands[cmd_name][
                    "config"
                ].in_type_desc
                # Output type
                devdict["commands"][cmd_name]["out_type"] = repr(
                    self.commands[cmd_name]["config"].out_type
                )
                # Output type description
                devdict["commands"][cmd_name]["out_type_desc"] = self.commands[cmd_name][
                    "config"
                ].out_type_desc
                if "value" in self.commands[cmd_name]:
                    devdict["commands"][cmd_name]["value"] = self.commands[cmd_name]["value"]

        def read_json_property(prop_name: str) -> None:
            """
            Add properties to dictionary.

            :param prop_name: property name
            """
            # Check that value has been read
            if "value" in self.properties[prop_name]:
                prop_val: Any = self.properties[prop_name]["value"]
                devdict["properties"][prop_name] = {}
                # pylint: disable-next=c-extension-no-member
                if type(prop_val) is tango._tango.StdStringVector:
                    devdict["properties"][prop_name]["value"] = []  # delimiter.join(prop_val)
                    for propv in prop_val:
                        devdict["properties"][prop_name]["value"].append(propv)
                else:
                    devdict["properties"][prop_name]["value"] = prop_val

        # Read attribute and command configuration
        self.logger.debug("Build JSON")
        self.read_config_all()

        devdict: dict = {}
        devdict["name"] = self.dev_name
        if not self.quiet_mode:
            devdict["errors"] = self.dev_errors
        devdict["green_mode"] = self.green_mode
        devdict["version"] = self.version
        devdict["device_access"] = self.dev_access
        if self.jargon:
            devdict["acronyms"] = self.jargon
        # Information
        if self.info is not None:
            devdict["info"] = {}
            devdict["info"]["dev_class"] = self.info.dev_class
            devdict["info"]["dev_type"] = self.info.dev_type
            devdict["info"]["doc_url"] = self.info.doc_url
            devdict["info"]["server_host"] = self.info.server_host
            devdict["info"]["server_id"] = self.info.server_id
            devdict["info"]["server_version"] = self.info.server_version
        # Attributes
        devdict["attributes"] = {}
        if self.attribs_found:
            for attrib in self.attribs_found:
                self.logger.debug("Read JSON attribute %s", attrib)
                read_json_attribute(attrib)
        else:
            self.logger.info("Reading %d JSON attributes -->", len(self.attribs))
            for attrib in progress_bar(
                self.attribs,
                not self.quiet_mode,
                prefix=f"Read {len(self.attribs)} JSON attributes :",
                suffix="complete",
                decimals=0,
                length=100,
            ):
                read_json_attribute(attrib)
        # Commands
        devdict["commands"] = {}
        if self.commands:
            for cmd in self.commands:
                self.logger.debug("Read JSON command %s", cmd)
                read_json_command(cmd)
        # Properties
        devdict["properties"] = {}
        if self.properties:
            for prop in self.properties:
                self.logger.debug("Read JSON property %s", prop)
                read_json_property(prop)
        self.logger.debug("Read device : %s", devdict)
        return devdict

    def write_attribute_value(self, attrib: str, value: str) -> int:
        """
        Set value of attribute.

        :param attrib: attribute name
        :param value: attribute value
        :return: error condition
        """
        # Check that attribute is known
        if attrib not in self.attributes:
            self.logger.error("Attribute %s not found in %s", attrib, self.attributes.keys())
            return 1
        # Check type
        devtype: Any = self.attributes[attrib]["data"]["type"]
        wval: Any
        if devtype == "DevEnum":
            wval = int(value)
        else:
            wval = value
        self.logger.info("Set attribute %s (%s) to %s (%s)", attrib, devtype, wval, type(wval))
        # Write a single attribute
        self.dev.write_attribute(attrib, wval)
        return 0

    def read_attribute_value(self) -> None:
        """Read device attributes."""
        self.logger.debug("Read %d attributes for %s", len(self.attributes), self.dev_name)
        for attrib in self.attributes:
            # Read a single attribute
            self.attributes[attrib]["data"] = {}
            try:
                attrib_data = self.dev.read_attribute(attrib)
            except tango.DevFailed as terr:
                err_msg = str(terr.args[-1].desc)
                self.logger.debug("Failed on attribute %s : %s", attrib, err_msg)
                self.attributes[attrib]["error"] = err_msg
                self.attributes[attrib]["data"]["type"] = "N/A"
                self.attributes[attrib]["data"]["data_format"] = "N/A"
                continue
            if attrib in self.block_items["attributes"]:
                self.logger.warning("Not reading attribute %s value", attrib)
                self.attributes[attrib]["data"]["value"] = "N/A"
            else:
                self.attributes[attrib]["data"]["value"] = attrib_data.value
            self.attributes[attrib]["data"]["type"] = str(attrib_data.type)
            self.attributes[attrib]["data"]["data_format"] = str(attrib_data.data_format)
            self.logger.debug(
                "Read attribute %s data : %s", attrib, self.attributes[attrib]["data"]
            )

    def read_command_value(self, run_commands: list, run_commands_name: list) -> None:
        """
        Read device commands.

        :param run_commands: commands safe to run without parameters
        :param run_commands_name: commands safe to run with device name as parameter
        """
        self.logger.debug("Read %d commands for %s", len(self.commands), self.dev_name)
        for cmd in self.commands:
            if cmd in run_commands:
                # Execute a command on a device
                try:
                    self.commands[cmd]["value"] = self.dev.command_inout(cmd)
                except tango.ConnectionFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning("Could not run command %s : %s", cmd, err_msg)
                    self.commands[cmd]["value"] = "N/A"
                    self.commands[cmd]["error"] = err_msg
                except tango.DevFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning("Could not run command %s : %s", cmd, err_msg)
                    self.commands[cmd]["value"] = "N/A"
                    self.commands[cmd]["error"] = err_msg
                self.logger.debug(
                    "Read command %s (%s) : %s",
                    cmd,
                    type(self.commands[cmd]["value"]),
                    self.commands[cmd]["value"],
                )
            elif cmd in run_commands_name:
                # Run command in/out with device name as parameter
                try:
                    self.commands[cmd]["value"] = self.dev.command_inout(cmd, self.dev_name)
                    self.logger.debug(
                        "Read command %s (%s) with arg %s : %s",
                        cmd,
                        type(self.commands[cmd]["value"]),
                        self.dev_name,
                        self.commands[cmd]["value"],
                    )
                except tango.DevFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning(
                        "Could not run command %s with device name : %s", cmd, err_msg
                    )
                    self.commands[cmd]["value"] = "N/A"
                    self.commands[cmd]["error"] = err_msg
            else:
                # Nothing to see here
                pass
        return

    def read_property_value(self) -> None:
        """Read device properties."""
        self.logger.debug("Read %d properties for %s", len(self.properties), self.dev_name)
        for prop in self.properties:
            # get_property returns this:
            # {'CspMasterFQDN': ['mid-csp/control/0']}
            if prop in self.block_items["properties"]:
                self.logger.warning("Not reading property %s value", prop)
                self.properties[prop]["value"] = ["N/R"]
                continue
            # Get a list of properties for a device
            try:
                self.properties[prop]["value"] = self.dev.get_property(prop)[prop]
            except tango.CommunicationFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.warning("Could not get property %s value: %s", prop, err_msg)
                self.properties[prop]["value"] = ["N/A"]
            self.logger.debug("Read property %s : %s", prop, self.properties[prop]["value"])
        return

    def print_list_attribute(self, lwid: int, show_val: bool = True) -> None:
        """
        Print list of devices with attribute.

        :param lwid: line width
        :param show_val: print value
        """
        n: int

        self.print_list("")
        n = 0
        for attrib in self.attributes.keys():
            if n:
                print(f"{' ':{lwid}}", end="")
            if show_val:
                try:
                    attrib_val = self.attributes[attrib]["data"]["value"]
                except KeyError:
                    attrib_val = "N/A"
                print(f" {attrib:40} {attrib_val}")
            else:
                print(f" {attrib}")
            n += 1

    def print_list_command(self, lwid: int, show_val: bool = True) -> None:
        """
        Print list of devices with command.

        :param lwid: line width
        :param show_val: print value
        """
        n: int

        self.print_list("")
        n = 0
        for cmd in self.commands.keys():
            if n:
                print(f"{' ':{lwid}}", end="")
            if show_val:
                if "value" in self.commands[cmd]:
                    cmdv = self.commands[cmd]["value"]
                    print(f" {cmd:40} {cmdv}")
                else:
                    print(f" {cmd}")
            else:
                print(f" {cmd}")
            n += 1

    def print_list_property(self, lwid: int, show_val: bool = True) -> None:
        """
        Print list of devices with property.

        :param lwid: line width
        :param show_val: print value
        """
        n: int

        self.print_list("")
        n = 0
        for prop in self.properties.keys():
            if n:
                print(f"{' ':{lwid}}", end="")
            if show_val:
                propv = ",".join(self.properties[prop]["value"])
                print(f" {prop:40} {propv}")
            else:
                print(f" {prop}")
            n += 1

    def print_html_all(self, html_body: bool, outf_name: str | None = None) -> None:
        """
        Print full HTML report.

        :param html_body: Flag to print HTML header and footer
        :param outf_name: Output file name
        """
        self.logger.debug("Print as HTML")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, outf_name
        )
        json_reader.print_html_all(html_body)

    def get_html_all(self, html_body: bool) -> None:
        """
        Print full HTML report.

        :param html_body: Flag to print HTML header and footer
        """
        self.logger.debug("Print as HTML")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, None
        )
        json_reader.print_html_all(html_body)

    def print_markdown_all(self) -> None:
        """Print full HTML report."""
        self.logger.debug("Print as Markdown")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, None
        )
        json_reader.print_markdown_all()

    def print_txt_all(self) -> None:
        """Print full HTML report."""
        self.logger.debug("Print as Text")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, None
        )
        json_reader.print_txt_all()

    def print_html_quick(self, html_body: bool) -> None:
        """
        Print shortened HTML report.

        :param html_body: Flag to print HTML header and footer
        """
        self.logger.debug("Print as shortened HTML")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, None
        )
        json_reader.print_html_quick(html_body)
