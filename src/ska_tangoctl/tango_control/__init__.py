"""Read and display Tango stuff."""

__all__ = [
    "check_tango",
    # TODO see below
    # "device_tree",
    "show_obs_state",
    "DispAction",
    "TangoControl",
    "TangoctlDeviceBasic",
    "TangoctlDevice",
    "TangoctlDeviceConfig",
    "TangoctlDevicesBasic",
    "TangoctlDevices",
    "TangoJsonReader",
    "TangoScript",
    "TestTangoDevice",
]

from ska_tangoctl.tango_control.check_tango_device import check_tango, show_obs_state
from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_config import TangoctlDeviceConfig
from ska_tangoctl.tango_control.read_tango_device import TangoctlDevice, TangoctlDeviceBasic
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevices, TangoctlDevicesBasic
from ska_tangoctl.tango_control.tango_control import TangoControl
from ska_tangoctl.tango_control.tango_json import TangoJsonReader
from ska_tangoctl.tango_control.test_tango_device import TestTangoDevice
from ska_tangoctl.tango_control.test_tango_script import TangoScript

# TODO weird error here
# WARNING: autodoc: failed to import module 'tango_control' from module 'ska_tangoctl';
# the following exception was raised:
# No module named gevent.
# You need to install gevent module to have access to PyTango gevent green mode.
# Consider using the futures green mode instead
# from ska_tangoctl.tango_control.tango_device_tree import device_tree
