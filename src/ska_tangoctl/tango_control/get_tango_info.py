"""Read information from Tango database."""

import json
import logging
import socket
import time
from typing import Any, Tuple

import numpy
import tango
from ska_control_model import AdminMode

from ska_mid_itf_engineering_tools.ska_jargon.ska_jargon import find_jargon  # type: ignore

PFIX1 = 17
PFIX2 = 33
PFIX3 = 50


def check_tango(tango_fqdn: str, tango_port: int = 10000) -> int:
    """
    Check Tango host address.

    :param tango_fqdn: fully qualified domain name
    :param tango_port: port number
    :return: error condition
    """
    try:
        tango_addr = socket.gethostbyname_ex(tango_fqdn)
        tango_ip = tango_addr[2][0]
    except socket.gaierror as e:
        print("Could not read address %s : %s" % (tango_fqdn, e))
        return 1
    print(f"TANGO_HOST={tango_fqdn}:{tango_port}")
    print(f"TANGO_HOST={tango_ip}:{tango_port}")
    return 0


def check_device(dev: tango.DeviceProxy) -> bool:
    """
    Check if device is online.

    :param dev: device handle
    :return: true when device is OK
    """
    try:
        dev.ping()
        return True
    except Exception:
        return False


class TangoDeviceInfo:
    """Read and display information about Tango device."""

    def __init__(  # noqa: C901
        self,
        logger: logging.Logger,
        cfg_data: Any,
        device_name: str,
    ):
        """
        Display Tango device.

        :param logger: logging handle
        :param cfg_data: configuration
        :param device_name: device name
        """
        # Connect to device proxy
        self.logger = logger
        self.dev: tango.DeviceProxy = tango.DeviceProxy(device_name)
        # Read state
        try:
            self.dev_state = self.dev.State()
            self.dev_str = f"{repr(self.dev_state).split('.')[3]}"
        except Exception:
            self.dev_state = None
            self.dev_str = "N/A"
        try:
            self.dev_name = self.dev.name()
            self.online = True
        except Exception:
            self.dev_name = device_name
            self.online = False
        try:
            self.dev_class = self.dev.info().dev_class
        except Exception:
            self.dev_class = "N/A"
        # self.evrythng = evrythng
        self.on_dev_count = 0
        self.ignore = cfg_data["ignore_device"]
        self.run_commands = cfg_data["run_commands"]
        self.run_commands_name = cfg_data["run_commands_name"]
        self.adminMode: int | None = None
        try:
            self.adminMode = self.dev.adminMode
        except AttributeError:
            self.adminMode = None
        self.logger.debug(
            "Admin mode: %d %s (%s)", self.adminMode, str(self.adminMode), type(self.adminMode)
        )
        self.adminModeStr: str = ""
        if self.adminMode is None:
            self.adminModeStr = "N/A"
        elif type(self.adminMode) is bool:
            if self.adminMode:
                self.adminModeStr = "OFFLINE"
            else:
                self.adminModeStr = "ONLINE"
        else:
            try:
                self.adminModeStr = str(self.adminMode).split(".")[1]
            except IndexError:
                self.logger.error("Could not read admin mode '%s'", str(self.adminMode))
                self.adminModeStr = str(self.adminMode)
        try:
            self.version = self.dev.versionId
        except AttributeError:
            self.version = "N/A"

    def check_device(self) -> bool:
        """
        Check if device is online.

        :return: true when device is OK
        """
        try:
            self.dev.ping()
            return True
        except Exception:
            return False

    def device_state(self) -> None:
        """Display status information for Tango device."""
        print(f"Device {self.dev_name}")
        if not self.online:
            return
        print(f"\tAdmin mode                     : {self.adminMode}")
        print(f"\tDevice status                  : {self.dev.Status()}")
        print(f"\tDevice state                   : {self.dev.State()}")
        try:
            print(f"\tObservation state              : {repr(self.dev.obsState)}")
            show_obs_state(self.dev.obsState)
        except AttributeError:
            self.logger.info("Device %s does not have an observation state", self.dev_name)
        print(f"versionId                        : {self.dev.versionId}")
        print(f"build State                      : {self.dev.buildState}")
        print(f"logging level                    : {self.dev.loggingLevel}")
        print(f"logging Targets                  : {self.dev.loggingTargets}")
        print(f"health State                     : {self.dev.healthState}")
        print(f"control Mode                     : {self.dev.controlMode}")
        print(f"simulation Mode                  : {self.dev.simulationMode}")
        print(f"test Mode                        : {self.dev.testMode}")
        print(f"long Running Commands In Queue   : {self.dev.longRunningCommandsInQueue}")
        print(f"long Running Command IDs InQueue : {self.dev.longRunningCommandIDsInQueue}")
        print(f"long Running Command Status      : {self.dev.longRunningCommandStatus}")
        print(f"long Running Command Progress    : {self.dev.longRunningCommandProgress}")
        print(f"long Running Command Result      : {self.dev.longRunningCommandResult}")

    def get_tango_admin(self) -> bool:
        """
        Read admin mode for Tango device.

        :return: True when device is in admin mode
        """
        csp_admin = self.dev.adminMode
        if csp_admin == AdminMode.ONLINE:
            print("Device admin mode online")
            return False
        if csp_admin == AdminMode.OFFLINE:
            print("Device admin mode offline")
        else:
            print(f"Device admin mode {csp_admin}")
        return True

    def set_tango_admin(self, dev_adm: bool, sleeptime: int = 2) -> bool:
        """
        Write admin mode for a Tango device.

        :param dev_adm: admin mode flag
        :param sleeptime: seconds to sleep
        :return: True when device is in admin mode
        """
        print(f"*** Set Adminmode to {dev_adm} and check state ***")
        if dev_adm:
            self.dev.adminMode = 1
        else:
            self.dev.adminMode = 0
        time.sleep(sleeptime)
        return self.get_tango_admin()

    def get_command(self, cmd: str, args: Any = None) -> Any:
        """
        Run command and get output.

        :param cmd: command name
        :param args: arguments for command
        :return: output of command
        """
        try:
            if args:
                self.logger.debug("Run command %s %s", cmd, args)
                inout = self.dev.command_inout(cmd, args)
            else:
                self.logger.debug("Run command %s", cmd)
                inout = self.dev.command_inout(cmd)
        except tango.DevFailed as terr:
            return f"<ERROR> \033[3m{terr.args[0].desc.strip()}\033[0m"
        if type(inout) is list:
            inout = str(inout[0])
        else:
            inout = str(inout)
        self.logger.debug("Command out <%s>", inout)
        if "\n" in inout:
            ios = str(inout).split("\n")
            rval = ios[0]
            for io in ios[1:]:
                rval += f"\n{' ':{PFIX3}} {io.strip()}"
        else:
            rval = inout
        self.logger.debug("Command return <%s>", rval)
        return rval

    def show_device_command_short(self, prefix: str, cmd: Any, fmt: str = "txt") -> None:
        """
        Print info on device command.

        :param prefix: print at front of line
        :param cmd: command name
        :param fmt: output format
        """
        print(f"{prefix} \033[1m{cmd:30}\033[0m", end="")
        if cmd in self.run_commands:
            cmd_io = self.get_command(cmd)
            if type(cmd_io) is list:
                lpre2 = "\n" + f"{' ':51}"
                cmd_val = lpre2.join(cmd_io)
            else:
                cmd_val = cmd_io
            print(f" {cmd_val}")
        elif cmd in self.run_commands_name:
            cmd_io = self.get_command(cmd, self.dev_name)
            print(f" {cmd_io}")
        else:
            print(" N/A")

    def show_device_command_full(self, prefix: str, cmd: Any, fmt: str = "txt") -> None:
        """
        Print info on device command.

        :param prefix: print at front of line
        :param cmd: command name
        :param fmt: output format
        """
        lpre = "\n" + f"{' ':55}"
        if cmd.cmd_name in self.run_commands:
            cmd_io = self.get_command(cmd.cmd_name)
            if type(cmd_io) is list:
                lpre2 = "\n" + f"{' ':51}"
                cmd_val = lpre2.join(cmd_io)
            else:
                cmd_val = cmd_io
            print(f" {cmd_val}")
        elif cmd.cmd_name in self.run_commands_name:
            cmd_io = self.get_command(cmd.cmd_name, self.dev_name)
            print(f" {cmd_io}")
        else:
            print(" N/A")
        # Polling status
        if self.dev.is_command_polled(cmd.cmd_name):
            print(f"{prefix:{PFIX3}} Polled     ")
        else:
            print(f"{prefix:{PFIX3}} Not polled ")
        # Input type description
        in_type_desc = cmd.in_type_desc
        if in_type_desc != "Uninitialised":
            if "\n" in in_type_desc:
                in_type_desc = in_type_desc[:-1].replace("\n", lpre)
            print(f"{prefix:{PFIX3}} IN  {in_type_desc}")
        # Output type description
        out_type_desc = cmd.out_type_desc
        if out_type_desc != "Uninitialised":
            if "\n" in out_type_desc:
                out_type_desc = out_type_desc[:-1].replace("\n", lpre)
            print(f"{prefix:{PFIX3}} OUT {out_type_desc}")

    def show_device_commands(self) -> None:
        """Print commands."""
        try:
            cmds = self.dev.get_command_config()
        except Exception:
            cmds = []
        if cmds:
            cmd = cmds[0]
            print(f"{'Commands':{PFIX1}} : \033[1m{cmd.cmd_name:30}\033[0m", end="")
            self.show_device_command_full(" ", cmd)
            for cmd in cmds[1:]:
                print(f"{' ':{PFIX1}}   \033[1m{cmd.cmd_name:30}\033[0m", end="")
                self.show_device_command_full(" ", cmd)

    def show_attribute_value_scalar(  # noqa: C901
        self, prefix: str, attrib_value: Any, fmt: str = "txt"
    ) -> None:
        """
        Print attribute scalar value.

        :param prefix: data prefix string
        :param attrib_value: attribute value
        :param fmt: output format
        """
        json_fmt = True
        try:
            attrib_json = json.loads(attrib_value)
        except Exception:
            attrib_json = {}
            json_fmt = False
        self.logger.debug("Scalar %s : %s", type(attrib_value), attrib_value)
        if not json_fmt:
            attrib_value = str(attrib_value)
            if "\n" in attrib_value:
                attrib_values = attrib_value.split("\n")
                print(f" '{attrib_values[0]}'")
                for attrib_val in attrib_values[1:]:
                    print(f"{prefix} '{attrib_val.strip()}'")
            else:
                print(f" '{attrib_value}'")
            return
        if type(attrib_json) is dict:
            if not attrib_json:
                print(" {}")
                return
            n = 0
            for value in attrib_json:
                print("")
                attr_value = attrib_json[value]
                if type(attr_value) is list:
                    for item in attr_value:
                        if type(item) is dict:
                            print(f"{prefix} {value} :")
                            for key in item:
                                print(f"{prefix+'    '} {key} : {item[key]}")
                        else:
                            print(f"{prefix+'    '} {item}")
                elif type(attr_value) is dict:
                    print(f"{prefix} {value}")
                    for key in attr_value:
                        key_value = attr_value[key]
                        if not key_value:
                            print(f"{prefix+'    '} {key} ?")
                        elif type(key_value) is str:
                            if key_value[0] == "{":
                                print(f"{prefix+'    '} {key} : DICT{key_value}")
                            else:
                                print(f"{prefix+'    '} {key} : STR{key_value}")
                        else:
                            print(f"{prefix+'    '} {key} : {key_value}")
                else:
                    print(f"{prefix} {value} : {attr_value}")
                n += 1
        elif type(attrib_json) is list:
            print(f" {attrib_value[0]}")
            for attrib_val in attrib_value[1:]:
                print(f"{prefix+'     '} {attrib_val}")
        elif type(attrib_value) is str:
            print(f" {attrib_value}")
        else:
            print(f" '{attrib_value}' (type {type(attrib_value)})")

    def show_attribute_value_spectrum(  # noqa: C901
        self, prefix: str, attrib_value: Any, fmt: str = "txt"
    ) -> None:  # noqa: C901
        """
        Print attribute spectrum value.

        :param prefix: data prefix string
        :param attrib_value: attribute value
        :param fmt: output format
        """
        self.logger.debug("Spectrum %s : %s", type(attrib_value), attrib_value)
        if type(attrib_value) is dict:
            if attrib_value:
                int_models = json.loads(attrib_value)  # type: ignore[arg-type]
                for key in int_models:
                    print(f"{prefix}   {key}")
                    int_model_values = int_models[key]
                    if type(int_model_values) is dict:
                        for value in int_model_values:
                            print(f"{prefix+'     '} {value} : {int_model_values[value]}")
                    else:
                        print(f"{prefix+'     '} {int_model_values}")
            else:
                print(" {}")
        elif type(attrib_value) is tuple:
            if attrib_value:
                a_val = attrib_value[0]
                if not a_val:
                    a_val = "''"
                print(f" {a_val}")
                for a_val in attrib_value[1:]:
                    if not a_val:
                        a_val = "''"
                    print(f"{prefix} {a_val}")
            else:
                print(" ()")
        elif type(attrib_value) is list:
            if attrib_value:
                print(f" {attrib_value[0]}")
                for attrib_val in attrib_value[1:]:
                    print(f"{prefix+'     '} {attrib_val}")
            else:
                print(" []")
        elif type(attrib_value) is numpy.ndarray:
            a_list = attrib_value.tolist()
            if a_list:
                print(f" {a_list[0]}")
                for a_val in a_list[1:]:
                    print(f"{prefix} {a_val}")
            else:
                print(" []")
        elif type(attrib_value) is str:
            print(f" {attrib_value}")
        elif attrib_value is None:
            print(" N/A")
        else:
            print(f" {type(attrib_value)}:{attrib_value}")

    def show_attribute_value_other(self, prefix: str, attrib_value: Any, fmt: str = "txt") -> None:
        """
        Print some other format.

        :param prefix: start of string
        :param attrib_value: attribute value
        :param fmt: output format
        """
        self.logger.debug("Attribute value %s : %s", type(attrib_value), attrib_value)
        if type(attrib_value) is numpy.ndarray:
            a_list = attrib_value.tolist()
            if a_list:
                print(f" {a_list[0]}")
                for a_val in a_list[1:]:
                    print(f"{prefix} {a_val}")
            else:
                print(" []")
        elif type(attrib_value) is tuple:
            if attrib_value:
                print(f" {attrib_value[0]}")
                for attrib_val in attrib_value[1:]:
                    print(f"{prefix} {attrib_val}")
            else:
                print(" ()")
        else:
            print(f" {attrib_value}")

    def read_attribute_value(self, attrib: str) -> Any:
        """
        Print attribute value.

        :param attrib: attribute name
        :return: attribute value
        """
        try:
            attrib_value = self.dev.read_attribute(attrib).value
        except tango.DevFailed as terr:
            print(f" <ERROR> \033[3m{terr.args[0].desc.strip()}\033[0m")
            attrib_value = None
        except Exception:
            print(" <could not be read>")
            attrib_value = None
        self.logger.debug("Read %s value : %s", attrib, attrib_value)
        return attrib_value

    def show_attribute_value(
        self, attrib: str, prefix: str, dry_run: bool, fmt: str = "txt"
    ) -> Any:  # noqa: C901
        """
        Print attribute value.

        :param attrib: attribute name
        :param prefix: data prefix string
        :param dry_run: skip reading values
        :param fmt: output format
        """
        if not dry_run:
            attrib_value = self.read_attribute_value(attrib)
        else:
            print(" <N/A>")
            attrib_value = None
        try:
            attrib_cfg = self.dev.get_attribute_config(attrib)
        except tango.ConnectionFailed:
            print(" <connection failed>")
            return
        data_format = attrib_cfg.data_format
        if not dry_run and attrib_value is not None:
            # pylint: disable-next=c-extension-no-member
            if data_format == tango._tango.AttrDataFormat.SCALAR:
                self.show_attribute_value_scalar(prefix, attrib_value)
            # pylint: disable-next=c-extension-no-member
            elif data_format == tango._tango.AttrDataFormat.SPECTRUM:
                self.show_attribute_value_spectrum(prefix, attrib_value)
            else:
                self.show_attribute_value_other(prefix, attrib_value)
        return attrib_value

    def show_attribute_config(
        self, attrib: str, prefix: str, dry_run: bool, attrib_value: Any, fmt: str = "txt"
    ) -> None:  # noqa: C901
        """
        Print attribute configuration.

        :param attrib: attribute name
        :param prefix: data prefix string
        :param dry_run: skip reading values
        :param attrib_value: attribute value
        :param fmt: output format
        """
        if self.dev.is_attribute_polled(attrib):
            print(f"{prefix} Polled")
        else:
            print(f"{prefix} Not polled")
        attrib_cfg = self.dev.get_attribute_config(attrib)
        events = attrib_cfg.events.arch_event.archive_abs_change
        print(f"{prefix} Event change : {events}")
        if not dry_run and attrib_value is not None:
            try:
                print(f"{prefix} Quality : {self.dev.read_attribute(attrib).quality}")
            except tango.ConnectionFailed:
                print(f"{prefix} Quality : <connection failed>")
        else:
            print(f"{prefix} Quality : <N/A>")

    def show_device_attributes(self, dry_run: bool, fmt: str) -> None:
        """
        Print attributes.

        :param dry_run: flag to skip reading of values
        :param fmt: output format
        """
        try:
            attribs = sorted(self.dev.get_attribute_list())
        except Exception:
            attribs = []
        if attribs:
            attrib = attribs[0]
            prefix = " " * 50
            print(f"{'Attributes':{PFIX1}} : \033[1m{attrib:30}\033[0m", end="")
            attrib_value = self.show_attribute_value(attrib, prefix, dry_run)
            self.show_attribute_config(attrib, prefix, dry_run, attrib_value)
            for attrib in attribs[1:]:
                print(f"{' ':{PFIX1}}   \033[1m{attrib:30}\033[0m", end="")
                attrib_value = self.show_attribute_value(attrib, prefix, dry_run)
                self.show_attribute_config(attrib, prefix, dry_run, attrib_value)

    def show_device_attributes_short(self, dry_run: bool, fmt: str) -> None:
        """
        Print attributes.

        :param dry_run: flag to skip reading of values
        :param fmt: output format
        """
        try:
            attribs = sorted(self.dev.get_attribute_list())
        except Exception:
            attribs = []
        if attribs:
            if dry_run:
                print(f"{'Attributes':{PFIX1}} : \033[1m{attribs[0]}\033[0m")
                for attrib in attribs[1:]:
                    print(f"{' ':{PFIX1}}   \033[1m{attrib}\033[0m")
                return
            attrib = attribs[0]
            prefix = " " * PFIX3
            print(f"{'Attributes':{PFIX1}} : \033[1m{attrib:30}\033[0m", end="")
            self.show_attribute_value(attrib, prefix, dry_run)
            for attrib in attribs[1:]:
                print(f"{' ':{PFIX1}}   \033[1m{attrib:30}\033[0m", end="")
                self.show_attribute_value(attrib, prefix, dry_run)

    def _show_property(self, props: list, fmt: str = "txt") -> None:  # noqa: C901
        """
        Display properties.

        :param props: properties
        :param fmt: output format
        """
        prop = props[0]
        prop_values = self.dev.get_property(prop)
        prop_list = prop_values[prop]
        if len(prop_list) == 1:
            print(f"{'Properties':{PFIX1}} : \033[1m{prop:30}\033[0m {prop_list[0]}")
        elif len(prop_list[0]) > 30 and len(prop_list[1]) > 30:
            print(f"{'Properties':{PFIX1}} : \033[1m{prop:30}\033[0m {prop_list[0]}")
            for prop_val in prop_list[1:]:
                print(f"{' ':{PFIX1}}   {' ':30} {prop_val}")
        else:
            print(
                f"{'Properties':{PFIX1}} : \033[1m{prop:30}\033[0m {prop_list[0]} "
                f" {prop_list[1]}"
            )
            n = 2
            while n < len(prop_list):
                print(f"{' ':{PFIX1}}   {' ':30} {prop_list[n]}  {prop_list[n+1]}")
                n += 2
        for prop in props[1:]:
            prop_values = self.dev.get_property(prop)
            prop_list = prop_values[prop]
            if len(prop_list) == 1:
                print(f"{' ':{PFIX1}}   \033[1m{prop:30}\033[0m {prop_list[0]}")
            elif len(prop_list[0]) > 30 and len(prop_list[1]) > 30:
                print(f"{' ':{PFIX1}}   \033[1m{prop:30}\033[0m {prop_list[0]}")
                for prop_val in prop_list[1:]:
                    print(f"{' ':{PFIX1}}   {' ':30} {prop_val}")
            else:
                print(f"{' ':{PFIX1}}   \033[1m{prop:30}\033[0m {prop_list[0]}  {prop_list[1]}")
                n = 2
                while n < len(prop_list):
                    prop1 = prop_list[n]
                    try:
                        prop2 = prop_list[n + 1]
                    except IndexError:
                        prop2 = ""
                    print(f"{' ':{PFIX1}}   {' ':30} {prop1}  {prop2}")
                    n += 2

    def _show_device_properties(self, prefix: str, dry_run: bool, fmt: str) -> None:  # noqa: C901
        """
        Print properties.

        :param prefix: start of line
        :param dry_run: flag to skip reading of values
        :param fmt: output format
        """
        try:
            props = sorted(self.dev.get_property_list("*"))
        except Exception as terr:
            self.logger.info(f"{terr}")
            props = []
        if dry_run:
            prop = props[0]
            print(f"{'Properties':{PFIX1}} : \033[1m{prop:30}\033[0m")
            for prop in props[1:]:
                print(f"{' ':{PFIX1}}   \033[1m{prop:30}\033[0m")
            return
        if len(props) == 1:
            prop = props[0]
            prop_values = self.dev.get_property(prop)
            prop_list = prop_values[prop]
            print(f"{'Properties':{PFIX1}} : \033[1m{prop:30}\033[0m {prop_list[0]}")
        elif props:
            self._show_property(props)
        else:
            print(f"{'Properties':{PFIX1}} : <NONE>")

    def _show_device_query(self, fmt: str) -> int:  # noqa: C901
        """
        Display Tango device in text format.

        :param fmt: output format
        :return: one if device is on, otherwise zero
        """
        rv = 1
        # pylint: disable-next=c-extension-no-member
        print(f"{'Device':{PFIX1}} : {self.dev_name}", end="")
        if not self.online:
            print(" <error>")
            return 0
        try:
            cmds = self.dev.get_command_list()
        except Exception:
            cmds = []
        print(f" {len(cmds)} \033[3mcommands\033[0m,", end="")
        try:
            attribs = sorted(self.dev.get_attribute_list())
        except Exception:
            attribs = []
        print(f" {len(attribs)} \033[1mattributes\033[0m")
        if self.adminMode is not None:
            print(f"{'Admin mode':{PFIX1}} : {self.adminMode}")
        dev_info = self.dev.info()
        if "State" in cmds:
            print(f"{'State':{PFIX1}} : {self.dev.State()}")
        if "Status" in cmds:
            dev_status = self.dev.Status().replace("\n", f"\n{' ':20}")
            print(f"{'Status':{PFIX1}} : {dev_status}")
        print(f"{'Description':{PFIX1}} : {self.dev.description()}")
        jargon = find_jargon(self.dev_name)
        if jargon:
            print(f"{'Acronyms':{PFIX1}} : {jargon}")
        print(f"{'Device class':{PFIX1}} : {dev_info.dev_class}")
        print(f"{'Server host':{PFIX1}} : {dev_info.server_host}")
        print(f"{'Server ID':{PFIX1}} : {dev_info.server_id}")
        if "DevLockStatus" in cmds:
            print(f"{'Lock status':{PFIX1}} : {self.dev.DevLockStatus(self.dev_name)}")
        if "DevPollStatus" in cmds:
            print(f"{'Poll status':{PFIX1}} : {self.dev.DevPollStatus(self.dev_name)}")
        # Get Logging Target
        if "GetLoggingTarget" in cmds:
            qdevs = self.dev.GetLoggingTarget(self.dev_name)
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Logging target':{PFIX1}} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':{PFIX1}} : {qdev}")
            else:
                print(f"{'Logging target':{PFIX1}} : none specified")
        else:
            print(f"{'Logging target':{PFIX1}} : <N/A>")
        # Print query classes
        if "QueryClass" in cmds:
            qdevs = self.dev.QueryClass()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query class':{PFIX1}} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':{PFIX1}} : {qdev}")
            else:
                print(f"{'Query class':{PFIX1}} : none specified")
        # Print query devices
        if "QueryDevice" in cmds:
            qdevs = self.dev.QueryDevice()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query devices':{PFIX1}} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':{PFIX1}} : {qdev}")
            else:
                print(f"{'Query devices':{PFIX1}} : none specified")
        # Print query sub-devices
        if "QuerySubDevice" in cmds:
            qdevs = self.dev.QuerySubDevice()
            if qdevs:
                qdev = qdevs[0]
                print(f"{'Query sub-devices':{PFIX1}} : {qdev}")
                for qdev in qdevs[1:]:
                    print(f"{' ':{PFIX1}} : {qdev}")
            else:
                print(f"{'Query sub-devices':{PFIX1}} : none specified")
        else:
            print(f"{'Query sub-devices':{PFIX1}} : <N/A>")
        print("")
        return rv

    def _show_device_short(self, dry_run: bool, fmt: str) -> int:  # noqa: C901
        """
        Display Tango device in text format.

        :param dry_run: flag to skip reading of values
        :param fmt: output format
        :return: one if device is on, otherwise zero
        """
        if not self.online:
            print(f"{'Device':{PFIX1}} : {self.dev_name} <offline>\n")
            return 0
        print(f"{'Device':{PFIX1}} : {self.dev_name}")
        if self.adminMode is not None:
            print(f"{'Admin mode':{PFIX1}} : {self.adminMode}")
        rv = 1
        # Read commands
        cmds: tuple
        try:
            cmds = self.dev.get_command_list()
        except Exception:
            cmds = ()
        # Print commands
        if cmds:
            if dry_run:
                print(f"{'Commands':{PFIX1}} : \033[1m{cmds[0]}\033[0m")
                for cmd in cmds[1:]:
                    print(f"{' ':{PFIX1}}   \033[1m{cmd}\033[0m")
            else:
                print(f"{'Commands':{PFIX1}} :", end="")
                self.show_device_command_short("", cmds[0])
                for cmd in cmds[1:]:
                    self.show_device_command_short(f"{' ':{PFIX1}}  ", cmd)
        # Print attributes
        prefix = f"{' ':{PFIX1}}"
        self.show_device_attributes_short(dry_run, fmt)
        # Print properties
        self._show_device_properties(prefix, dry_run, fmt)
        print()
        return rv

    def _show_device_full(self, dry_run: bool, fmt: str) -> int:  # noqa: C901
        """
        Display Tango device in text format.

        :param dry_run: flag to skip reading of values
        :param fmt: output format
        :return: one if device is on, otherwise zero
        """
        # pylint: disable-next=c-extension-no-member
        print(f"{'Device':{PFIX1}} : {self.dev_name}", end="")
        if not self.online:
            print(" <offline>\n")
            return 0
        print()
        rv = 1
        if self.adminMode is not None:
            print(f"{'Admin mode':{PFIX1}} : {self.adminMode}")
        # Read commands
        cmds: tuple
        try:
            cmds = self.dev.get_command_list()
        except Exception:
            cmds = ()
        dev_info = self.dev.info()
        # Read state
        if "State" in cmds:
            try:
                print(f"{'State':{PFIX1}} : {self.dev.State()}")
            except tango.ConnectionFailed:
                print(f"{'State':{PFIX1}} : <connection failed>")
                return 0
        # Read status
        if "Status" in cmds:
            try:
                dev_status = self.dev.Status().replace("\n", f"\n{' ':20}")
                print(f"{'Status':{PFIX1}} : {dev_status}")
            except tango.ConnectionFailed:
                print(f"{'Status':{PFIX1}} : <connection failed>")
                return 0
        # Read database information
        print(f"{'Description':{PFIX1}} : {self.dev.description()}")
        jargon = find_jargon(self.dev_name)
        if jargon:
            print(f"{'Acronyms':{PFIX1}} : {jargon}")
        try:
            print(f"{'Alias':{PFIX1}} : {self.dev.alias()}")
        except Exception:
            print(f"{'Alias':{PFIX1}} : N/A")
        print(f"{'Version info':{PFIX1}} : {self.dev.getversioninfo()[0]}")
        print(f"{'Database used':{PFIX1}} : {self.dev.is_dbase_used()}")
        print(f"{'Server host':{PFIX1}} : {dev_info.server_host}")
        print(f"{'Server ID':{PFIX1}} : {dev_info.server_id}")
        # Read other information
        print(f"{'Device class':{PFIX1}} : {dev_info.dev_class}")
        try:
            print(f"{'Resources'} : {self.dev.assignedresources}")
        except tango.DevFailed as terr:
            print(f"{'Resources':{PFIX1}} :")
            print(f" <ERROR> \033[3m{terr.args[0].desc.strip()}\033[0m")
        except AttributeError:
            pass
        try:
            print(f"{'VCC state':{PFIX1}} : {self.dev.assignedVccState}")
        except AttributeError:
            pass
        try:
            dev_obs = self.dev.obsState
            print(f"{'Observation':{PFIX1}} : {get_obs_state(dev_obs)}")
        except Exception:
            pass
        # Print commands
        self.show_device_commands()
        # Print attributes
        prefix = f"{' ':{PFIX1}}"
        self.show_device_attributes(dry_run, fmt)
        # Print properties
        self._show_device_properties(prefix, dry_run, fmt)
        return rv

    def show_device_markdown(self) -> int:  # noqa: C901
        """
        Display Tango device in mark-down format.

        :return: one if device is on, otherwise zero
        """
        rval = 0
        print(f"## Device *{self.dev_name}*")
        if not self.online:
            print("Error")
            return rval
        # Read database host
        print(f"### Database host\n{self.dev.get_db_host()}")
        if self.dev_state is not None:
            print(f"### State\n{self.dev_state}")
        else:
            print("### State\nNONE")
        # Read information
        try:
            print(f"### Information\n```\n{self.dev.info()}\n```")
        except Exception:
            print("### Information\n```\nNONE\n```")
        # Read commands
        try:
            cmds = sorted(self.dev.get_command_list())
            # Display version information
            if "GetVersionInfo" in cmds:
                verinfo = self.dev.GetVersionInfo()
                print(f"### Version\n```\n{verinfo[0]}\n```")
            # Display commands
            print("### Commands")
            print("```\n%s\n```" % "\n".join(cmds))
            # Read command configuration
            cmd_cfgs = self.dev.get_command_config()
            for cmd_cfg in cmd_cfgs:
                print(f"#### Command *{cmd_cfg.cmd_name}*")
                # print(f"```\n{cmd_cfg}\n```")
                print("|Name |Value |")
                print("|:----|:-----|")
                if cmd_cfg.cmd_tag != 0:
                    print(f"|cmd_tag|{cmd_cfg.cmd_tag}|")
                print(f"|disp_level|{cmd_cfg.disp_level}|")
                print(f"|in_type|{cmd_cfg.in_type}|")
                if cmd_cfg.in_type_desc != "Uninitialised":
                    print(f"|in_type|{cmd_cfg.in_type_desc}")
                print(f"|out_type|{cmd_cfg.out_type}|")
                if cmd_cfg.out_type_desc != "Uninitialised":
                    print(f"|in_type|{cmd_cfg.out_type_desc}")
        except Exception:
            cmds = []
            print("### Commands\n```\nNONE\n```")
        # Read status
        if "Status" in cmds:
            print(f"#### Status\n{self.dev.Status()}")
        else:
            print("#### Status\nNo Status command")
        # Read attributes
        print("### Attributes")
        # pylint: disable-next=c-extension-no-member
        if self.dev_state == tango._tango.DevState.ON:
            rval = 1
            attribs = sorted(self.dev.get_attribute_list())
            print("```\n%s\n```" % "\n".join(attribs))
            for attrib in attribs:
                print(f"#### Attribute *{attrib}*")
                try:
                    print("##### Value\n```\n{self.dev.read_attribute(attrib).value}\n```")
                except Exception:
                    print(f"```\n{attrib} could not be read\n```")
                try:
                    attrib_cfg = self.dev.get_attribute_config(attrib)
                    print(f"##### Description\n```\n{attrib_cfg.description}\n```")
                except Exception:
                    print(f"```\n{attrib} configuration could not be read\n```")
        else:
            print("```\nNot reading attributes in offline state\n```")
        print("")
        return rval

    def _show_device_list(self, fmt: str) -> int:
        """
        Display Tango device name only.

        :param fmt: output format
        :return: one if device is on, otherwise zero
        """
        # pylint: disable-next=c-extension-no-member
        # if self.dev_state != tango._tango.DevState.ON:
        #     print(f"     {self.dev_name} ({self.adminMode})")
        #     return 0
        if fmt == "md":
            print(
                f"|{self.dev_name}|{self.dev_str}|{self.adminModeStr}|{self.version}|"
                f"{self.dev_class}|"
            )
        else:
            print(
                f"{self.dev_name:40} {self.dev_str:10} {self.adminModeStr:11} {self.version:8}"
                f" {self.dev_class}"
            )
        return 1

    def show_device(self, disp_action: int, dry_run: bool, fmt: str) -> None:
        """
        Print device information.

        :param disp_action: display format flag
        :param dry_run: skip reading of attributes
        :param fmt: output format
        """
        # if fmt == "md":
        #     self.on_dev_count += self.show_device_markdown()
        if disp_action == 5:
            self.on_dev_count += self._show_device_short(dry_run, fmt)
        elif disp_action == 4:
            self.on_dev_count += self._show_device_list(fmt)
        elif disp_action == 3:
            self.on_dev_count += self._show_device_query(fmt)
        elif disp_action == 1:
            self.on_dev_count += self._show_device_full(dry_run, fmt)
        else:
            print("Nothing to do!")


