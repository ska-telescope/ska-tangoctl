#!/usr/bin/python
"""Display data arranged in a table."""
# type: ignore[import-untyped]

import logging
import os
import sys
from typing import Any

import tango
from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ska_tangoctl.tango_control.disp_action import DispAction
from ska_tangoctl.tango_control.read_tango_devices import TangoctlDevices, TangoctlDevicesBasic
from ska_tangoctl.tango_kontrol.get_namespaces import get_namespaces_list
from ska_tangoctl.tango_kontrol.tangoktl_config import TANGOKTL_CONFIG

logging.basicConfig(level=logging.WARNING)
_module_logger = logging.getLogger("tango_control")
_module_logger.setLevel(logging.INFO)


def get_devices_basic() -> TangoctlDevicesBasic:
    """
    Read basic devices.

    :return: class instance
    """
    cfg_data: Any = TANGOKTL_CONFIG
    the_devs: TangoctlDevicesBasic = TangoctlDevicesBasic(
        _module_logger,
        True,
        True,
        True,
        {},
        cfg_data,
        None,
        False,
        False,
        True,
        False,
        True,
        DispAction(DispAction.TANGOCTL_HTML),
    )
    return the_devs


def get_devices(
    dev_name: str | None,
    attrib_name: str | None,
    cmd_name: str | None,
    prop_name: str | None,
) -> TangoctlDevices:
    """
    Read devices.

    :param dev_name: device name
    :param attrib_name: attribute name
    :param cmd_name: command name
    :param prop_name: property name
    :return: class instance
    """
    cfg_data: Any = TANGOKTL_CONFIG
    tgo_name: str | None
    if dev_name is None:
        tgo_name = None
    elif len(dev_name) == 0:
        tgo_name = None
    else:
        tgo_name = dev_name
    the_devs: TangoctlDevices = TangoctlDevices(
        _module_logger,
        True,
        True,
        True,
        {},
        cfg_data,
        tgo_name,
        True,
        False,
        False,
        True,
        False,
        DispAction(DispAction.TANGOCTL_HTML),
        None,
        None,
        attrib_name,
        cmd_name,
        prop_name,
    )
    return the_devs


