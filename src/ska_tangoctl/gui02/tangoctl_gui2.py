"""Display data arranged in a table."""
import os
import sys
import logging
import tango
from typing import Any
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevicesBasic, TangoctlDevices
from ska_tangoctl.tango_control.tangoctl_config import TANGOCTL_CONFIG

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.INFO)


def get_devices_basic() -> TangoctlDevicesBasic:
    cfg_data: Any = TANGOCTL_CONFIG
    the_devs: TangoctlDevicesBasic = TangoctlDevicesBasic(
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
    the_devs.read_configs()
    return the_devs


def get_devices(dev_name: str) -> TangoctlDevices:
    cfg_data: Any = TANGOCTL_CONFIG
    tgo_name: str | None
    if len(dev_name) == 0:
        tgo_name = None
    else:
        tgo_name = dev_name
    the_devs: TangoctlDevices = TangoctlDevices(
        _module_logger,
        True,
        True,
        False,
        False,
        cfg_data,
        tgo_name,
        None,
        None,
        None,
        None,
        "html"
    )
    # the_devs.read_configs_all()
    the_devs.read_device_values()
    return the_devs


# class TableBasic(QTableWidget):
#     def __init__(self, parent=None):
#         super(TableBasic, self).__init__(parent)
#         self.setRowCount(0)
#
#     def read_data(self):
#         tango_host = form.edit.text()
#         os.environ["TANGO_HOST"] = tango_host
#         _module_logger.info(f"Reading data from %s", tango_host)
#         devs: TangoctlDevicesBasic
#         tango_devs: dict = {}
#         try:
#             devs = get_devices_basic()
#             tango_devs = devs.make_json()
#             _module_logger.error("Devices:> %s", tango_devs)
#         except tango.ConnectionFailed as terr:
#             err_msg = terr.args[0].desc.strip()
#             _module_logger.error("%s", err_msg)
#         except KeyboardInterrupt:
#             pass
#
#         row_count: int = len(tango_devs)
#         self.setRowCount(row_count)
#
#         res = list(tango_devs.keys())[0]
#         table_headers = list(tango_devs[res].keys())
#         table_headers.insert(0, "Device Name")
#         col_count: int = len(table_headers)
#         self.setColumnCount(col_count)
#         self.setHorizontalHeaderLabels(table_headers)
#         i: int = 0
#         for dev_name in tango_devs:
#             dev = tango_devs[dev_name]
#             item_dev_name = QTableWidgetItem(dev_name)
#             self.setItem(i, 0, item_dev_name)
#             j: int = 1
#             for field in dev:
#                 item_val = QTableWidgetItem(dev[field])
#                 self.setItem(i, j, item_val)
#                 j += 1
#             i += 1


class Table(QTableWidget):
    def __init__(self, parent=None):
        super(Table, self).__init__(parent)
        self.setRowCount(0)

    def read_data_basic(self):
        devs: TangoctlDevicesBasic
        tango_devs: dict = {}
        try:
            devs = get_devices_basic()
            tango_devs = devs.make_json()
            _module_logger.error("Devices:> %s", tango_devs)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("%s", err_msg)
        except KeyboardInterrupt:
            pass

        row_count: int = len(tango_devs)
        self.setRowCount(row_count)

        res = list(tango_devs.keys())[0]
        table_headers = list(tango_devs[res].keys())
        table_headers.insert(0, "Device Name")
        col_count: int = len(table_headers)
        self.setColumnCount(col_count)
        self.setHorizontalHeaderLabels(table_headers)
        i: int = 0
        for dev_name in tango_devs:
            dev = tango_devs[dev_name]
            item_dev_name = QTableWidgetItem(dev_name)
            self.setItem(i, 0, item_dev_name)
            j: int = 1
            for field in dev:
                item_val = QTableWidgetItem(dev[field])
                self.setItem(i, j, item_val)
                j += 1
            i += 1

    def read_data(self):
        devs: TangoctlDevices
        dev_name = form.edit_dev.text()
        tango_devs: dict = {}
        try:
            devs = get_devices(dev_name)
            tango_devs = devs.make_json()
            _module_logger.error("Devices:> %s", tango_devs)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("%s", err_msg)
        except KeyboardInterrupt:
            pass
        row_count: int = len(tango_devs)
        self.setRowCount(row_count)

        col_count: int = 7
        table_headers = ["Device", "Description", "Name", "Value", "", "", ""]
        self.setColumnCount(col_count)
        self.setHorizontalHeaderLabels(table_headers)
        row_num: int = 0
        table_fill = QTableWidgetItem("")
        # Read device name, e.g.  mid-csp/capability-fsp/0
        for dev_name in tango_devs:
            table_item = QTableWidgetItem(dev_name)
            self.setItem(row_num, 0, table_item)
            tango_item1 = tango_devs[dev_name]
            _module_logger.info("Add %d: %s %s",row_num, dev_name, type(tango_item1))
            # Read items, e.g. name, info, attributes
            for item1 in tango_item1:
                table_item = QTableWidgetItem(item1)
                self.setItem(row_num, 1, table_item)
                tango_item2 = tango_item1[item1]
                _module_logger.info("\t %d: %s %s",row_num, item1, type(tango_item2))
                if type(tango_item2) is dict:
                    for item2 in tango_item2:
                        table_item = QTableWidgetItem(item2)
                        self.setItem(row_num, 2, table_item)
                        tango_item3 = tango_item2[item2]
                        _module_logger.info("\t\t %d: %s %s",row_num, item2, type(tango_item3))
                        if type(tango_item3) is dict:
                            for item3 in tango_item3:
                                table_item = QTableWidgetItem(item3)
                                self.setItem(row_num, 3, table_item)
                                tango_item4 = tango_item3[item3]
                                _module_logger.info("\t\t\t %d: %s %s", row_num, item3, type(tango_item4))
                                if type(tango_item4) is dict:
                                    for item4 in tango_item4:
                                        table_item = QTableWidgetItem(item4)
                                        self.setItem(row_num, 4, table_item)
                                        tango_item5 = tango_item4[item4]
                                        _module_logger.info("\t\t\t\t %d: %s %s", row_num, item4, type(tango_item5))
                                        if type(tango_item5) is dict:
                                            for item5 in tango_item5:
                                                table_item = QTableWidgetItem(item5)
                                                self.setItem(row_num, 5, table_item)
                                                tango_item6 = tango_item5[item5]
                                                _module_logger.info("\t\t\t\t\t %d: %s %s", row_num, item5, type(tango_item6))
                                                if type(tango_item6) is list:
                                                    try:
                                                        item_val = ",".join(tango_item6)
                                                    except TypeError:
                                                        item_val = str(tango_item6)
                                                    table_item = QTableWidgetItem(item_val)
                                                else:
                                                    table_item = QTableWidgetItem(tango_item6)
                                                self.setItem(row_num, 6, table_item)
                                                _module_logger.info("\t\t\t\t\t\t item %d: %s", row_num, tango_item6)
                                                row_num += 1
                                                self.insertRow(row_num)
                                        elif type(tango_item5) is list:
                                            _module_logger.info("\t\t\t\t\t\t item %d: %s", row_num, tango_item5)
                                            try:
                                                item_val = ",".join(tango_item5)
                                            except TypeError:
                                                item_val = str(tango_item5)
                                            table_item = QTableWidgetItem(item_val)
                                            self.setItem(row_num, 5, table_item)
                                            row_num += 1
                                            self.insertRow(row_num)
                                        else:
                                            _module_logger.info("\t\t\t\t\t\t item %d: %s", row_num, tango_item5)
                                            table_item = QTableWidgetItem(tango_item5)
                                            self.setItem(row_num, 5, table_item)
                                            row_num += 1
                                            self.insertRow(row_num)
                                else:
                                    _module_logger.info("\t\t\t\t\t item %d: %s", row_num, tango_item4)
                                    table_item = QTableWidgetItem(str(tango_item4))
                                    self.setItem(row_num, 4, table_item)
                                    row_num += 1
                                    self.insertRow(row_num)
                        else:
                            _module_logger.info("\t\t\t item %d: %s", row_num, tango_item3)
                            table_item = QTableWidgetItem(str(tango_item3))
                            self.setItem(row_num, 3, table_item)
                            row_num += 1
                            self.insertRow(row_num)
                else:
                    _module_logger.info("\t\t item %d: %s", row_num, tango_item2)
                    table_item = QTableWidgetItem(str(tango_item2))
                    self.setItem(row_num, 2, table_item)
                    row_num += 1
                    self.insertRow(row_num)
        _module_logger.info("Created table with %d rows", self.rowCount())


class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        # Create widgets
        tango_host = os.getenv("TANGO_HOST")
        self.edit_host = QLineEdit(tango_host)
        self.edit_dev = QLineEdit("")
        self.button = QPushButton("Show Devices")
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.edit_host)
        layout.addWidget(self.edit_dev)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        self.button.clicked.connect(self.greetings)
        # Add radio buttons
        self.b1 = QRadioButton("List")
        self.b1.setChecked(True)
        self.b1.toggled.connect(lambda: self.btnstate(self.b1))
        layout.addWidget(self.b1)
        self.b2 = QRadioButton("Short")
        self.b2.toggled.connect(lambda: self.btnstate(self.b2))
        layout.addWidget(self.b2)

    def btnstate(self, b):
        if b.text() == "Button1":
            if b.isChecked():
                _module_logger.info("%s is selected", b.text())
            else:
                _module_logger.info("%s is deselected", b.text())

        if b.text() == "Button2":
            if b.isChecked():
                _module_logger.info("%s is selected", b.text())
            else:
                _module_logger.info("%s is deselected", b.text())

    def btn_selected(self) -> int:
        btn: int = 0
        if self.b1.isChecked():
            btn = 1
        elif self.b2.isChecked():
            btn = 2
        else:
            pass
        return btn

    def get_host(self) -> str:
        return self.edit_host.text()

    # Greets the user
    def greetings(self):
        tango_host = form.edit_host.text()
        os.environ["TANGO_HOST"] = tango_host
        _module_logger.info(f"Reading data from %s", tango_host)
        btn = self.btn_selected()
        if btn == 1:
            table.read_data_basic()
        elif btn == 2:
            table.read_data()
        else:
            table.read_data_basic()
        table.show()


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    table = Table()
    # table.show()
    # Run the main Qt loop
    sys.exit(app.exec())