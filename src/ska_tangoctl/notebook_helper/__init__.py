"""Read information from Tango database."""

import tango  # noqa: F401

# TODO fix the problem and uncomment the functions below
# They break the docs builder like this
# docstring of ska_tangoctl.notebook_helper.get_tango_notebook.show_device_commands:1:
# WARNING: py:class reference target not found: tango._tango.DeviceProxy
# The following are affected
# "connect_device",
# "check_device",
# "device_state",
# "setup_device",
# "get_tango_admin",
# "show_device_commands",
# "show_attribute_value",
# "show_device_attributes",
__all__ = [
    "check_tango",
    "set_tango_admin",
    "show_device_state",
    "show_command_inputs",
    "show_attribute_value_scalar",
    "show_attribute_value_spectrum",
    "show_device_query",
    "run_command",
    "show_device",
    "show_device_markdown",
    "show_devices",
    "check_command",
    "show_attributes",
    "show_commands",
    "get_obs_state",
    "show_obs_state",
    "show_long_running_command",
    "show_long_running_commands",
]

# TODO put these back, see above
# check_device,
# connect_device,
# device_state,
# get_tango_admin,
# setup_device,
# show_attribute_value,
# show_device_attributes,
# show_device_commands,
from ska_tangoctl.notebook_helper.get_tango_notebook import (
    check_command,
    check_tango,
    get_obs_state,
    run_command,
    set_tango_admin,
    show_attribute_value_scalar,
    show_attribute_value_spectrum,
    show_attributes,
    show_command_inputs,
    show_commands,
    show_device,
    show_device_markdown,
    show_device_query,
    show_device_state,
    show_devices,
    show_long_running_command,
    show_long_running_commands,
    show_obs_state,
)