class OkDialog(QDialog):
    """Dialog with OK button."""

    def __init__(self, headng: str, msg: str, parent: QWidget | None = None):
        """
        Display the button.

        :param headng: Heading of the button
        :param msg: Message
        :param parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle(headng)

        qbtn: QDialogButtonBox.StandardButton = QDialogButtonBox.StandardButton.Ok

        self.buttonBox: QDialogButtonBox = QDialogButtonBox(qbtn)
        self.buttonBox.accepted.connect(self.accept)

        self.layout: QVBoxLayout = QVBoxLayout()  # type: ignore[assignment]
        message: QLabel = QLabel(msg)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class OkCancelDialog(QDialog):
    """Dialog with OK and Cancel buttons."""

    def __init__(self, headng: str, msg: str, parent: QWidget | None = None):
        """
        Display the dialog.

        :param headng: Heading of the button
        :param msg: Message
        :param parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle(headng)

        qbtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QDialogButtonBox(qbtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout: QVBoxLayout = QVBoxLayout()  # type: ignore[assignment]
        message: QLabel = QLabel(msg)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class TabDialog(QDialog):
    """Set up tabs for the app."""

    def __init__(self, parent: QWidget | None = None):
        """
        Display the dialog.

        :param parent: Parent widget
        """
        super().__init__(parent)

        tab_widget: QTabWidget = QTabWidget()
        tab_widget.addTab(HostTab(self), "Tango Host")
        tab_widget.addTab(NamespaceTab(self), "K8S Namespaces")
        tab_widget.addTab(DeviceTab(self), "Tango Devices")
        tab_widget.addTab(AttributeTab(self), "Tango Attributes")
        tab_widget.addTab(CommandTab(self), "Tango Commands")
        tab_widget.addTab(PropertyTab(self), "Tango Properties")

        main_layout: QVBoxLayout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
        self.setWindowTitle("Tab Dialog")
        self.setStatusTip("OK")


class Table(QTableWidget):
    """Create new window with table."""

    def __init__(self, parent: Any = None):
        """
        Table creation.

        :param parent: parent window
        """
        super(Table, self).__init__(parent)
        self.setRowCount(0)

    def read_data_basic(self) -> None:
        """Read basic data only."""
        devs: TangoctlDevicesBasic
        tango_devs: dict = {}
        dlg: OkDialog
        try:
            # pylint: disable-next=possibly-used-before-assignment
            window.setStatusTip("Read Tango devices")
            devs = get_devices_basic()
            devs.read_configs()
            tango_devs = devs.make_json()
            _module_logger.error("Devices:> %s", tango_devs)
        except tango.ConnectionFailed as terr:
            err_msg: str = terr.args[0].desc.strip()
            _module_logger.error("%s", err_msg)
            window.setStatusTip("Error")
            dlg = OkDialog("Connection Failed", err_msg, self)
            dlg.exec()
        except KeyboardInterrupt:
            pass

        row_count: int = len(tango_devs)
        self.setRowCount(row_count)

        if not tango_devs:
            window.setStatusTip("Error")
            dlg = OkDialog("Tango Error", "Could not read Tango devices", self)
            dlg.exec()
            return

        res: str = list(tango_devs.keys())[0]
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

    def read_data(self, dev_name: str | None = None) -> dict:
        """
        Read all the data.

        :param dev_name: name of the device in triplet form
        :return: disctionary with matching devices
        """
        devs: TangoctlDevices
        tango_devs: dict = {}
        try:
            window.setStatusTip("Read Tango device")
            _module_logger.info("Read device: %s", dev_name)
            devs = get_devices(dev_name, None, None, None)
            devs.read_device_values()
            tango_devs = devs.make_json()
            _module_logger.error("Devices:> %s", tango_devs)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("%s", err_msg)
            window.setStatusTip("Error")
            dlg = OkDialog("Connection Failed", err_msg, self)
            dlg.exec()
        except KeyboardInterrupt:
            pass
        return tango_devs

    def read_attributes(self, attr_name: str | None = None) -> dict:
        """
        Read all the data.

        :param attr_name: name of the attribute
        :return: disctionary with matching devices
        """
        devs: TangoctlDevices
        tango_devs: dict = {}
        try:
            window.setStatusTip("Read attributes")
            devs = get_devices(None, attr_name, None, None)
            devs.read_device_values()
            tango_devs = devs.make_json()
            _module_logger.error("Devices:> %s", tango_devs)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("%s", err_msg)
            window.setStatusTip("Error")
            dlg = OkDialog("Connection Failed", err_msg, self)
            dlg.exec()
        except KeyboardInterrupt:
            pass
        row_count: int = len(tango_devs)
        self.setRowCount(row_count)
        return tango_devs

    def read_commands(self, cmd_name: str) -> dict:
        """
        Read all the data.

        :param cmd_name: name of the command
        :return: disctionary with matching devices
        """
        devs: TangoctlDevices
        tango_devs: dict = {}
        try:
            window.setStatusTip("Read commands")
            devs = get_devices(None, None, cmd_name, None)
            devs.read_device_values()
            tango_devs = devs.make_json()
            _module_logger.error("Devices:> %s", tango_devs)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("%s", err_msg)
            window.setStatusTip("Error")
            dlg = OkDialog("Connection Failed", err_msg, self)
            dlg.exec()
        except KeyboardInterrupt:
            pass
        row_count: int = len(tango_devs)
        self.setRowCount(row_count)
        return tango_devs

    def read_properties(self, prop_name: str) -> dict:
        """
        Read all the data.

        :param prop_name: name of the property
        :return: disctionary with matching devices
        """
        devs: TangoctlDevices
        tango_devs: dict = {}
        try:
            window.setStatusTip("Read properties")
            devs = get_devices(None, None, None, prop_name)
            devs.read_device_values()
            tango_devs = devs.make_json()
            _module_logger.error("Devices:> %s", tango_devs)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("%s", err_msg)
            window.setStatusTip("Error")
            # pylint: disable-next=possibly-used-before-assignment
            dlg.setStatusTip("Connection Failed")
            dlg.exec()
        except KeyboardInterrupt:
            pass
        row_count: int = len(tango_devs)
        self.setRowCount(row_count)
        return tango_devs

    def write_table(self, tango_devs: dict) -> None:  # noqa: C901
        """
        Write all the data.

        :param tango_devs: dictionary with matching devices
        """
        row_count: int = len(tango_devs)
        self.setRowCount(row_count)

        if not tango_devs:
            window.setStatusTip("Error")
            dlg = OkDialog("Write table data", "No data", self)
            dlg.exec()
            return

        window.setStatusTip("Write table")
        col_count: int = 7
        table_headers = ["Device", "Description", "Name", "Value", "", "", ""]
        self.setColumnCount(col_count)
        self.setHorizontalHeaderLabels(table_headers)
        row_num: int = 0
        # pylint: disable-next=unused-variable
        table_fill = QTableWidgetItem("")  # noqa: F841
        # Read device name, e.g.  mid-csp/capability-fsp/0
        for dev_name in tango_devs:
            table_item = QTableWidgetItem(dev_name)
            self.setItem(row_num, 0, table_item)
            tango_item1 = tango_devs[dev_name]
            _module_logger.info("Add %d: %s %s", row_num, dev_name, type(tango_item1))
            # Read items, e.g. name, info, attributes
            for item1 in tango_item1:
                table_item = QTableWidgetItem(item1)
                self.setItem(row_num, 1, table_item)
                tango_item2 = tango_item1[item1]
                _module_logger.info("\t %d: %s %s", row_num, item1, type(tango_item2))
                if type(tango_item2) is dict:
                    for item2 in tango_item2:
                        table_item = QTableWidgetItem(item2)
                        self.setItem(row_num, 2, table_item)
                        tango_item3 = tango_item2[item2]
                        _module_logger.info("\t\t %d: %s %s", row_num, item2, type(tango_item3))
                        if type(tango_item3) is dict:
                            for item3 in tango_item3:
                                table_item = QTableWidgetItem(item3)
                                self.setItem(row_num, 3, table_item)
                                tango_item4 = tango_item3[item3]
                                _module_logger.info(
                                    "\t\t\t %d: %s %s", row_num, item3, type(tango_item4)
                                )
                                if type(tango_item4) is dict:
                                    for item4 in tango_item4:
                                        table_item = QTableWidgetItem(item4)
                                        self.setItem(row_num, 4, table_item)
                                        tango_item5 = tango_item4[item4]
                                        _module_logger.info(
                                            "\t\t\t\t %d: %s %s", row_num, item4, type(tango_item5)
                                        )
                                        if type(tango_item5) is dict:
                                            for item5 in tango_item5:
                                                table_item = QTableWidgetItem(item5)
                                                self.setItem(row_num, 5, table_item)
                                                tango_item6 = tango_item5[item5]
                                                _module_logger.info(
                                                    "\t\t\t\t\t %d: %s %s",
                                                    row_num,
                                                    item5,
                                                    type(tango_item6),
                                                )
                                                if type(tango_item6) is list:
                                                    try:
                                                        item_val = ",".join(tango_item6)
                                                    except TypeError:
                                                        item_val = str(tango_item6)
                                                    table_item = QTableWidgetItem(item_val)
                                                else:
                                                    table_item = QTableWidgetItem(tango_item6)
                                                self.setItem(row_num, 6, table_item)
                                                _module_logger.info(
                                                    "\t\t\t\t\t\t item %d: %s",
                                                    row_num,
                                                    tango_item6,
                                                )
                                                row_num += 1
                                                self.insertRow(row_num)
                                        elif type(tango_item5) is list:
                                            _module_logger.info(
                                                "\t\t\t\t\t\t item %d: %s", row_num, tango_item5
                                            )
                                            try:
                                                item_val = ",".join(tango_item5)
                                            except TypeError:
                                                item_val = str(tango_item5)
                                            table_item = QTableWidgetItem(item_val)
                                            self.setItem(row_num, 5, table_item)
                                            row_num += 1
                                            self.insertRow(row_num)
                                        else:
                                            _module_logger.info(
                                                "\t\t\t\t\t\t item %d: %s", row_num, tango_item5
                                            )
                                            table_item = QTableWidgetItem(tango_item5)
                                            self.setItem(row_num, 5, table_item)
                                            row_num += 1
                                            self.insertRow(row_num)
                                else:
                                    _module_logger.info(
                                        "\t\t\t\t\t item %d: %s", row_num, tango_item4
                                    )
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
        self.setFixedWidth(1800)
        self.setFixedHeight(600)
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 200)
        self.setColumnWidth(3, 400)
        self.setColumnWidth(4, 400)
        self.setColumnWidth(5, 400)
        for col in range(self.columnCount()):
            _module_logger.info("Column %d width: %d", col, self.columnWidth(col))


