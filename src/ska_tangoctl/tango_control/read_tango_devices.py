"""Read and display Tango stuff."""

import datetime
import json
import logging
import os
import re
import sys
import time
from typing import IO, Any

import numpy as np
import pandas as pd
import tango
import yaml
from typing_extensions import TextIO

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.progress_bar import progress_bar
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.tango_json import TangoJsonReader

FILE_MODE: str = "w"


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


class TangoctlDevices:
    """Compile a dictionary of available Tango devices."""

    logger: logging.Logger

    def __init__(  # noqa: C901s
        self,
        logger: logging.Logger,
        tango_host: str | None,
        output_file: str | None,
        timeout_millis: int | None,
        show_attrib: bool,
        show_cmd: bool,
        show_prop: bool,
        dev_status: dict,
        cfg_data: dict,
        tgo_name: str | None,
        uniq_cls: bool,
        reverse: bool,
        evrythng: bool,
        quiet_mode: bool,
        xact_match: bool,
        disp_action: DispAction,
        k8s_ctx: str | None,
        k8s_ns: str | None,
        tgo_attrib: str | None = None,
        tgo_cmd: str | None = None,
        tgo_prop: str | None = None,
        dev_count: int = 0,
    ):
        """
        Get a dictionary of devices.

        :param logger: logging handle
        :param tango_host: Tango database host
        :param output_file: output file name
        :param timeout_millis: Tango device timeout in milliseconds
        :param show_attrib: flag to read attributes
        :param show_cmd: flag to read commands
        :param show_prop: flag to read properties
        :param dev_status: dictionary with status stuff
        :param cfg_data: configuration data in JSON format
        :param tgo_name: filter device name
        :param uniq_cls: only read one device per class
        :param reverse: sort in reverse order
        :param evrythng: read devices regardless of ignore list
        :param quiet_mode: flag for displaying progress bars
        :param xact_match: flag for exact matches
        :param disp_action: output format
        :param k8s_ctx: K8S context
        :param k8s_ns: K8S namespace
        :param tgo_attrib: filter attribute name
        :param tgo_cmd: filter command name
        :param tgo_prop: filter property name
        :param dev_count: number of Tango device to read (for testing)
        :raises Exception: when database connect fails
        """
        self.logger = logger
        self.timeout_millis: int | None = timeout_millis
        self.prog_bar: bool
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.prog_bar = False
        else:
            self.prog_bar = not quiet_mode

        self.show_attrib: bool = show_attrib
        self.show_cmd: bool = show_cmd
        self.show_prop: bool = show_prop
        self.dev_status: dict = dev_status
        self.cfg_data = cfg_data
        self.reverse: bool = reverse
        self.xact_match: bool = xact_match
        self.disp_action = disp_action
        self.k8s_ctx: str | None = k8s_ctx
        self.k8s_ns: str | None = k8s_ns
        self.tgo_name: str | None = tgo_name
        self.tgo_attrib: str | None = tgo_attrib
        self.tgo_cmd: str | None = tgo_cmd
        self.tgo_prop: str | None = tgo_prop
        self.quiet_mode = quiet_mode
        self.uniq_cls: bool = uniq_cls
        self.evrythng: bool = evrythng
        self.outf: IO[Any] | TextIO
        if output_file is not None:
            self.logger.info("Write output file %s", output_file)
            self.outf = open(output_file, FILE_MODE)
        else:
            self.outf = sys.stdout
        if dev_count:
            self.dev_count = dev_count
        else:
            self.dev_count = sys.maxsize

        self.logger.debug("Configuration: %s", self.cfg_data)
        self.delimiter = self.cfg_data["delimiter"]
        self.run_commands = self.cfg_data["run_commands"]
        self.logger.debug("Run commands %s", self.run_commands)
        self.run_commands_name = self.cfg_data["run_commands_name"]
        self.list_items = self.cfg_data["list_items"]
        self.block_items = self.cfg_data["block_items"]
        self.logger.debug("Run commands with name %s", self.run_commands_name)

        self.start_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.start_perf = time.perf_counter()
        self.attribs_found: list = []
        self.tgo_space: str = ""
        self.dev_classes: list = []

        self.devices: dict = {}
        self.device_list: list

        # Set Tango database host
        self.tango_host: str | None
        if tango_host is not None:
            self.tango_host = tango_host
        else:
            self.tango_host = os.getenv("TANGO_HOST")
            if self.tango_host is None:
                self.logger.error("No host specified and TANGO_HOST not set")
                raise Exception("Could not set Tango database host")
        os.environ["TANGO_HOST"] = self.tango_host

        # Get high level Tango object which contains the link to the static database
        database: tango.Database
        try:
            database = tango.Database()
        except Exception as oerr:
            self.logger.warning("Could not connect to Tango database %s", self.tango_host)
            raise oerr
        self.logger.debug("Connect to Tango database %s", self.tango_host)

        # Read devices
        self.device_names: list = []
        exported_devices = sorted(database.get_device_exported("*").value_string, reverse=reverse)
        self.logger.debug("Found %d exported devices", len(exported_devices))
        device_name: str
        n_devs = 0
        for device_name in exported_devices:
            if not self.evrythng:
                chk_fail: bool = False
                for dev_chk in self.cfg_data["ignore_device"]:
                    chk_len: int = len(dev_chk)
                    if device_name[0:chk_len] == dev_chk:
                        chk_fail = True
                        break
                if chk_fail:
                    self.logger.info(
                        "Skip device : '%s' matches '%s'",
                        device_name,
                        self.cfg_data["ignore_device"],
                    )
                    continue
            if self.tgo_name:
                ichk: str = device_name.lower()
                if self.tgo_name not in ichk:
                    self.logger.info("Ignore device : %s", device_name)
                    continue
            n_devs += 1
            if n_devs > self.dev_count:
                self.logger.warning("Stop reading devices after %d", n_devs)
                break
            self.logger.debug("Add device : %s", device_name)
            self.device_names.append(device_name)
        self.logger.debug("Found %d device names", len(self.device_names))

    def read_devices_nodb(self) -> None:
        """Read a single device without database connection."""
        trl = f"tango://{self.tango_host}/{self.tgo_name}#dbase=no"
        new_dev = TangoctlDevice(
            self.logger,
            self.outf,
            self.timeout_millis,
            self.show_attrib,
            self.show_cmd,
            self.show_prop,
            self.dev_status,
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
        self.devices[self.tgo_name] = new_dev

    def read_devices(self) -> None:  # noqa: C901
        """Read all devices."""
        if self.tgo_name:
            self.tgo_name = self.tgo_name.lower()
        self.logger.info(
            "Read devices with name %s attribute %s command %s property %s...",
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
        )

        self.list_items = self.cfg_data["list_items"]
        self.logger.info("List items : %s", self.list_items)
        self.block_items = self.cfg_data["block_items"]
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.quiet_mode = True
        ndevs = len(self.device_names)
        self.logger.info("Reading %d devices (unique %s) -->", ndevs, self.uniq_cls)

        n: int = 0
        for device_name in progress_bar(
            self.device_names,
            not self.quiet_mode,
            prefix=f"Read {len(self.device_names)} exported devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            n += 1
            try:
                new_dev = TangoctlDevice(
                    self.logger,
                    self.outf,
                    self.timeout_millis,
                    self.show_attrib,
                    self.show_cmd,
                    self.show_prop,
                    self.dev_status,
                    device_name,
                    self.reverse,
                    self.xact_match,
                    self.list_items,
                    self.block_items,
                    self.tgo_attrib,
                    self.tgo_cmd,
                    self.tgo_prop,
                )
                if self.tgo_attrib:
                    attribs_found: list = new_dev.check_for_attribute(self.tgo_attrib)
                    if attribs_found:
                        self.logger.debug(
                            "Device %s matched attributes %s", device_name, attribs_found
                        )
                        self.devices[device_name] = new_dev
                    else:
                        self.logger.debug(
                            "Skip device %s (attribute %s not found)", device_name, self.tgo_attrib
                        )
                elif self.tgo_cmd:
                    cmds_found: list = new_dev.check_for_command(self.tgo_cmd)
                    if cmds_found:
                        self.logger.debug("Device %s matched commands %s", device_name, cmds_found)
                        self.devices[device_name] = new_dev
                    else:
                        self.logger.debug(
                            "Skip device %s (command %s not found)", device_name, self.tgo_cmd
                        )
                elif self.tgo_prop:
                    props_found: list = new_dev.check_for_property(self.tgo_prop)
                    if props_found:
                        self.logger.debug(
                            "Device %s matched properties %s", device_name, props_found
                        )
                        self.devices[device_name] = new_dev
                    else:
                        self.logger.debug(
                            "Skip device %s (property %s not found)", device_name, self.tgo_prop
                        )
                elif self.uniq_cls:
                    dev_class: str = new_dev.dev_class
                    if dev_class == "---":
                        self.logger.debug(
                            f"Skip device {device_name} with unknown class {dev_class}"
                        )
                    elif dev_class not in self.dev_classes:
                        self.dev_classes.append(dev_class)
                        self.devices[device_name] = new_dev
                    else:
                        self.logger.debug(
                            f"Skip device {device_name} with known class {dev_class}"
                        )
                else:
                    self.logger.debug("Add device %s", device_name)
                    self.devices[device_name] = new_dev
            except Exception as e:
                self.logger.warning("%s", e)
                self.devices[device_name] = None
        self.logger.debug("Read %d devices", len(self.devices))

    def get_classes(self) -> dict:
        """
        Print list of device names.

        :return: dictionary with class and device names
        """
        self.logger.info("Listing classes of %d devices...", len(self.devices))
        klasses: dict = {}
        for device in self.devices:
            klass = self.devices[device].dev_class
            dev_name = self.devices[device].dev_name
            if klass not in klasses:
                klasses[klass] = []
            klasses[klass].append(dev_name)
        rdict: dict = {"classes": [], "tango_host": self.tango_host}
        for klass in klasses:
            rdict["classes"].append({"name": klass, "devices": klasses[klass]})
        self.logger.debug("Classes: %s", rdict)
        return rdict

    def read_attribute_values(self) -> None:
        """Read device attribute values."""
        self.logger.info("Reading attribute values of %d devices -->", len(self.devices))
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
        self.logger.info("Reading commands of %d devices -->", len(self.devices))
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
        self.logger.info("Reading properties of %d devices -->", len(self.devices))
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
        if not (self.dev_status or self.show_attrib or self.show_cmd or self.show_prop):
            self.logger.info("Reading basic information...")
        if self.dev_status and not self.show_attrib:
            self.logger.info("Reading status of devices...")
        if self.show_attrib:
            self.read_attribute_values()
        if self.show_cmd:
            self.logger.info("Reading command values from devices...")
            self.read_command_values()
        if self.show_prop:
            self.logger.info("Read property values from devices...")
            self.read_property_values()
        # self.logger.info("Read values for %d devices", len(self.devices))

    def read_configs(self) -> None:
        """Read additional data."""
        self.logger.info("Reading %d basic device configs -->", len(self.devices))
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

    def read_configs_all(self) -> None:
        """Read additional data."""
        self.logger.info("Reading %d device configs -->", len(self.devices))
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

    def make_json_short(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devs_list: list = []
        self.logger.info("Reading %d devices in short JSON format -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} JSON records :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.logger.debug("Read device %s: %s", device, self.devices[device])
            if self.devices[device] is not None:
                devs_list.append(self.devices[device].make_json_short())
        self.logger.debug("Read %d devices in short JSON format: %s", len(self.devices), devs_list)
        return {"devices": devs_list}

    def make_json(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devs_list: list = []
        self.logger.info("Reading %d devices in JSON format -->", len(self.devices))
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
        return {"devices": devs_list}

    def print_names_list(self) -> None:
        """Print list of device names."""
        self.logger.info("Listing %d device names...", len(self.device_names))
        print(f"Devices : {len(self.device_names)}")
        for device_name in self.device_names:
            print(f"\t{device_name}")

    '''
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
    '''

    def print_classes(self) -> None:
        """Print list of device names."""
        self.logger.info("Listing classes of %d devices...", len(self.devices))
        klasses: dict = {}
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
        self.logger.info("List %d basic devices in text format...", len(self.devices))
        if heading is not None:
            print(f"{heading}")
        print(f"Tango host : {os.getenv('TANGO_HOST')}")
        self.print_txt_heading(self.outf)
        for device in self.devices:
            if self.devices[device] is not None:
                self.devices[device].print_list()
            else:
                print(f"{device} (N/A)", file=self.outf)
        print(file=self.outf)

    def print_txt_short(self) -> None:
        """Print devices as text."""
        self.logger.info("Print devices as text (short)...")
        devsdict = self.make_json()
        json_reader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.outf
        )
        json_reader.print_txt_short()

    def print_txt_all(self) -> None:
        """Print devices as text."""
        self.logger.info("Print devices as text (all)...")
        devsdict = self.make_json()
        json_reader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.outf
        )
        if not self.quiet_mode:
            print("\n\n", file=self.outf)
        json_reader.print_txt_all()

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
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.outf
            )
            json_reader.print_txt_short()
        else:
            self.logger.info("Print devices (display action %s)...", disp_action)
            devsdict = self.make_json()
            json_reader = TangoJsonReader(
                self.logger, not self.prog_bar, self.tgo_space, devsdict, self.outf
            )
            if not self.quiet_mode:
                print("\n\n")
            json_reader.print_txt_all()

    def print_json_short(self, disp_action: DispAction) -> None:
        """
        Print in shortened JSON format.

        :param disp_action: display control flag
        """
        self.logger.info("Print devices as short JSON...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "timeout_millis": self.timeout_millis,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"context": self.k8s_ctx})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        ydevsdict.update(self.make_json_short())
        print(json.dumps(ydevsdict, indent=4, cls=NumpyEncoder), file=self.outf)

    def print_json(self, disp_action: DispAction) -> None:
        """
        Print in JSON format.

        :param disp_action: display control flag
        """
        self.logger.info("Print devices as JSON...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "timeout_millis": self.timeout_millis,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"context": self.k8s_ctx})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        ydevsdict.update(self.make_json())
        print(json.dumps(ydevsdict, indent=4, cls=NumpyEncoder), file=self.outf)

    def print_json_table(self) -> None:
        """Print in JSON format."""
        # TODO this is not much use and needs more work
        self.logger.info("Print devices as JSON table...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "timeout_millis": self.timeout_millis,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"context": self.k8s_ctx})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        ydevsdict.update(self.make_json())
        # df = pd.json_normalize(ydevsdict["devices"])
        # df.set_index(["name"], inplace=True)
        df = pd.DataFrame.from_dict(ydevsdict["devices"])
        print(df.head(10), file=self.outf)

    def print_markdown(self) -> None:
        """Print in JSON format."""
        self.logger.info("Print devices as markdown...")
        devsdict: dict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.outf
        )
        json_reader.print_markdown_all()

    def print_html(self, disp_action: DispAction) -> None:
        """
        Print in HTML format.

        :param disp_action: display control flag
        """
        self.logger.info("Print devices as HTML...")
        devsdict: dict = self.make_json()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger, not self.prog_bar, self.tgo_space, devsdict, self.outf
        )
        if disp_action.check(DispAction.TANGOCTL_LIST):
            json_reader.print_html_all(True)
        else:
            json_reader.print_html_quick(True)

    def print_yaml_short(self, disp_action: DispAction) -> None:
        """
        Print in short YAML format.

        :param disp_action: display control flag
        """
        self.logger.info("Print devices as short YAML...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "start_time": self.start_now,
            "timeout_millis": self.timeout_millis,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"context": self.k8s_ctx})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        ydevsdict.update(self.make_json_short())
        # Serialize a Python object into a YAML stream
        print(yaml.dump(ydevsdict), file=self.outf)

    def print_yaml(self, disp_action: DispAction) -> None:
        """
        Print in YAML format.

        :param disp_action: display control flag
        """
        self.logger.info("Print devices as YAML...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "start_time": self.start_now,
            "timeout_millis": self.timeout_millis,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"context": self.k8s_ctx})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        ydevsdict.update(self.make_json())
        # Serialize a Python object into a YAML stream
        print(yaml.dump(ydevsdict), file=self.outf)

    def print_txt_list_attributes(self, show_val: bool = True) -> None:
        """
        Print list of devices as plain text.

        :param show_val: print value
        """
        device: str
        lwid: int

        self.logger.info("List %d device attributes...", len(self.devices))
        lwid = self.print_txt_heading(self.outf, "")
        print(f" {'ATTRIBUTE':32}")
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].attributes:
                    self.devices[device].read_config()
                    self.devices[device].print_list_attribute(lwid, show_val)

    def print_txt_heading(self, outf: IO[Any] | TextIO, eol: str = "\n") -> int:
        """
        Print heading for list of devices.

        :param eol: printed at the end
        :param outf: output file stream
        :return: width of characters printed
        """
        line_width: int

        self.logger.info("List headings")
        print(f"\n{'DEVICE NAME':64} ", end="", file=self.outf)
        line_width = 65
        for attribute in self.list_items["attributes"]:
            field_name = attribute.upper()
            field_width = self.list_items["attributes"][attribute]
            line_width += int(re.sub(r"\D", "", field_width)) + 1
            print(f"{field_name:{field_width}} ", end="", file=self.outf)
        for command in self.list_items["commands"]:
            field_name = command.upper()
            field_width = self.list_items["commands"][command]
            line_width += int(re.sub(r"\D", "", field_width)) + 1
            print(f"{field_name:{field_width}} ", end="", file=self.outf)
        for tproperty in self.list_items["properties"]:
            field_name = tproperty.upper()
            field_width = self.list_items["properties"][tproperty]
            line_width += int(re.sub(r"\D", "", field_width)) + 1
            print(f"{field_name:{field_width}} ", end="", file=self.outf)
        print(f"{'CLASS':32}", end=eol, file=self.outf)
        line_width += 32
        return line_width

    def print_txt_list_commands(self, show_val: bool = True) -> None:
        """
        Print list of device commands.

        :param show_val: print value
        """
        device: str
        lwid: int

        self.logger.info("List %d device commands...", len(self.devices))
        lwid = self.print_txt_heading(self.outf, "")
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

        self.logger.info("List %d device properties...", len(self.devices))
        lwid = self.print_txt_heading(self.outf, "")
        print(f" {'PROPERTY':32}", file=self.outf)
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].properties:
                    self.devices[device].read_config()
                    self.devices[device].print_list_property(lwid, show_val)

    def read_attribute_names(self) -> dict:
        """
        Read device data.

        :return: dictionary of devices
        """
        the_attribs: dict = {}
        self.logger.info("Reading attribute names of %d devices -->", len(self.devices))
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
        self.logger.info("Reading command names of %d devices -->", len(self.devices))
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
        self.logger.info("Reading property names of %d devices -->", len(self.devices))
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

    def __del__(self) -> None:
        """Desctructor."""
        self.logger.debug("Shut down TangoctlDevices...")
        if self.outf != sys.stdout:
            self.outf.close()
