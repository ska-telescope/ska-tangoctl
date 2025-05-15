"""Read information from Tango database."""

import logging
import socket
from typing import Any, Tuple

import tango

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
    tango_addr: tuple[str, list[str], list[str]]
    tango_ip: str

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


def setup_device(logger: logging.Logger, dev_name: str) -> Tuple[int, tango.DeviceProxy | None]:
    """
    Set up device connection and timeouts.

    :param logger: logging handle
    :param dev_name: Tango device name
    :return: error condition and Tango device handle
    """
    csp_admin: int

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
    cmds: list
    cmds_found: list
    cmd: str

    cmds_found = []
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
    rc: int
    n: int

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
        print(f"\t{dev.longRunningCommandResult[n + 1]}", end="")
        print()
        n += 2
    print("\tCommand Status :")
    n = 0
    lstat = len(dev.longRunningCommandStatus)
    while n < lstat:
        print(f"\t\t{dev.longRunningCommandStatus[n + 1]:12}", end="")
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
    dev: tango.DeviceProxy

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
    database: tango.Database
    device_list: tango.DbDatum
    device: str
    cmds: tango.CommandInfoList
    cmd: tango.CommandInfo
    in_type_desc: str

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