class HostTab(QDialog):
    """Tab where host nme is filled in."""

    def __init__(self, parent: Any = None):
        """
        Create host tab.

        :param parent: parent window
        """
        super(HostTab, self).__init__(parent)
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

    def focusChanged(self) -> None:
        """Do this when the focus changes."""
        # TODO it never happens
        _module_logger.info("Focus changed to host tab")
        return

    def btnstate(self, b: QRadioButton) -> None:
        """
        Read button state.

        :param b: radio button widget
        """
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
        """
        Read button state.

        :return: 1 if button 1 is checked, 2 if button 2 is checked
        """
        btn: int = 0
        if self.b1.isChecked():
            btn = 1
        elif self.b2.isChecked():
            btn = 2
        else:
            pass
        return btn

    def get_host(self) -> str:
        """
        Read host name.

        :return: host name from edit box
        """
        return self.edit_host.text()

    def greetings(self) -> None:
        """Read the data."""
        tango_host = self.edit_host.text()
        os.environ["TANGO_HOST"] = tango_host
        _module_logger.info("Reading data from %s", tango_host)
        btn = self.btn_selected()
        if btn == 1:
            # pylint: disable-next=possibly-used-before-assignment
            table.read_data_basic()
        elif btn == 2:
            devs = table.read_data()
            table.write_table(devs)
        else:
            table.read_data_basic()
        table.show()


