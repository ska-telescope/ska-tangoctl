"""GUI for tangoctl."""
import logging
from typing import Any
from tkinter import ttk
import tkinter as tk

from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic
# from ska_tangoctl.tango_control.read_tango_device import TangoctlDeviceBasic
from ska_tangoctl.tango_control.tangoctl_config import TANGOCTL_CONFIG

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.INFO)


class Table:

    def __init__(self, root: tk.Tk, devs_dict: dict):
        total_rows = len(devs_dict)

        # code for creating table
        i: int = 0
        j: int = 0
        for dev_name in devs_dict:
            if not i:
                self.e = tk.Entry(root, width=40, fg='blue', font=('Arial', 12, 'bold'))
                self.e.grid(row=i, column=0)
                self.e.insert(tk.END, "Device name")
                j = 1
                for field in devs_dict[dev_name]:
                    self.e = tk.Entry(root, width=20, fg='blue', font=('Arial', 12, 'bold'))
                    self.e.grid(row=i, column=j)
                    self.e.insert(tk.END, field)
                    j += 1
                i += 1

            _module_logger.info("Add (%d) %s : %s", i, dev_name, devs_dict[dev_name])
            self.e = tk.Entry(root, width=40, fg='black', font=('Arial', 12, 'italic'))
            self.e.grid(row=i, column=0)
            self.e.insert(tk.END, dev_name)
            j = 1
            for field in devs_dict[dev_name]:
                self.e = tk.Entry(root, width=20, fg='black', font=('Arial', 12))
                self.e.grid(row=i, column=j)
                self.e.insert(tk.END, devs_dict[dev_name][field])
                j += 1
            i += 1


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


def tk_table(devs_dict: dict):
    window = tk.Tk()
    window.geometry("1300x820")
    t = Table(window, devs_dict)
    window.mainloop()


def tk_treeview(devs_dict: dict):
    # Python program to illustrate the usage of
    # treeview scrollbars using tkinter

    # Creating tkinter window
    window = tk.Tk()
    window.resizable(width=2, height=2)

    # Using treeview widget
    v_tree = ttk.Treeview(window, selectmode='browse')

    # Calling pack method w.r.to treeview
    v_tree.pack(side='right')

    # Constructing vertical scrollbar
    # with treeview
    ver_bar = ttk.Scrollbar(window, orient="vertical", command=v_tree.yview)
    hor_bar = ttk.Scrollbar(window, orient="vertical", command=v_tree.xview)

    # Calling pack method w.r.to vertical
    # scrollbar
    ver_bar.pack(side='right', fill='x')
    hor_bar.pack(side='bottom', fill='y')

    # Configuring treeview
    v_tree.configure(xscrollcommand=ver_bar.set, yscrollcommand=hor_bar.set)

    # Defining number of columns
    v_tree["columns"] = ("1", "2", "3", "4", "5", "6")

    # Defining heading
    v_tree['show'] = 'headings'

    # Assign width and anchor to columns
    v_tree.column("1", width=90, anchor='c')
    v_tree.column("2", width=90, anchor='se')
    v_tree.column("3", width=90, anchor='se')
    v_tree.column("4", width=90, anchor='se')
    v_tree.column("5", width=90, anchor='se')
    v_tree.column("6", width=90, anchor='se')

    # Assign heading names to columns
    v_tree.heading("1", text="Device Name")
    v_tree.heading("2", text="adminMode")
    v_tree.heading("3", text="versionId")
    v_tree.heading("4", text="State")
    v_tree.heading("5", text="SkaLevel")
    v_tree.heading("6", text="dev_class")

    # Inserting the items and their features to the
    # columns built
    n: int = 0
    for dev_name in devs_dict:
        dev = devs_dict[dev_name]
        dev_values = (dev_name, dev["adminMode"], dev["versionId"], dev["State"], dev["SkaLevel"], dev["dev_class"])
        v_tree.insert("", 'end', text=f"L{n}", values=dev_values)

    # Calling mainloop
    window.mainloop()


if __name__ == "__main__":
    devs: TangoctlDevicesBasic = get_devices()
    tango_devs: dict = devs.make_json()
    try:
        # tk_table(tango_devs)
        tk_treeview(tango_devs)
    except KeyboardInterrupt:
        pass
