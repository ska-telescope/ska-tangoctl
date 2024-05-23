"""Read and display Tango stuff."""

import json
import logging
import os
import re
from collections import OrderedDict
from typing import Any

import tango
import yaml

from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice, TangoctlDeviceBasic
from ska_tangoctl.tango_control.tango_json import TangoJsonReader, progress_bar


class TangoctlDevicesBasic:
    """Compile a dictionary of available Tango devices."""

    logger: logging.Logger

    def __init__(  # noqa: C901s
        self,
        logger: logging.Logger,
        uniq_cls: bool,
        quiet_mode: bool,
        reverse: bool,
        evrythng: bool,
        cfg_data: Any,
        tgo_name: str | None,
        fmt: str,
        ns_name: str | None = None,
    ):
        """
        Read list of Tango devices.

        :param logger: logging handle
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
            self.logger.info("Could not connect to basic Tango database %s", self.tango_host)
            raise oerr
        self.logger.info("Connect to basic Tango database %s", self.tango_host)

        # Read devices
        device_list = sorted(database.get_device_exported("*").value_string, reverse=reverse)
        self.logger.info("%d basic devices available", len(device_list))

        if tgo_name:
            tgo_name = tgo_name.lower()
        self.logger.info("Open basic device %s", tgo_name)

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
                new_dev = TangoctlDeviceBasic(logger, device, reverse, self.list_items)
                if uniq_cls:
                    dev_class = new_dev.dev_class
                    if dev_class == "---":
                        self.logger.info(
                            f"Skip basic device {device} with unknown class {dev_class}"
                        )
                    elif dev_class not in self.dev_classes:
                        self.dev_classes.append(dev_class)
                        self.devices[device] = new_dev
                    else:
                        self.logger.info(
                            f"Skip basic device {device} with known class {dev_class}"
                        )
                else:
                    self.devices[device] = new_dev
            except Exception as e:
                self.logger.info("%s", e)
                self.devices[device] = None

    def __del__(self) -> None:
        """Destructor."""
        tango_host = os.getenv("TANGO_HOST")
        self.logger.info("Shut down TangoctlDevicesBasic for host %s", tango_host)
        os.environ.pop("TANGO_HOST", None)

    def read_configs(self) -> None:
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
            if self.devices[device] is not None:
                self.devices[device].read_config()

    def make_json(self) -> dict:
        """
        Make dictionary of devices.

        :return: dictionary with device data
        """
        devdict: dict

        devdict = {}
        self.logger.info("List %d basic devices in JSON format...", len(self.devices))
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
        self.logger.info("List %d devices in text format...", len(self.devices))
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
        self.logger.info("Show %d basic devices in HTML format...", len(self.devices))
        print("<table>")
        self.print_html_heading()
        for device in self.devices:
            self.devices[device].print_html()
        print("</table>")

    def get_html_header(self) -> str:
        # Getting first key in dictionary
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
        self.logger.info("List %d basic devices in HTML format...", len(self.devices))
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

        self.logger.info("Read classes in %d devices...", len(self.devices))
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

        self.logger.info("Get classes in %d devices", len(self.devices))
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

        self.logger.info("Print JSON")
        devsdict = self.make_json()
        print(f'\n"{self.tango_host}":')
        print(f"{json.dumps(devsdict, indent=4)}")

    def print_yaml(self, disp_action: int) -> None:
        """
        Print in YAML format.

        :param disp_action: not used
        """
        devsdict: dict
        ydevsdict: dict = {}

        self.logger.info("Print YAML")
        devsdict = self.make_json()
        ydevsdict[self.tango_host] = devsdict
        print(yaml.dump(ydevsdict))


class TangoctlDevices(TangoctlDevicesBasic):
    """Compile a dictionary of available Tango devices."""

    def __init__(  # noqa: C901s
        self,
        logger: logging.Logger,
        uniq_cls: bool,
        quiet_mode: bool,
        reverse: bool,
        evrythng: bool,
        cfg_data: dict,
        tgo_name: str | None,
        tgo_attrib: str | None,
        tgo_cmd: str | None,
        tgo_prop: str | None,
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
        :param reverse: sort in reverse order
        :param evrythng: get commands and attributes regadrless of state
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

        self.logger = logger
        self.cfg_data = cfg_data
        self.output_file = output_file
        self.logger.info(
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
        self.logger.info("Run commands %s", self.run_commands)
        self.run_commands_name = self.cfg_data["run_commands_name"]
        self.list_items = self.cfg_data["list_items"]
        self.logger.info("Run commands with name %s", self.run_commands_name)
        self.prog_bar = not quiet_mode

        if nodb:
            trl = f"tango://{self.tango_host}/{tgo_name}#dbase=no"
            new_dev = TangoctlDevice(
                logger,
                not self.prog_bar,
                reverse,
                trl,
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
                        logger,
                        not self.prog_bar,
                        reverse,
                        device,
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

    def __del__(self) -> None:
        """Desctructor."""
        tango_host = os.getenv("TANGO_HOST")
        self.logger.debug("Shut down TangoctlDevices for host %s", tango_host)

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
            if self.devices[device] is not None:
                self.devices[device].read_attribute_value()

    def read_command_values(self) -> None:
        """Read device data."""
        self.logger.info("Read commands of %d devices...", len(self.devices))
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
        self.logger.info("Read properties of %d devices...", len(self.devices))
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

    def read_device_values(self) -> None:
        """Read device data."""
        self.logger.debug("Read attribute, command and property data from devices")
        self.read_attribute_values()
        self.read_command_values()
        self.read_property_values()
        self.logger.debug("Read %d devices", len(self.devices))

    def make_json(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devsdict: dict = {}
        self.logger.debug("Read %d JSON devices...", len(self.devices))
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
        return devsdict

    def print_txt_list_attrib(self) -> None:
        """Print list of devices with attribute name."""
        self.logger.info("Listing %d devices...", len(self.devices))
        for device in self.devices:
            print(f"{device}")
        return

    def print_txt_list(self, heading: str | None = None) -> None:
        """
        Print list of devices.

        :param heading: print at the top
        """
        self.logger.info("List %d devices...", len(self.devices))
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

        if disp_action == 4:
            self.logger.info("Print devices as text")
            self.print_txt_list(heading)
            print()
        elif disp_action == 3:
            self.logger.info("Print devices as text")
            devsdict = self.make_json()
            json_reader = TangoJsonReader(
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
            )
            json_reader.print_txt_quick()
        else:
            self.logger.info("Print devices as default (display action %d)", disp_action)
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

        self.logger.info("Print devices as JSON")
        devsdict = self.make_json()
        ydevsdict[self.tango_host] = devsdict
        if self.output_file is not None:
            self.logger.info("Write output file %s", self.output_file)
            with open(self.output_file, "a") as outf:
                outf.write(json.dumps(ydevsdict, indent=4))
        else:
            print(json.dumps(ydevsdict, indent=4))

    def print_markdown(self, disp_action: int) -> None:
        """
        Print in JSON format.

        :param disp_action: display control flag
        """
        devsdict: dict

        self.logger.info("Print devices as markdown")
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

        self.logger.info("Print devices as HTML")
        devsdict = self.make_json()
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
        devsdict: dict
        ydevsdict: dict = {}

        self.logger.info("Print devices as YAML")
        devsdict = self.make_json()
        ydevsdict[self.tango_host] = devsdict
        if self.output_file is not None:
            self.logger.info("Write output file %s", self.output_file)
            with open(self.output_file, "a") as outf:
                outf.write(yaml.dump(ydevsdict))
        else:
            print(yaml.dump(ydevsdict))

    def print_txt_list_attributes(self) -> None:
        """Print list of devices."""
        device: str
        lwid: int

        self.logger.info("List %d device attributes...", len(self.devices))
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

        self.logger.info("List %d device commands...", len(self.devices))
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

        self.logger.info("List %d device properties...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'PROPERTY':32}")
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].properties:
                    self.devices[device].read_config()
                    self.devices[device].print_list_property(lwid)