class NamespaceTab(QDialog):
    """Tab to select namespace."""

    def __init__(self, parent: QWidget | None = None):
        """
        Create namespace tab.

        :param parent: parent window
        """
        # pylint: disable-next=unused-variable
        super(NamespaceTab, self).__init__(parent)
        # Create widgets
        self.combo = QComboBox(self)
        self.button = QPushButton("Show Devices")
        self.button.move(100, 100)
        self.button.setFixedWidth(200)
        self.combo.addItem("")
        # pylint: disable-next=possibly-used-before-assignment
        for ns in ns_list:
            self.combo.addItem(ns)
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.combo)
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

    def focusChanged(self) -> None:
        """Do this when focus changes."""
        # TODO does not work
        _module_logger.info("Focus changed to namespace tab")
        return

    def btnstate(self, b: QRadioButton) -> None:
        """
        Read button state.

        :param b: radio button widget
        """
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
        """
        Read button state.

        :return: 1 if button 1 is checked, 2 if button 2 is checked
        """
        btn: int = 0
        if self.b1.isChecked():
            btn = 1
        elif self.b2.isChecked():
            btn = 2
        else:
            pass
        return btn

    # Greet the user
    def greetings(self) -> None:
        """Do the thing for the user."""
        ns: str = self.combo.currentText()
        tango_host: str = (
            TANGOKTL_CONFIG["databaseds_name"]
            + "."
            + ns
            + "."
            + TANGOKTL_CONFIG["top_level_domain"]
            + ":10000"
        )
        os.environ["TANGO_HOST"] = tango_host
        _module_logger.info("Reading data from %s", tango_host)
        btn: int = self.btn_selected()
        if btn == 1:
            table.read_data_basic()
        elif btn == 2:
            devs = table.read_data()
            table.write_table(devs)
        else:
            table.read_data_basic()
        table.show()


