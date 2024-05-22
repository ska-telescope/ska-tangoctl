"""GUI for tangoctl."""
import logging
import tkinter as tk
from typing import Any

from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic
from ska_tangoctl.tango_control.tangoctl_config import TANGOCTL_CONFIG

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
# _module_logger.setLevel(logging.INFO)


def get_devices() -> dict:
	cfg_data: Any = TANGOCTL_CONFIG
	devs: TangoctlDevicesBasic = TangoctlDevicesBasic(
		_module_logger,
		True,
		True,
		False,
		False,
		cfg_data,
		None,
		"json",
		None,
	)
	return devs.devices


def main():
	devs: dict = get_devices()
	_module_logger.info("Go devices %s", devs)
	# create a root window.
	top = tk.Tk()

	# create listbox object
	listbox = tk.Listbox(
		top,
		height=10,
		width=20,
		bg="grey",
		activestyle="dotbox",
		font="Helvetica",
		fg="yellow",
	)

	# Define the size of the window.
	top.geometry("400x250")

	# Define a label for the list.
	label = tk.Label(top, text = " Tango devices")

	# insert elements by their
	# index and names.
	n = 0
	for dev in devs:
		n += 1
		listbox.insert(n, dev)

	# pack the widgets
	label.pack()
	listbox.pack()

	# Function for printing the selected listbox value(s)
	def selected_item():
		# Traverse listbox and print corresponding value(s)
		for i in listbox.curselection():
			dev_name = listbox.get(i)
			print(f"{dev_name}: {devs[dev_name]}")

	# Create button widget and map command parameter to selected item
	btn = tk.Button(top, text='Print Selected', command=selected_item)

	# Place button and listbox
	btn.pack(side='bottom')
	listbox.pack()

	# Display until user exits
	top.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
