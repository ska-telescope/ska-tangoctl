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
    """
    Use treeview scrollbars with tkinter.

    :param devs_dict: dictionary with device names as keys
    """

    # Create window
    window = tk.Tk()
    window.resizable(width=2, height=2)

    # Use treeview widget
    v_tree = ttk.Treeview(window, selectmode='browse')

    # Calling pack method w.r.to treeview
    v_tree.pack(side='right')

    # Construct vertical scrollbar with treeview
    ver_bar = ttk.Scrollbar(window, orient="vertical", command=v_tree.yview)
    hor_bar = ttk.Scrollbar(window, orient="vertical", command=v_tree.xview)

    # Call pack method w.r.to vertical scrollbar
    ver_bar.pack(side='right', fill='x')
    hor_bar.pack(side='bottom', fill='y')

    # Configure treeview
    v_tree.configure(xscrollcommand=ver_bar.set, yscrollcommand=hor_bar.set)

    # Define number of columns
    v_tree["columns"] = ("1", "2", "3", "4", "5", "6")

    # Define heading
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

    # Insert items and their features to columns
    n: int = 0
    for dev_name in devs_dict:
        dev = devs_dict[dev_name]
        dev_values = (dev_name, dev["adminMode"], dev["versionId"], dev["State"], dev["SkaLevel"], dev["dev_class"])
        v_tree.insert("", 'end', text=f"L{n}", values=dev_values)

    # Call mainloop
    window.mainloop()


def tk_foo(devs_dict: dict):
    sh_barroot = tk.Tk()
    sh_barcontainer = ttk.Frame(sh_barroot)
    sh_barcanvas = tk.Canvas(sh_barcontainer, width=1500, height=800, background='grey')
    sh_barvscrollbar = ttk.Scrollbar(sh_barcontainer, orient="vertical", command=sh_barcanvas.yview)
    sh_barhscrollbar = ttk.Scrollbar(sh_barcontainer, orient="horizontal", command=sh_barcanvas.xview)
    sh_barscrollable_frame = ttk.Frame(sh_barcanvas)

    sh_barscrollable_frame.bind(
        "<Configure>",
        lambda e: sh_barcanvas.configure(
            scrollregion=sh_barcanvas.bbox("all")
        )
    )

    sh_barcanvas.create_window(0, 0, window=sh_barscrollable_frame, anchor="nw")
    sh_barcanvas.configure(yscrollcommand=sh_barvscrollbar.set)
    sh_barcanvas.configure(xscrollcommand=sh_barhscrollbar.set)

    res = list(devs_dict.keys())[0]
    table_headers = list(devs_dict[res].keys())
    table_headers.insert(0, "Device Name")
    _module_logger.info("Headers: %s", table_headers)

    j: int = 0
    for table_header in table_headers:
        wid: int
        if not j:
            wid = 50
        else:
            wid = 25
        current_entry = tk.Entry(sh_barscrollable_frame, width=wid, justify='left')
        current_entry.insert(0, table_header)
        current_entry.configure(state='disabled', disabledforeground='blue')
        current_entry.grid(row=0, column=j)
        j += 1

    i: int = 1
    for dev_name in devs_dict:
        j = 0
        dev = devs_dict[dev_name]
        current_entry = tk.Entry(sh_barscrollable_frame, width=50, justify='left')
        current_entry.insert(0, dev_name)
        current_entry.configure(state='disabled', disabledforeground='blue')
        current_entry.grid(row=i, column=j)
        j += 1
        for field in dev:
            current_entry = tk.Entry(sh_barscrollable_frame, width=25, justify='left')
            current_entry.insert(0, dev[field])
            current_entry.configure(state='disabled', disabledforeground='blue')
            current_entry.grid(row=i, column=j)
            j += 1
        i += 1

    sh_barcontainer.grid()
    sh_barcanvas.grid()
    sh_barvscrollbar.grid(row=0, column=1, sticky="ns")
    sh_barhscrollbar.grid(row=1, column=0, sticky="ew")

    sh_barroot.mainloop()


if __name__ == "__main__":
    devs: TangoctlDevicesBasic = get_devices()
    tango_devs: dict = devs.make_json()
    try:
        # tk_table(tango_devs)
        # tk_treeview(tango_devs)
        tk_foo(tango_devs)
    except KeyboardInterrupt:
        pass