class DeviceTab(QDialog):
    """Tab to select a device."""

    def __init__(self, parent: QWidget | None = None):
        """
        Create device tab.

        :param parent: parent window
        """
        super(DeviceTab, self).__init__(parent)
        # Create widgets
        self.combo: QComboBox = QComboBox(self)
        self.combo.currentIndexChanged.connect(self.change_namespace)
        self.combo2: QComboBox = QComboBox(self)
        self.combo2.addItem("")
        self.button: QPushButton = QPushButton("Show Device")
        self.combo.addItem("")
        for ns in ns_list:
            self.combo.addItem(ns)
        # Create layout and add widgets
        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.combo2)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        self.button.clicked.connect(self.greetings)

    def focusChanged(self) -> None:
        """Do this when focus changes."""
        # TODO does not work
        _module_logger.info("Change focus on attribute tab")
        return

    def change_namespace(self, e: QEvent) -> None:
        """
        React to change of namespace.

        :param e: QT event thing
        """
        devs: Any
        cfg_data: Any = TANGOKTL_CONFIG
        ns: str = self.combo.currentText()
        if ns == "":
            return
        _module_logger.info("Namespace for attributes changed to %s", ns)
        tango_host: str = (
            TANGOKTL_CONFIG["databaseds_name"]
            + "."
            + ns
            + "."
            + TANGOKTL_CONFIG["top_level_domain"]
            + ":10000"
        )
        os.environ["TANGO_HOST"] = tango_host
        try:
            devs = TangoctlDevicesBasic(
                _module_logger,
                True,
                True,
                True,
                {},
                cfg_data,
                None,
                True,
                False,
                True,
                False,
                True,
                DispAction(DispAction.TANGOCTL_HTML),
            )
            for dev_name in devs.devices:
                self.combo2.addItem(dev_name)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("Connection failed: %s", err_msg)
            window.setStatusTip("Error")
            dlg = OkDialog("Connection Failed", err_msg, self)
            dlg.exec()
        return

    def greetings(self) -> None:
        """Greets the user."""
        window.setStatusTip("Device")
        ns: str = self.combo.currentText()
        tango_host: str = (
            TANGOKTL_CONFIG["databaseds_name"]
            + "."
            + ns
            + "."
            + TANGOKTL_CONFIG["top_level_domain"]
            + ":10000"
        )
        os.environ["TANGO_HOST"] = tango_host
        dev_name: str = self.combo2.currentText()
        _module_logger.info("Reading data for %s from %s", dev_name, tango_host)
        devs: dict = table.read_data(dev_name)
        table.write_table(devs)
        table.show()


