"""Read and display Tango stuff."""

import json
import logging
import sys
from typing import Any

import numpy
import tango

from ska_mid_itf_engineering_tools.tango_control.ska_jargon import find_jargon
from ska_mid_itf_engineering_tools.tango_control.tango_json import TangoJsonReader, progress_bar


class TangoctlDeviceBasic:
    """Compile a basic dictionary for a Tango device."""

    logger: logging.Logger

    def __init__(  # noqa: C901
        self,
        logger: logging.Logger,
        device: str,
        list_values: dict = {},
        timeout_millis: float = 500,
    ):
        """
        Iniltialise the thing.

        :param logger: logging handle
        :param device: device name
        :param list_values: dictionary with values to process
        :param timeout_millis: timeout in milliseconds
        """
        self.logger = logger
        self.logger.debug("Open device %s", device)
        self.dev: tango.DeviceProxy
        self.info: str = "---"
        self.version: str = "---"
        self.status: str = "---"
        self.adminMode: Any = None
        self.adminModeStr: str = "---"
        self.dev_name: str
        self.dev_class: str
        self.dev_state: Any = None
        self.dev_str: str = "---"
        self.list_values: dict
        self.dev_errors: list = []
        self.attribs: list
        self.cmds: list
        self.props: list
        # Set up Tango device
        self.dev = tango.DeviceProxy(device)
        self.dev.set_timeout_millis(timeout_millis)
        try:
            self.dev_name = self.dev.name()
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.info("Could not read device name for %s ; %s", device, err_msg)
            self.dev_errors.append(f"Could not read name of {device} : {err_msg}")
            self.dev_name = f"{device} (N/A)"
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.info("Could not read name for device %s", device)
            self.dev_name = f"{device} (N/A)"
            self.dev_errors.append(f"Could not read info : {err_msg}")
        self.list_values = list_values
        self.green_mode: Any = str(self.dev.get_green_mode())
        self.dev_access: str = str(self.dev.get_access_control())
        # Read attributes
        try:
            self.attribs = sorted(self.dev.get_attribute_list())
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.info("Could not read attributes for %s", device)
            self.dev_errors.append(f"Could not read attributes : {err_msg}")
            self.attribs = []
        # Read commands
        try:
            self.cmds = sorted(self.dev.get_command_list())
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.info("Could not read commands for %s", device)
            self.dev_errors.append(f"Could not read commands : {err_msg}")
            self.cmds = []
        # Read properties
        try:
            self.props = sorted(self.dev.get_property_list("*"))
        except tango.NonDbDevice:
            self.logger.info("Not reading properties in nodb mode")
            self.props = []
        try:
            self.dev_class = self.dev.info().dev_class
        except tango.DevFailed:
            self.dev_class = "---"

    def read_config(self) -> None:  # noqa: C901
        """
        Read additional data.

        State, adminMode and versionId are specific to devices
        """
        try:
            self.info = self.dev.info()
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.info("Could not read device %s : %s", self.dev_name, err_msg)
            self.dev_errors.append(f"Could not read device : {err_msg}")
            return
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.info("Could not read device %s : %s", self.dev_name, err_msg)
            self.dev_errors.append(f"Could not read device : {err_msg}")
            return
        # Read version ID, where applicable
        if "versionId" not in self.attribs:
            self.version = "---"
        elif "versionId" in self.list_values["attributes"]:
            try:
                self.version = self.dev.versionId
            except tango.CommunicationFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.info("Could not read %s version : %s", self.dev_name, err_msg)
                self.dev_errors.append(f"Could not read {self.dev_name} name : {err_msg}")
                self.version = "N/A"
            except AttributeError as oerr:
                self.logger.info("Could not read %s version : %s", self.dev_name, str(oerr))
                self.version = "N/A"
            if self.version is None:
                self.version = "N/A"
        else:
            self.version = "---"
        # Read state, where applicable
        if "State" not in self.cmds:
            self.dev_state = "---"
        elif "State" in self.list_values["commands"]:
            try:
                self.dev_state = self.dev.State()
            except tango.CommunicationFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.info("Could not read %s state : %s", self.dev_name, err_msg)
            except TypeError as oerr:
                self.logger.info("Could not read %s state : %s", self.dev_name, str(oerr))
                self.dev_state = "N/A"
        else:
            self.dev_state = "---"
        try:
            self.dev_str = f"{repr(self.dev_state).split('.')[3]}"
        except IndexError:
            self.dev_str = f"{repr(self.dev_state)}"
        # Read admin mode, where applicable
        if "adminMode" not in self.attribs:
            self.adminMode = "---"
        elif "adminMode" in self.list_values["attributes"]:
            try:
                self.adminMode = self.dev.adminMode
                # self.logger.debug("Admin mode: %s", self.adminMode)
            except tango.CommunicationFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.info("Could not read %s admin mode : %s", self.dev_name, err_msg)
            except AttributeError as oerr:
                self.logger.info("Could not read %s version : %s", self.dev_name, str(oerr))
                self.adminMode = "N/A"
            try:
                self.adminModeStr = str(self.adminMode).split(".")[-1]
            except IndexError as oerr:
                self.logger.info("Could not read %s version : %s", self.dev_name, str(oerr))
                self.adminModeStr = str(self.adminMode)
        else:
            self.adminMode = "---"

    def print_list(self) -> None:
        """Print data."""
        print(
            f"{self.dev_name:64} {self.dev_str:10} {self.adminModeStr:11} {self.version:8}"
            f" {self.dev_class}"
        )

    def print_html(self) -> None:
        """Print data."""
        self.read_config()
        print(
            f"<tr><td>{self.dev_name}</td><td>{self.dev_str}</td><td>{self.adminModeStr}</td>"
            f"<td>{self.version}</td><td>{self.dev_class}</td></tr>"
        )

    def make_json(self) -> dict:
        """
        Build dictionary.

        :return: dictionary with device data
        """
        devdict: dict = {}
        devdict["name"] = self.dev_name
        devdict["state"] = self.dev_str
        devdict["adminMode"] = self.adminModeStr
        devdict["version"] = self.version
        devdict["class"] = self.dev_class
        return devdict


