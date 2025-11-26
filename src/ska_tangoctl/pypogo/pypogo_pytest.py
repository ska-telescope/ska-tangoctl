"""Generate test code for instrument."""

# pylint: disable=duplicate-code
# mypy: disable-error-code="attr-defined,union-attr"

import inspect
import json
import logging
import os
import sys
from typing import Any

from ska_tangoctl.pypogo.pypogo_globals import CURRENT_TIME, EOL, HOME_PATH, PYTHON_PATH


class PyPogoTestsMixin:
    """Generate code for Python tests."""

    logger: logging.Logger
    skip_tests: bool = False
    cls_name: str
    ofstream: Any
    protected_tests: dict = {}

    def read_protected_tests(self, py_file_name: str | None) -> None:
        """
        Read code for protected attribute tests.

        :param py_file_name: file name
        """
        if not os.path.isfile(py_file_name):
            self.logger.warning("File %s does not exist", py_file_name)
            return
        py_code: str = ""
        py_key: str = ""
        self.logger.info("Read code file %s", py_file_name)
        with open(py_file_name, "r", encoding="utf-8") as py_file:
            for py_line in py_file:
                py_line = py_line.rstrip()
                self.logger.debug("Read code line '%s'", py_line)
                if "# PROTECTED TEST (" in py_line and py_line[-5:] == "START":
                    # Find the index of the opening bracket
                    start_index = py_line.find('(')

                    # Find the index of the closing bracket after the opening bracket
                    end_index = py_line.find(')', start_index)

                    # Check if both brackets were found
                    if start_index != -1 and end_index != -1:
                        # Extract the substring
                        py_key = py_line[start_index + 1 : end_index]
                        # print(py_key)
                        self.logger.debug("Start PROTECTED TEST '%s'", py_key)
                elif "# PROTECTED TEST END" in py_line:
                    self.logger.debug("End PROTECTED TEST '%s' :\n%s", py_key, py_code)
                    self.protected_tests[py_key] = py_code
                    py_key = ""
                    py_code = ""
                elif py_key:
                    py_code += f'{py_line}{EOL}'
                else:
                    pass
        self.logger.debug(
            "Read PROTECTED TESTS:\n%s", json.dumps(self.protected_tests, indent=4)
        )

    def print_test_header(self, co_file: str) -> None:
        """
        Print test code.
        """
        print(
            f'"""{EOL}'
            f'Tests for Tango device {self.cls_name}.{EOL}'
            f'{EOL}'
            f'Last update {CURRENT_TIME} by {inspect.currentframe().f_code.co_name}{EOL}'
            f'See {co_file}{EOL}'
            f'"""{EOL}'
            f'{EOL}'
            f'# pylint: disable=too-many-lines{EOL}'
            f'# pylint: disable=too-many-instance-attributes{EOL}'
            f'# pylint: disable=too-many-public-methods{EOL}'
            f'# pylint: disable=duplicate-code{EOL}'
            f'# pylint: disable=line-too-long{EOL}'
            f'{EOL}'
            f'import pytest  # noqa: F401{EOL}'
            f'import tango{EOL}'
            f'from ska_control_model import AdminMode{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_test_device_name(self) -> None: # noqa: C901
        """
        Print test code for device proxy.
        """
        test_id = f"{self.cls_name}.device_name.test"
        if self.skip_tests:
            print(
                f'@pytest.mark.xfail{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_device_name(device_name: str) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test admin mode read/write.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}'
            f'    assert device_name != "", "Tango device name not set"{EOL}'
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_test_device_proxy(self) -> None: # noqa: C901
        """
        Print test code for device proxy.
        """
        test_id = f"{self.cls_name}.device_proxy.test"
        if self.skip_tests:
            print(
                f'@pytest.mark.xfail{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_device_proxy(device_name: str, device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test admin mode read/write.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}'
            f'    assert device_proxy is not None, f"No proxy for {{device_name}}"{EOL}'
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_test_admin_mode(self) -> None: # noqa: C901
        """
        Print test code for admin mode.
        """
        attrib_name = "adminMode"
        test_id = f"{self.cls_name}.{attrib_name}.test_rw"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        if self.skip_tests:
            print(
                f'@pytest.mark.xfail{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_admin_mode(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test admin mode read/write.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        else:
            print(
                f'    print("Set admin mode to ONLINE"){EOL}'
                f'    device_proxy.adminMode = AdminMode.ONLINE{EOL}'
                f'    assert device_proxy.adminMode == AdminMode.ONLINE{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def _read_write_test(self, attrib_name: str, field_type: str, attributes: dict):
        print(
            f"    # Read the {field_type} value, write it back and read it again{EOL}"
            f"    attrib_val = device_proxy.{attrib_name}{EOL}"
            f"    device_proxy.{attrib_name} = attrib_val{EOL}"
            f'    attrib_val2: {field_type} = device_proxy.{attrib_name}{EOL}'
            f'    assert attrib_val == attrib_val2{EOL}',
            file=self.ofstream,
            end="",
        )
        attribute_values: list
        try:
            attribute_value = attributes[attrib_name]["write"]["value"]
        except KeyError:
            attribute_value = '""'
        if "test_values" in attributes[attrib_name]["write"]:
            attribute_values = attributes[attrib_name]["write"]["test_values"].split(",")
        else:
            attribute_values = [attribute_value]
        # Write and read again
        for attribute_value in attribute_values:
            if str(attribute_value).replace('"', "") == "":
                self.logger.info("No value for attribute %s", attrib_name)
                continue
            if field_type == "bit":
                self.logger.info("Use int instead of bit for %s", attrib_name)
                field_type = "int"
            if field_type == "arbitrary_block":
                self.logger.info("Skip arbitrary block %s", attrib_name)
                continue
            self.logger.info("Add read/write test for %s (%s)", attrib_name, field_type)
            if field_type == "str":
                print(
                    f'    # String value{EOL}'
                    f'    print(\'Set attribute {attrib_name} to "{attribute_value}"\'){EOL}'
                    f'    device_proxy.{attrib_name} = "{attribute_value}"{EOL}'
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    assert device_proxy.{attrib_name} == "{attribute_value}"{EOL}',
                    file=self.ofstream,
                    end="",
                )
            elif field_type == "bool":
                print(
                    f'    # Boolean value{EOL}'
                    f'    print(\'Set attribute {attrib_name} to "{attribute_value}"\'){EOL}'
                    f'    device_proxy.{attrib_name} = {attribute_value}{EOL}'
                    f'    print("{attrib_name} : %s" % str(bool(device_proxy.{attrib_name}))){EOL}'
                    f'    assert device_proxy.{attrib_name} is {attribute_value}{EOL}',
                    file=self.ofstream,
                    end="",
                )
            else:
                print(
                    f'    # Value with type {field_type}{EOL}'
                    f'    device_proxy.{attrib_name} = {attribute_value}{EOL}'
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    assert device_proxy.{attrib_name} == {attribute_value}{EOL}',
                    file=self.ofstream,
                    end="",
                )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_test_rw(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_rw"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        self.logger.info("Test %s Tango attribute %s (read/write)", field_type, attrib_name)
        # Read
        if self.skip_tests:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_{attrib_name}_rw(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test {field_type} Tango attribute {attrib_name} read/write.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        else:
            self._read_write_test(attrib_name, field_type, attributes)
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end=""
        )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_test_invalid(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_invalid"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        print(
            f'@pytest.mark.xfail{EOL}'
            f'def test_{attrib_name}_invalid(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test maximum value of {field_type} Tango attribute {attrib_name}.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        elif "valid_values" in attributes[attrib_name]["write"]:
            valid_values = attributes[attrib_name]["write"]["valid_values"].split(",")
            print(
                    f'    new_value = "{valid_values[0]}{valid_values[-1]}"{EOL}'
                    f'    device_proxy.{attrib_name} = new_value{EOL}'
                    f'    assert device_proxy.{attrib_name} == new_value{EOL}'
                    f'    # PROTECTED TEST END{EOL}'
                    f'{EOL}{EOL}',
                    file=self.ofstream,
                    end="",
                )
        else:
            print(
                f'    # Nothing to see here{EOL}'
                f'    pass{EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_test_max(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_invalid"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        if "max_value" in attributes[attrib_name]["write"]:
            max_value = attributes[attrib_name]["write"]["max_value"]
            if max_value is None:
                self.logger.info("No max value for %s", attrib_name)
                return
            if field_type == "bit":
                self.logger.info("Use int instead of bit for %s", attrib_name)
                field_type = "int"
            if field_type == "arbitrary_block":
                self.logger.info("Skip arbitrary block %s", attrib_name)
                return
            self.logger.info("Add negative test for %s max (%s)", attrib_name, field_type)
            print(
                f'def test_{attrib_name}_max(device_proxy: tango.DeviceProxy) -> None:{EOL}'
                f'    """{EOL}'
                f'    Test maximum value of {field_type} Tango attribute {attrib_name}.{EOL}'
                f'{EOL}'
                f'    :param device_proxy: Tango device proxy{EOL}'
                f'    """{EOL}'
                f'    # PROTECTED TEST ({test_id}) START{EOL}',
                file=self.ofstream,
                end="",
            )
            if prot_code:
                print(f'{prot_code}', file=self.ofstream, end="")
            else:
                print(
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    new_value = {max_value} * 2{EOL}'
                    f'    device_proxy.{attrib_name} = new_value{EOL}'
                    f'    assert device_proxy.{attrib_name} != new_value{EOL}',
                    file=self.ofstream,
                    end="",
                )
            print(
                f'    # PROTECTED TEST END{EOL}'
                f'{EOL}{EOL}',
                file=self.ofstream,
                end="",
            )
        else:
            self.logger.info("No maximum value for attribute %s", attrib_name)

    # pylint: disable-next=too-many-branches,too-many-statements
    def print_attribute_test_min(  # noqa: C901
        self, attrib_name: str, field_type: str, attributes: dict
    ) -> None:
        """
        Print read/write test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        :param attributes: dictionary with attributes
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_invalid"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        if "min_value" in attributes[attrib_name]["write"]:
            min_value = attributes[attrib_name]["write"]["min_value"]
            if min_value is None:
                self.logger.info("No min value for %s", attrib_name)
                return
            if field_type == "bit":
                self.logger.info("Use int instead of bit for %s", attrib_name)
                field_type = "int"
            if field_type == "arbitrary_block":
                self.logger.info("Skip arbitrary block %s", attrib_name)
                return
            self.logger.info("Add xfail test for %s min (%s)", attrib_name, field_type)
            print(
                f'@pytest.mark.xfail{EOL}'
                f'def test_{attrib_name}_min(device_proxy: tango.DeviceProxy) -> None:{EOL}'
                f'    """{EOL}'
                f'    Test minimum value of {field_type} Tango attribute {attrib_name}.{EOL}'
                f'{EOL}'
                f'    :param device_proxy: Tango device proxy{EOL}'
                f'    """{EOL}'
                f'    # PROTECTED TEST ({test_id}) START{EOL}',
                file=self.ofstream,
                end="",
            )
            if prot_code:
                print(f'{prot_code}', file=self.ofstream, end="")
            else:
                print(
                    f'    new_value: {field_type}{EOL}'
                    f'    print("{attrib_name} : %s" % str(device_proxy.{attrib_name})){EOL}'
                    f'    test_value = {min_value}{EOL}'
                    f'    if test_value == 0:{EOL}'
                    f'        new_value = {field_type}(test_value - 1){EOL}'
                    f'    elif test_value < 0:{EOL}'
                    f'        new_value = {field_type}(test_value * 2){EOL}'
                    f'    else:{EOL}'
                    f'        new_value = {field_type}(test_value / 2){EOL}'
                    f'    device_proxy.{attrib_name} = new_value{EOL}'
                    f'    assert device_proxy.{attrib_name} == new_value{EOL}',
                    file=self.ofstream,
                    end="",
                )
            print(
                f'    # PROTECTED TEST END{EOL}'
                f'{EOL}{EOL}',
                file=self.ofstream,
                end="",
            )
        else:
            self.logger.info("No minimum value for attribute %s", attrib_name)

    def print_attribute_test_ro(self, attrib_name: str, field_type: str) -> None:
        """
        Print read-only test code for device channels.

        :param attrib_name: attribute name
        :param field_type: data type, i.e. str, bool, float, int
        """
        test_id = f"{self.cls_name}.{attrib_name}.test_ro"
        prot_code: str = ""
        if test_id in self.protected_tests:
            prot_code = self.protected_tests[test_id]
        self.logger.info("Test %s Tango attribute %s (read)", field_type, attrib_name)
        # Read
        if self.skip_tests:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'def test_{attrib_name}_ro(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test {field_type} Tango attribute {attrib_name} (read).{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({test_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        else:
            print(
                f'    attrib_val: {field_type} = device_proxy.{attrib_name}{EOL}'
                f'    print("{attrib_name} : %s" % str(attrib_val)){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_attribute_tests(self, attributes: dict, special_attributes: dict) -> None:
        """
        Print test code for device channels.

        :param attributes: dictionary with attributes
        :param special_attributes: dictionary with special attributes
        """
        self.logger.debug("Test Tango devices:\n%s", json.dumps(attributes, indent=4))
        for attrib_name in attributes:
            if attrib_name in special_attributes:
                self.logger.error("Skip special attribute %s ", attrib_name)
            elif "read" in attributes[attrib_name] and "write" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                self.print_attribute_test_rw(attrib_name, field_type, attributes)
                self.print_attribute_test_invalid(attrib_name, field_type, attributes)
                self.print_attribute_test_max(attrib_name, field_type, attributes)
                self.print_attribute_test_min(attrib_name, field_type, attributes)
            elif "read" in attributes[attrib_name]:
                field_type = attributes[attrib_name]["read"]["field_type"]
                self.print_attribute_test_ro(attrib_name, field_type)
            elif "write" in attributes[attrib_name]:
                self.print_command_test(attrib_name, attributes)
            else:
                self.logger.error("Attribute %s has no read or write values", attrib_name)

    def print_command_test(self, command_name: str, cmds: dict, skip_test: bool) -> None:
        """
        Print write-only test code for device channels.

        :param command_name: attribute name
        :param cmds: dictionary with attributes
        :param skip_test: skip this test
        """
        cmd_id = f"{self.cls_name}.{command_name}.command"
        prot_code: str = ""
        if cmd_id in self.protected_tests:
            prot_code = self.protected_tests[cmd_id]
        self.logger.info("Test Tango command %s (write-only)", command_name)
        if skip_test:
            print(
                f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                file=self.ofstream,
                end="",
            )
        elif "pytest" in cmds[command_name]:
            if skip_test or cmds[command_name] == "skip":
                print(
                    f'@pytest.mark.skip(reason="can not be tested at this stage"){EOL}',
                    file=self.ofstream,
                    end="",
                )
        else:
            pass
        # Write command
        print(
            f'def test_cmd_{command_name}(device_proxy: tango.DeviceProxy) -> None:{EOL}'
            f'    """{EOL}'
            f'    Test Tango command {command_name}.{EOL}'
            f'{EOL}'
            f'    :param device_proxy: Tango device proxy{EOL}'
            f'    """{EOL}'
            f'    # PROTECTED TEST ({cmd_id}) START{EOL}',
            file=self.ofstream,
            end="",
        )
        if prot_code:
            print(f'{prot_code}', file=self.ofstream, end="")
        else:
            print(
                f'    print("Send command {command_name}"){EOL}'
                f'    device_proxy.{command_name}(){EOL}',
                file=self.ofstream,
                end="",
            )
        print(
            f'    # PROTECTED TEST END{EOL}'
            f'{EOL}{EOL}',
            file=self.ofstream,
            end="",
        )

    def print_commands_tests(self, cmds: dict, skip_tests: bool) -> None:
        """
        Write test code for Python commands.

        :param cmds: dictionary with commands
        :param skip_tests: skip these tests
        """
        for cmd_name in cmds:
            self.print_command_test(cmd_name, cmds, skip_tests)

    def print_python_tests(
        self,
        file_path: str | None,
        skip_tests: bool,
        special_attributes: dict,
    ) -> None:
        """
        Write code for device tests.

        :param file_path: output file e.g. "test_oscilloscope_device.py"
        :param skip_tests: flag all tests to be skipped
        :param special_attributes: attributes for which test code will not be geneated
        """
        dev_attributes: dict = self.read_xml_attributes()
        dev_commands: dict = self.read_xml_commands()
        self.skip_tests = skip_tests
        co_file = (
            inspect.currentframe()
            .f_code.co_filename.replace(HOME_PATH, "")
            .replace(PYTHON_PATH, "src")
        )
        if file_path is not None:
            self.logger.info("Write %s test file %s", self.cls_name, file_path)
            # pylint: disable-next=consider-using-with
            self.ofstream = open(file_path, "w+", encoding="utf-8")
        else:
            self.logger.info("Write %s tests", self.cls_name)
            self.ofstream = sys.stdout
        self.print_test_header(co_file)
        self.print_test_device_name()
        self.print_test_device_proxy()
        self.print_test_admin_mode()
        self.print_attribute_tests(dev_attributes, special_attributes)
        self.skip_tests = True
        self.print_commands_tests(dev_commands, self.skip_tests)
        if file_path is not None:
            self.ofstream.close()
            self.format_with_black(file_path)
