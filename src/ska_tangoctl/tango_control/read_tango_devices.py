"""Read and display Tango stuff."""

import datetime
import json
import logging
import os
import time

import tango
import yaml

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.progress_bar import progress_bar
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.read_tango_devices_basic import NumpyEncoder, TangoctlDevicesBasic
from ska_tangoctl.tango_control.tango_json import TangoJsonReader


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
        xact_match: bool = False,
        disp_action: DispAction = DispAction(DispAction.TANGOCTL_JSON),
        k8s_ns: str | None = None,
        nodb: bool = False,
    ):
        """
        Get a dictionary of devices.

        :param logger: logging handle
        :param show_attrib: flag to read attributes
        :param show_cmd: flag to read commands
        :param show_prop: flag to read properties
        :param show_status: dictionary with status stuff
        :param cfg_data: configuration data in JSON format
        :param tgo_name: filter device name
        :param uniq_cls: only read one device per class
        :param reverse: sort in reverse order
        :param evrythng: read devices regardless of ignore list
        :param tgo_attrib: filter attribute name
        :param tgo_cmd: filter command name
        :param tgo_prop: filter property name
        :param quiet_mode: flag for displaying progress bars
        :param output_file: output file name
        :param xact_match: flag for exact matches
        :param disp_action: output format
        :param k8s_ns: K8S namespace
        :param nodb: flag to run without database
        :raises Exception: when database connect fails
        """
        super().__init__(
            logger,
            show_attrib,
            show_cmd,
            show_prop,
            show_status,
            cfg_data,
            tgo_name,
            uniq_cls,
            reverse,
            evrythng,
            disp_action,
            quiet_mode,
            xact_match,
            None,
        )
        self.start_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.start_perf = time.perf_counter()
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
        self.block_items: dict
        self.k8s_ns = k8s_ns
        self.tgo_name: str | None = tgo_name
        self.tgo_attrib: str | None = tgo_attrib
        self.tgo_cmd: str | None = tgo_cmd
        self.tgo_prop: str | None = tgo_prop

        self.cfg_data = cfg_data
        self.output_file = output_file
        self.logger.debug(
            "Read devices %s : attribute %s command %s property %s...",
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
        )
        # Get Tango database host
        self.tango_host = os.getenv("TANGO_HOST")

        self.logger.debug("Configuration: %s", self.cfg_data)
        self.delimiter = self.cfg_data["delimiter"]
        self.run_commands = self.cfg_data["run_commands"]
        self.logger.debug("Run commands %s", self.run_commands)
        self.run_commands_name = self.cfg_data["run_commands_name"]
        self.list_items = self.cfg_data["list_items"]
        self.block_items = self.cfg_data["block_items"]
        self.logger.debug("Run commands with name %s", self.run_commands_name)
        self.prog_bar = not quiet_mode

        if nodb:
            trl = f"tango://{self.tango_host}/{tgo_name}#dbase=no"
            new_dev = TangoctlDevice(
                self.logger,
                self.show_attrib,
                self.show_cmd,
                self.show_prop,
                self.show_status,
                trl,
                not self.prog_bar,
                self.reverse,
                self.list_items,
                self.block_items,
                self.tgo_attrib,
                self.tgo_cmd,
                self.tgo_prop,
                self.xact_match,
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
            self.logger.debug("Reading %d devices available -->", len(device_list))

            if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
                self.prog_bar = False
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
                        self.block_items,
                        tgo_attrib,
                        tgo_cmd,
                        tgo_prop,
                        xact_match,
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
        self.logger.debug("Shut down TangoctlDevices for host %s...", tango_host)

    def read_attribute_values(self) -> None:
        """Read device attribute values."""
        self.logger.debug("Reading attribute values of %d devices -->", len(self.devices))
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
        """Read device commands."""
        self.logger.debug("Reading commands of %d devices -->", len(self.devices))
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
        """Read device properties."""
        self.logger.debug("Reading properties of %d devices -->", len(self.devices))
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
        """Read device values."""
        if not (self.show_status or self.show_attrib or self.show_cmd or self.show_prop):
            self.logger.info("Reading basic information...")
        if self.show_status and not self.show_attrib:
            self.logger.info("Reading status of devices...")
        if self.show_attrib:
            self.logger.info("Reading attribute values from devices...")
            self.read_attribute_values()
        if self.show_cmd:
            self.logger.info("Reading command values from devices...")
            self.read_command_values()
        if self.show_prop:
            self.logger.info("Read property values from devices...")
            self.read_property_values()
        # self.logger.info("Read values for %d devices", len(self.devices))

    def read_configs_all(self) -> None:
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
                self.devices[device].read_config_all()

    def make_json(self) -> list:
        """
        Read device data.

        :return: list
        """
        devs_list: list = []
        self.logger.debug("Reading %d devices in JSON format -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} JSON records :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                devs_list.append(self.devices[device].make_json())
        self.logger.debug("Read %d devices in JSON format: %s", len(self.devices), devs_list)
        return devs_list

    def print_names_list(self) -> None:
        """Print list of device names."""
        self.logger.debug("Listing %d device names...", len(self.devices))
        print(f"Devices : {len(self.devices)}")
        for device in self.devices:
            print(f"\t{device}")

    def get_classes(self) -> dict:
        """
        Print list of device names.

        :return: dictionary with class and device names
        """
        self.logger.debug("Listing classes of %d devices...", len(self.devices))
        klasses: dict = {}
        for device in self.devices:
            klass = self.devices[device].dev_class
            dev_name = self.devices[device].dev_name
            if klass not in klasses:
                klasses[klass] = []
            klasses[klass].append(dev_name)
        rdict: dict = {"classes": [], "namespace": self.k8s_ns, "tango_host": self.tango_host}
        for klass in klasses:
            rdict["classes"].append({"name": klass, "devices": klasses[klass]})
        self.logger.debug("Classes: %s", rdict)
        return rdict

    def print_classes(self) -> None:
        """Print list of device names."""
        self.logger.debug("Listing classes of %d devices...", len(self.devices))
        klasses = {}
        for device in self.devices:
            klass = self.devices[device].dev_class
            dev_name = self.devices[device].dev_name
            if klass not in klasses:
                klasses[klass] = []
            klasses[klass].append(dev_name)
        print(f"Classes : {len(klasses)}")
        for klass in klasses:
            print(f"\t{klass} : ")
            for dev_name in klasses[klass]:
                print(f"\t\t{dev_name}")

    def print_txt_list(self, heading: str | None = None) -> None:
        """
        Print list of devices.

        :param heading: print at the top
        """
        self.logger.debug("Listing %d devices...", len(self.devices))
        for device in self.devices:
            print(f"\t{device}")

    def print_txt(self, disp_action: DispAction, heading: str | None = None) -> None:
        """
        Print in text format.

        :param disp_action: display control flag
        :param heading: to be printed on the top
        """
        devsdict: dict
        json_reader: TangoJsonReader

        if disp_action.check(DispAction.TANGOCTL_LIST):
            self.logger.info("Print devices as text (list)...")
            self.print_txt_list(heading)
            print()
        elif disp_action.check(DispAction.TANGOCTL_SHORT):
            self.logger.info("Print devices as text (short)...")
            devsdict = self.make_json()
            json_reader = TangoJsonReader(
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
            )
            json_reader.print_txt_quick()
        else:
            self.logger.info("Print devices (display action %s)...", disp_action)
            devsdict = self.make_json()
            json_reader = TangoJsonReader(
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
            )
            if not self.quiet_mode:
                print("\n\n")
            json_reader.print_txt_all()

    def print_json(self, disp_action: DispAction) -> None:
        """
        Print in JSON format.

        :param disp_action: display control flag
        """
        self.logger.debug("Print devices as JSON...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "namespace": self.k8s_ns,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": time.perf_counter() - self.start_perf,
            "devices": self.make_json(),
        }
        if self.output_file is not None:
            self.logger.debug("Write output file %s", self.output_file)
            with open(self.output_file, "a") as outf:
                outf.write(json.dumps(ydevsdict, indent=4, cls=NumpyEncoder))
        else:
            print(json.dumps(ydevsdict, indent=4, cls=NumpyEncoder))

    def print_markdown(self) -> None:
        """Print in JSON format."""
        self.logger.debug("Print devices as markdown...")
        devsdict: dict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
        )
        json_reader.print_markdown_all()

    def print_html(self, disp_action: DispAction) -> None:
        """
        Print in HTML format.

        :param disp_action: display control flag
        """
        self.logger.debug("Print devices as HTML...")
        devsdict: dict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.output_file
        )
        if disp_action.check(DispAction.TANGOCTL_LIST):
            json_reader.print_html_all(True)
        else:
            json_reader.print_html_quick(True)

    def print_yaml(self, disp_action: DispAction) -> None:
        """
        Print in YAML format.

        :param disp_action: display control flag
        """
        self.logger.debug("Print devices as YAML...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "namespace": self.k8s_ns,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": time.perf_counter() - self.start_perf,
            "devices": self.make_json(),
        }
        # Serialize a Python object into a YAML stream
        if self.output_file is not None:
            self.logger.debug("Write output file %s", self.output_file)
            with open(self.output_file, "a") as outf:
                outf.write(yaml.dump(ydevsdict))
        else:
            print(yaml.dump(ydevsdict))

    def print_txt_list_attributes(self, show_val: bool = True) -> None:
        """
        Print list of devices as plain text.

        :param show_val: print value
        """
        device: str
        lwid: int

        self.logger.debug("List %d device attributes...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'ATTRIBUTE':32}")
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].attributes:
                    self.devices[device].read_config()
                    self.devices[device].print_list_attribute(lwid, show_val)

    def print_txt_list_commands(self, show_val: bool = True) -> None:
        """
        Print list of device commands.

        :param show_val: print value
        """
        device: str
        lwid: int

        self.logger.debug("List %d device commands...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'COMMAND':32}")
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].commands:
                    self.devices[device].read_config()
                    self.devices[device].print_list_command(lwid, show_val)

    def print_txt_list_properties(self, show_val: bool = True) -> None:
        """
        Print list of device properties.

        :param show_val: print value
        """
        device: str

        self.logger.debug("List %d device properties...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'PROPERTY':32}")
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].properties:
                    self.devices[device].read_config()
                    self.devices[device].print_list_property(lwid, show_val)
