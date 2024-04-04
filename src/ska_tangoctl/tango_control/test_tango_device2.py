#!/usr/bin/python
"""Test devices from Tango database."""

import logging
import os
import time
from typing import Any

import tango


class TestTangoDevice:
    """Test a Tango device."""

    def __init__(self, logger: logging.Logger, device_name: str):  # noqa: C901
        """
        Get going.

        :param logger: logging handle
        :param device_name: Tango device name
        """
        self.logger: logging.Logger = logger
        self.adminMode: int | None = None
        self.attribs: list = []
        self.cmds: list = []
        self.dev: tango.DeviceProxy | None
        err_msg: str
        self.logger.info("Connect device proxy to %s", device_name)
        try:
            self.dev = tango.DeviceProxy(device_name)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            print(f"[FAILED] {device_name} connection failed : {err_msg}")
            self.logger.debug(terr)
            self.dev = None
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            print(f"[FAILED] {device_name} device failed : {err_msg}")
            self.logger.debug(terr)
            self.dev = None
        if self.dev is not None:
            try:
                self.adminMode = self.dev.adminMode
                print(f"[  OK  ] admin mode {self.adminMode}")
            except AttributeError as terr:
                self.adminMode = None
                self.logger.debug(terr)
            try:
                self.dev_name = self.dev.name()
            except tango.DevFailed:
                self.dev_name = device_name + " (N/A)"
            try:
                self.attribs = self.dev.get_attribute_list()
            except tango.DevFailed:
                self.attribs = []
            try:
                self.cmds = self.dev.get_command_list()
            except tango.DevFailed:
                self.cmds = []
        self.dev_status: str | None = None
        self.dev_state: int | None = None
        self.simMode: int | None = None

    def get_admin_mode(self) -> int | None:
        """
        Read attribute for admin mode.

        :return: attribute value
        """
        if self.dev is None:
            return None
        if "  " not in self.attribs:
            print(f"[ WARN ] {self.dev_name} does not have an adminMode attribute")
            self.adminMode = None
            return None
        try:
            self.adminMode = self.dev.adminMode
            print(f"[  OK  ] admin mode {self.adminMode}")
        except AttributeError as terr:
            print("[FAILED] could not read admin mode")
            self.logger.debug(terr)
            self.adminMode = None
        return self.adminMode

    def get_simulation_mode(self) -> int | None:
        """
        Read attribute for simulation mode.

        :return: attribute value
        """
        if self.dev is None:
            return None
        if "simulationMode" not in self.attribs:
            print(f"[ WARN ] {self.dev_name} does not have a simulationMode attribute")
        try:
            self.simMode = self.dev.simulationMode
            print(f"[  OK  ] simulation mode {self.simMode}")
        except AttributeError as terr:
            print("[FAILED] could not read simulation mode")
            self.logger.debug(terr)
            self.simMode = None
        return self.simMode

    def set_simulation_mode(self, dev_sim: int | None) -> int | None:
        """
        Set attribute for simulation mode.

        :param dev_sim: attribute value
        :return: error condition
        """
        if self.dev is None:
            return None
        if "simulationMode" not in self.attribs:
            print(f"[ WARN ] {self.dev_name} does not have a simulationMode attribute")
        try:
            self.dev.simulationMode = dev_sim
            self.simMode = self.dev.simulationMode
            print(f"[  OK  ] simulation mode set to {self.simMode}")
        except AttributeError as terr:
            print(f"[FAILED] could not set simulation mode to {dev_sim}")
            self.logger.debug(terr)
            self.simMode = None
            return 1
        if dev_sim != self.simMode:
            print(f"[FAILED] simulation mode should be {dev_sim} but is {self.simMode}")
        return 0

    def check_device(self) -> bool:
        """
        Check that device is online.

        :return: online condition
        """
        if self.dev is None:
            return False
        try:
            self.dev.ping()
            print(f"[  OK  ] {self.dev_name} is online")
        except tango.DevFailed as terr:
            print(f"[FAILED] {self.dev_name} is not online")
            self.logger.debug(terr.args[-1].desc)
            return False
        return True

    def show_device_attributes(self, show: bool = False) -> None:
        """
        Display number and names of attributes.

        :param show: flag to print names
        """
        print(f"[  OK  ] {self.dev_name} has {len(self.attribs)} attributes")
        if show:
            for attrib in sorted(self.attribs):
                print(f"\t{attrib}")

    def read_device_attributes(self) -> None:
        """Read all attributes of this device."""
        self.logger.debug("Read attribute %s values", self.dev_name)
        if self.dev is None:
            return
        print(f"[  OK  ] {self.dev_name} read {len(self.attribs)} attributes")
        for attrib in sorted(self.attribs):
            time.sleep(2)
            try:
                attrib_value = self.dev.read_attribute(attrib).value
                print(f"[  OK  ] {self.dev_name} attribute {attrib} : {attrib_value}")
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(f"[FAILED] {self.dev_name} attribute {attrib} could not be read : {err_msg}")
                self.logger.debug(terr)

    def show_device_commands(self, show: bool = False) -> None:
        """
        Display number and names of commands.

        :param show: flag to print names
        """
        print(f"[  OK  ] {self.dev_name} has {len(self.cmds)} commands")
        if show:
            for cmd in sorted(self.cmds):
                print(f"\t{cmd}")

    def admin_mode_off(self) -> None:
        """Turn admin mode off."""
        if self.dev is None:
            return
        if self.adminMode is None:
            return
        if self.adminMode == 1:
            self.logger.info("Turn device admin mode off")
            try:
                self.dev.adminMode = 0
                self.adminMode = self.dev.adminMode
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(f"[FAILED] {self.dev_name} admin mode could not be turned off : {err_msg}")
                self.logger.debug(terr)
                return
            self.adminMode = self.dev.adminMode
        print(f"[  OK  ] {self.dev_name} admin mode set to off, now ({self.adminMode})")

    def device_status(self) -> int | None:
        """
        Print device status.

        :return: device state
        """
        if self.dev is None:
            return None
        if "Status" not in self.cmds:
            print(f"[FAILED] {self.dev.dev_name} does not have Status command")
        if "State" not in self.cmds:
            print(f"[FAILED] {self.dev.dev_name} does not have State command")
            return None
        self.dev_status = self.dev.Status()
        self.dev_state = self.dev.State()
        print(f"[  OK  ] {self.dev_name} state : {self.dev_state} ({self.dev_state:d})")
        print(f"[  OK  ] {self.dev_name} status : {self.dev_status}")
        return self.dev_state

    def device_on(self) -> int:
        """
        Turn this device on.

        :return: error condition
        """
        dev_on: Any
        err_msg: str

        self.logger.debug("Turn device %s on", self.dev_name)
        if self.dev is None:
            return 1
        if "On" not in self.cmds:
            print(f"[FAILED] {self.dev_name} does not have On command")
            return 1
        cmd_cfg: tango.CommandInfo = self.dev.get_command_config("On")
        if cmd_cfg.in_type_desc == "Uninitialised":
            try:
                dev_on = self.dev.On()
                print(f"[  OK  ] {self.dev_name} turned on, now {dev_on}")
                return 1
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(f"[FAILED] {self.dev_name} could not be turned on : {err_msg}")
                self.logger.debug(terr)
        else:
            try:
                dev_on = self.dev.On([])
                print(f"[  OK  ] {self.dev_name} turned on, now {dev_on}")
                return 1
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(
                    f"[FAILED] {self.dev_name} could not be turned on (device failed) : {err_msg}"
                )
                self.logger.debug(terr)
                return 1
            except TypeError as terr:
                print(
                    f"[FAILED] {self.dev_name} could not be turned on"
                    f" (parameter type should be {cmd_cfg.in_type_desc})"
                )
                self.logger.debug(terr)
                return 1
        return 0

    def device_off(self) -> int:
        """
        Turn this device off.

        :return: error condition
        """
        dev_off: Any
        err_msg : str

        self.logger.debug("Turn device %s off", self.dev_name)
        if self.dev is None:
            return 1
        if "Off" not in self.cmds:
            print(f"[FAILED] {self.dev_name} does not have Off command")
            return 1
        cmd_cfg: tango.CommandInfo = self.dev.get_command_config("Off")
        if cmd_cfg.in_type_desc == "Uninitialised":
            try:
                dev_off = self.dev.Off()
                print(f"[  OK  ] {self.dev_name} turned off, now {dev_off}")
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(f"[FAILED] {self.dev_name} could not be turned off : {err_msg}")
                self.logger.debug(terr)
                return 1
        else:
            try:
                dev_off = self.dev.Off([])
                print(f"[  OK  ] {self.dev_name} turned off, now {dev_off}")
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(f"[FAILED] {self.dev_name} could not be turned off : {err_msg}")
                self.logger.debug(terr)
                return 1
        return 0

    def device_standby(self) -> int:
        """
        Set this device to standby mode.

        :return: error condition
        """
        dev_standby: Any
        err_msg: str

        self.logger.debug("Set device %s on standby", self.dev_name)
        if self.dev is None:
            return 1
        if "Standby" not in self.cmds:
            print(f"[FAILED] {self.dev.dev_name} does not have Standby command")
            return 1
        cmd_cfg: tango.CommandInfo = self.dev.get_command_config("Standby")
        if cmd_cfg.in_type_desc == "Uninitialised":
            try:
                dev_standby = self.dev.Standby()
                print(f"[  OK  ] {self.dev_name} switched to standby, now {dev_standby}")
                return 0
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(f"[FAILED] {self.dev_name} could not be switched to standby : {err_msg}")
                self.logger.debug(terr)
        else:
            try:
                dev_standby = self.dev.Standby([])
                print(f"[  OK  ] {self.dev_name} switched to standby, now {dev_standby}")
                return 0
            except tango.DevFailed as terr:
                err_msg = terr.args[0].desc.strip()
                print(f"[FAILED] {self.dev_name} could not be switched to standby : {err_msg}")
                self.logger.debug(terr)
        return 1

    def admin_mode_on(self) -> None:
        """Turn admin mode on."""
        err_msg: str

        self.logger.info("Turn device admin mode on")
        if self.dev is None:
            return
        try:
            self.dev.adminMode = 1
            self.adminMode = self.dev.adminMode
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            print(f"[FAILED] {self.dev_name} admin mode could not be turned on : {err_msg}")
            self.logger.debug(terr)
            return
        print(f"[  OK  ] {self.dev_name} admin mode turned on, now ({self.adminMode})")

    def set_admin_mode(self, admin_mode: int) -> int:
        """
        Change admin mode.

        :param admin_mode: new value
        :return: error condition
        """
        err_msg: str

        self.logger.info("Set device admin mode to %d", admin_mode)
        if self.dev is None:
            return 1
        try:
            self.dev.adminMode = admin_mode
            self.adminMode = self.dev.adminMode
        except tango.DevFailed as terr:
            err_msg = terr.args[0].desc.strip()
            print(f"[FAILED] {self.dev_name} admin mode could not be changed : {err_msg}")
            self.logger.debug(terr)
            return 1
        if self.adminMode != admin_mode:
            print(
                f"[FAILED] {self.dev_name} admin mode is {self.adminMode}"
                f" but should be {admin_mode}"
            )
            return 1
        print(f"[  OK  ] {self.dev_name} admin mode set to ({self.adminMode})")
        return 0

    def test_admin_mode(self, dev_admin: int) -> int:
        """
        Test admin mode.

        :param dev_admin: new value
        :return: error condition
        """
        self.check_device()
        self.get_simulation_mode()
        # Read admin mode
        self.get_admin_mode()
        if self.adminMode is not None:
            self.set_admin_mode(dev_admin)
        return 0

    def test_off(self, dev_sim: int | None) -> int:
        """
        Test that device can be turned off.

        :param dev_sim: flag for hardware simulation.
        :return: error condition
        """
        self.check_device()
        self.get_simulation_mode()
        if dev_sim is not None:
            self.set_simulation_mode(dev_sim)
        self.show_device_attributes()
        self.show_device_commands()
        # Read admin mode
        self.get_admin_mode()
        # Read state
        self.device_status()
        # Turn device off
        self.device_off()
        # Turn on admin mode
        self.admin_mode_on()
        # Read state
        self.device_status()
        return 0

    def test_on(self, dev_sim: int | None) -> int:
        """
        Test that device can be turned on.

        :param dev_sim: flag for hardware simulation.
        :return: error condition
        """
        self.check_device()
        self.get_simulation_mode()
        if dev_sim is not None:
            self.set_simulation_mode(dev_sim)
        self.show_device_attributes()
        self.show_device_commands()
        # Read admin mode, turn off
        self.get_admin_mode()
        self.admin_mode_off()
        # Turn device on
        init_state = self.device_status()
        # pylint: disable-next=c-extension-no-member
        if init_state == tango._tango.DevState.ON:
            print("[ WARN ] device is already on")
        else:
            self.device_on()
        self.device_status()
        return 0

    def test_standby(self, dev_sim: int | None) -> int:
        """
        Test that device can be placed into standby mode.

        :param dev_sim: flag for hardware simulation.
        :return: error condition
        """
        self.check_device()
        self.get_simulation_mode()
        if dev_sim is not None:
            self.set_simulation_mode(dev_sim)
        self.get_admin_mode()
        self.device_standby()
        self.device_status()
        return 0

    def test_status(self) -> int:
        """
        Test that device status can be read.

        :return: error condition
        """
        self.check_device()
        self.get_simulation_mode()
        self.get_admin_mode()
        self.device_status()
        return 0

    def test_simulation_mode(self, dev_sim: int | None) -> int:
        """
        Test that device hardware simulation can be set.

        :param dev_sim: flag for hardware simulation.
        :return: error condition
        """
        self.check_device()
        self.get_simulation_mode()
        self.set_simulation_mode(dev_sim)
        self.get_simulation_mode()
        return 0

    def test_all(self, show_attrib: bool) -> int:
        """
        Test everything that device can do.

        :param show_attrib: flag for attributes display.
        :return: error condition
        """
        init_admin_mode: int | None
        init_state: int | None

        self.check_device()
        self.get_simulation_mode()
        self.show_device_attributes()
        self.show_device_commands()
        # Read admin mode, turn on ond off
        init_admin_mode = self.get_admin_mode()
        if self.adminMode is not None:
            self.admin_mode_on()
            self.admin_mode_off()
        # Read state
        init_state = self.device_status()
        # Turn device on
        # pylint: disable-next=c-extension-no-member
        if init_state == tango._tango.DevState.ON:
            print("[ WARN ] device is already on")
        else:
            self.device_on()
        self.device_status()
        # Read attribute values
        if show_attrib:
            self.read_device_attributes()
        else:
            print("[ WARN ] skip reading attributes")
        # Turn device off
        self.device_off()
        self.device_status()
        # pylint: disable-next=c-extension-no-member
        if self.dev_state == tango._tango.DevState.ON:
            print("[FAILED] device is still on")
        # Turn device back on, if neccesary
        # pylint: disable-next=c-extension-no-member
        if init_state == tango._tango.DevState.ON:
            print("[ WARN ] turn device back on")
            self.device_on()
            self.device_status()
        # Turn device admin mode back on, if neccesary
        if init_admin_mode == 1:
            print("[ WARN ] turn admin mode back to on")
            self.admin_mode_on()
        return 0

    def test_subscribe(self, attrib: str) -> int:
        """
        Test subscribed to event.

        :param attrib: attribute name
        :return: error condition
        """
        err_msg: str
        evnt_id: int
        events: Any

        print(f"[  OK  ] subscribe to events for {self.dev_name} {attrib}")
        if self.dev is None:
            return 1
        evnt_id = self.dev.subscribe_event(
            attrib, tango.EventType.CHANGE_EVENT, tango.utils.EventCallback()
        )
        print(f"[  OK  ] subscribed to event ID {evnt_id}")
        time.sleep(15)
        try:
            events = self.dev.get_events(evnt_id)
            print(f"[  OK  ] got events {events}")
        except tango.EventSystemFailed as terr:
            err_msg = terr.args[0].desc.strip()
            print(f"[ WARN ] got no events for {self.dev_name} {attrib} : {err_msg}")
            self.logger.debug(terr)
        try:
            self.dev.devc.unsubscribe_event(evnt_id)
            print(f"[  OK  ] unsubscribed from event ID {evnt_id}")
        except AttributeError as oerr:
            print(f"[ WARN ] could not unsubscribe from event ID {evnt_id}")
            self.logger.debug(oerr)
        return 0

    def run_test(  # noqa: C901
        self,
        dry_run: bool,
        dev_admin: int | None,
        dev_off: bool,
        dev_on: bool,
        dev_sim: int | None,
        dev_standby: bool,
        dev_status: bool,
        show_command: bool,
        show_attrib: bool,
        tgo_attrib: str | None,
        tgo_name: str | None,
        tango_port: int,
    ) -> int:
        """
        Run tests on Tango devices.

        :param dry_run: only show what will be done
        :param dev_admin: check admin mode
        :param dev_off: turn device on
        :param dev_on: turn device off
        :param dev_sim: simulation flag
        :param dev_standby: place device in standby
        :param dev_status: set device status
        :param show_command: test device commands
        :param show_attrib: test device attributes
        :param tgo_attrib: name of attribute
        :param tgo_name: device name
        :param tango_port: device port
        :return: error condition
        """
        if dev_admin is not None and tgo_name is not None:
            self.test_admin_mode(dev_admin)
        elif dev_off and tgo_name is not None:
            self.test_off(dev_sim)
        elif dev_on and tgo_name is not None:
            self.test_on(dev_sim)
        elif dev_standby and tgo_name is not None:
            self.test_standby(dev_sim)
        elif dev_status and tgo_name is not None:
            self.test_status()
        elif dev_sim is not None and tgo_name is not None:
            self.test_simulation_mode(dev_sim)
        elif show_command and tgo_name is not None:
            self.check_device()
            # TODO for future use
            # dut.get_simulation_mode()
            self.show_device_attributes(True)
            self.show_device_commands(True)
        elif tgo_attrib is not None and tgo_name is not None:
            self.test_subscribe(tgo_attrib)
        elif tgo_name is not None:
            dut: TestTangoDevice = TestTangoDevice(self.logger, tgo_name)
            if dut.dev is None:
                print(f"[FAILED] could not open device {tgo_name}")
                return 1
            dut.test_all(show_attrib)
        else:
            pass
        return 0


class TestTangoDevices:
    """Compile a list of available Tango devices."""

    def __init__(self, logger: logging.Logger, evrythng: bool, cfg_data: Any):
        """
        Read Tango device names.

        :param logger: logging handle
        :param evrythng: include the kitchen sink
        :param cfg_data: configuration data
        :raises Exception: connect to Tango database failed
        """
        database: tango.Database
        device_list: tango.DbDatum
        device: str

        self.logger = logger
        self.tango_devices: list = []
        # Connect to database
        try:
            database = tango.Database()
        except Exception:
            tango_host = os.getenv("TANGO_HOST")
            self.logger.error("[FAILED] Could not connect to Tango database %s", tango_host)
            raise Exception("Could not connect to Tango database %s", tango_host)
        # Read devices
        device_list = database.get_device_exported("*")
        print(f"[  OK  ] {len(device_list)} devices available")

        for device in sorted(device_list.value_string):
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
            self.logger.debug("Add device %s", device)
            self.tango_devices.append(device)

        self.logger.info("Found %d devices", len(self.tango_devices))
