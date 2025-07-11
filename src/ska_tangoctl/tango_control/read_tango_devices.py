"""Read and display Tango stuff."""

import datetime
import json
import logging
import os
import re
import sys
import time
from typing import Any

import numpy as np
import pandas as pd
import tango
import yaml

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.progress_bar import progress_bar
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice
from ska_tangoctl.tango_control.tango_json import TangoJsonReader

try:
    from ska_tangoctl.k8s_info.get_k8s_info import KubernetesInfo
except ModuleNotFoundError:
    KubernetesInfo = None  # type: ignore[assignment,misc]

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
        outf: Any,
        timeout_millis: int | None,
        dev_status: dict,
        cfg_data: dict,
        tgo_name: str | None,
        uniq_cls: bool,
        disp_action: DispAction,
        k8s_ctx: str | None,
        k8s_cluster: str | None,
        k8s_ns: str | None,
        domain_name: str | None,
        tgo_attrib: str | None = None,
        tgo_cmd: str | None = None,
        tgo_prop: str | None = None,
        tgo_class: str | None = None,
        dev_count: int = 0,
    ):
        """
        Get a dictionary of devices.

        :param logger: logging handle
        :param tango_host: Tango database host
        :param outf: output file pointer
        :param timeout_millis: Tango device timeout in milliseconds
        :param dev_status: dictionary with status stuff
        :param cfg_data: configuration data in JSON format
        :param tgo_name: filter device name
        :param uniq_cls: only read one device per class
        :param disp_action: output format
        :param k8s_ctx: K8S context
        :param k8s_cluster: K8S cluster
        :param k8s_ns: K8S namespace
        :param domain_name: K8S domain name
        :param tgo_attrib: filter attribute name
        :param tgo_cmd: filter command name
        :param tgo_prop: filter property name
        :param tgo_class: filter class name
        :param dev_count: number of Tango device to read (for testing)
        :raises Exception: when database connect fails
        """
        self.logger = logger
        self.disp_action = disp_action
        self.timeout_millis: int | None = timeout_millis
        self.prog_bar: bool
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.prog_bar = False
        else:
            self.prog_bar = not self.disp_action.quiet_mode

        self.dev_status: dict = dev_status
        self.cfg_data = cfg_data
        self.k8s_ctx: str | None = k8s_ctx
        self.k8s_cluster: str | None = k8s_cluster
        self.k8s_ns: str | None = k8s_ns
        self.domain_name: str | None = domain_name
        self.tgo_name: str | None = tgo_name
        self.tgo_attrib: str | None = tgo_attrib
        self.tgo_cmd: str | None = tgo_cmd
        self.tgo_prop: str | None = tgo_prop
        self.tgo_class: str | None = tgo_class
        if self.tgo_class is not None:
            self.tgo_class = self.tgo_class.lower()
        self.uniq_cls: bool = uniq_cls
        self.outf: Any = outf
        if dev_count:
            self.dev_count = dev_count
        else:
            self.dev_count = sys.maxsize

        self.logger.debug("Devices configuration : %s", self.cfg_data)
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
        self.good_pods: dict = {}
        self.bad_pods: dict = {}

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
        exported_devices = sorted(
            database.get_device_exported("*").value_string, reverse=self.disp_action.reverse
        )
        self.logger.debug("Found %d exported devices", len(exported_devices))
        device_name: str
        n_devs = 0
        for device_name in exported_devices:
            if not self.disp_action.evrythng:
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
                    self.logger.info("Ignore device : %s (not '%s')", self.tgo_name, ichk)
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
            self.disp_action,
            self.outf,
            self.timeout_millis,
            self.dev_status,
            trl,
            self.list_items,
            self.block_items,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
            self.k8s_ctx,
            self.domain_name,
            indent=self.disp_action.indent,
        )
        self.devices[self.tgo_name] = new_dev

    def read_device_hosts(self) -> list:
        """Compile a list of hosts."""
        hosts: list = []
        db = tango.Database()
        for host_name in self.bad_pods:
            self.logger.info(
                "Reading IP address of host %s running devices %s",
                host_name,
                ",".join(self.bad_pods[host_name]),
            )
            host: dict = {}
            host["name"] = host_name
            host["devices"] = []
            host["addresses"] = []
            for device_name in self.bad_pods[host_name]:
                device_info: tango.DbDevFullInfo = db.get_device_info(device_name)
                host["devices"].append(
                    {
                        "name": device_name,
                        "class_name": device_info.class_name,
                        "ds_full_name": device_info.ds_full_name,
                        "exported": device_info.exported,
                        "ior": device_info.ior,
                        "pid": device_info.pid,
                        "started_date": device_info.started_date,
                        "stopped_date": device_info.stopped_date,
                        "version": device_info.version,
                    }
                )
                if not host["addresses"]:
                    ip_addrs: list = []
                    k8s: KubernetesInfo = KubernetesInfo(self.logger, self.k8s_ctx)
                    pod_name = "ska-tango-base-itango-console"
                    exec_command = ["catior", device_info.ior]
                    if self.k8s_ns is not None:
                        ior = k8s.exec_command(self.k8s_ns, pod_name, exec_command)
                        host["catior"] = ior.split("\n")
                        for line in ior.split("\n"):
                            self.logger.debug("%s", line)
                            if "IIOP" in line:
                                ip_addr = line.split(" ")[3]
                                ip_addrs.append(ip_addr)
                        host["addresses"] = ip_addrs
            hosts.append(host)
        return hosts

    def read_devices(self) -> None:  # noqa: C901
        """Read all devices."""
        if self.tgo_name:
            self.tgo_name = self.tgo_name.lower()
        self.logger.info(
            "Reading devices with name %s attribute %s command %s property %s...",
            self.tgo_name,
            self.tgo_attrib,
            self.tgo_cmd,
            self.tgo_prop,
        )

        self.list_items = self.cfg_data["list_items"]
        self.logger.info("List items : %s", self.list_items)
        self.block_items = self.cfg_data["block_items"]
        if self.logger.getEffectiveLevel() in (logging.DEBUG, logging.INFO):
            self.disp_action.quiet_mode = True
        ndevs = len(self.device_names)
        self.logger.info("Reading %d devices (unique %s) -->", ndevs, self.uniq_cls)

        dev_class: str
        n: int = 0
        for device_name in progress_bar(
            self.device_names,
            not self.disp_action.quiet_mode,
            prefix=f"Read {len(self.device_names)} exported devices :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            n += 1
            try:
                new_dev = TangoctlDevice(
                    self.logger,
                    self.disp_action,
                    self.outf,
                    self.timeout_millis,
                    self.dev_status,
                    device_name,
                    self.list_items,
                    self.block_items,
                    self.tgo_attrib,
                    self.tgo_cmd,
                    self.tgo_prop,
                    self.k8s_ctx,
                    self.domain_name,
                    indent=self.disp_action.indent,
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
                elif self.tgo_class:
                    dev_class = new_dev.dev_class.lower()
                    if self.tgo_class == dev_class:
                        self.logger.debug(
                            "Device %s matched class %s", device_name, self.tgo_class
                        )
                        self.devices[device_name] = new_dev
                    else:
                        self.logger.debug("Skip device %s with class %s", device_name, dev_class)
                elif self.uniq_cls:
                    dev_class = new_dev.dev_class
                    if dev_class == "---":
                        self.logger.debug(
                            "Skip device %s with unknown class %s", device_name, dev_class
                        )
                    elif dev_class not in self.dev_classes:
                        self.dev_classes.append(dev_class)
                        self.devices[device_name] = new_dev
                    else:
                        self.logger.debug(
                            "Skip device %s with known class %s", device_name, dev_class
                        )
                else:
                    self.logger.debug("Add device %s", device_name)
                    self.devices[device_name] = new_dev
            except Exception as e:
                self.logger.warning("Could not instantiate device %s: %s", device_name, e)
                self.devices[device_name] = None
        self.logger.info("Read %d devices", len(self.devices))

    def get_classes(self) -> dict:
        """
        Print list of device names.

        :return: dictionary with class and device names
        """
        self.logger.info("Getting classes of %d devices...", len(self.devices))
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
        self.logger.info("Got classes of %d devices...", len(self.devices))
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

    def read_procs(self) -> None:
        """Read device processes."""
        rc: int
        pod_name: str | None
        self.logger.info("Reading processes for %d devices -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} processes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is None:
                self.logger.warning("Device is empty")
                return
            dev: TangoctlDevice = self.devices[device]
            if dev.info is not None:
                pod_name = dev.info.server_host
                if pod_name in self.bad_pods:
                    self.logger.info("Skip bad pod %s", pod_name)
                    continue
            else:
                pod_name = None
            rc = dev.read_procs(self.k8s_ns)
            if rc:
                self.bad_pods[pod_name] = []
                self.bad_pods[pod_name].append(device)

    def read_pods(self) -> None:
        """Read device pods."""
        rc: int
        pod_name: str | None
        self.logger.info("Reading pods for %d devices -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} processes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                dev: TangoctlDevice = self.devices[device]
                if dev.info is not None:
                    pod_name = dev.info.server_host
                    if pod_name in self.bad_pods:
                        self.logger.info("Skip bad pod %s", pod_name)
                        continue
                else:
                    pod_name = None
                if pod_name is not None:
                    rc = dev.read_pod(self.k8s_ns)
                    if rc:
                        if pod_name not in self.good_pods:
                            self.good_pods[pod_name] = {
                                "api_version": "N/A",
                                "kind": "N/A",
                                "metadata": {"name": pod_name, "namespace": self.k8s_ns},
                            }
                        self.bad_pods[pod_name] = []
                        self.bad_pods[pod_name].append(device)
                    if pod_name not in self.good_pods:
                        self.good_pods[pod_name] = dev.pod_desc

    def read_logs(self) -> None:
        """Read device logs."""
        rc: int
        pod_name: str | None
        self.logger.info("Reading logs for %d devices -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} processes :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                dev: TangoctlDevice = self.devices[device]
                pod_name = dev.info.server_host
                if pod_name in self.bad_pods:
                    self.logger.info("Skip bad pod %s", pod_name)
                    continue
                dev.read_procs(self.k8s_ns)
                rc = dev.read_pod(self.k8s_ns)
                if rc:
                    self.bad_pods[pod_name] = device
                    continue
                if pod_name not in self.good_pods:
                    self.good_pods[pod_name] = []
                self.good_pods[pod_name].append(dev.pod_desc)

    def read_device_values(self) -> None:
        """Read device values."""
        self.logger.debug("Reading device values: %s", self.disp_action.show())
        if not (
            self.dev_status
            or self.disp_action.show_attrib
            or self.disp_action.show_cmd
            or self.disp_action.show_prop
        ):
            self.logger.info("Reading basic information...")
            # TODO do something here
        if self.dev_status and not self.disp_action.show_attrib:
            self.logger.info("Reading status of devices...")
            # TODO do something here
        if self.disp_action.show_attrib:
            self.logger.info("Reading attribute values...")
            self.read_attribute_values()
        if self.disp_action.show_cmd:
            self.logger.info("Reading command values from devices...")
            self.read_command_values()
        if self.disp_action.show_prop:
            self.logger.info("Read property values from devices...")
            self.read_property_values()
        if self.disp_action.show_proc:
            self.logger.info("Read processes running on host...")
            self.read_procs()
        if self.disp_action.show_pod:
            self.logger.info("Read pods...")
            self.read_pods()
        else:
            self.logger.debug("Skip pods...")
        if self.disp_action.show_log:
            self.logger.info("Read K8S logs...")
            self.read_logs()
        # self.logger.info("Read values for %d devices", len(self.devices))

    def read_configs(self) -> None:
        """Read additional data."""
        self.logger.debug("Reading %d device configs -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            not self.disp_action.quiet_mode,
            prefix=f"Read {len(self.devices)} device configs :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                dev: TangoctlDevice = self.devices[device]
                dev.read_config()
        self.logger.info("Read %d device configs -->", len(self.devices))

    def read_configs_all(self) -> None:
        """Read additional data."""
        self.logger.debug("Reading all %d device configs -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            not self.disp_action.quiet_mode,
            prefix=f"Read {len(self.devices)} device configs :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                self.devices[device].read_config_all()
        self.logger.info("Read all %d device configs -->", len(self.devices))

    def make_devices_json_small(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devs_list: list = []
        self.logger.info("Reading %d devices in JSON small format -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} JSON records :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            self.logger.debug("Reading device %s", device)
            if self.devices[device] is not None:
                dev = self.devices[device]
                devs_list.append(dev.make_json_small())
        self.logger.debug("Read %d devices in JSON small format: %s", len(self.devices), devs_list)
        return {"devices": devs_list}

    def make_devices_json_medium(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devs_list: list = []
        self.logger.info("Reading %d devices in JSON medium format -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} JSON records :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                dev = self.devices[device]
                devs_list.append(dev.make_json_medium())
        self.logger.debug(
            "Read %d devices in JSON medium format: %s", len(self.devices), devs_list
        )
        return {"devices": devs_list}

    def make_devices_json_large(self) -> dict:
        """
        Read device data.

        :return: dictionary
        """
        devs_list: list = []
        self.logger.info("Reading %d devices in JSON large format -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            self.prog_bar,
            prefix=f"Read {len(self.devices)} JSON records :",
            suffix="complete",
            decimals=0,
            length=100,
        ):
            if self.devices[device] is not None:
                dev = self.devices[device]
                devs_list.append(dev.make_json_large())
        self.logger.debug("Read %d devices in JSON large format: %s", len(self.devices), devs_list)
        return {"devices": devs_list}

    # def make_devices_json(self) -> dict:
    #     """
    #     Read device data.
    #
    #     :return: dictionary
    #     """
    #     devs_list: list = []
    #     self.logger.info("Reading %d devices in JSON format -->", len(self.devices))
    #     for device in progress_bar(
    #         self.devices,
    #         self.prog_bar,
    #         prefix=f"Read {len(self.devices)} JSON records :",
    #         suffix="complete",
    #         decimals=0,
    #         length=100,
    #     ):
    #         if self.devices[device] is not None:
    #             dev = self.devices[device]
    #             devs_list.append(dev.make_json())
    #     self.logger.debug("Read %d devices in JSON format: %s", len(self.devices), devs_list)
    #     return {"devices": devs_list}

    def print_names_list(self) -> None:
        """Print list of device names."""
        self.logger.info("Listing %d device names...", len(self.device_names))
        print(f"Devices : {len(self.device_names)}", file=self.outf)
        for device_name in self.device_names:
            print(f"\t{device_name}", file=self.outf)

    def print_classes(self) -> None:
        """Print list of device names."""
        self.logger.info("Printing classes of %d devices...", len(self.devices))
        klasses: dict = {}
        for device in self.devices:
            klass = self.devices[device].dev_class
            dev_name = self.devices[device].dev_name
            if klass not in klasses:
                klasses[klass] = []
            klasses[klass].append(dev_name)
        print(f"Classes : {len(klasses)}", file=self.outf)
        for klass in klasses:
            print(f"\t{klass} : ", file=self.outf)
            for dev_name in klasses[klass]:
                print(f"\t\t{dev_name}", file=self.outf)

    def print_txt_list(self, heading: str | None = None) -> None:
        """
        Print list of devices.

        :param heading: print at the top
        """
        self.logger.info("Listing %d basic devices in text format...", len(self.devices))
        if heading is not None:
            print(f"{heading}", file=self.outf)
        print(f"Tango host : {os.getenv('TANGO_HOST')}", file=self.outf)
        self.print_txt_heading()
        for device in self.devices:
            if self.devices[device] is not None:
                self.devices[device].print_list()
            else:
                print(f"{device} (N/A)", file=self.outf)
        print(file=self.outf)

    def print_txt_small(self) -> None:
        """Print devices as text."""
        self.logger.info("Print devices as text (short)...")
        devsdict = self.make_devices_json_small()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger,
            self.disp_action.indent,
            not self.prog_bar,
            self.tgo_space,
            devsdict,
            self.outf,
        )
        json_reader.print_txt_small()

    def print_txt_medium(self) -> None:
        """Print devices as text."""
        self.logger.info("Printing devices as text (all)...")
        devsdict = self.make_devices_json_medium()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger,
            self.disp_action.indent,
            not self.prog_bar,
            self.tgo_space,
            devsdict,
            self.outf,
        )
        if not self.disp_action.quiet_mode:
            print("\n\n", file=self.outf)
        json_reader.print_txt_medium()

    def print_txt_large(self) -> None:
        """Print devices as text."""
        self.logger.info("Printing devices as text (all)...")
        devsdict = self.make_devices_json_large()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger,
            self.disp_action.indent,
            not self.prog_bar,
            self.tgo_space,
            devsdict,
            self.outf,
        )
        if not self.disp_action.quiet_mode:
            print("\n\n", file=self.outf)
        json_reader.print_txt_large()

    def print_txt(self, heading: str | None = None) -> None:
        """
        Print in text format.

        :param heading: to be printed on the top
        """
        devsdict: dict
        json_reader: TangoJsonReader

        if self.disp_action.check(DispAction.TANGOCTL_LIST):
            self.logger.info("Printing devices as text (list)...")
            self.print_txt_list(heading)
            print(file=self.outf)
        elif self.disp_action.size == "S":
            self.logger.info("Printing devices as text (small)...")
            devsdict = self.make_devices_json_small()
            json_reader = TangoJsonReader(
                self.logger,
                self.disp_action.indent,
                not self.prog_bar,
                self.tgo_space,
                devsdict,
                self.outf,
            )
            json_reader.print_txt_small()
        elif self.disp_action.size == "L":
            self.logger.info("Printing devices as text (large)...")
            devsdict = self.make_devices_json_large()
            json_reader = TangoJsonReader(
                self.logger,
                self.disp_action.indent,
                not self.prog_bar,
                self.tgo_space,
                devsdict,
                self.outf,
            )
            json_reader.print_txt_large()
        else:
            self.logger.info("Printing devices (display action %s)...", self.disp_action)
            devsdict = self.make_devices_json_medium()
            json_reader = TangoJsonReader(
                self.logger,
                self.disp_action.indent,
                not self.prog_bar,
                self.tgo_space,
                devsdict,
                self.outf,
            )
            if not self.disp_action.quiet_mode:
                print("\n\n", file=self.outf)
            json_reader.print_txt_medium()

    def print_json_small(self) -> None:
        """Print in shortened JSON format."""
        self.logger.info("Printing devices as small JSON...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "timeout_millis": self.timeout_millis,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"active_context": self.k8s_ctx})
        if self.k8s_cluster is not None:
            ydevsdict.update({"active_ccluster": self.k8s_cluster})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        if self.domain_name is not None:
            ydevsdict.update({"domain_name": self.domain_name})
        ydevsdict.update(self.make_devices_json_small())
        pods_list: list = []
        for good_pod in self.good_pods:
            pod = self.good_pods[good_pod]
            containers_lst: list = []
            containers = pod["spec"]["containers"]
            for container in containers:
                container_dict = {
                    "name": container["name"],
                    "command": container["command"],
                    "args": container["args"],
                    "resources": container["resources"],
                }
                containers_lst.append(container_dict)
            pod_dict: dict = {
                "api_version": pod["api_version"],
                "kind": pod["kind"],
                "metadata": {
                    "name": pod["metadata"]["name"],
                    "namespace": pod["metadata"]["namespace"],
                },
                "spec": {
                    "containers": containers_lst,
                    "hostname": pod["spec"]["hostname"],
                },
                "status": {
                    "host_ip": pod["status"]["host_ip"],
                    "pod_ip": pod["status"]["pod_ip"],
                    "phase": pod["status"]["phase"],
                    "start_time": pod["status"]["start_time"],
                },
            }
            pods_list.append(pod_dict)
        ydevsdict.update({"pods": pods_list})
        if not self.disp_action.indent:
            self.disp_action.indent = 4
        print(
            json.dumps(ydevsdict, indent=self.disp_action.indent, cls=NumpyEncoder, default=str),
            file=self.outf,
        )

    def print_json_medium(self) -> None:
        """Print in JSON medium format."""
        self.logger.info("Printing devices as medium JSON...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "timeout_millis": self.timeout_millis,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"active_context": self.k8s_ctx})
        if self.k8s_cluster is not None:
            ydevsdict.update({"active_cluster": self.k8s_cluster})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        if self.domain_name is not None:
            ydevsdict.update({"domain_name": self.domain_name})
        ydevsdict.update(self.make_devices_json_medium())
        pods_list: list = []
        for good_pod in self.good_pods:
            pod = self.good_pods[good_pod]
            containers_lst: list = []
            containers = pod["spec"]["containers"]
            for container in containers:
                volume_mounts: list = []
                for volume_mount in container["volume_mounts"]:
                    volume_mounts.append(
                        {
                            "name": volume_mount["name"],
                            "mount_path": volume_mount["mount_path"],
                            "sub_path": volume_mount["sub_path"],
                            "read_only": volume_mount["read_only"],
                        }
                    )
                container_dict = {
                    "name": container["name"],
                    "command": container["command"],
                    "args": container["args"],
                    "env": container["env"],
                    "ports": container["ports"],
                    "resources": container["resources"],
                    "volume_mounts": volume_mounts,
                }
                containers_lst.append(container_dict)
            pod_dict: dict = {
                "api_version": pod["api_version"],
                "kind": pod["kind"],
                "metadata": {
                    "creation_timestamp": pod["metadata"]["creation_timestamp"],
                    "labels": pod["metadata"]["labels"],
                    "name": pod["metadata"]["name"],
                    "namespace": pod["metadata"]["namespace"],
                },
                "spec": {
                    "containers": containers_lst,
                    "hostname": pod["spec"]["hostname"],
                    "restart_policy": pod["spec"]["restart_policy"],
                },
                "status": {
                    "host_ip": pod["status"]["host_ip"],
                    "pod_ip": pod["status"]["pod_ip"],
                    "phase": pod["status"]["phase"],
                    "start_time": pod["status"]["start_time"],
                },
            }
            pods_list.append(pod_dict)
        ydevsdict.update({"pods": pods_list})
        hosts: list = self.read_device_hosts()
        ydevsdict.update({"hosts": hosts})
        if not self.disp_action.indent:
            self.disp_action.indent = 4
        print(
            json.dumps(ydevsdict, indent=self.disp_action.indent, cls=NumpyEncoder, default=str),
            file=self.outf,
        )

    def print_json_large(self) -> None:
        """Print in JSON format."""
        self.logger.info("Printing devices as large JSON...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "timeout_millis": self.timeout_millis,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"active_context": self.k8s_ctx})
        if self.k8s_cluster is not None:
            ydevsdict.update({"active_cluster": self.k8s_cluster})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        if self.domain_name is not None:
            ydevsdict.update({"domain_name": self.domain_name})
        ydevsdict.update(self.make_devices_json_large())
        pods_list: list = []
        for good_pod in self.good_pods:
            pods_list.append(self.good_pods[good_pod])
        ydevsdict.update({"pods": pods_list})
        hosts: list = self.read_device_hosts()
        ydevsdict.update({"hosts": hosts})
        if not self.disp_action.indent:
            self.disp_action.indent = 4
        print(
            json.dumps(ydevsdict, indent=self.disp_action.indent, cls=NumpyEncoder, default=str),
            file=self.outf,
        )

    def print_json(self) -> None:
        """Print in JSON format."""
        if self.disp_action.size == "L":
            self.print_json_large()
        elif self.disp_action.size == "S":
            self.print_json_small()
        else:
            self.print_json_medium()

    def print_json_table(self) -> None:
        """Print in JSON format."""
        # TODO this is not much use and needs more work
        self.logger.debug("Printing devices as JSON table...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "timeout_millis": self.timeout_millis,
            "start_time": self.start_now,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"active_context": self.k8s_ctx})
        if self.k8s_cluster is not None:
            ydevsdict.update({"active_cluster": self.k8s_cluster})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        if self.domain_name is not None:
            ydevsdict.update({"domain_name": self.domain_name})
        ydevsdict.update(self.make_devices_json_large())
        ydevsdict.update({"pods": self.good_pods})
        # df = pd.json_normalize(ydevsdict["devices"])
        # df.set_index(["name"], inplace=True)
        df = pd.DataFrame.from_dict(ydevsdict["devices"])
        print(df.head(10), file=self.outf)
        self.logger.info("Printed devices as JSON table...")

    def print_markdown(self) -> None:
        """Print in JSON format."""
        self.logger.debug("Printing devices as markdown...")
        devsdict: dict = self.make_devices_json_large()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger,
            self.disp_action.indent,
            not self.prog_bar,
            self.tgo_space,
            devsdict,
            self.outf,
        )
        json_reader.print_markdown_large()
        self.logger.info("Printed %d devices as markdown...", len(devsdict))

    def print_html(self) -> None:
        """Print in HTML format."""
        self.logger.debug("Printing devices as HTML...")
        devsdict: dict = self.make_devices_json_large()
        json_reader: TangoJsonReader = TangoJsonReader(
            self.logger,
            self.disp_action.indent,
            not self.prog_bar,
            self.tgo_space,
            devsdict,
            self.outf,
        )
        if self.disp_action.size == "L":
            json_reader.print_html_large(True)
        elif self.disp_action.size == "M":
            json_reader.print_html_large(True)
        else:
            json_reader.print_html_small(True)
        self.logger.info("Printed %d devices as HTML...", len(devsdict))

    def print_yaml_small(self) -> None:
        """Print in YAML small format."""
        self.logger.debug("Printing devices as small YAML...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "start_time": self.start_now,
            "timeout_millis": self.timeout_millis,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"active_context": self.k8s_ctx})
        if self.k8s_cluster is not None:
            ydevsdict.update({"active_cluster": self.k8s_cluster})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        if self.domain_name is not None:
            ydevsdict.update({"domain_name": self.domain_name})
        ydevsdict.update(self.make_devices_json_small())
        ydevsdict.update({"pods": self.good_pods})
        # Serialize a Python object into a YAML stream
        print(yaml.dump(ydevsdict, indent=self.disp_action.indent), file=self.outf)
        self.logger.info("Printed devices as small YAML...")

    def print_yaml_medium(self) -> None:
        """Print in YAML medium format."""
        self.logger.debug("Printing devices as medium YAML...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "start_time": self.start_now,
            "timeout_millis": self.timeout_millis,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"active_context": self.k8s_ctx})
        if self.k8s_cluster is not None:
            ydevsdict.update({"active_cluster": self.k8s_cluster})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        if self.domain_name is not None:
            ydevsdict.update({"domain_name": self.domain_name})
        ydevsdict.update(self.make_devices_json_medium())
        ydevsdict.update({"pods": self.good_pods})
        # Serialize a Python object into a YAML stream
        print(yaml.dump(ydevsdict, indent=self.disp_action.indent), file=self.outf)
        self.logger.info("Printed devices as medium YAML...")

    def print_yaml_large(self) -> None:
        """Print in YAML large format."""
        self.logger.debug("Printing devices as large YAML...")
        ydevsdict: dict = {
            "tango_host": self.tango_host,
            "start_time": self.start_now,
            "timeout_millis": self.timeout_millis,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_time": float(f"{(time.perf_counter() - self.start_perf):.3e}"),
        }
        if self.k8s_ctx is not None:
            ydevsdict.update({"active_context": self.k8s_ctx})
        if self.k8s_cluster is not None:
            ydevsdict.update({"active_cluster": self.k8s_cluster})
        if self.k8s_ns is not None:
            ydevsdict.update({"namespace": self.k8s_ns})
        if self.domain_name is not None:
            ydevsdict.update({"domain_name": self.domain_name})
        ydevsdict.update(self.make_devices_json_large())
        ydevsdict.update({"pods": self.good_pods})
        # Serialize a Python object into a YAML stream
        print(yaml.dump(ydevsdict, indent=self.disp_action.indent), file=self.outf)
        self.logger.info("Printed devices as large YAML...")

    def print_yaml(self) -> None:
        """Print in YAML format."""
        if self.disp_action.size == "S":
            self.print_yaml_small()
        elif self.disp_action.size == "M":
            self.print_yaml_medium()
        else:
            self.print_yaml_large()

    def print_txt_list_attributes(self, show_val: bool = True) -> None:
        """
        Print list of devices as plain text.

        :param show_val: print value
        """
        device: str
        lwid: int

        self.logger.debug("Listing %d device attributes...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'ATTRIBUTE':32}", file=self.outf)
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].attributes:
                    self.devices[device].read_config()
                    self.devices[device].print_list_attribute(lwid, show_val)
        self.logger.info("Listed %d device attributes...", len(self.devices))

    def print_txt_heading(self, eol: str = "\n") -> int:
        """
        Print heading for list of devices.

        :param eol: printed at the end
        :return: width of characters printed
        """
        line_width: int

        self.logger.debug("Listing headings")
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
        self.logger.info("Listed headings")
        return line_width

    def print_txt_list_commands(self, show_val: bool = True) -> None:
        """
        Print list of device commands.

        :param show_val: print value
        """
        device: str
        lwid: int

        self.logger.debug("Listing %d device commands...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'COMMAND':32}", file=self.outf)
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].commands:
                    self.devices[device].read_config()
                    self.devices[device].print_list_command(lwid, show_val)
        self.logger.info("Listed %d device commands...", len(self.devices))

    def print_txt_list_properties(self, show_val: bool = True) -> None:
        """
        Print list of device properties.

        :param show_val: print value
        """
        device: str

        self.logger.debug("Listing %d device properties...", len(self.devices))
        lwid = self.print_txt_heading("")
        print(f" {'PROPERTY':32}", file=self.outf)
        for device in self.devices:
            if self.devices[device] is not None:
                if self.devices[device].properties:
                    self.devices[device].read_config()
                    self.devices[device].print_list_property(lwid, show_val)
        self.logger.info("Listed %d device properties...", len(self.devices))

    def read_attribute_names(self) -> dict:
        """
        Read device data.

        :return: dictionary of devices
        """
        the_attribs: dict = {}
        self.logger.debug("Reading attribute names of %d devices -->", len(self.devices))
        for device in progress_bar(
            self.devices,
            not self.disp_action.quiet_mode,
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
        self.logger.info("Read attribute names of %d devices: %s", len(the_attribs), the_attribs)
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
            not self.disp_action.quiet_mode,
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
        self.logger.info("Read command names of %d devices: %s", len(the_commands), the_commands)
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
            not self.disp_action.quiet_mode,
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