def setup_device(logger: logging.Logger, dev_name: str) -> Tuple[int, tango.DeviceProxy | None]:
    """
    Set up device connection and timeouts.

    :param logger: logging handle
    :param dev_name: Tango device name
    :return: error condition and Tango device handle
    """
    print("*** Setup Device connection and Timeouts ***")
    print(f"Tango device : {dev_name}")
    dev = tango.DeviceProxy(dev_name)
    # check AdminMode
    csp_admin = dev.adminMode
    if csp_admin:
        # Set Adminmode to OFFLINE and check state
        dev.adminMode = 0
        csp_admin = dev.adminMode
        if csp_admin:
            logger.error("Could not turn off admin mode")
            return 1, None
    return 0, dev


def check_command(logger: logging.Logger, dev: Any, c_name: str | None, min_str_len: int) -> list:
    """
    Read commands from database.

    :param logger: logging handle
    :param dev: device handle
    :param c_name: command name
    :param min_str_len: mininum string length below which only exact matches are allowed
    :return: list of commands
    """
    cmds_found: list = []
    if c_name is None:
        return cmds_found
    try:
        cmds = sorted(dev.get_command_list())
    except Exception:
        cmds = []
    logger.info("Check commands %s", cmds)
    c_name = c_name.lower()
    if len(c_name) <= min_str_len:
        for cmd in sorted(cmds):
            if c_name == cmd.lower():
                cmds_found.append(cmd)
    else:
        for cmd in sorted(cmds):
            if c_name in cmd.lower():
                cmds_found.append(cmd)
    return cmds_found


