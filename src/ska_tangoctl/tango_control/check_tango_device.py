"""Start and check Tango device."""

import logging
import socket
import time
from typing import Any

import tango
from ska_control_model import AdminMode

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger(__name__)
_module_logger.setLevel(logging.WARNING)


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


def device_state(dev: tango.DeviceProxy) -> None:
    """
    Display status information for Tango device.

    :param dev: Tango device handle
    """
    dev_name = dev.name()
    print(f"Device {dev_name}")
    print(f"\tAdmin mode                     : {dev.adminMode}")
    print(f"\tDevice status                  : {dev.Status()}")
    print(f"\tDevice state                   : {dev.State()}")
    try:
        print(f"\tObservation state              : {repr(dev.obsState)}")
        show_obs_state(dev.obsState)
    except AttributeError:
        _module_logger.info("Device %s does not have an observation state", dev_name)
    print(f"versionId                        : {dev.versionId}")
    print(f"build State                      : {dev.buildState}")
    print(f"logging level                    : {dev.loggingLevel}")
    print(f"logging Targets                  : {dev.loggingTargets}")
    print(f"health State                     : {dev.healthState}")
    print(f"control Mode                     : {dev.controlMode}")
    print(f"simulation Mode                  : {dev.simulationMode}")
    print(f"test Mode                        : {dev.testMode}")
    print(f"long Running Commands In Queue   : {dev.longRunningCommandsInQueue}")
    print(f"long Running Command IDs InQueue : {dev.longRunningCommandIDsInQueue}")
    print(f"long Running Command Status      : {dev.longRunningCommandStatus}")
    print(f"long Running Command Progress    : {dev.longRunningCommandProgress}")
    print(f"long Running Command Result      : {dev.longRunningCommandResult}")


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


def set_tango_admin(dev: Any, dev_adm: bool, sleeptime: int = 2) -> bool:
    """
    Write admin mode for a Tango device.

    :param dev: Tango device
    :param dev_adm: admin mode flag
    :param sleeptime: seconds to sleep
    :return: True when device is in admin mode
    """
    print(f"*** Set Adminmode to {dev_adm} and check state ***")
    if dev_adm:
        dev.adminMode = 1
    else:
        dev.adminMode = 0
    time.sleep(sleeptime)
    return get_tango_admin(dev)


def get_tango_admin(dev: tango.DeviceProxy) -> bool:
    """
    Read admin mode for a Tango device.

    :param dev: Tango device handle
    :return: True when device is in admin mode
    """
    csp_admin = dev.adminMode
    if csp_admin == AdminMode.ONLINE:
        print("Device admin mode online")
        return False
    if csp_admin == AdminMode.OFFLINE:
        print("Device admin mode offline")
    else:
        print(f"Device admin mode {csp_admin}")
    return True
