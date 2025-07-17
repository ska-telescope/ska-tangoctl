"""Read and display Tango stuff."""

import json
import logging
import os
from typing import Any

import numpy
import tango

try:
    from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
except ModuleNotFoundError:
    KubernetesInfo = None  # type: ignore[assignment,misc]
from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.progress_bar import progress_bar
from ska_tangoctl.tango_control.tango_json import TangoJsonReader
from ska_tangoctl.tla_jargon.tla_jargon import find_jargon

DEFAULT_TIMEOUT_MILLIS: int = 500


class TangoctlDevice:
    """Compile a dictionary for a Tango device."""

    def __init__(  # noqa: C901
        self,
        logger: logging.Logger,
        disp_action: DispAction,
        outf: Any,
        timeout_millis: int | None,
        dev_status: dict,
        device: str,
        list_items: dict,
        block_items: dict,
        tgo_attrib: str | None,
        tgo_cmd: str | None,
        tgo_prop: str | None,
        k8s_ctx: str | None,
        domain_name: str | None,
        indent: int = 0,
    ):
        """
        Iniltialise the thing.

        :param logger: logging handle
        :param disp_action: display settings
        :param outf: output file pointer
        :param timeout_millis: Tango device timeout in milliseconds
        :param dev_status: flag to read status
        :param device: device name
        :param list_items: attributes, commands or properties in list output
        :param block_items: attributes, commands or properties not to be shown in list output
        :param tgo_attrib: attribute filter
        :param tgo_cmd: command filter
        :param tgo_prop: property filter
        :param k8s_ctx: Kubernetes context
        :param domain_name: Kubernetes domain name
        :param indent: indentation for JSON and YAML
        :raises Exception: could not open device
        """
        self.commands: dict = {}
        self.attributes: dict = {}
        self.properties: dict = {}
        self.procs: dict = {}
        self.pod_name: str | None = None
        self.pod_desc: dict = {}
        self.attribs_found: list = []
        self.props_found: list = []
        self.cmds_found: list = []
        self.indent: int = indent
        self.info: tango.DeviceInfo
        self.quiet_mode: bool = True
        self.outf: Any = outf
        self.attribs: list
        self.cmds: list
        self.props: list
        self.list_items: dict
        self.timeout_millis: int | None

        self.logger: logging.Logger = logger
        self.disp_action: DispAction = disp_action
        if timeout_millis is None:
            self.timeout_millis = DEFAULT_TIMEOUT_MILLIS
        else:
            self.timeout_millis = timeout_millis
        self.dev: tango.DeviceProxy
        self.dev_name: str = "?"
        self.version: str = "?"
        self.status: str = "?"
        self.adminMode: int | None = None
        self.adminModeStr: str = "---"
        self.dev_class: str
        self.dev_state: Any = None
        self.dev_errors: list = []
        self.dev_values: dict = {}
        self.db_host: str = "?"
        self.db_port: int = 0
        self.tango_lib: int = 0
        self.domain_name: str | None = domain_name
        self.k8s_ctx: str | None = k8s_ctx
        err_msg: str

        # Set up Tango device
        tango_host = os.getenv("TANGO_HOST")
        self.list_items = list_items
        self.logger.debug(
            "Open device %s (%s) status %s (list items %s)",
            device,
            tango_host,
            dev_status,
            list_items,
        )
        try:
            self.dev = tango.DeviceProxy(device)
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            self.logger.warning("Tango device failed: %s", err_msg)
            self.dev_errors.append(f"Tango device failed: {err_msg}")
            self.dev = None
        except RuntimeError as rerr:
            self.logger.warning("Tango runtime error: %s", rerr)
            self.dev_errors.append(f"Tango runtime error: {rerr}")
            self.dev = None
        if self.dev is None:
            device = device.lower()
            self.logger.debug("Retry device %s", device)
            try:
                self.dev = tango.DeviceProxy(device)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.dev_name = f"{device} (N/A)"
                self.logger.warning(
                    "Could not open device %s (%s) : %s", device, tango_host, err_msg
                )
                raise Exception(f"Could not open device {device} ({tango_host}) : {err_msg}")
        self.dev.set_timeout_millis(self.timeout_millis)

        # Read device name and database info
        self.dev_name = self.read_info(device, "name", True)
        if self.dev_name is None:
            self.dev_name = f"{device} (N/A)"
        self.db_host = self.read_info(device, "get_db_host", True)
        if self.db_host is None:
            self.db_host = "N/A"
        self.db_port = self.read_info(device, "get_db_port_num")
        if self.db_port is None:
            self.db_port = 0
        self.tango_lib = self.read_info(device, "get_tango_lib_version", True)
        if self.tango_lib is None:
            self.tango_lib = 0

        # Read information on the device and device class name
        try:
            self.info = self.dev.info()
            self.dev_class = self.info.dev_class
        except Exception as eerr:
            self.logger.warning("Could not read device class: %s", str(eerr))
            self.dev_class = "N/A"

        # Read green mode and access control type for this DeviceProxy
        self.green_mode: Any = str(self.dev.get_green_mode())
        self.dev_access: str = str(self.dev.get_access_control())

        # Read status
        if dev_status:
            self.attribs = dev_status["attributes"]
            self.cmds = dev_status["commands"]
            self.props = dev_status["properties"]
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
        if self.disp_action.show_attrib:
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
        if self.disp_action.show_cmd:
            try:
                self.cmds = sorted(self.dev.get_command_list(), reverse=self.disp_action.reverse)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.warning("Could not read commands for %s", device)
                self.dev_errors.append(f"Could not read commands : {err_msg}")
                self.cmds = []
            self.logger.debug("Got %d commands for %s", len(self.cmds), self.dev_name)

        # Get the list of property names for the device
        if self.disp_action.show_prop:
            try:
                self.props = sorted(
                    self.dev.get_property_list("*"), reverse=self.disp_action.reverse
                )
            except tango.NonDbDevice:
                self.logger.info("Not reading properties in nodb mode")
                self.props = []
            self.logger.debug("Got %d properties for %s", len(self.props), self.dev_name)

        self.logger.debug(
            "Open device %s (attributes %s, commands %s, properties %s)",
            device,
            tgo_attrib,
            tgo_cmd,
            tgo_prop,
        )
        self.list_items = list_items
        self.block_items = block_items

        # Set quiet mode, i.e. do not display progress bars
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        if tgo_attrib:
            tgo_attrib = tgo_attrib.lower()

        # Check commands
        for cmd in self.cmds:
            if self.disp_action.xact_match and tgo_cmd:
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
            if self.disp_action.xact_match and tgo_attrib:
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
            if self.disp_action.xact_match and tgo_prop:
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
            "Add device %s with %d attributes, %d commands and %d properties, class %s",
            device,
            len(self.attributes),
            len(self.commands),
            len(self.properties),
            self.dev_class,
        )

        # Other stuff
        # self. = self.dev.get_()
        self.fqdn = self.read_info(device, "get_fqdn")
        self.idl_version = self.read_info(device, "get_idl_version")
        # TODO figure this out
        # self. =  self.dev.get_locker()
        self.logging_level = self.read_info(device, "get_logging_level")
        self.logging_target = self.read_info(device, "get_logging_target")
        self.pipe_config = self.read_info(device, "get_pipe_config")
        self.source = self.read_info(device, "get_source")
        self.timeout_millis = self.read_info(device, "get_timeout_millis")
        self.transparency_reconnection = self.read_info(device, "get_transparency_reconnection")

        # TODO deal with very messy string
        # try:
        #     self.componentstates = self.dev.getcomponentstates()
        # except AttributeError as ae:
        #     self.logger.info("Could not read component states attribute: %s", str(ae))
        #     self.componentstates = {}
        # except Exception as gcse:
        #     self.logger.info("Could not read component states: %s", str(gcse))
        #     self.componentstates = {}
        # self.logger.debug("Componentstates: %s", self.componentstates)

        # Check name for acronyms
        if self.disp_action.show_jargon:
            self.jargon = find_jargon(self.dev_name)
        else:
            self.jargon = ""

    def read_info(self, device: str, info: str, log_it: bool = False) -> Any:  # noqa: C901
        """
        Read device name and database info.

        :param device: device name
        :param info: what to read
        :param log_it: log warning when read fails
        :returns: String with information read from Tango
        """
        info_data: str | None
        try:
            if info == "name":
                info_data = self.dev.name()
            elif info == "get_db_host":
                info_data = self.dev.get_db_host()
            elif info == "get_db_port_num":
                info_data = self.dev.get_db_port_num()
            elif info == "get_tango_lib_version":
                info_data = self.dev.get_tango_lib_version()
            elif info == "get_fqdn":
                info_data = self.dev.get_fqdn()
            elif info == "get_idl_version":
                info_data = self.dev.get_idl_version()
            elif info == "get_logging_level":
                info_data = self.dev.get_logging_level()
            elif info == "get_logging_target":
                info_data = self.dev.get_logging_target()
            elif info == "get_pipe_config":
                info_data = self.dev.get_pipe_config()
            elif info == "get_source":
                info_data = self.dev.get_source()
            elif info == "get_timeout_millis":
                info_data = self.dev.get_timeout_millis()
            elif info == "get_transparency_reconnection":
                info_data = self.dev.get_transparency_reconnection()
            # elif info == "":
            #     info_data = self.dev.()
            else:
                self.logger.warning("Can't read device %s %s", device, info)
                info_data = None
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            if log_it:
                self.logger.warning("Failed to read device %s %s : %s", device, info, err_msg)
                self.dev_errors.append(f"Could not read device {device} {info} : {err_msg}")
            else:
                self.logger.debug("Failed to read device %s %s : %s", device, info, err_msg)
            info_data = None
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            if log_it:
                self.logger.warning("Connection failed reading device %s %s", device, info)
                self.dev_errors.append(
                    f"Connection failed reading device {device} {info} : {err_msg}"
                )
            else:
                self.logger.debug("Connection failed reading device %s %s", device, info)
            info_data = None
        return info_data

    def __del__(self) -> None:
        """Destructor."""
        self.logger.debug("Shut down TangoctlDevice for %s", self.dev_name)

    def read_config(self) -> None:  # noqa: C901
        """
        Read additional data as configured in JSON file.

        State, adminMode and versionId are specific to devices
        """
        attribute: Any
        command: Any
        dev_val: Any
        err_msg: str

        self.logger.debug("Reading configuration of device %s", self.dev_name)
        # Names of attributes to be read
        attribs: list
        if self.attribs:
            attribs = self.attribs
        else:
            attribs = list(self.list_items["attributes"].keys())
        self.logger.debug("Reading attributes : %s", attribs)
        # Names of commands to be read
        cmds: list
        if self.cmds:
            cmds = self.cmds
        else:
            cmds = list(self.list_items["commands"].keys())
        self.logger.debug("Reading commands : %s", cmds)
        # Names of properties to be read
        props: list
        if self.props:
            props = self.props
        else:
            props = list(self.list_items["properties"].keys())
        self.logger.debug("Reading properties : %s", props)
        # Read configured attribute values
        if "attributes" in self.list_items:
            self.logger.debug("Reading attributes : %s", self.list_items["attributes"])
            for attribute in self.list_items["attributes"]:
                if type(attribute) is list:
                    attribute = attribute[0]
                if attribute not in attribs:
                    self.logger.info("Attribute %s not in %s", attribute, attribs)
                    try:
                        self.dev_values[attribute] = "-"
                    except TypeError:
                        self.logger.error("Could not update attribute %s", attribute)
                    continue
                # Read a single attribute
                try:
                    dev_attrib = self.dev.read_attribute(attribute)
                    dev_val_type = dev_attrib.type
                    if dev_val_type == tango._tango.CmdArgType.DevEnum:
                        dev_attr_cfg = self.dev.get_attribute_config(attribute)
                        dev_val = dev_attr_cfg.enum_labels[dev_attrib.value]
                    else:
                        dev_val = dev_attrib.value
                    self.logger.debug(
                        "Read device %s attribute %s value : %s", self.dev_name, attribute, dev_val
                    )
                except tango.DevFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.debug(
                        "Device %s failed for attribute %s : %s",
                        self.dev_name,
                        attribute,
                        err_msg,
                    )
                    dev_val = ""
                except tango.CommunicationFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning(
                        "Communication failed for device %s attribute %s : %s",
                        self.dev_name,
                        attribute,
                        err_msg,
                    )
                    self.dev_errors.append(
                        f"Communication failed for device {self.dev_name} attribute {attribute} :"
                        f" {err_msg}"
                    )
                    dev_val = "N/A"
                except AttributeError as oerr:
                    self.logger.warning(
                        "Attribute error for device %s attribute %s : %s",
                        self.dev_name,
                        attribute,
                        str(oerr),
                    )
                    self.dev_errors.append(
                        f"Attribute error for device {self.dev_name} attribute {attribute} :"
                        f" {str(oerr)}"
                    )
                    dev_val = "N/A"
                except TypeError as yerr:
                    self.logger.warning(
                        "Type error for device %s attribute %s : %s",
                        self.dev_name,
                        attribute,
                        str(yerr),
                    )
                    self.dev_errors.append(
                        f"Type error for device {self.dev_name} attribute {attribute} :"
                        f" {str(yerr)}"
                    )
                    dev_val = "N/A"
                self.logger.debug("Read attribute %s value: %s", attribute, dev_val)
                self.dev_values[attribute] = dev_val
        # Read configured command values
        if "commands" in self.list_items:
            self.logger.debug("Reading commands : %s", self.list_items["commands"])
            for command in self.list_items["commands"]:
                if type(command) is list:
                    command = command[0]
                if command not in cmds:
                    self.logger.info("Command %s not in %s", command, cmds)
                    self.dev_values[command] = "-"
                    continue
                # Execute a command on a device
                try:
                    dev_val = str(self.dev.command_inout(command))
                    self.logger.debug(
                        "Read device %s command %s value : %s", self.dev_name, command, dev_val
                    )
                except tango.DevFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning(
                        "Read device %s command %s failed : %s", self.dev_name, command, err_msg
                    )
                    self.dev_errors.append(
                        f"Read device {self.dev_name} command {command} failed : {err_msg}"
                    )
                    dev_val = "N/A"
                except tango.CommunicationFailed as terr:
                    err_msg = terr.args[0].desc.strip()
                    self.logger.warning(
                        "Could not read device %s command %s : %s", self.dev_name, command, err_msg
                    )
                    self.dev_errors.append(
                        f"Could not read device {self.dev_name} command {command} : {err_msg}"
                    )
                    dev_val = "N/A"
                except AttributeError as oerr:
                    self.logger.warning(
                        "Could not device %s command %s : %s", self.dev_name, command, str(oerr)
                    )
                    self.dev_errors.append(
                        f"Could not read device {self.dev_name} command {command} : {str(oerr)}"
                    )
                    dev_val = "N/A"
                except TypeError as yerr:
                    self.logger.warning(
                        "Type error for device %s command %s : %s",
                        self.dev_name,
                        command,
                        str(yerr),
                    )
                    self.dev_errors.append(
                        f"Type error for device {self.dev_name} command {command} :{str(yerr)}"
                    )
                    dev_val = "N/A"
                self.logger.debug("Read command %s: %s", command, dev_val)
                self.dev_values[command] = dev_val
        # Read configured command values
        if "properties" in self.list_items:
            self.logger.debug("Reading properties : %s", self.list_items["properties"])
            for tproperty in self.list_items["properties"]:
                if tproperty not in props:
                    self.logger.debug("Property %s not in %s", tproperty, props)
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
        self.logger.debug("Read configuration of device %s", self.dev_name)

    def read_config_all(self) -> None:
        """Read attribute and command configuration."""
        attrib: str
        cmd: str
        err_msg: str

        self.logger.debug("Reading all configurations from device %s", self.dev_name)
        # Read attribute configuration
        for attrib in self.attributes:
            self.logger.debug("Read attribute config from %s", attrib)
            # Read the attribute configuration for a single attribute
            try:
                self.attributes[attrib]["config"] = self.dev.get_attribute_config(attrib)
                self.attributes[attrib]["poll_period"] = self.dev.get_attribute_poll_period(attrib)
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
                self.attributes[attrib]["poll_period"] = None
        self.logger.debug("Device %s attributes: %s", self.dev_name, self.attributes)
        # Read command configuration
        for cmd in self.commands:
            self.logger.debug("Read command config from %s", cmd)
            # Read the configuration for a single command
            try:
                self.commands[cmd]["config"] = self.dev.get_command_config(cmd)
                self.commands[cmd]["poll_period"] = self.dev.get_command_poll_period(cmd)
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
                self.commands[cmd]["poll_period"] = None
        self.logger.debug("Device %s commands: %s", self.dev_name, self.commands)
        self.logger.debug("Read all configurations from device %s", self.dev_name)

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
        for prop in self.properties:
            if chk_prop in prop.lower():
                self.props_found.append(prop)
        return self.props_found

    def make_json_small(self) -> dict:  # noqa: C901
        """
        Convert internal values to JSON.

        :returns: dictionary
        """

        def read_json_attribute(attr_name: str) -> dict:
            """
            Add attribute to dictionary.

            :param attr_name: attribute name
            :returns: dictionary
            """
            self.logger.debug("Read JSON attribute %s", attr_name)
            # Check for unknown attribute
            attrib_dict: dict = {}
            attrib_dict["name"] = attr_name
            if attr_name not in self.attributes:
                self.logger.debug("Unknown attribute %s not shown", attr_name)
                return attrib_dict
            attrib_dict["data"] = {}
            # Check for attribute error
            if "error" in self.attributes[attr_name]:
                if self.attributes[attr_name]["error"]:
                    attrib_dict["error"] = str(self.attributes[attr_name]["error"])
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
                    attrib_dict["data"]["value"] = {}
                    for key in data_val:
                        attrib_dict["data"]["value"][key] = data_val[key]
                elif type(data_val) is numpy.ndarray:
                    attrib_dict["data"]["value"] = data_val.tolist()
                elif type(data_val) is list:
                    attrib_dict["data"]["value"] = data_val
                elif type(data_val) is tuple:
                    attrib_dict["data"]["value"] = list(data_val)
                elif type(data_val) is str:
                    if not data_val:
                        attrib_dict["data"]["value"] = ""
                    elif data_val[0] == "{" and data_val[-1] == "}":
                        attrib_dict["data"]["value"] = json.loads(data_val)
                    else:
                        attrib_dict["data"]["value"] = data_val
                else:
                    attrib_dict["data"]["value"] = str(data_val)
            else:
                pass
            return attrib_dict

        self.logger.debug("Building small JSON")
        devdict: dict = {}
        devdict["name"] = self.dev_name
        devdict["errors"] = self.dev_errors
        # Attributes
        devdict["attributes"] = []
        if self.attribs_found:
            for attrib in self.attribs_found:
                self.logger.debug("Read JSON attribute %s", attrib)
                devdict["attributes"].append(read_json_attribute(attrib))
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
                devdict["attributes"].append(read_json_attribute(attrib))

        self.logger.debug("Built small JSON : %s", devdict)
        return devdict

    def make_json_medium(self) -> dict:  # noqa: C901
        """
        Convert internal values to medium size JSON.

        :return: dictionary
        """

        def read_json_attribute(attr_name: str) -> dict:
            """
            Add attribute to dictionary.

            :param attr_name: attribute name
            :returns: dictionary
            """
            self.logger.debug("Read JSON attribute %s", attr_name)
            # Check for unknown attribute
            attrib_dict: dict = {}
            attrib_dict["name"] = attr_name
            attrib_dict["config"] = {}
            if attr_name not in self.attributes:
                self.logger.debug("Unknown attribute %s not shown", attr_name)
                return attrib_dict
            attrib_dict["data"] = {}
            # Check for attribute error
            if "error" in self.attributes[attr_name]:
                attrib_dict["error"] = str(self.attributes[attr_name]["error"])
            # Other stuff
            attrib_dict["poll_period"] = self.attributes[attr_name]["poll_period"]
            # Check that data value has been read
            if "data" not in self.attributes[attr_name]:
                pass
            elif "value" in self.attributes[attr_name]["data"]:
                data_val: Any = self.attributes[attr_name]["data"]["value"]
                self.logger.debug(
                    "Attribute %s data type %s: %s", attr_name, type(data_val), data_val
                )
                # Check data type
                attrib_dict["data"]["type"] = str(self.attributes[attr_name]["data"]["type"])
                attrib_dict["data"]["pytype"] = str(self.attributes[attr_name]["data"]["pytype"])
                if type(data_val) is dict:
                    attrib_dict["data"]["value"] = {}
                    for key in data_val:
                        attrib_dict["data"]["value"][key] = data_val[key]
                elif type(data_val) is numpy.ndarray:
                    attrib_dict["data"]["value"] = data_val.tolist()
                elif type(data_val) is list:
                    attrib_dict["data"]["value"] = data_val
                elif type(data_val) is tuple:
                    attrib_dict["data"]["value"] = list(data_val)
                elif type(data_val) is str:
                    if not data_val:
                        attrib_dict["data"]["value"] = ""
                    elif data_val[0] == "{" and data_val[-1] == "}":
                        attrib_dict["data"]["value"] = json.loads(data_val)
                    else:
                        attrib_dict["data"]["value"] = data_val
                elif attrib_dict["data"]["type"] == "DevEnum":
                    if "enum_labels" in attrib_dict["config"]:
                        attrib_dict["data"]["value"] = attrib_dict["config"]["enum_labels"][
                            data_val
                        ]
                    else:
                        attrib_dict["data"]["value"] = str(data_val)
                else:
                    attrib_dict["data"]["value"] = str(data_val)
            else:
                pass
            return attrib_dict

        def read_json_command(cmd_name: str) -> dict:
            """
            Add commands to dictionary.

            :param cmd_name: command name
            :returns: dictionary
            """
            cmd_dict: dict = {}
            cmd_dict["name"] = cmd_name
            cmd_dict["poll_period"] = self.commands[cmd_name]["poll_period"]
            # Check for error message
            if "error" in self.commands[cmd_name]:
                cmd_dict["error"] = self.commands[cmd_name]["error"]
            # Check command configuration
            cmd_dict["config"] = {}
            if self.commands[cmd_name]["config"] is not None:
                cmd_cfg = self.commands[cmd_name]["config"]
                # Input type
                cmd_dict["config"]["in_type"] = repr(cmd_cfg.in_type)
                # Output type
                cmd_dict["config"]["out_type"] = repr(cmd_cfg.out_type)
                cmd_dict["config"]["cmd_tag"] = cmd_cfg.cmd_tag
                cmd_dict["config"]["disp_level"] = str(cmd_cfg.disp_level)
                if "value" in self.commands[cmd_name]:
                    cmd_dict["value"] = self.commands[cmd_name]["value"]
            return cmd_dict

        def read_json_property(prop_name: str) -> dict:
            """
            Add properties to dictionary.

            :param prop_name: property name
            :returns: dictionary
            """
            # Check that value has been read
            prop_dict: dict = {}
            prop_dict["name"] = prop_name
            if "value" in self.properties[prop_name]:
                prop_val: Any = self.properties[prop_name]["value"]
                # pylint: disable-next=c-extension-no-member
                if type(prop_val) is tango._tango.StdStringVector:
                    prop_dict["value"] = []  # delimiter.join(prop_val)
                    for propv in prop_val:
                        prop_dict["value"].append(propv)
                else:
                    prop_dict["value"] = prop_val
            return prop_dict

        # Read attribute and command configuration
        self.logger.debug("Building medium JSON")
        self.read_config_all()

        devdict: dict = {}
        devdict["name"] = self.dev_name
        devdict["errors"] = self.dev_errors
        devdict["db_host"] = self.db_host
        devdict["db_port"] = self.db_port
        devdict["tango_lib"] = self.tango_lib
        devdict["green_mode"] = self.green_mode
        devdict["version"] = self.version
        devdict["device_access"] = self.dev_access
        devdict["fqdn"] = self.fqdn
        devdict["idl_version"] = self.idl_version
        devdict["logging_level"] = self.logging_level
        if self.logging_target is not None:
            devdict["logging_target"] = list(self.logging_target)
        else:
            devdict["logging_target"] = []
        if self.pipe_config is not None:
            devdict["pipe_config"] = list(self.pipe_config)
        else:
            devdict["pipe_config"] = []
        devdict["source"] = self.source
        devdict["timeout_millis"] = self.timeout_millis
        devdict["transparency_reconnection"] = self.transparency_reconnection
        # TODO not ready for the big time yet
        # devdict["componentstates"] = self.componentstates

        if self.jargon:
            devdict["acronyms"] = self.jargon
        # Information
        devdict["info"] = {}
        if self.info is not None:
            devdict["info"]["dev_class"] = self.info.dev_class
            devdict["info"]["dev_type"] = self.info.dev_type
            devdict["info"]["server_host"] = self.info.server_host
        else:
            devdict["info"] = {}
        # Attributes
        devdict["attributes"] = []
        if self.attribs_found:
            for attrib in self.attribs_found:
                self.logger.debug("Read JSON attribute %s", attrib)
                devdict["attributes"].append(read_json_attribute(attrib))
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
                devdict["attributes"].append(read_json_attribute(attrib))
        # Commands
        devdict["commands"] = []
        if self.commands:
            for cmd in self.commands:
                self.logger.debug("Read JSON command %s", cmd)
                devdict["commands"].append(read_json_command(cmd))
        # Properties
        devdict["properties"] = []
        if self.properties:
            for prop in self.properties:
                self.logger.debug("Read JSON property %s", prop)
                devdict["properties"].append(read_json_property(prop))
        # Processes
        if self.procs:
            devdict["processes"] = {"output": self.procs["output"]}
        else:
            devdict["processes"] = {}
        self.logger.debug("Built medium JSON : %s", devdict)
        return devdict

    def make_json_large(self) -> dict:  # noqa: C901
        """
        Convert internal values to JSON.

        :return: dictionary
        """

        def read_json_attribute(attr_name: str) -> dict:
            """
            Add attribute to dictionary.

            :param attr_name: attribute name
            :returns: dictionary
            """
            self.logger.debug("Read JSON attribute %s", attr_name)
            # Check for unknown attribute
            attrib_dict: dict = {}
            attrib_dict["name"] = attr_name
            attrib_dict["config"] = {}
            if attr_name not in self.attributes:
                self.logger.debug("Unknown attribute %s not shown", attr_name)
                return attrib_dict
            attrib_dict["data"] = {}
            # Check for attribute error
            if "error" in self.attributes[attr_name]:
                attrib_dict["error"] = str(self.attributes[attr_name]["error"])
            # Check attribute configuration
            if self.attributes[attr_name]["config"] is not None:
                attr_cfg = self.attributes[attr_name]["config"]
                # Description
                try:
                    attrib_dict["config"]["description"] = attr_cfg.description
                except UnicodeDecodeError:
                    attrib_dict["config"]["description"] = "N/A"
                # Alarms
                dev_items = attr_cfg.alarms
                attrib_dict["config"]["alarms"] = {
                    "delta_t": dev_items.delta_t,
                    "delta_val": dev_items.delta_val,
                    "extensions": list(dev_items.extensions),
                    "max_alarm": dev_items.max_alarm,
                    "max_warning": dev_items.max_warning,
                    "min_alarm": dev_items.min_alarm,
                    "min_warning": dev_items.min_warning,
                }
                # Events
                dev_items = attr_cfg.events
                attrib_dict["config"]["events"] = {
                    "arch_event": {
                        "archive_abs_change": dev_items.arch_event.archive_abs_change,
                        "archive_period": dev_items.arch_event.archive_period,
                        "archive_rel_change": dev_items.arch_event.archive_rel_change,
                        "extensions": list(dev_items.arch_event.extensions),
                    },
                    "ch_event": {
                        "abs_change": dev_items.ch_event.abs_change,
                        "extensions": list(dev_items.ch_event.extensions),
                        "rel_change": dev_items.ch_event.rel_change,
                    },
                    "per_event": {
                        "extensions": list(dev_items.per_event.extensions),
                        "period": dev_items.per_event.period,
                    },
                }
                attrib_dict["config"]["sys_extensions"] = list(attr_cfg.sys_extensions)
                # Root name
                attrib_dict["config"]["root_attr_name"] = attr_cfg.root_attr_name
                # Format
                attrib_dict["config"]["format"] = attr_cfg.format
                # Data format
                attrib_dict["config"]["data_format"] = str(attr_cfg.data_format)
                # Display level
                attrib_dict["config"]["disp_level"] = str(attr_cfg.disp_level)
                # Data type
                dtype = attr_cfg.data_type
                # pylint: disable-next=c-extension-no-member
                if dtype == tango._tango.CmdArgType.DevEnum:
                    attrib_dict["config"]["enum_labels"] = list(attr_cfg.enum_labels)
                tydict = tango.CmdArgType.names
                attrib_dict["config"]["data_type"] = list(tydict.keys())[
                    list(tydict.values()).index(attr_cfg.data_type)
                ]
                # Display unit
                attrib_dict["config"]["display_unit"] = attr_cfg.display_unit
                # Standard unit
                attrib_dict["config"]["standard_unit"] = attr_cfg.standard_unit
                # Writable
                attrib_dict["config"]["writable"] = str(attr_cfg.writable)
                attrib_dict["config"]["max_dim_x"] = attr_cfg.max_dim_x
                attrib_dict["config"]["max_dim_y"] = attr_cfg.max_dim_y
                attrib_dict["config"]["max_alarm"] = attr_cfg.max_alarm
                attrib_dict["config"]["max_value"] = attr_cfg.max_value
                attrib_dict["config"]["memorized"] = str(attr_cfg.memorized)
                attrib_dict["config"]["min_alarm"] = attr_cfg.min_alarm
                attrib_dict["config"]["min_value"] = attr_cfg.min_value
                # Writable attribute name
                attrib_dict["config"]["writable_attr_name"] = attr_cfg.writable_attr_name
            # Other stuff
            attrib_dict["poll_period"] = self.attributes[attr_name]["poll_period"]
            # Check that data value has been read
            if "data" not in self.attributes[attr_name]:
                pass
            elif "value" in self.attributes[attr_name]["data"]:
                data_val: Any = self.attributes[attr_name]["data"]["value"]
                self.logger.debug(
                    "Attribute %s data type %s: %s", attr_name, type(data_val), data_val
                )
                # Check data type
                attrib_dict["data"]["type"] = str(self.attributes[attr_name]["data"]["type"])
                attrib_dict["data"]["pytype"] = str(self.attributes[attr_name]["data"]["pytype"])
                if type(data_val) is dict:
                    attrib_dict["data"]["value"] = {}
                    for key in data_val:
                        attrib_dict["data"]["value"][key] = data_val[key]
                elif type(data_val) is numpy.ndarray:
                    attrib_dict["data"]["value"] = data_val.tolist()
                elif type(data_val) is list:
                    attrib_dict["data"]["value"] = data_val
                elif type(data_val) is tuple:
                    attrib_dict["data"]["value"] = list(data_val)
                elif type(data_val) is str:
                    if not data_val:
                        attrib_dict["data"]["value"] = ""
                    elif data_val[0] == "{" and data_val[-1] == "}":
                        attrib_dict["data"]["value"] = json.loads(data_val)
                    else:
                        attrib_dict["data"]["value"] = data_val
                elif attrib_dict["data"]["type"] == "DevEnum":
                    if "enum_labels" in attrib_dict["config"]:
                        attrib_dict["data"]["value"] = attrib_dict["config"]["enum_labels"][
                            data_val
                        ]
                    else:
                        attrib_dict["data"]["value"] = str(data_val)
                else:
                    attrib_dict["data"]["value"] = str(data_val)
                # Data format, e.g. "SCALAR"
                attrib_dict["data"]["data_format"] = str(
                    self.attributes[attr_name]["data"]["data_format"]
                )
            else:
                pass
            return attrib_dict

        def read_json_command(cmd_name: str) -> dict:
            """
            Add commands to dictionary.

            :param cmd_name: command name
            :returns: dictionary
            """
            cmd_dict: dict = {}
            cmd_dict["name"] = cmd_name
            cmd_dict["poll_period"] = self.commands[cmd_name]["poll_period"]
            # Check for error message
            if "error" in self.commands[cmd_name]:
                cmd_dict["error"] = self.commands[cmd_name]["error"]
            # Check command configuration
            cmd_dict["config"] = {}
            if self.commands[cmd_name]["config"] is not None:
                cmd_cfg = self.commands[cmd_name]["config"]
                # Input type
                cmd_dict["config"]["in_type"] = repr(cmd_cfg.in_type)
                # Input type description
                cmd_dict["config"]["in_type_desc"] = cmd_cfg.in_type_desc
                # Output type
                cmd_dict["config"]["out_type"] = repr(cmd_cfg.out_type)
                # Output type description
                cmd_dict["config"]["out_type_desc"] = cmd_cfg.out_type_desc
                cmd_dict["config"]["cmd_tag"] = cmd_cfg.cmd_tag
                cmd_dict["config"]["disp_level"] = str(cmd_cfg.disp_level)
                if "value" in self.commands[cmd_name]:
                    cmd_dict["value"] = self.commands[cmd_name]["value"]
            return cmd_dict

        def read_json_property(prop_name: str) -> dict:
            """
            Add properties to dictionary.

            :param prop_name: property name
            :returns: dictionary
            """
            # Check that value has been read
            prop_dict: dict = {}
            prop_dict["name"] = prop_name
            if "value" in self.properties[prop_name]:
                prop_val: Any = self.properties[prop_name]["value"]
                # pylint: disable-next=c-extension-no-member
                if type(prop_val) is tango._tango.StdStringVector:
                    prop_dict["value"] = []  # delimiter.join(prop_val)
                    for propv in prop_val:
                        prop_dict["value"].append(propv)
                else:
                    prop_dict["value"] = prop_val
            return prop_dict

        # Read attribute and command configuration
        self.logger.debug("Building large JSON")
        self.read_config_all()

        devdict: dict = {}
        devdict["name"] = self.dev_name
        devdict["errors"] = self.dev_errors
        devdict["db_host"] = self.db_host
        devdict["db_port"] = self.db_port
        devdict["tango_lib"] = self.tango_lib
        devdict["green_mode"] = self.green_mode
        devdict["version"] = self.version
        devdict["device_access"] = self.dev_access
        devdict["fqdn"] = self.fqdn
        devdict["idl_version"] = self.idl_version
        devdict["logging_level"] = self.logging_level
        if self.logging_target is not None:
            devdict["logging_target"] = list(self.logging_target)
        else:
            devdict["logging_target"] = []
        if self.pipe_config is not None:
            devdict["pipe_config"] = list(self.pipe_config)
        else:
            devdict["pipe_config"] = []
        devdict["source"] = self.source
        devdict["timeout_millis"] = self.timeout_millis
        devdict["transparency_reconnection"] = self.transparency_reconnection
        # TODO not ready for the big time yet
        # devdict["componentstates"] = self.componentstates

        if self.jargon:
            devdict["acronyms"] = self.jargon
        # Information
        devdict["info"] = {}
        if self.info is not None:
            devdict["info"]["dev_class"] = self.info.dev_class
            devdict["info"]["dev_type"] = self.info.dev_type
            devdict["info"]["doc_url"] = self.info.doc_url
            devdict["info"]["server_host"] = self.info.server_host
            devdict["info"]["server_id"] = self.info.server_id
            devdict["info"]["server_version"] = self.info.server_version
        else:
            devdict["info"] = {}
        # Read alias where applicable
        try:
            devdict["aliases"] = self.dev.get_device_alias_list()
        except AttributeError as oerr:
            self.logger.debug("Could not read device %s alias : %s", self.dev_name, str(oerr))
            devdict["aliases"] = "N/A"
        # Attributes
        devdict["attributes"] = []
        if self.attribs_found:
            for attrib in self.attribs_found:
                self.logger.debug("Read JSON attribute %s", attrib)
                devdict["attributes"].append(read_json_attribute(attrib))
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
                devdict["attributes"].append(read_json_attribute(attrib))
        # Commands
        devdict["commands"] = []
        if self.commands:
            for cmd in self.commands:
                self.logger.debug("Read JSON command %s", cmd)
                devdict["commands"].append(read_json_command(cmd))
        # Properties
        devdict["properties"] = []
        if self.properties:
            for prop in self.properties:
                self.logger.debug("Read JSON property %s", prop)
                devdict["properties"].append(read_json_property(prop))
        # Processes
        devdict["processes"] = self.procs
        self.logger.debug("Built large JSON : %s", devdict)
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
        self.logger.debug("Set attribute %s (%s) to %s (%s)", attrib, devtype, wval, type(wval))
        # Write a single attribute
        self.dev.write_attribute(attrib, wval)
        return 0

    def read_attribute_value(self) -> None:
        """Read device attributes."""
        self.logger.debug("Reading %d attributes for %s", len(self.attributes), self.dev_name)
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
            self.attributes[attrib]["data"]["pytype"] = type(attrib_data.value).__name__
            self.attributes[attrib]["data"]["data_format"] = str(attrib_data.data_format)
            self.logger.debug(
                "Read attribute %s data : %s", attrib, self.attributes[attrib]["data"]
            )
        self.logger.debug("Read %d attributes for %s", len(self.attributes), self.dev_name)

    def read_command_value(self, run_commands: list, run_commands_name: list) -> None:
        """
        Read device commands.

        :param run_commands: commands safe to run without parameters
        :param run_commands_name: commands safe to run with device name as parameter
        """
        self.logger.debug("Reading %d commands for %s", len(self.commands), self.dev_name)
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
        self.logger.debug("Read %d commands for %s", len(self.commands), self.dev_name)
        return

    def read_property_value(self) -> None:
        """Read device properties."""
        self.logger.debug("Reading %d properties for %s", len(self.properties), self.dev_name)
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
        self.logger.debug("Read %d properties for %s", len(self.properties), self.dev_name)
        return

    def print_list(self, eol: str = "\n") -> None:
        """
        Print data.

        :param eol: printed at the end
        """
        self.read_config()
        self.logger.debug("Print list: %s", self.list_items)
        self.logger.debug("Use values: %s", self.dev_values)
        print(f"{self.dev_name:64} ", end="", file=self.outf)
        for attribute in self.list_items["attributes"]:
            field_value = self.dev_values[attribute]
            field_width = self.list_items["attributes"][attribute]
            self.logger.debug(f"Print attribute {attribute} : {field_value} {field_width=}")
            print(f"{field_value:{field_width}} ", end="", file=self.outf)
        for command in self.list_items["commands"]:
            field_value = self.dev_values[command]
            field_width = self.list_items["commands"][command]
            self.logger.debug(f"Print command {command} : {field_value} ({field_width=})")
            print(f"{field_value:{field_width}} ", end="", file=self.outf)
        for tproperty in self.list_items["properties"]:
            field_value = self.dev_values[tproperty]
            field_width = self.list_items["properties"][tproperty]
            self.logger.debug(f"Print property {tproperty} : {field_value} ({field_width=})")
            print(f"{field_value:{field_width}} ", end="", file=self.outf)
        print(f"{self.dev_class:32}", end=eol, file=self.outf)

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
                print(f"{' ':{lwid}}", end="", file=self.outf)
            if show_val:
                try:
                    attrib_val = self.attributes[attrib]["data"]["value"]
                except KeyError:
                    attrib_val = "N/A"
                print(f" {attrib:40} {attrib_val}", file=self.outf)
            else:
                print(f" {attrib}", file=self.outf)
            n += 1
        self.logger.debug("Listed %d attributes", len(self.attributes))

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
                print(f"{' ':{lwid}}", end="", file=self.outf)
            if show_val:
                if "value" in self.commands[cmd]:
                    cmdv = self.commands[cmd]["value"]
                    print(f" {cmd:40} {cmdv}", file=self.outf)
                else:
                    print(f" {cmd}", file=self.outf)
            else:
                print(f" {cmd}", file=self.outf)
            n += 1
        self.logger.debug("Listed %d commands", len(self.commands))

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
                print(f"{' ':{lwid}}", end="", file=self.outf)
            if show_val:
                propv = ",".join(self.properties[prop]["value"])
                print(f" {prop:40} {propv}", file=self.outf)
            else:
                print(f" {prop}", file=self.outf)
            n += 1
        self.logger.debug("Listed %d properties", len(self.properties))

    def print_html_large(self, html_body: bool) -> None:
        """
        Print full HTML report.

        :param html_body: Flag to print HTML header and footer
        """
        self.logger.debug("Printing as large HTML")
        devsdict = {f"{self.dev_name}": self.make_json_large()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.indent, self.quiet_mode, None, devsdict, self.outf
        )
        json_reader.print_html_large(html_body)

    def print_html_small(self, html_body: bool) -> None:
        """
        Print shortened HTML report.

        :param html_body: Flag to print HTML header and footer
        """
        self.logger.debug("Printing as small HTML")
        devsdict = {f"{self.dev_name}": self.make_json_small()}
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, self.indent, self.quiet_mode, None, devsdict, self.outf
        )
        json_reader.print_html_small(html_body)

    def device_run_cmd(self, ns_name: str, pod_name: str, pod_cmd: str) -> dict:
        """
        Run a command in specified pod.

        :param ns_name: namespace
        :param pod_name: pod name
        :param pod_cmd: command to run
        :returns: dictionary with output information
        """
        pod: dict = {}
        if KubernetesInfo is None:
            return pod
        k8s: KubernetesInfo = KubernetesInfo(self.logger, None)
        pod["name"] = pod_name
        pod["command"] = pod_cmd
        self.logger.info("Running command in device pod %s : '%s'", pod_name, pod_cmd)
        pod_exec: list = pod_cmd.split(" ")
        resps: str = k8s.exec_pod_command(ns_name, pod_name, pod_exec)
        pod["output"] = []
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
                else:
                    pod["output"].append(resp)
        else:
            pod["output"].append(resps)
        self.logger.debug(
            "Ran command '%s' with output: %s bytes, %d lines",
            pod_cmd,
            len(resps),
            len(pod["output"]),
        )
        self.logger.debug("Command %s output: %s", pod_cmd, pod)
        return pod

    def read_procs(self, ns_name: str | None) -> int:
        """
        Read processes running on host.

        :param ns_name: namespace
        :returns: error condition
        """
        self.logger.debug("Reading processes")
        if self.info is None:
            self.procs = {}
            return 1
        if ns_name is None:
            self.logger.warning("Namespace for processes not set")
            self.procs = {}
            return 1
        pod_name = self.info.server_host
        procs_cmd: str = "ps -ef"
        self.procs = self.device_run_cmd(ns_name, pod_name, procs_cmd)
        if not self.procs:
            self.logger.warning("Could not read %d processes")
            return 1
        self.logger.debug("Read %d processes", len(self.procs))
        return 0

    def read_pod(self, ns_name: str | None) -> int:
        """
        Read info about pod running this device.

        :param ns_name: namespace
        :returns: error condition
        """
        if KubernetesInfo is None:
            self.logger.warning("Kubernetes not supported")
            return 1
        if ns_name is None:
            self.logger.warning("Namespace for pod not set")
            self.pod_desc = {}
            return 1
        self.pod_name = self.info.server_host
        self.logger.debug("Reading description of pod : %s", self.pod_name)
        if self.pod_name is None:
            self.logger.warning("Could not read server host for device %s", self.dev_name)
            self.dev_errors.append(f"Could not read server host for device {self.dev_name}")
            self.pod_desc = {}
            return 1
        k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
        pod_desc: Any = k8s.get_pod_desc(ns_name, self.pod_name)
        if pod_desc is None:
            self.pod_desc = {}
            return 1
        self.pod_desc = pod_desc.to_dict()
        self.logger.info("Read description of pod : %s", self.pod_name)
        self.logger.debug(
            "Pod description :\n%s", json.dumps(self.pod_desc, indent=4, default=str)
        )
        return 0