OBSERVATION_STATES = [
    "EMPTY",
    "RESOURCING",
    "IDLE",
    "CONFIGURING",
    "READY",
    "SCANNING",
    "ABORTING",
    "ABORTED",
    "RESETTING",
    "FAULT",
    "RESTARTING",
]


def get_obs_state(obs_stat: int) -> str:
    """
    Display Python enumerated type for observing state.

    :param obs_stat: observing state numeric value
    :return: state description
    """
    return OBSERVATION_STATES[obs_stat]


def show_obs_state(obs_stat: int) -> None:  # noqa: C901
    """
    Display Python enumerated type for observing state.

    :param obs_stat: observing state numeric value
    """
    if obs_stat == 0:
        # EMPTY = 0
        print(
            """EMPTY:
        The sub-array has no resources allocated and is unconfigured.
        """
        )
    elif obs_stat == 1:
        # RESOURCING = 1
        # In normal science operations these will be the resources required
        # for the upcoming SBI execution.
        #
        # This may be a complete de/allocation, or it may be incremental. In
        # both cases it is a transient state; when the resourcing operation
        # completes, the subarray will automatically transition to EMPTY or
        # IDLE, according to whether the subarray ended up having resources or
        # not.
        #
        # For some subsystems this may be a very brief state if resourcing is
        # a quick activity.
        print(
            """RESOURCING:
        Resources are being allocated to, or deallocated from, the subarray.
        """
        )
    elif obs_stat == 2:
        # IDLE = 2
        print(
            """IDLE:
        The subarray has resources allocated but is unconfigured.
        """
        )
    elif obs_stat == 3:
        # CONFIGURING = 3
        print(
            """CONFIGURING:
        The subarray is being configured for an observation.
        This is a transient state; the subarray will automatically
        transition to READY when configuring completes normally.
        """
        )
    elif obs_stat == 4:
        # READY = 4
        print(
            """READY:
        The subarray is fully prepared to scan, but is not scanning.
        It may be tracked, but it is not moving in the observed coordinate
        system, nor is it taking data.
        """
        )
    elif obs_stat == 5:
        # SCANNING = 5
        print(
            """SCANNING:
        The subarray is scanning.
        It is taking data and, if needed, all components are synchronously
        moving in the observed coordinate system.
        Any changes to the sub-systems are happening automatically (this
        allows for a scan to cover the case where the phase centre is moved
        in a pre-defined pattern).
        """
        )
    elif obs_stat == 6:
        # ABORTING = 6
        print(
            """ABORTING:
         The subarray has been interrupted and is aborting what it was doing.
        """
        )
    elif obs_stat == 7:
        # ABORTED = 7
        print("""ABORTED: The subarray is in an aborted state.""")
    elif obs_stat == 8:
        # RESETTING = 8
        print(
            """RESETTING:
        The subarray device is resetting to a base (EMPTY or IDLE) state.
        """
        )
    elif obs_stat == 9:
        # FAULT = 9
        print(
            """FAULT:
        The subarray has detected an error in its observing state.
        """
        )
    elif obs_stat == 10:
        # RESTARTING = 10
        print(
            """RESTARTING:
        The subarray device is restarting.
        After restarting, the subarray will return to EMPTY state, with no
        allocated resources and no configuration defined.
        """
        )
    else:
        print(f"Unknown state {obs_stat}")


