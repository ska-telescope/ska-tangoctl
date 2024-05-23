"""GUI for tangoctl."""
import logging
import tkinter as tk
from typing import Any
import tkinter.messagebox
from tkhtmlview import HTMLLabel

from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic
from ska_tangoctl.tango_control.read_tango_device import TangoctlDeviceBasic
from ska_tangoctl.tango_control.tangoctl_config import TANGOCTL_CONFIG

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.INFO)


def get_devices_dict() -> dict:
	cfg_data: Any = TANGOCTL_CONFIG
	devs: TangoctlDevicesBasic = TangoctlDevicesBasic(
		_module_logger,
		True,
		True,
		False,
		False,
		cfg_data,
		None,
		"html",
		None,
	)
	return devs.devices


def get_devices() -> TangoctlDevicesBasic:
	cfg_data: Any = TANGOCTL_CONFIG
	devs: TangoctlDevicesBasic = TangoctlDevicesBasic(
		_module_logger,
		True,
		True,
		False,
		False,
		cfg_data,
		None,
		"html",
		None,
	)
	devs.read_configs()
	return devs


	cfg_data: Any = TANGOCTL_CONFIG
	devs: TangoctlDevicesBasic = TangoctlDevicesBasic(
		_module_logger,
		True,
		True,
		False,
		False,
		cfg_data,
		None,
		"html",
		None,
	)
	return devs.get_html()


def main():
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

	devs: TangoctlDevicesBasic = get_devices()
	_module_logger.info("Got devices %s", devs)

	# insert elements by index and names.
	n = 0
	for dev in devs.devices:
		n += 1
		listbox.insert(n, dev)

	# pack the widgets
	label.pack()
	listbox.pack()

	# Function for printing the selected listbox value(s)
	def selected_item(event=None):
		# Traverse listbox and print corresponding value(s)
		for i in listbox.curselection():
			dev_name = listbox.get(i)
			# print(f"{dev_name}: {devs[dev_name]}")
			tkinter.messagebox.showinfo(dev_name, devs[dev_name])

	# function to open a new window
	# on a button click
	def open_new_window():

		# Toplevel object which will
		# be treated as a new window
		new_window = tk.Toplevel(top)

		# sets the title of the
		# Toplevel widget
		new_window.title("New Window")

		# sets the geometry of toplevel
		new_window.geometry("300x600")

		dev_txt = ""
		# Traverse listbox and print corresponding value(s)
		for i in listbox.curselection():
			dev_name = listbox.get(i)
			dev_attribs = "\n".join(devs[dev_name].attribs)
			dev_txt += f"{dev_name}:\n{dev_attribs}\n"

		# A Label widget to show in toplevel
		tk.Label(new_window, text=dev_txt).pack()

	def new_window_scroll():

		dev_txt = ""
		# Traverse listbox and print corresponding value(s)
		for i in listbox.curselection():
			dev_name = listbox.get(i)
			dev_attribs = "\n".join(devs[dev_name].attribs)
			# dev_txt += f"{dev_name}:\n{dev_attribs}\n"
			dev_txt += f"{dev_name}:\n{devs[dev_name].get_html()}\n"

		window = tk.Tk()
		window.geometry("250x200")

		sv_bar = tk.Scrollbar(window)
		sv_bar.pack(side=tk.RIGHT, fill="y")

		sh_bar = tk.Scrollbar(window, orient=tk.HORIZONTAL)
		sh_bar.pack(side=tk.BOTTOM, fill="x")

		t_box = tk.Text(
			window,
			height=500,
			width=500,
			yscrollcommand=sv_bar.set,
			xscrollcommand=sh_bar.set,
			wrap="none"
		)

		# t_box = tk.Text(window,
		# 			   height=500,
		# 			   width=500,
		# 			   yscrollcommand=sv_bar.set,
		# 			   xscrollcommand=sh_bar.set,
		# 			   wrap="none")

		t_box.pack(expand=0, fill=tk.BOTH)

		# t_box.insert(tk.END, Num_Horizontal)
		t_box.insert(tk.END, dev_txt)

		sh_bar.config(command=t_box.xview)
		sv_bar.config(command=t_box.yview)

		# window.mainloop()

	def new_window_html():

		# Traverse listbox and print corresponding value(s)
		devs_html: str = "<table border=0 cellpadding=0 cellspacing=0>\n"
		n: int = 0
		for i in listbox.curselection():
			dev_name = listbox.get(i)
			# print(f"{dev_name}: {devs[dev_name]}")
			h_dev: TangoctlDeviceBasic = devs.devices[dev_name]
			h_dev.read_config()
			if not n:
				devs_html += h_dev.get_html_header()
			devs_html += h_dev.get_html()
			n += 1
		devs_html += "</table>"
		_module_logger.info("HTML: %s", devs_html)

		window = tk.Tk()
		window.geometry("250x200")

		dev_label = HTMLLabel(window, html=devs_html)
		dev_label.pack(pady=20, padx=20)

	def new_window_html_all():
		# devs_html += devs.get_html_header()
		devs_html: str = devs.get_html()
		_module_logger.info("HTML: %s", devs_html)

		window = tk.Tk()
		window.geometry("250x200")

		dev_label = HTMLLabel(window, html=devs_html)
		dev_label.pack(pady=20, padx=20)

	listbox.bind('<Double-1>', selected_item)
	listbox.pack()

	# Create button widget and map command parameter to selected item
	# btn = tk.Button(top, text='Print Selected', command=new_window_scroll)
	btn = tk.Button(top, text='Print Selected', command=new_window_html)
	# Place button and listbox
	btn.pack(side='bottom')
	listbox.pack()

	btn2 = tk.Button(top, text='Print All', command=new_window_html_all)
	# Place button and listbox
	btn2.pack(side='bottom')
	listbox.pack()

	# Display until user exits
	top.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