class AttributeTab(QDialog):
    """Tab to select an attribute."""

    def __init__(self, parent: QWidget | None = None):
        """
        Create attribute tab.

        :param parent: parent window
        """
        super(AttributeTab, self).__init__(parent)
        # Create widgets
        self.combo: QComboBox = QComboBox(self)
        self.combo.currentIndexChanged.connect(self.change_namespace)
        self.combo2: QComboBox = QComboBox(self)
        self.combo2.addItem("")
        self.button: QPushButton = QPushButton("Show Attribute")
        self.combo.addItem("")
        for ns in ns_list:
            self.combo.addItem(ns)
        # Create layout and add widgets
        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.combo2)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        self.button.clicked.connect(self.greetings)

    def focusChanged(self) -> None:
        """Do this when focus changes."""
        # TODO does not work
        _module_logger.info("Change focus on attribute tab")
        return

    def change_namespace(self, e: QEvent) -> None:
        """
        React to change of namespace.

        :param e: QT event thing
        """
        cfg_data: Any = TANGOKTL_CONFIG
        ns: str = self.combo.currentText()
        if ns == "":
            return
        _module_logger.info("Namespace for attributes changed to %s", ns)
        # TODO this only works for context za-itf-k8s-master01-k8s
        tango_host: str = "tango-databaseds." + ns + ".svc.miditf.internal.skao.int:10000"
        os.environ["TANGO_HOST"] = tango_host
        try:
            devs = TangoctlDevicesBasic(
                _module_logger,
                True,
                True,
                True,
                {},
                cfg_data,
                None,
                True,
                False,
                False,
                True,
                True,
                DispAction(DispAction.TANGOCTL_HTML),
            )
            the_attribs = devs.read_attribute_names()
            for attr_name in the_attribs:
                self.combo2.addItem(attr_name)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("Connection failed: %s", err_msg)
            dlg = OkCancelDialog("Connection Failed", err_msg, self)
            if dlg.exec():
                _module_logger.info("Success")
            else:
                _module_logger.info("Cancel")
        return

    def greetings(self) -> None:
        """Read and display the attributes."""
        window.setStatusTip("Attributes")
        ns: str = self.combo.currentText()
        # TODO this only works for context za-itf-k8s-master01-k8s
        tango_host: str = "tango-databaseds." + ns + ".svc.miditf.internal.skao.int:10000"
        os.environ["TANGO_HOST"] = tango_host
        attr_name: str = self.combo2.currentText()
        _module_logger.info("Reading data for attribute %s from %s", attr_name, tango_host)
        devs: dict = table.read_attributes(attr_name)
        table.write_table(devs)
        table.show()


class CommandTab(QDialog):
    """Tab to select a command."""

    def __init__(self, parent: QWidget | None = None):
        """
        Create command tab.

        :param parent: parent window
        """
        super(CommandTab, self).__init__(parent)
        # Create widgets
        self.combo: QComboBox = QComboBox(self)
        self.combo.currentIndexChanged.connect(self.change_namespace)
        self.combo2 = QComboBox(self)
        self.combo2.addItem("")
        self.button: QPushButton = QPushButton("Show Command")
        self.combo.addItem("")
        for ns in ns_list:
            self.combo.addItem(ns)
        # Create layout and add widgets
        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.combo2)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        self.button.clicked.connect(self.greetings)

    def focusChanged(self) -> None:
        """Do this when focus changes."""
        # TODO does not work
        _module_logger.info("Change focus on command tab")
        return

    def change_namespace(self, e: QEvent) -> None:
        """
        React to change of namespace.

        :param e: QT event thing
        """
        cfg_data: Any = TANGOKTL_CONFIG
        ns: str = self.combo.currentText()
        if ns == "":
            return
        _module_logger.info("Namespace for commands changed to %s", ns)
        # TODO this only works for context za-itf-k8s-master01-k8s
        tango_host: str = "tango-databaseds." + ns + ".svc.miditf.internal.skao.int:10000"
        os.environ["TANGO_HOST"] = tango_host
        try:
            devs = TangoctlDevicesBasic(
                _module_logger,
                True,
                True,
                True,
                {},
                cfg_data,
                None,
                True,
                False,
                False,
                True,
                True,
                DispAction(DispAction.TANGOCTL_HTML),
            )
            the_commands = devs.read_command_names()
            for cmd_name in the_commands:
                self.combo2.addItem(cmd_name)
        except tango.ConnectionFailed as terr:
            err_msg: str = terr.args[0].desc.strip()
            _module_logger.error("Connection failed: %s", err_msg)
            window.setStatusTip("Error")
            dlg = OkDialog("Connection Failed", err_msg, self)
            dlg.exec()
        return

    def greetings(self) -> None:
        """Read and display the commands."""
        window.setStatusTip("Commands")
        ns: str = self.combo.currentText()
        # TODO this only works for context za-itf-k8s-master01-k8s
        tango_host: str = "tango-databaseds." + ns + ".svc.miditf.internal.skao.int:10000"
        os.environ["TANGO_HOST"] = tango_host
        cmd_name: str = self.combo2.currentText()
        _module_logger.info("Reading data for attribute %s from %s", cmd_name, tango_host)
        devs: dict = table.read_commands(cmd_name)
        table.write_table(devs)
        table.show()