def show_long_running_command(dev: Any) -> int:
    """
    Display long-running command.

    :param dev: Tango device handle
    :return: error condition
    """
    rc = len(dev.longRunningCommandsInQueue)
    print(f"Long running commands on device {dev.name()} : {rc} items")
    print("\tCommand IDs In Queue :")
    for qcmd in dev.longRunningCommandIDsInQueue:
        print(f"\t\t{qcmd}")
    print("\tCommand Progress :")
    for qcmd in dev.longRunningCommandProgress:
        print(f"\t\t{qcmd}")
    print("\tCommand Result :")
    n = 0
    lstat = len(dev.longRunningCommandResult)
    while n < lstat:
        print(f"\t\t{dev.longRunningCommandResult[n]}", end="")
        print(f"\t{dev.longRunningCommandResult[n+1]}", end="")
        print()
        n += 2
    print("\tCommand Status :")
    n = 0
    lstat = len(dev.longRunningCommandStatus)
    while n < lstat:
        print(f"\t\t{dev.longRunningCommandStatus[n+1]:12}", end="")
        print(f"\t{dev.longRunningCommandStatus[n]}")
        n += 2
    print("\tCommands In Queue :")
    for qcmd in dev.longRunningCommandsInQueue:
        print(f"\t\t{qcmd}")
    return rc


