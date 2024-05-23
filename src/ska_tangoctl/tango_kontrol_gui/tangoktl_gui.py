"""GUI for tangoctl."""
import json
import logging
import os
import tkinter as tk
from typing import Any

from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic
from ska_tangoctl.tango_control.read_tango_device import TangoctlDeviceBasic
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


def main():
    devs: TangoctlDevicesBasic = get_devices()
    devs_dict: dict = devs.make_json()

    # create a root window.
    window = tk.Tk()
    window.geometry("1300x820")

    # sv_bar = tk.Scrollbar(window)
    # sv_bar.pack(side=tk.RIGHT, fill="y")
    #
    # sh_bar = tk.Scrollbar(window, orient=tk.HORIZONTAL)
    # sh_bar.pack(side=tk.BOTTOM, fill="x")
    #
    # t_box = tk.Text(
    #     window,
    #     height=500,
    #     width=500,
    #     yscrollcommand=sv_bar.set,
    #     xscrollcommand=sh_bar.set,
    #     wrap="none"
    # )
    #
    # t_box.pack(expand=0, fill=tk.BOTH)
    #
    # # t_box.insert(tk.END, Num_Horizontal)
    # # dev_txt = os.getenv("TANGO_HOST")
    # dev_txt = json.dumps(devsdict, indent=4)
    # t_box.insert(tk.END, dev_txt)
    #

    t = Table(window, devs_dict)
    # sh_bar.config(command=t_box.xview)
    # sv_bar.config(command=t_box.yview)
    window.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