class PropertyTab(QDialog):
    """Tab to select a property."""

    def __init__(self, parent: QWidget | None = None):
        """
        Create property tab.

        :param parent: parent window
        """
        super(PropertyTab, self).__init__(parent)
        # Create widgets
        self.combo: QComboBox = QComboBox(self)
        self.combo.currentIndexChanged.connect(self.change_namespace)
        self.combo2: QComboBox = QComboBox(self)
        self.combo2.addItem("")
        self.button: QPushButton = QPushButton("Show Property")
        self.combo.addItem("")
        ns: str
        for ns in ns_list:
            self.combo.addItem(ns)
        # Create layout and add widgets
        layout: QVBoxLayout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.combo2)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        self.button.clicked.connect(self.greetings)

    def focusChanged(self) -> None:
        """Do this when focus changes."""
        # TODO nothing to see here
        _module_logger.info("Change focus on property tab")
        return

    def change_namespace(self, e: QEvent) -> None:
        """
        React to change of namespace.

        :param e: QT event thing
        """
        cfg_data: Any = TANGOKTL_CONFIG
        ns: str = self.combo.currentText()
        if ns == "":
            return
        _module_logger.info("Namespace for properties changed to %s", ns)
        # TODO this only works for context za-itf-k8s-master01-k8s
        tango_host: str = "tango-databaseds." + ns + ".svc.miditf.internal.skao.int:10000"
        os.environ["TANGO_HOST"] = tango_host
        devs: TangoctlDevicesBasic
        try:
            devs = TangoctlDevicesBasic(
                _module_logger,
                True,
                True,
                True,
                {},
                cfg_data,
                None,
                True,
                True,
                False,
                False,
                True,
                DispAction(DispAction.TANGOCTL_HTML),
            )
            the_properties = devs.read_property_names()
            for prop_name in the_properties:
                self.combo2.addItem(prop_name)
        except tango.ConnectionFailed as terr:
            err_msg = terr.args[0].desc.strip()
            _module_logger.error("Connection failed: %s", err_msg)
            window.setStatusTip("Error")
            dlg = OkDialog("Connection Failed", err_msg, self)
            dlg.exec()
        return

    def greetings(self) -> None:
        """Read and display the properties."""
        window.setStatusTip("Properties")
        ns = self.combo.currentText()
        # TODO this only works for context za-itf-k8s-master01-k8s
        tango_host = "tango-databaseds." + ns + ".svc.miditf.internal.skao.int:10000"
        os.environ["TANGO_HOST"] = tango_host
        prop_name = self.combo2.currentText()
        _module_logger.info("Reading data for command %s from %s", prop_name, tango_host)
        cmds = table.read_properties(prop_name)
        table.write_table(cmds)
        table.show()


class MainWindow(QMainWindow):
    """This is where it begins."""

    def __init__(self) -> None:
        """Start here."""
        super().__init__()

        self.setWindowTitle("Tango Control")
        self.setStatusBar(QStatusBar(self))
        self.setStatusTip("OK")

        # Create the tabs
        tab_dialog = TabDialog()
        tab_dialog.setFixedWidth(800)

        self.setCentralWidget(tab_dialog)


if __name__ == "__main__":
    # Create the Qt Application
    app = QApplication(sys.argv)

    _ctx_name, ns_list = get_namespaces_list(_module_logger, None)

    # Create the table
    table = Table()

    window = MainWindow()

    window.show()

    if not ns_list:
        window.setStatusTip("Error")
        dlg = OkDialog("Kubernetes Error", "Could not read namespaces")
        dlg.exec()

    # Run the main Qt loop
    sys.exit(app.exec())