def show_long_running_commands(dev_name: str) -> int:
    """
    Display long-running commands.

    :param dev_name: Tango device name
    :return: error condition
    """
    dev = tango.DeviceProxy(dev_name)
    show_long_running_command(dev)
    return 0


def show_command_inputs(
    logger: logging.Logger, tango_host: str, tgo_in_type: str, min_str_len: int
) -> None:
    """
    Display commands with given input type.

    :param logger: logging handle
    :param tango_host: Tango database host address and port
    :param tgo_in_type: input type, e.g. Uninitialised
    :param min_str_len: mininum string length below which only exact matches are allowed
    """
    # Connect to database
    try:
        database = tango.Database()
    except Exception:
        logger.error("Could not connect to Tango database %s", tango_host)
        return
    # Read devices
    device_list = database.get_device_exported("*")
    logger.info(f"{len(device_list)} devices available")

    logger.info("Read %d devices" % (len(device_list)))

    for device in sorted(device_list.value_string):
        dev, _dev_state = tango.DeviceProxy(device)
        try:
            cmds = dev.get_command_config()
        except Exception:
            cmds = []
        if cmds:
            for cmd in cmds:
                in_type_desc = cmd.in_type_desc.lower()
                logger.info("Command %s type %s", cmd, in_type_desc)
                # TODO implement partial matches
                if in_type_desc == tgo_in_type:
                    print(f"{'Commands':{PFIX1}} : \033[3m{cmd.cmd_name}\033[0m ({in_type_desc})")
                else:
                    print(f"{'Commands':{PFIX1}} : {cmd.cmd_name} ({in_type_desc})")
