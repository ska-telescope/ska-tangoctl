"""Read and display Tango stuff."""

import logging
from typing import Any

import tango

from ska_mid_itf_engineering_tools.tango_control.read_tango_device import (
    TangoctlDeviceBasic,
    progress_bar,
)


class TangoctlDeviceConfig(TangoctlDeviceBasic):
    """Read all the configuration on offer."""

    def __init__(
        self,
        logger: logging.Logger,
        quiet_mode: bool,
        device: str,
    ):
        """
        Get it on.

        :param logger: logging handle
        :param quiet_mode: do not display progress bar
        :param device: device name
        """
        self.prog_bar: bool = True
        self.dev: tango.DeviceProxy
        self.attributes: dict = {}
        self.commands: dict = {}
        self.properties: dict = {}
        self.dev_name: str
        self.green_mode: Any = None

        super().__init__(logger, device)
        self.logger.info("Open device %s config", device)

        for attrib in self.attribs:
            self.logger.debug("Read attribute config %s", attrib)
            self.attributes[attrib] = {}
            try:
                self.attributes[attrib]["data"] = self.dev.read_attribute(attrib)
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                self.logger.debug("Could not read %s : %s", attrib, err_msg)
                self.attributes[attrib]["data"] = None
            self.attributes[attrib]["config"] = self.dev.get_attribute_config(attrib)
        cmds = self.dev.get_command_list()
        for cmd in sorted(cmds):
            self.logger.debug("Read command config %s", cmd)
            self.commands[cmd] = {}
            self.commands[cmd]["config"] = self.dev.get_command_config(cmd)
        try:
            props = self.dev.get_property_list("*")
        except tango.NonDbDevice:
            self.logger.info("Not reading properties in nodb mode")
            props = []
        for prop in sorted(props):
            self.logger.debug("Read property %s", prop)
            self.properties[prop] = {}
        self.info: Any = self.dev.info()
        self.green_mode = self.dev.get_green_mode()
        self.prog_bar = not quiet_mode
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.prog_bar = False

    def get_json(self, delimiter: str = ",") -> dict:  # noqa: C901
        """
        Convert internal values to JSON.

        :param delimiter: field are seperated by this
        :return: dictionary
        """

        def set_attribute() -> None:
            """Add attribute to dictionary."""
            data: Any = self.attributes[attrib]["data"]
            if data is None:
                return
            devdict["attributes"][attrib]["data"] = {}
            devdict["attributes"][attrib]["data"]["data_format"] = str(data.data_format)
            devdict["attributes"][attrib]["data"]["dim_x"] = data.dim_x
            devdict["attributes"][attrib]["data"]["dim_y"] = data.dim_y
            devdict["attributes"][attrib]["data"]["has_failed"] = str(data.has_failed)
            devdict["attributes"][attrib]["data"]["is_empty"] = str(data.is_empty)
            devdict["attributes"][attrib]["data"]["name"] = data.name
            devdict["attributes"][attrib]["data"]["nb_read"] = data.nb_read
            devdict["attributes"][attrib]["data"]["nb_written"] = data.nb_written
            devdict["attributes"][attrib]["data"]["quality"] = str(data.quality)
            r_dimension = data.r_dimension
            devdict["attributes"][attrib]["data"]["r_dimension"] = {}
            devdict["attributes"][attrib]["data"]["r_dimension"]["dim_x"] = r_dimension.dim_x
            devdict["attributes"][attrib]["data"]["r_dimension"]["dim_y"] = r_dimension.dim_y
            devt = data.time
            devdict["attributes"][attrib]["data"]["time"] = {}
            devdict["attributes"][attrib]["data"]["time"]["tv_nsec"] = devt.tv_nsec
            devdict["attributes"][attrib]["data"]["time"]["tv_sec"] = devt.tv_sec
            devdict["attributes"][attrib]["data"]["time"]["tv_usec"] = devt.tv_usec
            devdict["attributes"][attrib]["data"]["type"] = str(data.type)
            devdict["attributes"][attrib]["data"]["value"] = str(data.value)
            devdict["attributes"][attrib]["data"]["w_dim_x"] = data.w_dim_x
            devdict["attributes"][attrib]["data"]["w_dim_y"] = data.w_dim_y
            devdict["attributes"][attrib]["data"]["w_dimension"] = {}
            w_dimension = data.w_dimension
            devdict["attributes"][attrib]["data"]["w_dimension"]["dim_x"] = w_dimension.dim_x
            devdict["attributes"][attrib]["data"]["w_dimension"]["dim_y"] = w_dimension.dim_y
            devdict["attributes"][attrib]["data"]["w_value"] = str(data.w_value)

        def set_attribute_config() -> None:
            """Add attribute configuration to dictionary."""
            devdict["attributes"][attrib]["config"] = {}
            dcfg: Any = self.attributes[attrib]["config"]
            alarms: Any = dcfg.alarms
            devdict["attributes"][attrib]["config"]["alarms"] = {}
            devdict["attributes"][attrib]["config"]["alarms"]["delta_t"] = alarms.delta_t
            devdict["attributes"][attrib]["config"]["alarms"]["delta_val"] = alarms.delta_val
            devdict["attributes"][attrib]["config"]["alarms"]["extensions"] = str(
                alarms.extensions
            )
            devdict["attributes"][attrib]["config"]["alarms"]["max_alarm"] = alarms.max_alarm
            devdict["attributes"][attrib]["config"]["alarms"]["max_warning"] = alarms.max_warning
            devdict["attributes"][attrib]["config"]["alarms"]["min_alarm"] = alarms.min_alarm
            devdict["attributes"][attrib]["config"]["alarms"]["min_warning"] = alarms.min_warning
            devdict["attributes"][attrib]["config"]["data_format"] = str(dcfg.data_format)
            devdict["attributes"][attrib]["config"]["data_type"] = str(dcfg.data_type)
            devdict["attributes"][attrib]["config"]["description"] = dcfg.description
            devdict["attributes"][attrib]["config"]["disp_level"] = str(dcfg.disp_level)
            devdict["attributes"][attrib]["config"]["display_unit"] = dcfg.display_unit
            enum_labels = dcfg.enum_labels
            devdict["attributes"][attrib]["config"]["enum_labels"] = f"{enum_labels}"
            devdict["attributes"][attrib]["config"]["events"] = {}
            devdict["attributes"][attrib]["config"]["events"]["arch_event"] = {}
            arch_event = dcfg.events.arch_event
            devdict["attributes"][attrib]["config"]["events"]["arch_event"][
                "archive_abs_change"
            ] = arch_event.archive_abs_change
            devdict["attributes"][attrib]["config"]["events"]["arch_event"][
                "archive_period"
            ] = arch_event.archive_period
            devdict["attributes"][attrib]["config"]["events"]["arch_event"][
                "archive_rel_change"
            ] = arch_event.archive_rel_change
            devdict["attributes"][attrib]["config"]["events"]["arch_event"]["extensions"] = str(
                arch_event.extensions
            )
            devdict["attributes"][attrib]["config"]["events"]["ch_event"] = {}
            ch_event = dcfg.events.ch_event
            devdict["attributes"][attrib]["config"]["events"]["ch_event"][
                "abs_change"
            ] = ch_event.abs_change
            devdict["attributes"][attrib]["config"]["events"]["ch_event"]["extensions"] = str(
                ch_event.extensions
            )
            devdict["attributes"][attrib]["config"]["events"]["ch_event"][
                "rel_change"
            ] = ch_event.rel_change
            devdict["attributes"][attrib]["config"]["events"]["per_event"] = {}
            per_event = dcfg.events.per_event
            devdict["attributes"][attrib]["config"]["events"]["per_event"]["extensions"] = str(
                per_event.extensions
            )
            devdict["attributes"][attrib]["config"]["events"]["per_event"][
                "period"
            ] = per_event.period
            extensions: Any = dcfg.extensions
            devdict["attributes"][attrib]["config"]["extensions"] = f"{extensions}"
            devdict["attributes"][attrib]["config"]["format"] = dcfg.format
            devdict["attributes"][attrib]["config"]["label"] = dcfg.label
            devdict["attributes"][attrib]["config"]["max_alarm"] = dcfg.max_alarm
            devdict["attributes"][attrib]["config"]["max_dim_x"] = dcfg.max_dim_x
            devdict["attributes"][attrib]["config"]["max_dim_y"] = dcfg.max_dim_y
            devdict["attributes"][attrib]["config"]["max_value"] = dcfg.max_value
            devdict["attributes"][attrib]["config"]["memorized"] = str(dcfg.memorized)
            devdict["attributes"][attrib]["config"]["min_alarm"] = dcfg.min_alarm
            devdict["attributes"][attrib]["config"]["min_value"] = dcfg.min_value
            devdict["attributes"][attrib]["config"]["name"] = dcfg.name
            devdict["attributes"][attrib]["config"]["root_attr_name"] = dcfg.root_attr_name
            devdict["attributes"][attrib]["config"]["standard_unit"] = dcfg.standard_unit
            sys_extensions: Any = dcfg.sys_extensions
            devdict["attributes"][attrib]["config"]["sys_extensions"] = f"{sys_extensions}"
            devdict["attributes"][attrib]["config"]["unit"] = dcfg.unit
            devdict["attributes"][attrib]["config"]["writable"] = str(dcfg.writable)
            devdict["attributes"][attrib]["config"]["writable_attr_name"] = dcfg.writable_attr_name

        def set_command_config() -> None:
            """Add command to dictionary."""
            devdict["commands"][cmd] = {}
            devdict["commands"][cmd]["cmd_name"] = self.commands[cmd]["config"].cmd_name
            devdict["commands"][cmd]["cmd_tag"] = self.commands[cmd]["config"].cmd_tag
            devdict["commands"][cmd]["in_type"] = str(self.commands[cmd]["config"].in_type)
            devdict["commands"][cmd]["in_type_desc"] = self.commands[cmd]["config"].in_type_desc
            devdict["commands"][cmd]["out_type"] = str(self.commands[cmd]["config"].out_type)
            devdict["commands"][cmd]["out_type_desc"] = self.commands[cmd]["config"].out_type_desc

        devdict: dict = {}
        devdict["name"] = self.dev_name
        devdict["errors"] = self.dev_errors
        devdict["version"] = self.version
        devdict["info"] = {}
        devdict["info"]["dev_class"] = self.info.dev_class
        devdict["info"]["dev_type"] = self.info.dev_type
        devdict["info"]["doc_url"] = self.info.doc_url
        devdict["info"]["server_host"] = self.info.server_host
        devdict["info"]["server_id"] = self.info.server_id
        devdict["info"]["server_version"] = self.info.server_version
        devdict["attributes"] = {}
        self.logger.info("Set attributes...")
        # Run "for attrib in self.attributes:"
        for attrib in progress_bar(
            self.attributes,
            self.prog_bar,
            prefix=f"Set {len(self.attributes)} attributes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            devdict["attributes"][attrib] = {}
            self.logger.debug("Set attribute %s", attrib)
            set_attribute()
            set_attribute_config()
        devdict["commands"] = {}
        cmd: str
        for cmd in self.commands:
            self.logger.debug("Set command %s", cmd)
            set_command_config()

        self.logger.info("INFO: %s", devdict)
        return devdict