class TangoctlDevice(TangoctlDeviceBasic):
    """Compile a dictionary for a Tango device."""

    def __init__(  # noqa: C901
        self,
        logger: logging.Logger,
        quiet_mode: bool,
        device: str,
        tgo_attrib: str | None,
        tgo_cmd: str | None,
        tgo_prop: str | None,
    ):
        """
        Iniltialise the thing.

        :param logger: logging handle
        :param quiet_mode: flag for displaying progress bars
        :param device: device name
        :param tgo_attrib: attribute filter
        :param tgo_cmd: command filter
        :param tgo_prop: property filter
        """
        self.commands: dict = {}
        self.attributes: dict = {}
        self.properties: dict = {}
        self.command_config: Any
        self.attribs_found: list = []
        self.props_found: list = []
        self.cmds_found: list = []
        self.info: Any
        self.quiet_mode: bool = True
        self.outf = sys.stdout
        # Run base class constructor
        super().__init__(logger, device)
        self.logger.debug(
            "New device %s (attributes %s, commands %s, properties %s)",
            device,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
        )
        self.quiet_mode = quiet_mode
        # Set quiet mode, i.e. do not display progress bars
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        if tgo_attrib:
            tgo_attrib = tgo_attrib.lower()
        # Check commands
        for cmd in self.cmds:
            if tgo_cmd:
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
            if tgo_attrib:
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
            if tgo_prop:
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
            self.logger.info("Could not read info from %s : %s", device, err_msg)
            self.dev_errors.append(f"Could not read info: {err_msg}")
            self.info = None
        self.version: str
        # Check version
        try:
            self.version = self.dev.versionId
        except AttributeError as oerr:
            self.logger.info("Could not read device %s version ID : %s", self.dev_name, str(oerr))
            self.version = "N/A"
        except tango.CommunicationFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.info("Could not read device %s version ID : %s", self.dev_name, err_msg)
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
        self.jargon = find_jargon(self.dev_name)

    def read_config(self) -> None:
        """Read attribute and command configuration."""
        self.logger.info("Read config from device %s", self.dev_name)
        # Read attribute configuration
        for attrib in self.attributes:
            self.logger.debug("Read attribute config from %s", attrib)
            try:
                self.attributes[attrib]["config"] = self.dev.get_attribute_config(attrib)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.info(
                    "Could not not read attribute %s config for %s : %s",
                    attrib,
                    self.dev_name,
                    err_msg,
                )
                self.attributes[attrib]["error"] = err_msg
                self.attributes[attrib]["config"] = None
        # Read command configuration
        for cmd in self.commands:
            self.logger.debug("Read command config from %s", cmd)
            try:
                self.commands[cmd]["config"] = self.dev.get_command_config(cmd)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.info(
                    "Could not not read command %s config for %s : %s", cmd, self.dev_name, err_msg
                )
                self.commands[cmd]["error"] = err_msg
                self.commands[cmd]["config"] = None

    def check_for_attribute(self, tgo_attrib: str | None) -> list:
        """
        Filter by attribute name.

        :param tgo_attrib: attribute name
        :return: list of device names matched
        """
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
        self.logger.debug(
            "Check %d props for %s : %s", len(self.commands), tgo_prop, self.commands
        )
        self.props_found = []
        if not tgo_prop:
            return self.props_found
        chk_prop: str = tgo_prop.lower()
        for cmd in self.properties:
            if chk_prop in cmd.lower():
                self.props_found.append(cmd)
        return self.props_found

    def make_json(self, delimiter: str = ",") -> dict:  # noqa: C901
        """
        Convert internal values to JSON.

        :param delimiter: field are seperated by this
        :return: dictionary
        """

        def set_json_attribute(attr_name: str) -> None:
            """
            Add attribute to dictionary.

            :param attr_name: attribute name
            """
            self.logger.debug("Set attribute %s", attr_name)
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
                devdict["attributes"][attr_name]["config"]["description"] = self.attributes[
                    attr_name
                ]["config"].description
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

        def set_json_command(cmd_name: str) -> None:
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

        def set_json_property(prop_name: str) -> None:
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
        self.read_config()

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
                set_json_attribute(attrib)
        else:
            # Run "for attrib in self.attribs:"
            for attrib in progress_bar(
                self.attribs,
                not self.quiet_mode,
                prefix=f"Read {len(self.attribs)} JSON attributes :",
                suffix="complete",
                decimals=0,
                length=100,
            ):
                set_json_attribute(attrib)
        # Commands
        devdict["commands"] = {}
        if self.commands:
            for cmd in self.commands:
                self.logger.debug("Set command %s", cmd)
                set_json_command(cmd)
        # Properties
        devdict["properties"] = {}
        if self.properties:
            for prop in self.properties:
                self.logger.debug("Set property %s", prop)
                set_json_property(prop)
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
        self.dev.write_attribute(attrib, wval)
        return 0

    def read_attribute_value(self) -> None:
        """Read device attributes."""
        self.logger.info(f"Read {len(self.attributes)} attributes for {self.dev_name}")
        for attrib in self.attributes:
            # Attribute data
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
        self.logger.info("Read %d commands for %s", len(self.commands), self.dev_name)
        for cmd in self.commands:
            if cmd in run_commands:
                # Run command in/out
                try:
                    self.commands[cmd]["value"] = self.dev.command_inout(cmd)
                except tango.ConnectionFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.info("Could not run command %s : %s", cmd, err_msg)
                    self.commands[cmd]["value"] = "N/A"
                    self.commands[cmd]["error"] = err_msg
                except tango.DevFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.info("Could not run command %s : %s", cmd, err_msg)
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
                    self.logger.info(
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
        self.logger.info(f"Read {len(self.properties)} properties for {self.dev_name}")
        for prop in self.properties:
            # get_property returns this:
            # {'CspMasterFQDN': ['mid-csp/control/0']}
            self.properties[prop]["value"] = self.dev.get_property(prop)[prop]
            self.logger.debug("Read property %s : %s", prop, self.properties[prop]["value"])
        return

    def print_list_attribute(self) -> None:
        """Print data."""
        print(
            f"{self.dev_name:40} {self.dev_str:10} {self.adminModeStr:11} {self.version:8}"
            f" {self.dev_class:24} ",
            end="",
        )
        n = 0
        for attrib in self.attributes.keys():
            if n:
                print(f"{' ':40} {' ':10} {' ':11} {' ':8} {' ':24} ", end="")
            print(f"{attrib}")
            n += 1

    def print_list_command(self) -> None:
        """Print data."""
        print(
            f"{self.dev_name:40} {self.dev_str:10} {self.adminModeStr:11} {self.version:8}"
            f" {self.dev_class:24} ",
            end="",
        )
        n = 0
        for cmd in self.commands.keys():
            if n:
                print(f"{' ':40} {' ':10} {' ':11} {' ':8} {' ':24} ", end="")
            print(f"{cmd}")
            n += 1

    def print_list_property(self) -> None:
        """Print data."""
        print(
            f"{self.dev_name:40} {self.dev_str:10} {self.adminModeStr:11} {self.version:8}"
            f" {self.dev_class:24} ",
            end="",
        )
        n = 0
        for prop in self.properties.keys():
            if n:
                print(f"{' ':40} {' ':10} {' ':11} {' ':8} {' ':24} ", end="")
            print(f"{prop}")
            n += 1

    def print_html_all(self, html_body: bool) -> None:
        """
        Print full HTML report.

        :param html_body: Flag to print HTML header and footer
        """
        self.logger.info("Print as HTML")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, None
        )
        json_reader.print_html_all(html_body)

    def print_markdown_all(self) -> None:
        """Print full HTML report."""
        self.logger.info("Print as Markdown")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, None
        )
        json_reader.print_markdown_all()

    def print_txt_all(self) -> None:
        """Print full HTML report."""
        self.logger.info("Print as Text")
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
        self.logger.info("Print as shortened HTML")
        devsdict = {f"{self.dev_name}": self.make_json()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.quiet_mode, None, devsdict, None
        )
        json_reader.print_html_quick(html_body)
